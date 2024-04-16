/*
 *    Copyright 2023 The ChampSim Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "cache.h"

#include <algorithm>
#include <iterator>

#include "champsim.h"
#include "champsim_constants.h"
#include "util.h"
#include "vmem.h"
// #include "cxl_memory.h"

#include <chrono>

#ifndef SANITY_CHECK
#define NDEBUG
#endif

extern VirtualMemory vmem;
extern uint8_t warmup_complete[NUM_CPUS];
// extern CXL_MEMORY CXL;
extern bool L2_PA;
extern uint64_t L2_PA_ratio;
extern uint64_t on_chip_icn_hops[NUM_CPUS+1][NUM_CPUS+1];
uint64_t get_cache_bank(uint64_t addr){
  uint64_t bankID = (addr>>LOG2_BLOCK_SIZE)%NUM_CPUS;
  return bankID;
} 
uint64_t fold_addr(uint64_t addr){
  //assume 64bit addr
  uint64_t folded_addr = 0;
  uint64_t n_segments = 64 / FOLD_BITS;
  uint64_t fold_mask = (1<<FOLD_BITS) - 1;
  if(64%FOLD_BITS>0){n_segments++;}
  for(uint64_t i=0; i<n_segments;i++){
    uint64_t masked_segment = (addr>>(FOLD_BITS*i)) & fold_mask;
    folded_addr = folded_addr ^ masked_segment;
  }
  if(folded_addr >  SIZEOF_PC_COUNTER){cout<<"folded_addr: "<<folded_addr<<endl;}
  assert(folded_addr < SIZEOF_PC_COUNTER);
  return folded_addr;
}
void CACHE::inc_pam_pc_counter(uint64_t folded_addr){
  if(PC_COUNTER[folded_addr]<((1<<NUMBITS_PC_COUNTER)-1))
    PC_COUNTER[folded_addr]++;
  //cout<<"inc_pam_pc_counter, PC_COUNTER["<<folded_addr<<"]="<<PC_COUNTER[folded_addr]<<endl;
}
void CACHE::dec_pam_pc_counter(uint64_t folded_addr){
  if(PC_COUNTER[folded_addr]>0)
    PC_COUNTER[folded_addr]--;
  //cout<<"dec_pam_pc_counter, PC_COUNTER["<<folded_addr<<"]="<<PC_COUNTER[folded_addr]<<endl;
}

bool CACHE::check_pam_pc_counter(uint64_t folded_addr){
  if(PC_COUNTER[folded_addr]> ((1<<(NUMBITS_PC_COUNTER-1))-1) ){
    return true;
  }
  return false;
}

void CACHE::handle_fill()
{
  while (writes_available_this_cycle > 0) {
    auto fill_mshr = MSHR.begin();
    if (fill_mshr == std::end(MSHR) || fill_mshr->event_cycle > current_cycle)
      return;


    // find victim
    uint32_t set = get_set(fill_mshr->address);

    auto set_begin = std::next(std::begin(block), set * NUM_WAY);
    auto set_end = std::next(set_begin, NUM_WAY);
    auto first_inv = std::find_if_not(set_begin, set_end, is_valid<BLOCK>());
    uint32_t way = std::distance(set_begin, first_inv);
    if (way == NUM_WAY)
      way = impl_replacement_find_victim(fill_mshr->cpu, fill_mshr->instr_id, set, &block.data()[set * NUM_WAY], fill_mshr->ip, fill_mshr->address,
                                         fill_mshr->type);

    bool success = filllike_miss(set, way, *fill_mshr);
    if (!success)
      return;

    if (way != NUM_WAY) {
      // update processed packets
      fill_mshr->data = block[set * NUM_WAY + way].data;

      for (auto ret : fill_mshr->to_return)
        ret->return_data(&(*fill_mshr));
    }

    MSHR.erase(fill_mshr);
    writes_available_this_cycle--;
  }
}

void CACHE::handle_writeback()
{
  while (writes_available_this_cycle > 0) {
    if (!WQ.has_ready())
      return;

    // handle the oldest entry
    PACKET& handle_pkt = WQ.front();

    // access cache
    uint32_t set = get_set(handle_pkt.address);
    uint32_t way = get_way(handle_pkt.address, set);

    BLOCK& fill_block = block[set * NUM_WAY + way];

    if (way < NUM_WAY) // HIT
    {
      impl_replacement_update_state(handle_pkt.cpu, set, way, fill_block.address, handle_pkt.ip, 0, handle_pkt.type, 1);

      // COLLECT STATS
      sim_hit[handle_pkt.cpu][handle_pkt.type]++;
      sim_access[handle_pkt.cpu][handle_pkt.type]++;
      // if(NAME=="LLC"){
      //   llc_accs_last_interval++;
      // }


      // mark dirty
      fill_block.dirty = 1;
    } else // MISS
    {
      bool success;
      if (handle_pkt.type == RFO && handle_pkt.to_return.empty()) {
        success = readlike_miss(handle_pkt);
      } else {
        // find victim
        auto set_begin = std::next(std::begin(block), set * NUM_WAY);
        auto set_end = std::next(set_begin, NUM_WAY);
        auto first_inv = std::find_if_not(set_begin, set_end, is_valid<BLOCK>());
        way = std::distance(set_begin, first_inv);
        if (way == NUM_WAY)
          way = impl_replacement_find_victim(handle_pkt.cpu, handle_pkt.instr_id, set, &block.data()[set * NUM_WAY], handle_pkt.ip, handle_pkt.address,
                                             handle_pkt.type);

        success = filllike_miss(set, way, handle_pkt);
      }

      if (!success)
        return;
    }

    // remove this entry from WQ
    writes_available_this_cycle--;
    WQ.pop_front();
  }
}

void CACHE::handle_read()
{
  while (reads_available_this_cycle > 0) {

    if (!RQ.has_ready())
      return;

    // handle the oldest entry
    PACKET& handle_pkt = RQ.front();

    // A (hopefully temporary) hack to know whether to send the evicted paddr or
    // vaddr to the prefetcher
    ever_seen_data |= (handle_pkt.v_address != handle_pkt.ip);

    uint32_t set = get_set(handle_pkt.address);
    uint32_t way = get_way(handle_pkt.address, set);

    if (way < NUM_WAY) // HIT
    {
      readlike_hit(set, way, handle_pkt);
    } else {
      bool success = readlike_miss(handle_pkt);
      if (!success)
        return;
    }

    // remove this entry from RQ
    RQ.pop_front();
    reads_available_this_cycle--;
  }
}

void CACHE::handle_prefetch()
{
  while (reads_available_this_cycle > 0) {
    if (!PQ.has_ready())
      return;

    // handle the oldest entry
    PACKET& handle_pkt = PQ.front();

    uint32_t set = get_set(handle_pkt.address);
    uint32_t way = get_way(handle_pkt.address, set);

    if (way < NUM_WAY) // HIT
    {
      readlike_hit(set, way, handle_pkt);
    } else {
      bool success = readlike_miss(handle_pkt);
      if (!success)
        return;
    }

    // remove this entry from PQ
    PQ.pop_front();
    reads_available_this_cycle--;
  }
}

void CACHE::readlike_hit(std::size_t set, std::size_t way, PACKET& handle_pkt)
{
  DP(if (warmup_complete[handle_pkt.cpu]) {
    std::cout << "[" << NAME << "] " << __func__ << " hit";
    std::cout << " instr_id: " << handle_pkt.instr_id << " address: " << std::hex << (handle_pkt.address >> OFFSET_BITS);
    std::cout << " full_addr: " << handle_pkt.address;
    std::cout << " full_v_addr: " << handle_pkt.v_address << std::dec;
    std::cout << " type: " << +handle_pkt.type;
    std::cout << " cycle: " << current_cycle << std::endl;
  });

  BLOCK& hit_block = block[set * NUM_WAY + way];

  handle_pkt.data = hit_block.data;

  // update prefetcher on load instruction
  if (should_activate_prefetcher(handle_pkt.type) && handle_pkt.pf_origin_level < fill_level) {
    cpu = handle_pkt.cpu;
    uint64_t pf_base_addr = (virtual_prefetch ? handle_pkt.v_address : handle_pkt.address) & ~bitmask(match_offset_bits ? 0 : OFFSET_BITS);
    handle_pkt.pf_metadata = impl_prefetcher_cache_operate(pf_base_addr, handle_pkt.ip, 1, handle_pkt.type, handle_pkt.pf_metadata);
  }

  // update replacement policy
  impl_replacement_update_state(handle_pkt.cpu, set, way, hit_block.address, handle_pkt.ip, 0, handle_pkt.type, 1);

  // COLLECT STATS
  sim_hit[handle_pkt.cpu][handle_pkt.type]++;
  sim_access[handle_pkt.cpu][handle_pkt.type]++;
  if(NAME=="LLC"){
    llc_accs_last_interval++;
	if(handle_pkt.l2_parallel_access){
	    PA_hit++;
	}
  }

  for (auto ret : handle_pkt.to_return)
    ret->return_data(&handle_pkt);

  
  #if ALLOW_PAM!=NOPAM
  //auto start = std::chrono::high_resolution_clock::now();
  //for LLC, need to allocate PA_wait_second_return entry for return from mem
    if (NAME.find("LLC") != std::string::npos) {
      if(handle_pkt.l2_parallel_access){
        //check for already returned. if found, just erase it and don't add to wait_second_return
        auto early_return = std::find_if(LLC_early_returned.begin(), LLC_early_returned.end(), eq_addr<PACKET>(handle_pkt.address, OFFSET_BITS));
        // auto tmp1 = std::chrono::high_resolution_clock::now();
        // auto duration_tmp1 = std::chrono::duration_cast<std::chrono::nanoseconds>(tmp1 - start);
        // cout<<"in segment1 - time_ after seraching early_return: "<<duration_tmp1.count()<<" nanoseconds"<<endl;
        if(early_return != LLC_early_returned.end()){ // request returned from mem before it reached LLC
          LLC_early_returned.erase(early_return);
          auto LLC_er_size = LLC_early_returned.size();
          // cout<<"in segment1 - LLC_early_returned.size: "<<LLC_er_size<<endl;
          // auto tmp2 = std::chrono::high_resolution_clock::now();
          // auto duration_tmp2 = std::chrono::duration_cast<std::chrono::nanoseconds>(tmp2 - tmp1);
          
          // cout<<"in segment1 - time taken to erase early_reutrn from list: "<<duration_tmp2.count()<<" nanoseconds"<<endl;
        }
        else{
          PA_wait_second_return.insert(std::end(PA_wait_second_return), handle_pkt);
          // auto tmp2 = std::chrono::high_resolution_clock::now();
          // auto duration_tmp2 = std::chrono::duration_cast<std::chrono::nanoseconds>(tmp2 - tmp1);
          // cout<<"in segment1 - time taken to insert to PA_wait_second_return list: "<<duration_tmp2.count()<<" nanoseconds"<<endl;
        }
      }
    }
    // auto end = std::chrono::high_resolution_clock::now();
    // auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    // std::cout << "Time taken by code segment1: " << duration.count() << " nanoseconds" << std::endl;
  #endif

  // update prefetch stats and reset prefetch bit
  if (hit_block.prefetch) {
    pf_useful++;
    hit_block.prefetch = 0;
  }
}

bool CACHE::readlike_miss(PACKET& handle_pkt)
{
  DP(if (warmup_complete[handle_pkt.cpu]) {
    std::cout << "[" << NAME << "] " << __func__ << " miss";
    std::cout << " instr_id: " << handle_pkt.instr_id << " address: " << std::hex << (handle_pkt.address >> OFFSET_BITS);
    std::cout << " full_addr: " << handle_pkt.address;
    std::cout << " full_v_addr: " << handle_pkt.v_address << std::dec;
    std::cout << " type: " << +handle_pkt.type;
    std::cout << " cycle: " << current_cycle << std::endl;
  });

  // check mshr
  auto mshr_entry = std::find_if(MSHR.begin(), MSHR.end(), eq_addr<PACKET>(handle_pkt.address, OFFSET_BITS));
  bool mshr_full = (MSHR.size() == MSHR_SIZE);



  if (mshr_entry != MSHR.end()) // miss already inflight
  {
    // update fill location
    mshr_entry->fill_level = std::min(mshr_entry->fill_level, handle_pkt.fill_level);

    packet_dep_merge(mshr_entry->lq_index_depend_on_me, handle_pkt.lq_index_depend_on_me);
    packet_dep_merge(mshr_entry->sq_index_depend_on_me, handle_pkt.sq_index_depend_on_me);
    packet_dep_merge(mshr_entry->instr_depend_on_me, handle_pkt.instr_depend_on_me);
    packet_dep_merge(mshr_entry->to_return, handle_pkt.to_return);

    if (mshr_entry->type == PREFETCH && handle_pkt.type != PREFETCH) {
      // Mark the prefetch as useful
      if (mshr_entry->pf_origin_level == fill_level)
        pf_useful++;

      uint64_t prior_event_cycle = mshr_entry->event_cycle;
      *mshr_entry = handle_pkt;

      // in case request is already returned, we should keep event_cycle
      mshr_entry->event_cycle = prior_event_cycle;
    }
  } else {
    if (mshr_full){  // not enough MSHR resource
      return false; // TODO should we allow prefetches anyway if they will not
                    // be filled to this level?
    }

    bool is_read = prefetch_as_load || (handle_pkt.type != PREFETCH);

    // check to make sure the lower level queue has room for this read miss
    int queue_type = (is_read) ? 1 : 3;
    if (lower_level->get_occupancy(queue_type, handle_pkt.address) == lower_level->get_size(queue_type, handle_pkt.address))
      return false;
    
    #if ALLOW_PAM!=NOPAM
    // auto start2 = std::chrono::high_resolution_clock::now();
    if (NAME.find("L2C") != std::string::npos) {
      // TODO fill these out for setting l2_parallel_access bit
      #if ALLOW_PAM==PAM_PC_COUNTER
      //dbg
      // cout<<"PAM_PC_COUNTER, IP: "<<std::hex<<handle_pkt.ip<<std::dec<<endl;
      // if(handle_pkt.ip==0){
      //   cout<<"IP value is 0 in PAM_PC_COUNTER check, instr_id: "<<std::hex<<handle_pkt.instr_id<<std::dec<<endl;
      // }
      /// end dbg
      uint64_t folded_addr = fold_addr(handle_pkt.ip);
      bool do_pam = check_pam_pc_counter(folded_addr);
      if(do_pam){
        if(((CACHE *)lower_level)->lower_level->get_occupancy(queue_type, handle_pkt.address) == ((CACHE *)lower_level)->lower_level->get_size(queue_type, handle_pkt.address))
        // if (CXL.get_occupancy(queue_type, handle_pkt.address) == CXL.get_size(queue_type, handle_pkt.address))
          {return false;}
        handle_pkt.l2_parallel_access=true;
        if(warmup_complete[handle_pkt.cpu]){
          PAM_count_per_l2c++;        
        }
      }
      //check mispredict for counter
      bool inLLC = ((CACHE *) lower_level)->probe_entry(handle_pkt.address);
      if(inLLC){
        handle_pkt.llc_hit=true;
        //dec_pam_pc_counter(folded_addr);
        if(do_pam){PAM_false_positive++;}
      }
      else{
        //inc_pam_pc_counter(folded_addr);
        if(!do_pam){PAM_false_negative++;}
      }
      #endif
      #if ALLOW_PAM==PAM_IDEAL_PREDICTOR
      bool inLLC = ((CACHE *) lower_level)->probe_entry(handle_pkt.address);
      if(!inLLC){
        if(((CACHE *)lower_level)->lower_level->get_occupancy(queue_type, handle_pkt.address) == ((CACHE *)lower_level)->lower_level->get_size(queue_type, handle_pkt.address))
        // if (CXL.get_occupancy(queue_type, handle_pkt.address) == CXL.get_size(queue_type, handle_pkt.address))
          {return false;}
        handle_pkt.l2_parallel_access=true;
        if(warmup_complete[handle_pkt.cpu]){
          PAM_count_per_l2c++;
        }
      }
      #endif
      #if ALLOW_PAM==PAM_STATIC_THRESHOLD
      // TODO if access will be parallel, also check occupancy vs size at mem moduel(CXL)
      if(L2_PA){
        bool inLLC = ((CACHE *) lower_level)->probe_entry(handle_pkt.address);
        //if(inLLC){
        uint64_t randval = rand() % 100;
        if(randval < L2_PA_ratio){
          if(((CACHE *)lower_level)->lower_level->get_occupancy(queue_type, handle_pkt.address) == ((CACHE *)lower_level)->lower_level->get_size(queue_type, handle_pkt.address))
          // if (CXL.get_occupancy(queue_type, handle_pkt.address) == CXL.get_size(queue_type, handle_pkt.address))
            {return false;}
          handle_pkt.l2_parallel_access=true;
          if(warmup_complete[handle_pkt.cpu]){
            PAM_count_per_l2c++;
            if(inLLC){PAM_false_positive++;}
          }
        }
        else{
          if(warmup_complete[handle_pkt.cpu]){
            if(!inLLC){PAM_false_negative++;}
          }
        }
      }
      #endif
    }
    
    // auto end2 = std::chrono::high_resolution_clock::now();
    // auto duration2 = std::chrono::duration_cast<std::chrono::nanoseconds>(end2 - start2);
    // std::cout << "Time taken by code segment2: " << duration2.count() << " nanoseconds" << std::endl;
    #endif


    // Allocate an MSHR
    //std::__cxx11::list<PACKET>::iterator tmpit;
    bool mshr_allocated=false;
    if (handle_pkt.fill_level <= fill_level) {
      auto it = MSHR.insert(std::end(MSHR), handle_pkt);
      it->cycle_enqueued = current_cycle;
      it->event_cycle = std::numeric_limits<uint64_t>::max();
      //tmpit=it;
      mshr_allocated=true;
    }


    #if ALLOW_PAM!=NOPAM
    // auto start3 = std::chrono::high_resolution_clock::now();
    if (NAME.find("LLC") != std::string::npos) { 
      //if PA, LLC does not issue memory request (already sent to mem from L2 in parallel)
      if(handle_pkt.l2_parallel_access){
        //check if it returned early
        //cout<<"checking early_return in LLC"<<endl;
        auto early_return = std::find_if(LLC_early_returned.begin(), LLC_early_returned.end(), eq_addr<PACKET>(handle_pkt.address, OFFSET_BITS));
        //cout<<"assigned early return"<<endl;
        if(early_return != LLC_early_returned.end()){ // request returned from mem before it reached LLC
          //cout<<"early return entry found"<<endl;
          if(mshr_allocated){
              //cout<<"mshr was allocated"<<endl;
              // tmpit->data = early_return->data;
              // tmpit->pf_metadata = early_return->pf_metadata;
              // tmpit->event_cycle = current_cycle;
              auto mshr_entry = std::find_if(MSHR.begin(), MSHR.end(), eq_addr<PACKET>(handle_pkt.address, OFFSET_BITS));
              auto first_unreturned = std::find_if(MSHR.begin(), MSHR.end(), [](auto x) { return x.event_cycle == std::numeric_limits<uint64_t>::max(); });
              mshr_entry->data = early_return->data;
              mshr_entry->pf_metadata = early_return->pf_metadata;
              mshr_entry->event_cycle = current_cycle; // Set as ready
              //cout<<"before iter_swap"<<endl;
              std::iter_swap(mshr_entry, first_unreturned);
              //cout<<"after iter_swap"<<endl;
              //LLC_early_returned.erase(early_return);
              //cout<<"after LLC_early_returned.erase"<<endl;
          }
          LLC_early_returned.erase(early_return);
        }
        //cout<<"return from this readlike_miss call"<<endl;
        return true;
      }
    }
    // auto end3 = std::chrono::high_resolution_clock::now();
    // auto duration3 = std::chrono::duration_cast<std::chrono::nanoseconds>(end3 - start3);
    // std::cout << "Time taken by code segment3: " << duration3.count() << " nanoseconds" << std::endl;
    #endif

    if (handle_pkt.fill_level <= fill_level)
      handle_pkt.to_return = {this};
    else
      handle_pkt.to_return.clear();

    // TODO 
    #if ALLOW_PAM!=NOPAM
    // auto start4 = std::chrono::high_resolution_clock::now();
    if (NAME.find("L2C") != std::string::npos) {
      if(handle_pkt.l2_parallel_access){//this should have been decided earlier
        if (handle_pkt.fill_level <= fill_level){handle_pkt.to_return.push_back((CACHE*)lower_level);}
        if (!is_read){
          ((CACHE *)lower_level)->lower_level->add_pq(&handle_pkt);
          // CXL.add_pq(&handle_pkt);
        }
        else{
          ((CACHE *)lower_level)->lower_level->add_rq(&handle_pkt);
          // CXL.add_rq(&handle_pkt);
        }
        //cout<<"add_rq'd to mem as PAM, count @"<<NAME<<": "<<PAM_count_per_l2c<<", false_positive: "<<PAM_false_positive<<", false_negative: "<<PAM_false_negative<<endl;
      }

      // //TODO fill these out for l2_pa condition
      // #if ALLOW_PAM==PAM_PC_COUNTER
      // if(handle_pkt.l2_parallel_access){//this should have been decided earlier
      //   if (handle_pkt.fill_level <= fill_level){handle_pkt.to_return.push_back((CACHE*)lower_level);}
      //   if (!is_read){
      //     CXL.add_pq(&handle_pkt);
      //   }
      //   else{
      //     CXL.add_rq(&handle_pkt);
      //   }
      // }
      // #endif
      // #if ALLOW_PAM==PAM_IDEAL_PREDICTOR
      // #endif
      // #if ALLOW_PAM==PAM_STATIC_THRESHOLD
      // if(L2_PA){
      //   //set pkt field l2_parallel_access and add_rq/pq to CXL
      //   //TODO - since add_pq takes pointers, maybe I need to make new copies of the packets? might have to look into this if things break
      //   if (handle_pkt.fill_level <= fill_level){handle_pkt.to_return.push_back((CACHE*)lower_level);}
      //   handle_pkt.l2_parallel_access=true;
      //   if (!is_read){
      //     CXL.add_pq(&handle_pkt);
      //   }
      //   else{
      //     CXL.add_rq(&handle_pkt);
      //   }
      // }
      // #endif
    }
    // auto end4 = std::chrono::high_resolution_clock::now();
    // auto duration4 = std::chrono::duration_cast<std::chrono::nanoseconds>(end4 - start4);
    // for request to LLC, reset to_return to only this L2C
    if (handle_pkt.fill_level <= fill_level)
      handle_pkt.to_return = {this};
    //std::cout << "Time taken by code segment4: " << duration4.count() << " nanoseconds" << std::endl;
    #endif
    if (!is_read)
      lower_level->add_pq(&handle_pkt);
    else{
      lower_level->add_rq(&handle_pkt);
    }
  }

  // update prefetcher on load instructions and prefetches from upper levels
  if (should_activate_prefetcher(handle_pkt.type) && handle_pkt.pf_origin_level < fill_level) {
    cpu = handle_pkt.cpu;
    uint64_t pf_base_addr = (virtual_prefetch ? handle_pkt.v_address : handle_pkt.address) & ~bitmask(match_offset_bits ? 0 : OFFSET_BITS);
    handle_pkt.pf_metadata = impl_prefetcher_cache_operate(pf_base_addr, handle_pkt.ip, 0, handle_pkt.type, handle_pkt.pf_metadata);
  }

  return true;
}

bool CACHE::filllike_miss(std::size_t set, std::size_t way, PACKET& handle_pkt)
{
  DP(if (warmup_complete[handle_pkt.cpu]) {
    std::cout << "[" << NAME << "] " << __func__ << " miss";
    std::cout << " instr_id: " << handle_pkt.instr_id << " address: " << std::hex << (handle_pkt.address >> OFFSET_BITS);
    std::cout << " full_addr: " << handle_pkt.address;
    std::cout << " full_v_addr: " << handle_pkt.v_address << std::dec;
    std::cout << " type: " << +handle_pkt.type;
    std::cout << " cycle: " << current_cycle << std::endl;
  });

  bool bypass = (way == NUM_WAY);
#ifndef LLC_BYPASS
  assert(!bypass);
#endif
  assert(handle_pkt.type != WRITEBACK || !bypass);

  BLOCK& fill_block = block[set * NUM_WAY + way];
  bool evicting_dirty = !bypass && (lower_level != NULL) && fill_block.dirty;
  uint64_t evicting_address = 0;

  if (!bypass) {
    if (evicting_dirty) {
      PACKET writeback_packet;

      writeback_packet.fill_level = lower_level->fill_level;
      writeback_packet.cpu = handle_pkt.cpu;
      writeback_packet.address = fill_block.address;
      writeback_packet.data = fill_block.data;
      writeback_packet.instr_id = handle_pkt.instr_id;
      writeback_packet.ip = 0;
      writeback_packet.type = WRITEBACK;

      auto result = lower_level->add_wq(&writeback_packet);
      if (result == -2)
        return false;
    }

    if (ever_seen_data)
      evicting_address = fill_block.address & ~bitmask(match_offset_bits ? 0 : OFFSET_BITS);
    else
      evicting_address = fill_block.v_address & ~bitmask(match_offset_bits ? 0 : OFFSET_BITS);

    if (fill_block.prefetch)
      pf_useless++;

    if (handle_pkt.type == PREFETCH)
      pf_fill++;

    fill_block.valid = true;
    fill_block.prefetch = (handle_pkt.type == PREFETCH && handle_pkt.pf_origin_level == fill_level);
    fill_block.dirty = (handle_pkt.type == WRITEBACK || (handle_pkt.type == RFO && handle_pkt.to_return.empty()));
    fill_block.address = handle_pkt.address;
    fill_block.v_address = handle_pkt.v_address;
    fill_block.data = handle_pkt.data;
    fill_block.ip = handle_pkt.ip;
    fill_block.cpu = handle_pkt.cpu;
    fill_block.instr_id = handle_pkt.instr_id;
  }

  uint64_t miss_lat = current_cycle - handle_pkt.cycle_enqueued;
  if (warmup_complete[handle_pkt.cpu] && (handle_pkt.cycle_enqueued != 0)){
    //total_miss_latency += current_cycle - handle_pkt.cycle_enqueued;
    total_miss_latency[handle_pkt.cpu] += miss_lat;
	  if(this->fill_level == 6){
      int hist_index = miss_lat / 24; // divide by 2.4 to convert to ns, then by 10 for histogram(10ns per bucket)
	    if(hist_index>199) hist_index=199;
      lat_hist[handle_pkt.cpu][hist_index]++;
    }
	// //std::cout<<this->fill_level<<std::endl;
	// std::cout<<"cycle_enqueued: "<<handle_pkt.cycle_enqueued<<std::endl;
	// std::cout<<"miss_lat  	  : "<<current_cycle - handle_pkt.cycle_enqueued<<std::endl;
	// }
  }
  

  // update prefetcher
  cpu = handle_pkt.cpu;
  handle_pkt.pf_metadata =
      impl_prefetcher_cache_fill((virtual_prefetch ? handle_pkt.v_address : handle_pkt.address) & ~bitmask(match_offset_bits ? 0 : OFFSET_BITS), set, way,
                                 handle_pkt.type == PREFETCH, evicting_address, handle_pkt.pf_metadata);

  // update replacement policy
  impl_replacement_update_state(handle_pkt.cpu, set, way, handle_pkt.address, handle_pkt.ip, 0, handle_pkt.type, 0);

  // COLLECT STATS
  sim_miss[handle_pkt.cpu][handle_pkt.type]++;
  sim_access[handle_pkt.cpu][handle_pkt.type]++;

  if(NAME=="LLC"){
    llc_misses_last_interval++;
    llc_accs_last_interval++;
  }

  return true;
}

// std::chrono::_V2::system_clock::time_point last_ts;
void CACHE::operate()
{
  //dbg
  //if(NAME=="LLC"){
  //auto curts = std::chrono::high_resolution_clock::now();
  //auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(curts - last_ts);
  //std::cout << "Time taken for a full cycle @ LLC: " << duration.count() << " nanoseconds" << std::endl;
  //last_ts = curts;
  //}
  #if ALLOW_PAM==PAM_STATIC_THRESHOLD
  if(NAME=="LLC"){
    if(current_cycle > l2_pa_next_period){
      set_l2_pa();
    }
  }
  #endif

  operate_writes();
  operate_reads();

  impl_prefetcher_cycle_operate();
}

uint64_t CACHE::set_l2_pa(){
  
  uint64_t l2miss_BW = llc_accs_last_interval * 64 * 24 / (10 * PAM_INTERVAL);
  uint64_t llcmiss_BW = llc_misses_last_interval * 64 * 24 / (10 * PAM_INTERVAL);

  bool prev_l2pa = L2_PA;
  if(llcmiss_BW < TH_L2PA){
    L2_PA = true;
    //if(llcmiss_BW!=0){
    if(l2miss_BW!=0){
      //
      cout<<"TH_L2PA: "<<TH_L2PA<<", l2miss_BW: "<<l2miss_BW<<", llc_miss_BW: "<<llcmiss_BW<<endl;
      //

      //L2_PA_ratio=(TH_L2PA - l2miss_BW) * 100 / llcmiss_BW;
      L2_PA_ratio=(TH_L2PA - llcmiss_BW) * 100 / l2miss_BW;
      cout<<"L2_PA_ratio set to: "<<L2_PA_ratio<<endl;
    }
    else{L2_PA_ratio=1; }//cornercase at start
  }
  else{
    L2_PA = false;
    L2_PA_ratio=0;
    cout<<"L2_PA_ratio set to: 0"<<endl;
  }
  //dbg
  if(L2_PA!=prev_l2pa){
    cout<<"L2 Parallel Access switched to "<<L2_PA<<endl;
  }

  //dbg
  //cout<<"set_l2_pa() @ cycle "<<current_cycle<<", L2_PA="<<L2_PA<<", consumed_BW: "<<consumed_BW<<" (BW_threshold: "<<TH_L2PA<<")"<<endl;

  l2_pa_next_period=current_cycle+PAM_INTERVAL;
  llc_accs_last_interval=0;
  llc_misses_last_interval=0;
  return 0;
}

void CACHE::operate_writes()
{
  // perform all writes
  writes_available_this_cycle = MAX_WRITE;
  handle_fill();
  handle_writeback();

  WQ.operate();
}

void CACHE::operate_reads()
{
  // perform all reads
  reads_available_this_cycle = MAX_READ;
  handle_read();
  va_translate_prefetches();
  handle_prefetch();

  RQ.operate();
  PQ.operate();
  VAPQ.operate();
}

uint32_t CACHE::get_set(uint64_t address) { return ((address >> OFFSET_BITS) & bitmask(lg2(NUM_SET))); }

uint32_t CACHE::get_way(uint64_t address, uint32_t set)
{
  auto begin = std::next(block.begin(), set * NUM_WAY);
  auto end = std::next(begin, NUM_WAY);
  return std::distance(begin, std::find_if(begin, end, eq_addr<BLOCK>(address, OFFSET_BITS)));
}

int CACHE::invalidate_entry(uint64_t inval_addr)
{
  uint32_t set = get_set(inval_addr);
  uint32_t way = get_way(inval_addr, set);

  if (way < NUM_WAY)
    block[set * NUM_WAY + way].valid = 0;

  return way;
}

bool CACHE::probe_entry(uint64_t addr)
{
  uint32_t set = get_set(addr);
  uint32_t way = get_way(addr, set);

  if (way < NUM_WAY){
    return true;
  }
  return false;  
}

int CACHE::add_rq(PACKET* packet)
{
  assert(packet->address != 0);
  RQ_ACCESS++;

  if(NAME=="LLC"){
	  if(packet->l2_parallel_access){
		  PA_count++;
	  }
  }
  //dbg
  // if(NAME=="LLC"){
  //   uint64_t to_return_size = packet->to_return.size();
  //   cout<<"packet added to LLC RQ has "<<to_return_size<<" to returns"<<endl;
  //   for (auto ret : packet->to_return)
  //     std::cout<<((CACHE*)ret)->NAME<<std::endl;

  // }

  DP(if (warmup_complete[packet->cpu]) {
    std::cout << "[" << NAME << "_RQ] " << __func__ << " instr_id: " << packet->instr_id << " address: " << std::hex << (packet->address >> OFFSET_BITS);
    std::cout << " full_addr: " << packet->address << " v_address: " << packet->v_address << std::dec << " type: " << +packet->type
              << " occupancy: " << RQ.occupancy();
  })

  // check for the latest writebacks in the write queue
  champsim::delay_queue<PACKET>::iterator found_wq = std::find_if(WQ.begin(), WQ.end(), eq_addr<PACKET>(packet->address, match_offset_bits ? 0 : OFFSET_BITS));

  if (found_wq != WQ.end()) {

    DP(if (warmup_complete[packet->cpu]) std::cout << " MERGED_WQ" << std::endl;)

    packet->data = found_wq->data;
    for (auto ret : packet->to_return)
      ret->return_data(packet);

    WQ_FORWARD++;
    return -1;
  }

  // check for duplicates in the read queue
  auto found_rq = std::find_if(RQ.begin(), RQ.end(), eq_addr<PACKET>(packet->address, OFFSET_BITS));
  if (found_rq != RQ.end()) {

    DP(if (warmup_complete[packet->cpu]) std::cout << " MERGED_RQ" << std::endl;)

    packet_dep_merge(found_rq->lq_index_depend_on_me, packet->lq_index_depend_on_me);
    packet_dep_merge(found_rq->sq_index_depend_on_me, packet->sq_index_depend_on_me);
    packet_dep_merge(found_rq->instr_depend_on_me, packet->instr_depend_on_me);
    packet_dep_merge(found_rq->to_return, packet->to_return);

    RQ_MERGED++;

    return 0; // merged index
  }

  // check occupancy
  if (RQ.full()) {
    RQ_FULL++;

    DP(if (warmup_complete[packet->cpu]) std::cout << " FULL" << std::endl;)

    return -2; // cannot handle this request
  }

  // if there is no duplicate, add it to RQ
  if (warmup_complete[cpu])
    RQ.push_back(*packet);
  else
    RQ.push_back_ready(*packet);

  DP(if (warmup_complete[packet->cpu]) std::cout << " ADDED" << std::endl;)

  RQ_TO_CACHE++;
  return RQ.occupancy();
}

int CACHE::add_wq(PACKET* packet)
{
  WQ_ACCESS++;

  DP(if (warmup_complete[packet->cpu]) {
    std::cout << "[" << NAME << "_WQ] " << __func__ << " instr_id: " << packet->instr_id << " address: " << std::hex << (packet->address >> OFFSET_BITS);
    std::cout << " full_addr: " << packet->address << " v_address: " << packet->v_address << std::dec << " type: " << +packet->type
              << " occupancy: " << RQ.occupancy();
  })

  // check for duplicates in the write queue
  champsim::delay_queue<PACKET>::iterator found_wq = std::find_if(WQ.begin(), WQ.end(), eq_addr<PACKET>(packet->address, match_offset_bits ? 0 : OFFSET_BITS));

  if (found_wq != WQ.end()) {

    DP(if (warmup_complete[packet->cpu]) std::cout << " MERGED" << std::endl;)

    WQ_MERGED++;
    return 0; // merged index
  }

  // Check for room in the queue
  if (WQ.full()) {
    DP(if (warmup_complete[packet->cpu]) std::cout << " FULL" << std::endl;)

    ++WQ_FULL;
    return -2;
  }

  // if there is no duplicate, add it to the write queue
  if (warmup_complete[cpu])
    WQ.push_back(*packet);
  else
    WQ.push_back_ready(*packet);

  DP(if (warmup_complete[packet->cpu]) std::cout << " ADDED" << std::endl;)

  WQ_TO_CACHE++;
  WQ_ACCESS++;

  return WQ.occupancy();
}

int CACHE::prefetch_line(uint64_t pf_addr, bool fill_this_level, uint32_t prefetch_metadata)
{
  pf_requested++;

  PACKET pf_packet;
  pf_packet.type = PREFETCH;
  pf_packet.fill_level = (fill_this_level ? fill_level : lower_level->fill_level);
  pf_packet.pf_origin_level = fill_level;
  pf_packet.pf_metadata = prefetch_metadata;
  pf_packet.cpu = cpu;
  pf_packet.address = pf_addr;
  pf_packet.v_address = virtual_prefetch ? pf_addr : 0;

  if (virtual_prefetch) {
    if (!VAPQ.full()) {
      VAPQ.push_back(pf_packet);
      return 1;
    }
  } else {
    int result = add_pq(&pf_packet);
    if (result != -2) {
      if (result > 0)
        pf_issued++;
      return 1;
    }
  }

  return 0;
}

int CACHE::prefetch_line(uint64_t ip, uint64_t base_addr, uint64_t pf_addr, bool fill_this_level, uint32_t prefetch_metadata)
{
  static bool deprecate_printed = false;
  if (!deprecate_printed) {
    std::cout << "WARNING: The extended signature CACHE::prefetch_line(ip, "
                 "base_addr, pf_addr, fill_this_level, prefetch_metadata) is "
                 "deprecated."
              << std::endl;
    std::cout << "WARNING: Use CACHE::prefetch_line(pf_addr, fill_this_level, "
                 "prefetch_metadata) instead."
              << std::endl;
    deprecate_printed = true;
  }
  return prefetch_line(pf_addr, fill_this_level, prefetch_metadata);
}

void CACHE::va_translate_prefetches()
{
  // TEMPORARY SOLUTION: mark prefetches as translated after a fixed latency
  if (VAPQ.has_ready()) {
    VAPQ.front().address = vmem.va_to_pa(cpu, VAPQ.front().v_address).first;

    // move the translated prefetch over to the regular PQ
    int result = add_pq(&VAPQ.front());

    // remove the prefetch from the VAPQ
    if (result != -2)
      VAPQ.pop_front();

    if (result > 0)
      pf_issued++;
  }
}

int CACHE::add_pq(PACKET* packet)
{
  assert(packet->address != 0);
  PQ_ACCESS++;

  DP(if (warmup_complete[packet->cpu]) {
    std::cout << "[" << NAME << "_WQ] " << __func__ << " instr_id: " << packet->instr_id << " address: " << std::hex << (packet->address >> OFFSET_BITS);
    std::cout << " full_addr: " << packet->address << " v_address: " << packet->v_address << std::dec << " type: " << +packet->type
              << " occupancy: " << RQ.occupancy();
  })

  // check for the latest wirtebacks in the write queue
  champsim::delay_queue<PACKET>::iterator found_wq = std::find_if(WQ.begin(), WQ.end(), eq_addr<PACKET>(packet->address, match_offset_bits ? 0 : OFFSET_BITS));

  if (found_wq != WQ.end()) {

    DP(if (warmup_complete[packet->cpu]) std::cout << " MERGED_WQ" << std::endl;)

    packet->data = found_wq->data;
    for (auto ret : packet->to_return)
      ret->return_data(packet);

    WQ_FORWARD++;
    return -1;
  }

  // check for duplicates in the PQ
  auto found = std::find_if(PQ.begin(), PQ.end(), eq_addr<PACKET>(packet->address, OFFSET_BITS));
  if (found != PQ.end()) {
    DP(if (warmup_complete[packet->cpu]) std::cout << " MERGED_PQ" << std::endl;)

    found->fill_level = std::min(found->fill_level, packet->fill_level);
    packet_dep_merge(found->to_return, packet->to_return);

    PQ_MERGED++;
    return 0;
  }

  // check occupancy
  if (PQ.full()) {

    DP(if (warmup_complete[packet->cpu]) std::cout << " FULL" << std::endl;)

    PQ_FULL++;
    return -2; // cannot handle this request
  }

  // if there is no duplicate, add it to PQ
  if (warmup_complete[cpu])
    PQ.push_back(*packet);
  else
    PQ.push_back_ready(*packet);

  DP(if (warmup_complete[packet->cpu]) std::cout << " ADDED" << std::endl;)

  PQ_TO_CACHE++;
  return PQ.occupancy();
}

void CACHE::return_data(PACKET* packet)
{
  // check MSHR information
  RETURN_DATA_CALLS++;
  auto mshr_entry = std::find_if(MSHR.begin(), MSHR.end(), eq_addr<PACKET>(packet->address, OFFSET_BITS));
  auto first_unreturned = std::find_if(MSHR.begin(), MSHR.end(), [](auto x) { return x.event_cycle == std::numeric_limits<uint64_t>::max(); });

  #if ALLOW_PAM!=NOPAM
  // auto start5 = std::chrono::high_resolution_clock::now();
  bool l2orllc=false;
  if (NAME.find("L2C") != std::string::npos) {
    l2orllc=true;
    #if ALLOW_PAM==PAM_PC_COUNTER
    if(mshr_entry == MSHR.end()){
      uint64_t folded_addr = fold_addr(packet->ip);
      if(mshr_entry->llc_hit){
        dec_pam_pc_counter(folded_addr);
      }
      else{
        inc_pam_pc_counter(folded_addr);
      }
    }
    #endif
  }

  if (NAME.find("LLC") != std::string::npos) {l2orllc=true;}
  if(l2orllc){  
    if(packet->l2_parallel_access){
      //dbg
      //cout<<NAME<<" got return_data for parallel access"<<endl;
      bool already_returned = false;
      if(mshr_entry == MSHR.end()) {
        already_returned=true;
      }
      else if(mshr_entry->event_cycle!=std::numeric_limits<uint64_t>::max()){
        already_returned=true;
        //cout<<"WARN - data returned to "<<NAME<<" but mshr was still there at second return for parallel access"<<endl; //this is fine, but want to see if it occurs at all
      }
      if(already_returned){
        //check PA_wait_second_return for san check. and then just return
        //if(NAME=="LLC"){cout<<"segfaultcheck before finding PA_secondret_entry, PA_wait_second_return size: "<< PA_wait_second_return.size()<<endl;}
        auto PA_secondret_entry = std::find_if(PA_wait_second_return.begin(), PA_wait_second_return.end(), eq_addr<PACKET>(packet->address, OFFSET_BITS));
        //if(NAME=="LLC"){cout<<"segfaultcheck after finding PA_secondret_entry"<<endl;}
        if(PA_secondret_entry==PA_wait_second_return.end()){
          //cout<<"Data returned to "<<NAME<<" , but wasn't in MSHR or PA_wait_second_return. Inserting to LLC_early_returned"<<endl;
          //TODO - add to LLC_early_returned
          if(NAME!="LLC"){cout<<"WARN - data returned to "<<NAME<<" , but wasn't in MSHR or PA_wait_second_return"<<endl;}
          //dbg
          auto llc_er_duplicate_check = std::find_if(LLC_early_returned.begin(), LLC_early_returned.end(), eq_addr<PACKET>(packet->address, OFFSET_BITS));
          if(llc_er_duplicate_check!=LLC_early_returned.end()){
            cout<<"in inserting LLC_early_returned - found duplicate, cursize: "<<LLC_early_returned.size()<<endl;
          }
          ///
          LLC_early_ret_count++;
          LLC_early_returned.insert(std::end(LLC_early_returned), *packet);
          //cout<<"Inserted to LLC_early_returned"<<endl;
        }
        else{
          PA_wait_second_return.erase(PA_secondret_entry);
          //dbg
          //cout<<"data returned for the second time, found in PA_wait_second_return, resulting size: "<<PA_wait_second_return.size()<<endl;
        }
        return;
      }

    }
  }
  // auto end5 = std::chrono::high_resolution_clock::now();
  // auto duration5 = std::chrono::duration_cast<std::chrono::nanoseconds>(end5 - start5);
  // std::cout << "Time taken by code segment5: " << duration5.count() << " nanoseconds" << std::endl;
  #endif

  // sanity check
  if (mshr_entry == MSHR.end()) {
    std::cerr << "[" << NAME << "_MSHR] " << __func__ << " instr_id: " << packet->instr_id << " cannot find a matching entry!";
    std::cerr << " address: " << std::hex << packet->address;
    std::cerr << " v_address: " << packet->v_address;
    std::cerr << " address: " << (packet->address >> OFFSET_BITS) << std::dec;
    std::cerr << " event: " << packet->event_cycle << " current: " << current_cycle << std::endl;
    return;
  }

  // MSHR holds the most updated information about this request
  mshr_entry->data = packet->data;
  mshr_entry->pf_metadata = packet->pf_metadata;
  mshr_entry->event_cycle = current_cycle + (warmup_complete[cpu] ? FILL_LATENCY : 0);
  //TODO add noc delay at return to l2
  if (NAME.find("L2C") != std::string::npos) {
    uint64_t l2_id = cpu;
    uint64_t returner_id = 0;
    //if from mem, returner_id=NUM_CPUS
    //else, returner_id = get_cache_bank(packet->address);
    if(packet->ret_from_mem){returner_id = NUM_CPUS;}
    else{returner_id = get_cache_bank(packet->address);}
    uint64_t noc_delay = on_chip_icn_hops[l2_id][returner_id] * CYCLES_PER_NOC_HOP + SERIALIZATION_DELAY;
    mshr_entry->event_cycle = mshr_entry->event_cycle + noc_delay;

  }
  if(NAME=="LLC"){
    uint64_t returner_id = NUM_CPUS;
    uint64_t l3_id = get_cache_bank(packet->address);
    uint64_t noc_delay = on_chip_icn_hops[l3_id][returner_id] * CYCLES_PER_NOC_HOP + SERIALIZATION_DELAY;
    mshr_entry->event_cycle = mshr_entry->event_cycle + noc_delay;
  }

  DP(if (warmup_complete[packet->cpu]) {
    std::cout << "[" << NAME << "_MSHR] " << __func__ << " instr_id: " << mshr_entry->instr_id;
    std::cout << " address: " << std::hex << (mshr_entry->address >> OFFSET_BITS) << " full_addr: " << mshr_entry->address;
    std::cout << " data: " << mshr_entry->data << std::dec;
    std::cout << " index: " << std::distance(MSHR.begin(), mshr_entry) << " occupancy: " << get_occupancy(0, 0);
    std::cout << " event: " << mshr_entry->event_cycle << " current: " << current_cycle << std::endl;
  });

  // Order this entry after previously-returned entries, but before non-returned
  // entries
  std::iter_swap(mshr_entry, first_unreturned);

  //TODO - if l2 and pkt did PA, add entry to PA_wait_second_return
  #if ALLOW_PAM!=NOPAM
  //auto start6 = std::chrono::high_resolution_clock::now();
    if (NAME.find("L2C") != std::string::npos) {
      if(packet->l2_parallel_access){
        PA_wait_second_return.insert(std::end(PA_wait_second_return), *packet);
      }
    }
  // auto end6 = std::chrono::high_resolution_clock::now();
  // auto duration6 = std::chrono::duration_cast<std::chrono::nanoseconds>(end6 - start6);
  // std::cout << "Time taken by code segment6: " << duration6.count() << " nanoseconds" << std::endl;
  #endif
}

uint32_t CACHE::get_occupancy(uint8_t queue_type, uint64_t address)
{
  if (queue_type == 0)
    return std::count_if(MSHR.begin(), MSHR.end(), is_valid<PACKET>());
  else if (queue_type == 1)
    return RQ.occupancy();
  else if (queue_type == 2)
    return WQ.occupancy();
  else if (queue_type == 3)
    return PQ.occupancy();

  return 0;
}

uint32_t CACHE::get_size(uint8_t queue_type, uint64_t address)
{
  if (queue_type == 0)
    return MSHR_SIZE;
  else if (queue_type == 1)
    return RQ.size();
  else if (queue_type == 2)
    return WQ.size();
  else if (queue_type == 3)
    return PQ.size();

  return 0;
}

bool CACHE::should_activate_prefetcher(int type) { return (1 << static_cast<int>(type)) & pref_activate_mask; }

void CACHE::print_deadlock()
{
  if (!std::empty(MSHR)) {
    std::cout << NAME << " MSHR Entry" << std::endl;
    std::size_t j = 0;
    for (PACKET entry : MSHR) {
      std::cout << "[" << NAME << " MSHR] entry: " << j++ << " instr_id: " << entry.instr_id;
      std::cout << " address: " << std::hex << (entry.address >> LOG2_BLOCK_SIZE) << " full_addr: " << entry.address << std::dec << " type: " << +entry.type;
      std::cout << " fill_level: " << +entry.fill_level << " event_cycle: " << entry.event_cycle << std::endl;
    }
  } else {
    std::cout << NAME << " MSHR empty" << std::endl;
  }
}
