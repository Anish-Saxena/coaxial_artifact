#include "cxl_memory.h"
#include <algorithm>
#include "champsim_constants.h"
#include "util.h"
#include "cache.h"

extern uint8_t all_warmup_complete;

int CXL_MEMORY::add_rq(PACKET* packet) 
{
    RQ_ACCESS++;
    if (all_warmup_complete < NUM_CPUS) {
        // #if ALLOW_PAM
        //     if(packet->l2_parallel_access){
        //         //dbg
        //         std::cout<<"l2_pam seen at CXL_MEMORY add_rq, to_return.size: "<< packet->to_return.size()<<std::endl;
        //         for (auto ret : packet->to_return)
        //             std::cout<<((CACHE*)ret)->NAME<<std::endl;
        //         //dbgend
        //         uint64_t n_returns = packet->to_return.size();
        //         if(n_returns!=2){std::cout<<"MEM(CXL_MEMORY): to return destinations for PA is not 2 but: "<<n_returns <<std::endl;}
        //     }
        // #endif
        for (auto ret : packet->to_return)
            ret->return_data(packet);

        return -1; // Fast-forward
    }

    auto& channel = channels[get_channel(packet->address)];

    channel.s_reads++;

    // check for the latest writebacks in the write queue
    auto found_wq = std::find_if(channel.WQ.begin(), channel.WQ.end(), 
                                eq_addr<PACKET>(packet->address, LOG2_BLOCK_SIZE));
    if (found_wq != channel.WQ.end()) {
        packet->ret_from_mem=true;
        channel.s_rd_to_wr_forward++;
        packet->data = found_wq->data;
        for (auto ret : packet->to_return)
        ret->return_data(packet);
        return -1;
    }

    // check for duplicates in the read queue
    auto found_rq = std::find_if(std::begin(channel.RQ), std::end(channel.RQ), 
                                eq_addr<PACKET>(packet->address, LOG2_BLOCK_SIZE));
    if (found_rq != std::end(channel.RQ)) {
        channel.s_read_dup_merged++;
        packet_dep_merge(found_rq->lq_index_depend_on_me, packet->lq_index_depend_on_me);
        packet_dep_merge(found_rq->sq_index_depend_on_me, packet->sq_index_depend_on_me);
        packet_dep_merge(found_rq->instr_depend_on_me, packet->instr_depend_on_me);
        packet_dep_merge(found_rq->to_return, packet->to_return);

        return 0; // merged index
    }

    if (channel.RQ.full()) {
        channel.s_rq_full++;
        return -2;
    }

    channel.RQ.push_back(*packet);
    return channel.RQ.occupancy();
}

int CXL_MEMORY::add_wq(PACKET* packet) 
{
    if (all_warmup_complete < NUM_CPUS)
        return -1; // Fast-forward
    
    auto& channel = channels[get_channel(packet->address)];
    channel.s_writes++;

    // check for duplicates in the write queue
    auto found_wq = std::find_if(channel.WQ.begin(), channel.WQ.end(), 
                                eq_addr<PACKET>(packet->address, LOG2_BLOCK_SIZE));
    if (found_wq != channel.WQ.end()) {
        channel.s_wr_dup_merged++;
        return 0; // merged index
    }

    // Check for room in the queue
    if (channel.WQ.full()) {
        channel.s_wq_full++;
        return -2;
    }

    packet->event_cycle = current_cycle;
    channel.WQ.push_back(*packet);

    return channel.WQ.occupancy();
}

int CXL_MEMORY::add_pq(PACKET* packet) { return add_rq(packet); }

void CXL_MEMORY::return_data(PACKET* packet)
{
    auto& channel = channels[get_channel(packet->address)];
    if (channel.RespQ.full()) {
        std::cout << "[PANIC] CXL RespQ full! Exiting..." << std::endl;
        assert(0);
    }
    packet->event_cycle = current_cycle;
    // Restore callback to LLC
    packet->to_return = packet->on_return_to_cxl;
    packet->ret_from_mem=true;
    channel.s_resps++;
    channel.RespQ.push_back(*packet);
}

void CXL_MEMORY::operate() 
{
    s_cycles++;
    operate_bus();
    operate_channel();
}

void CXL_MEMORY::operate_bus() 
{
    handle_responses();
    handle_writes();
    
    for (auto& channel: channels) {
        channel.RespQ.operate();
        channel.WQ.operate();
    }
}

void CXL_MEMORY::operate_channel()
{
    handle_reads();

    for (auto& channel: channels) {
        channel.RQ.operate();
    }
}

void CXL_MEMORY::handle_responses()
{
    for (auto& channel: channels) {
        if (channel.bus.rd_pkt_valid) {
            channel.s_rdbus_cycles_occ++;
        }
        // Send completed response on read bus to LLC
        if (channel.bus.rd_pkt_valid && channel.bus.rd_bus_cycle_available <= current_cycle) {
            //dbg
            // #if ALLOW_PAM
            // if(channel.bus.active_rd_resp_on_bus->l2_parallel_access){
            //     uint64_t n_returns = channel.bus.active_rd_resp_on_bus->to_return.size();
            //     if(n_returns!=2){std::cout<<"MEM(CXL_MEMORY): to return destinations for PA is not 2 but: "<<n_returns <<std::endl;}
            // }
            // #endif
            //std::cout<<"AFter warmup - 2_pam seen at CXL_MEMORY add_rq, to_return.size: "<< channel.bus.active_rd_resp_on_bus->to_return.size()<<std::endl;
            // for (auto ret : channel.bus.active_rd_resp_on_bus->to_return)
            //         std::cout<<((CACHE*)ret)->NAME<<std::endl;

            channel.bus.active_rd_resp_on_bus->ret_from_mem=true;
            for (auto ret : channel.bus.active_rd_resp_on_bus->to_return) {
                ret->return_data(&(*channel.bus.active_rd_resp_on_bus));
            }
            channel.bus.rd_pkt_valid = false;
            channel.RespQ.pop_front();
        }
        // Put a new resp on bus if bus is free and respQ has new ready resp
        if (!channel.bus.rd_pkt_valid && channel.RespQ.has_ready()) {
            channel.bus.active_rd_resp_on_bus = &channel.RespQ.front();
            channel.s_rd_tot_qdelay += 
                    current_cycle - channel.bus.active_rd_resp_on_bus->event_cycle - tCXL;
            channel.bus.rd_pkt_valid = true;
            channel.bus.rd_bus_cycle_available = current_cycle + tRD;
        }
        else if (channel.RespQ.has_ready() && ((channel.bus.active_rd_resp_on_bus->address 
                >> LOG2_BLOCK_SIZE)) != (channel.RespQ.front().address >> LOG2_BLOCK_SIZE)) {
            // RespQ has ready resp but bus is busy
            channel.s_rdbus_cycles_congested++;
        }
    }
}

void CXL_MEMORY::handle_writes()
{
    for (auto& channel: channels) {
        if (channel.bus.wr_pkt_valid) {
            channel.s_wrbus_cycles_occ++;
        }
        // Send completed req on write bus to DRAM
        if (channel.bus.wr_pkt_valid && channel.bus.wr_bus_cycle_available <= current_cycle) {
            if (lower_level->get_occupancy(2, channel.bus.active_wr_req_on_bus->address)
                == lower_level->get_size(2, channel.bus.active_wr_req_on_bus->address)) {
                // DRAM's write queue is full, will retry next cycle
                channel.s_wr_dram_wq_full_retry++;
                continue;
            }
            else {
                // Add Write req to DRAM's WQ
                PACKET& handle_pkt = channel.WQ.front();
                lower_level->add_wq(&handle_pkt);
                channel.bus.wr_pkt_valid = false;
                channel.WQ.pop_front();
            }
        }
        // Put a new req on bus if bus is free and WQ has new ready req
        if (!channel.bus.wr_pkt_valid && channel.WQ.has_ready()) {
            channel.bus.active_wr_req_on_bus = &channel.WQ.front();
            channel.s_wr_tot_qdelay += 
                current_cycle - channel.bus.active_wr_req_on_bus->event_cycle - tCXL;
            channel.bus.wr_pkt_valid = true;
            channel.bus.wr_bus_cycle_available = current_cycle + tWR;
        }
        else if (channel.WQ.has_ready() && ((channel.bus.active_wr_req_on_bus->address 
                >> LOG2_BLOCK_SIZE)) != (channel.WQ.front().address >> LOG2_BLOCK_SIZE)) {
            // WQ has ready req but bus is busy
            channel.s_wrbus_cycles_congested++;
        }
    }
}

void CXL_MEMORY::handle_reads()
{
    for (auto& channel: channels) {
        while (channel.RQ.has_ready()) {
            PACKET& handle_pkt = channel.RQ.front();
            if (lower_level->get_occupancy(1, handle_pkt.address) 
                == lower_level->get_size(1, handle_pkt.address)) {
                // DRAM's read queue is full, will retry next cycle
                channel.s_rd_dram_rq_full_retry++;
                break;
            }
            else {
                // Ensure CXL intercepts the response to add delay
                handle_pkt.on_return_to_cxl = handle_pkt.to_return;
                handle_pkt.to_return = {this};
                // Add Read req to DRAM's RQ
                lower_level->add_rq(&handle_pkt);
                channel.RQ.pop_front();
            }
        }
    }
}

uint32_t CXL_MEMORY::get_occupancy(uint8_t queue_type, uint64_t address) {
    auto& channel = channels[get_channel(address)];
    if (queue_type == 1)
        return channel.RQ.occupancy();
    else if (queue_type == 2)
        return channel.WQ.occupancy();
    else if (queue_type == 3)
        return channel.RQ.occupancy();
    
    return -1;
}

uint32_t CXL_MEMORY::get_size(uint8_t queue_type, uint64_t address)
{
    auto& channel = channels[get_channel(address)];
    if (queue_type == 1)
        return channel.RQ.size();
    else if (queue_type == 2)
        return channel.WQ.size();
    else if (queue_type == 3)
        return channel.RQ.size();

    return -1;
}

uint32_t CXL_MEMORY::get_channel(uint64_t address) {
    // We want 2 consecutive lines to go to same CXL channel 
    // Note that each DDR5 channel contains 2 sub-channels
    return (((address >> LOG2_BLOCK_SIZE)/2)%CXL_CHANNELS);
}

void CXL_MEMORY::ResetStats() {
    s_cycles = 0;
    for (auto& channel: channels) {
        channel.s_reads = 0, channel.s_writes = 0, channel.s_resps = 0, 
        channel.s_read_dup_merged = 0, channel.s_rd_to_wr_forward = 0,
        channel.s_rq_full = 0, channel.s_wr_dup_merged = 0, channel.s_wq_full = 0, 
        channel.s_rdbus_cycles_congested = 0, channel.s_rdbus_cycles_occ = 0, 
        channel.s_wr_dram_wq_full_retry = 0, channel.s_wrbus_cycles_occ = 0,
        channel.s_wrbus_cycles_congested = 0, channel.s_rd_dram_rq_full_retry = 0, 
        channel.s_rd_tot_qdelay = 0, channel.s_wr_tot_qdelay = 0;
    }
}

void CXL_MEMORY::PrintStats() {
    std::cout << std::endl;
    std::cout << "CXL-PCIe Stats" << std::endl;
    std::cout << "CXL_CYCLES " << s_cycles << std::endl;
    std::cout << "CUMULATIVE_STATS_OVER_ALL_CHANNELS" << std::endl;
    uint64_t cum_stats[16] = {0};
    std::string stat_prefix = "CXL_";
    std::string statnames[16] = {"READS", "WRITES", "RESPONSES", "DUP_READS_MERGED", "RD_TO_WR_FORWARDS",
            "CXL_RQ_FULL", "DUP_WRITES_MERGED", "CXL_WQ_FULL", "RDBUS_CYCLES_CONGESTED", 
            "RDBUS_CYCLES_OCC", "DRAM_WQ_FULL_RETRY", "WRBUS_CYCLES_OCC", "WRBUS_CYCLES_CONGESTED",
            "DRAM_RQ_FULL_RETRY", "READS_CXL_TOT_QDELAY", "WRITES_CXL_TOT_QDELAY"};
    for (auto& channel: channels) {
        cum_stats[0] += channel.s_reads;
        cum_stats[1] += channel.s_writes;
        cum_stats[2] += channel.s_resps;
        cum_stats[3] += channel.s_read_dup_merged;
        cum_stats[4] += channel.s_rd_to_wr_forward;
        cum_stats[5] += channel.s_rq_full;
        cum_stats[6] += channel.s_wr_dup_merged;
        cum_stats[7] += channel.s_wq_full;
        cum_stats[8] += channel.s_rdbus_cycles_congested;
        cum_stats[9] += channel.s_rdbus_cycles_occ;
        cum_stats[10] += channel.s_wr_dram_wq_full_retry;
        cum_stats[11] += channel.s_wrbus_cycles_occ;
        cum_stats[12] += channel.s_wrbus_cycles_congested;
        cum_stats[13] += channel.s_rd_dram_rq_full_retry;
        cum_stats[14] += channel.s_rd_tot_qdelay;
        cum_stats[15] += channel.s_wr_tot_qdelay;
    }
    for (int i = 0; i < 16; i++) {
        std::cout << stat_prefix << statnames[i] << " " << cum_stats[i] << std::endl;
    }
    std::cout << std::endl;
    std::cout << "AVERAGED_OUT_OR_RATIO_STATS" << std::endl;
    float rd_avg_qdelay_ns = ((1.0*cum_stats[14])/(CXL_IO_FREQ/1000.0))/cum_stats[2];
    float wr_avg_qdelay_ns = ((1.0*cum_stats[15])/(CXL_IO_FREQ/1000.0))/cum_stats[1];
    float rd_bus_util = (1.0*cum_stats[9])/(1.0*CXL_CHANNELS*s_cycles);
    float wr_bus_util = (1.0*cum_stats[11])/(1.0*CXL_CHANNELS*s_cycles);
    float rd_bus_congested = (1.0*cum_stats[8])/(1.0*CXL_CHANNELS*s_cycles);
    float wr_bus_congested = (1.0*cum_stats[12])/(1.0*CXL_CHANNELS*s_cycles);

    std::cout << stat_prefix << "READS_QDELAY_NS " << rd_avg_qdelay_ns << std::endl;
    std::cout << stat_prefix << "WRITES_QDELAY_NS " << wr_avg_qdelay_ns << std::endl;
    std::cout << stat_prefix << "RDBUS_UTILIZATION " << rd_bus_util << std::endl;
    std::cout << stat_prefix << "WRBUS_UTILIZATION " << wr_bus_util << std::endl;
    std::cout << stat_prefix << "RDBUS_CONGESTED " << rd_bus_congested << std::endl;
    std::cout << stat_prefix << "WRBUS_CONGESTED " << wr_bus_congested << std::endl;
    std::cout << std::endl;
}