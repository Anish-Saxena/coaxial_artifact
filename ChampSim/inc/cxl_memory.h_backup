#ifndef CXL_DRAM_H
#define CXL_DRAM_H

#include <array>
#include <cmath>
#include <limits>

#include "champsim_constants.h"
#include "delay_queue.hpp"
#include "memory_class.h"
#include "operable.h"
#include "util.h"

/*
* CXL-PCIe interface
* READS: Each read goes into the read queue which delays it by tCXL and then relays it to DRAM.
* Upon its return from DRAM, it is added to the response queue which delays it by another tCXL
* and then sends it back to the cache while limiting bandwidth.
* WRITES: Each write goes into the write queue which delays it by tCXL and then limits bandwidth 
* before relaying the packet to the DRAM.
*/

class CXL_MEMORY : public champsim::operable, public MemoryRequestConsumer, public MemoryRequestProducer
{
public:
  const std::string NAME;
  const static uint64_t tCXL = detail::ceil(1.0 * tCXL_DRAM_NANOSECONDS * CXL_IO_FREQ / 1000);
  const static uint64_t tRD = detail::ceil(1.0 * BLOCK_SIZE*8.0/(CXL_RD_BW*CXL_RD_CH_WIDTH_BITS) 
                                                  * CXL_IO_FREQ / 1000);
  const static uint64_t tWR = detail::ceil(1.0 * BLOCK_SIZE*8.0/(CXL_WR_BW*CXL_WR_CH_WIDTH_BITS) 
                                                  * CXL_IO_FREQ / 1000);
  struct CXL_BUS {
    PACKET* active_rd_resp_on_bus = NULL;
    PACKET* active_wr_req_on_bus = NULL;
    uint64_t rd_bus_cycle_available = 0, wr_bus_cycle_available = 0;
    bool rd_pkt_valid = false, wr_pkt_valid = false;
  };
  struct CXL_CHANNEL {
    // RespQ must accommodate more requests due to limited read bandwidth
    champsim::delay_queue<PACKET> RQ{CXL_RQ_SIZE, tCXL},
                                  WQ{CXL_WQ_SIZE, tCXL},
                                  RespQ{detail::ceil(32.0*CXL_RQ_SIZE/CXL_RD_BW), tCXL};
    struct CXL_BUS bus = {};
    uint64_t s_reads = 0, s_writes = 0, s_resps = 0, s_read_dup_merged = 0, s_rd_to_wr_forward = 0,
            s_rq_full = 0, s_wr_dup_merged = 0, s_wq_full = 0, s_rdbus_cycles_congested = 0, 
            s_rdbus_cycles_occ = 0, s_wr_dram_wq_full_retry = 0, s_wrbus_cycles_occ = 0,
            s_wrbus_cycles_congested = 0, s_rd_dram_rq_full_retry = 0, s_rd_tot_qdelay = 0,
            s_wr_tot_qdelay = 0;
  };

  uint64_t s_cycles = 0;
  uint64_t RQ_ACCESS=0;

  std::array<struct CXL_CHANNEL, CXL_CHANNELS> channels;

  int add_rq(PACKET* packet) override;
  int add_wq(PACKET* packet) override;
  int add_pq(PACKET* packet) override;
  void return_data(PACKET* packet) override;

  void operate() override;
  void operate_bus();
  void operate_channel();

  void handle_responses();
  void handle_writes();
  void handle_reads();

  uint32_t get_occupancy(uint8_t queue_type, uint64_t address) override;
  uint32_t get_size(uint8_t queue_type, uint64_t address) override;
  uint32_t get_channel(uint64_t address);

  void PrintStats();
  void ResetStats();

  CXL_MEMORY(std::string name, double freq_scale, unsigned fill_level, MemoryRequestConsumer* ll)
          : champsim::operable(freq_scale), MemoryRequestConsumer(fill_level), 
            MemoryRequestProducer(ll), NAME(name)
  {
    std::cout << "Initialized CXL memory with " << CXL_CHANNELS << " channels" << std::endl;
    std::cout << "tCXL " << tCXL << " tRD " << tRD << " tWR " << tWR << std::endl;
  }
};

#endif
