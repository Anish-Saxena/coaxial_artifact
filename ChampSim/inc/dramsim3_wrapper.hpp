#ifndef __DRAMSIM3__H
#define __DRAMSIM3__H

#include "champsim_constants.h"
#include "memory_class.h"
#include "operable.h"
#include "dramsim3.h"
#include "util.h"

namespace dramsim3 {
    class MemorySystem;
};

extern uint8_t all_warmup_complete;

// This is a wrapper so DRAMSim (which only returns trans. addr) can communicate
// with ChampSim API (which requires explicit packet->to_return->return_data calls)
// We maintain a "Meta-RQ" to send callbacks to LLC (relies on LLC MSHR to merge duplicate reqs)
class DRAMSim3_DRAM: public champsim::operable, public MemoryRequestConsumer
{
public:
    DRAMSim3_DRAM(double freq_scale, const std::string& config_file, const std::string& output_dir):
        champsim::operable(freq_scale), 
        MemoryRequestConsumer(std::numeric_limits<unsigned>::max()) {
            memory_system_ = new dramsim3::MemorySystem(config_file, output_dir,
                                            std::bind(&DRAMSim3_DRAM::ReadCallBack, this, std::placeholders::_1),
                                            std::bind(&DRAMSim3_DRAM::WriteCallBack, this, std::placeholders::_1));
            std::cout << "DRAMSim3_DRAM init" << std::endl;   
        }


    int add_rq(PACKET* packet) override {
        if (all_warmup_complete < NUM_CPUS) {
            for (auto ret : packet->to_return)
                ret->return_data(packet);

            return -1; // Fast-forward
        }

        // Check for duplicates
        auto rq_it = std::find_if(std::begin(RQ), std::end(RQ), 
                                    eq_addr<PACKET>(packet->address, LOG2_BLOCK_SIZE));
        if (rq_it != std::end(RQ)) {
            // We shouldn't get duplicates as LLC MSHR handles it
            // std::cout << "[PANIC] Cannot add to DRAM RQ as it already contains packet! Exiting..." << std::endl;
            // assert(0);
            //this could happen with Parallel access from L2
            std::cout << "[WARN] Cannot add to DRAM RQ as it already contains packet! Just return in this corner casepacket->instr_id: "<<packet->instr_id << std::endl;
            for (auto ret : packet->to_return){
                // TODO - LLC might have merged the MSHR entries, so might have to not return to LLC
                ret->return_data(packet);
            }
            return get_occupancy(1, packet->address); 
            
        } 
        
        // Find empty slot
        rq_it = std::find_if_not(std::begin(RQ), std::end(RQ), is_valid<PACKET>());
        if (rq_it == std::end(RQ) || memory_system_->WillAcceptTransaction(packet->address, false) == false) {
			std::cout<<"[PANIC] RQ cannot accept entries or DRAMSim3 cannot accept transaction! packet->instr_id: "<<packet->instr_id<<std::endl;
            assert(0); // This should not happen as we check occupancy before calling add_rq
        }
        // Call to DRAMSim
        memory_system_->AddTransaction(packet->address, false);

        // Add to RQ
        // Remember this packet to later return data
        *rq_it = *packet;

        return get_occupancy(1, packet->address);
    }

    int add_wq(PACKET* packet) override {
        if (all_warmup_complete < NUM_CPUS)
            return -1; // Fast-forward

        // If DRAMSim cannot take new req, return
        if (!memory_system_->WillAcceptTransaction(packet->address, true)) {
            return -2;
        }
        // Call to DRAMSim
        memory_system_->AddTransaction(packet->address, true);
        return 0;
    }

    int add_pq(PACKET* packet) override {
        return add_rq(packet);
    }

    void operate() override {
        memory_system_->ClockTick();
    }

    uint32_t get_occupancy(uint8_t queue_type, uint64_t address) override {
        if (queue_type == 1) {
            if (!memory_system_->WillAcceptTransaction(address, false)) {
                // DRAMSim cannot accept transaction, this addr must not be inserted
                return RQ.size();
            }
            else {
                return std::count_if(std::begin(RQ), std::end(RQ), is_valid<PACKET>());
            }
        }
        else if (queue_type == 2) {
            return memory_system_->WillAcceptTransaction(address, true) ? 0 : RQ.size();
        }
        else if (queue_type == 3)
            return get_occupancy(1, address);

        return -1;        
    }
    uint32_t get_size(uint8_t queue_type, uint64_t address) override {
        if (queue_type == 1)
            return RQ.size();
        else if (queue_type == 2)
            return RQ.size();
        else if (queue_type == 3)
            return get_size(1, address);
        return -1;
    }

    void ReadCallBack(uint64_t addr) { 
        auto rq_pkt = std::find_if(std::begin(RQ), std::end(RQ), 
                                    eq_addr<PACKET>(addr, LOG2_BLOCK_SIZE));
        if (rq_pkt != std::end(RQ)) {
            for (auto ret : rq_pkt->to_return) 
                ret->return_data(&(*rq_pkt));
            *rq_pkt = {};
        }
        else {
            std::cout << "[PANIC] RQ packet not found on DRAMSim req completion! Exiting..." 
                        << std::endl;
            assert(0);
        }
    }
    void WriteCallBack(uint64_t addr) { return; }
    void PrintStats() { memory_system_->PrintStats(); }
    void ResetStats() { memory_system_->ResetStats(); }
protected:
    dramsim3::MemorySystem* memory_system_;
    std::vector<PACKET> RQ{DRAM_RQ_SIZE*DRAM_CHANNELS}; // Meta-RQ for callbacks
};

#endif
