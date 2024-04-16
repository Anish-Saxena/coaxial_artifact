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

#ifndef CACHE_H
#define CACHE_H

#include <functional>
#include <list>
#include <string>
#include <vector>

#include "champsim.h"
#include "delay_queue.hpp"
#include "memory_class.h"
#include "ooo_cpu.h"
#include "operable.h"
#include <chrono>

// virtual address space prefetching
#define VA_PREFETCH_TRANSLATION_LATENCY 2

#define NOPAM 0
#define PAM_PC_COUNTER 1
#define PAM_IDEAL_PREDICTOR 2
#define PAM_STATIC_THRESHOLD 3

#define FOLD_BITS 9
#define SIZEOF_PC_COUNTER 512
#define NUMBITS_PC_COUNTER 3

#define DDR5_BW 38
#define PAM_INTERVAL 100000 // set L2_PA every N cycles

#define CYCLES_PER_NOC_HOP 6 // 3, X2 for rtt
#define SERIALIZATION_DELAY 4 // 2, X2 for both ways?

extern std::array<O3_CPU*, NUM_CPUS> ooo_cpu;

class CACHE : public champsim::operable, public MemoryRequestConsumer, public MemoryRequestProducer
{
public:
  uint32_t cpu;
  const std::string NAME;
  const uint32_t NUM_SET, NUM_WAY, WQ_SIZE, RQ_SIZE, PQ_SIZE, MSHR_SIZE;
  const uint32_t HIT_LATENCY, FILL_LATENCY, OFFSET_BITS;
  std::vector<BLOCK> block{NUM_SET * NUM_WAY};
  const uint32_t MAX_READ, MAX_WRITE;
  uint32_t reads_available_this_cycle, writes_available_this_cycle;
  const bool prefetch_as_load;
  const bool match_offset_bits;
  const bool virtual_prefetch;
  bool ever_seen_data = false;
  //bool L2_PA = true;
  const unsigned pref_activate_mask = (1 << static_cast<int>(LOAD)) | (1 << static_cast<int>(PREFETCH));

  const uint64_t TH_L2PA = (DDR5_BW * DRAM_CHANNELS * PAM_TH) / 200; //BW threshold for allowing L2 Parallel Access 50%
  //const uint64_t TH_L2PA = (DDR5_BW * DRAM_CHANNELS * 50) / 100; //BW threshold for allowing L2 Parallel Access 50%
  //const uint64_t TH_L2PA = (DDR5_BW * DRAM_CHANNELS * 60) / 100; //BW threshold for allowing L2 Parallel Access 60%
  //const uint64_t TH_L2PA = (DDR5_BW * DRAM_CHANNELS * 70) / 100; //BW threshold for allowing L2 Parallel Access 60%
  uint64_t llc_misses_last_interval=0;
  uint64_t llc_accs_last_interval = 0;
  uint64_t l2_pa_next_period=0;

  // prefetch stats
  uint64_t pf_requested = 0, pf_issued = 0, pf_useful = 0, pf_useless = 0, pf_fill = 0;

  // queues
  champsim::delay_queue<PACKET> RQ{RQ_SIZE, HIT_LATENCY}, // read queue
      PQ{PQ_SIZE, HIT_LATENCY},                           // prefetch queue
      VAPQ{PQ_SIZE, VA_PREFETCH_TRANSLATION_LATENCY},     // virtual address prefetch queue
      WQ{WQ_SIZE, HIT_LATENCY};                           // write queue

  std::list<PACKET> MSHR; // MSHR
  std::list<PACKET> PA_wait_second_return;
  std::list<PACKET> LLC_early_returned;

  uint64_t PC_COUNTER[SIZEOF_PC_COUNTER];

  std::chrono::_V2::system_clock::time_point last_ts;

  uint64_t sim_access[NUM_CPUS][NUM_TYPES] = {}, sim_hit[NUM_CPUS][NUM_TYPES] = {}, sim_miss[NUM_CPUS][NUM_TYPES] = {}, roi_access[NUM_CPUS][NUM_TYPES] = {},
           roi_hit[NUM_CPUS][NUM_TYPES] = {}, roi_miss[NUM_CPUS][NUM_TYPES] = {};

  uint64_t RQ_ACCESS = 0, RQ_MERGED = 0, RQ_FULL = 0, RQ_TO_CACHE = 0, PQ_ACCESS = 0, PQ_MERGED = 0, PQ_FULL = 0, PQ_TO_CACHE = 0, WQ_ACCESS = 0, WQ_MERGED = 0,
           WQ_FULL = 0, WQ_FORWARD = 0, WQ_TO_CACHE = 0;
  uint64_t RETURN_DATA_CALLS = 0, LLC_early_ret_count=0;
  uint64_t PA_count=0, PA_hit=0;
  uint64_t PAM_false_positive = 0; //issued PA but was hit in LLC
  uint64_t PAM_false_negative=0; // didn't issue PA but was miss in LLC
  uint64_t PAM_count_per_l2c=0;

  uint64_t total_miss_latency[NUM_CPUS] = {0};
  uint64_t lat_hist[NUM_CPUS][200]={0};

  // functions
  int add_rq(PACKET* packet) override;
  int add_wq(PACKET* packet) override;
  int add_pq(PACKET* packet) override;

  void return_data(PACKET* packet) override;
  void operate() override;
  void operate_writes();
  void operate_reads();

  uint64_t set_l2_pa();
  void inc_pam_pc_counter(uint64_t folded_addr);
  void dec_pam_pc_counter(uint64_t folded_addr);
  bool check_pam_pc_counter(uint64_t folded_addr);

  uint32_t get_occupancy(uint8_t queue_type, uint64_t address) override;
  uint32_t get_size(uint8_t queue_type, uint64_t address) override;

  uint32_t get_set(uint64_t address);
  uint32_t get_way(uint64_t address, uint32_t set);

  int invalidate_entry(uint64_t inval_addr);
  bool probe_entry(uint64_t addr);
  int prefetch_line(uint64_t pf_addr, bool fill_this_level, uint32_t prefetch_metadata);
  int prefetch_line(uint64_t ip, uint64_t base_addr, uint64_t pf_addr, bool fill_this_level, uint32_t prefetch_metadata); // deprecated

  void add_mshr(PACKET* packet);
  void va_translate_prefetches();

  void handle_fill();
  void handle_writeback();
  void handle_read();
  void handle_prefetch();

  void readlike_hit(std::size_t set, std::size_t way, PACKET& handle_pkt);
  bool readlike_miss(PACKET& handle_pkt);
  bool filllike_miss(std::size_t set, std::size_t way, PACKET& handle_pkt);

  bool should_activate_prefetcher(int type);

  void print_deadlock() override;

#include "cache_modules.inc"

  const repl_t repl_type;
  const pref_t pref_type;

  // constructor
  CACHE(std::string v1, double freq_scale, unsigned fill_level, uint32_t v2, int v3, uint32_t v5, uint32_t v6, uint32_t v7, uint32_t v8, uint32_t hit_lat,
        uint32_t fill_lat, uint32_t max_read, uint32_t max_write, std::size_t offset_bits, bool pref_load, bool wq_full_addr, bool va_pref,
        unsigned pref_act_mask, MemoryRequestConsumer* ll, pref_t pref, repl_t repl)
      : champsim::operable(freq_scale), MemoryRequestConsumer(fill_level), MemoryRequestProducer(ll), NAME(v1), NUM_SET(v2), NUM_WAY(v3), WQ_SIZE(v5),
        RQ_SIZE(v6), PQ_SIZE(v7), MSHR_SIZE(v8), HIT_LATENCY(hit_lat), FILL_LATENCY(fill_lat), OFFSET_BITS(offset_bits), MAX_READ(max_read),
        MAX_WRITE(max_write), prefetch_as_load(pref_load), match_offset_bits(wq_full_addr), virtual_prefetch(va_pref), pref_activate_mask(pref_act_mask),
        repl_type(repl), pref_type(pref)
  {
    std::cout << "Init " << v1 << " size " << (NUM_SET * NUM_WAY * BLOCK_SIZE)/1024 << "KB" << std::endl;
    if(NAME=="LLC"){
      cout<<"PAM Threshold: "<<TH_L2PA<<"GB/s"<<endl;
    }
    if (NAME.find("L2C") != std::string::npos) {
      for(int i=0; i<SIZEOF_PC_COUNTER;i++){
        PC_COUNTER[i]=1<<(NUMBITS_PC_COUNTER-1);
      }
    }
  }
};

#endif
