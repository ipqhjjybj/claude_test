#pragma once

#include <memory>
#include <vector>
#include <string>
#include <rte_common.h>
#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_mempool.h>
#include <rte_mbuf.h>
#include <rte_lcore.h>

namespace binance_stream {

class DPDKManager {
public:
    struct Config {
        uint16_t nb_rxd = 1024;
        uint16_t nb_txd = 1024;
        uint32_t mempool_cache_size = 256;
        uint32_t mempool_priv_size = 0;
        uint32_t mempool_data_room_size = RTE_MBUF_DEFAULT_BUF_SIZE;
        std::vector<std::string> eal_args;
    };

    static DPDKManager& getInstance();
    
    int initialize(const Config& config);
    void cleanup();
    
    bool isInitialized() const { return initialized_; }
    struct rte_mempool* getMbufPool() const { return mbuf_pool_; }
    
    uint16_t getNumPorts() const { return nb_ports_; }
    uint16_t getPortId(uint16_t index) const;
    
    int configurePorts();
    int startPorts();
    void stopPorts();
    
    void printPortStats(uint16_t port_id);
    void printEthStats();

private:
    DPDKManager() = default;
    ~DPDKManager();
    
    DPDKManager(const DPDKManager&) = delete;
    DPDKManager& operator=(const DPDKManager&) = delete;
    
    int initializeEAL(const std::vector<std::string>& eal_args);
    int createMbufPool(const Config& config);
    int checkPortCapabilities();
    
    bool initialized_ = false;
    struct rte_mempool* mbuf_pool_ = nullptr;
    uint16_t nb_ports_ = 0;
    std::vector<uint16_t> port_ids_;
    Config config_;
    
    static const struct rte_eth_conf port_conf_default_;
};

} // namespace binance_stream