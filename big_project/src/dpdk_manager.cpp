#include "dpdk_manager.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <rte_ethdev.h>
#include <rte_mempool.h>
#include <rte_malloc.h>

namespace binance_stream {

const struct rte_eth_conf DPDKManager::port_conf_default_ = {
    .rxmode = {
        .mq_mode = RTE_ETH_MQ_RX_RSS,
        .offloads = RTE_ETH_RX_OFFLOAD_CHECKSUM,
    },
    .rx_adv_conf = {
        .rss_conf = {
            .rss_key = nullptr,
            .rss_hf = RTE_ETH_RSS_IP | RTE_ETH_RSS_TCP | RTE_ETH_RSS_UDP,
        },
    },
    .txmode = {
        .mq_mode = RTE_ETH_MQ_TX_NONE,
        .offloads = RTE_ETH_TX_OFFLOAD_CHECKSUM,
    },
};

DPDKManager& DPDKManager::getInstance() {
    static DPDKManager instance;
    return instance;
}

DPDKManager::~DPDKManager() {
    cleanup();
}

int DPDKManager::initialize(const Config& config) {
    if (initialized_) {
        std::cout << "DPDK Manager already initialized" << std::endl;
        return 0;
    }

    config_ = config;

    // Initialize EAL
    if (initializeEAL(config.eal_args) < 0) {
        std::cerr << "Failed to initialize EAL" << std::endl;
        return -1;
    }

    // Create mbuf pool
    if (createMbufPool(config) < 0) {
        std::cerr << "Failed to create mbuf pool" << std::endl;
        rte_eal_cleanup();
        return -1;
    }

    // Check port capabilities
    if (checkPortCapabilities() < 0) {
        std::cerr << "Failed to check port capabilities" << std::endl;
        cleanup();
        return -1;
    }

    initialized_ = true;
    std::cout << "DPDK Manager initialized successfully with " << nb_ports_ << " ports" << std::endl;
    return 0;
}

void DPDKManager::cleanup() {
    if (!initialized_) {
        return;
    }

    stopPorts();

    if (mbuf_pool_) {
        rte_mempool_free(mbuf_pool_);
        mbuf_pool_ = nullptr;
    }

    rte_eal_cleanup();
    initialized_ = false;
    std::cout << "DPDK Manager cleaned up" << std::endl;
}

int DPDKManager::initializeEAL(const std::vector<std::string>& eal_args) {
    std::vector<char*> argv;
    std::vector<std::string> args = eal_args;
    
    if (args.empty()) {
        args = {"dpdk_app", "-l", "0-3", "-n", "4"};
    }

    for (auto& arg : args) {
        argv.push_back(const_cast<char*>(arg.c_str()));
    }

    int ret = rte_eal_init(argv.size(), argv.data());
    if (ret < 0) {
        std::cerr << "EAL initialization failed: " << rte_strerror(-ret) << std::endl;
        return ret;
    }

    std::cout << "EAL initialized successfully" << std::endl;
    return 0;
}

int DPDKManager::createMbufPool(const Config& config) {
    unsigned int nb_mbufs = 8192;
    unsigned int socket_id = rte_socket_id();

    mbuf_pool_ = rte_pktmbuf_pool_create(
        "MBUF_POOL",
        nb_mbufs,
        config.mempool_cache_size,
        config.mempool_priv_size,
        config.mempool_data_room_size,
        socket_id
    );

    if (!mbuf_pool_) {
        std::cerr << "Failed to create mbuf pool: " << rte_strerror(rte_errno) << std::endl;
        return -1;
    }

    std::cout << "Mbuf pool created successfully" << std::endl;
    return 0;
}

int DPDKManager::checkPortCapabilities() {
    nb_ports_ = rte_eth_dev_count_avail();
    
    if (nb_ports_ == 0) {
        std::cout << "No Ethernet ports available" << std::endl;
        return 0;
    }

    port_ids_.clear();
    port_ids_.reserve(nb_ports_);

    uint16_t port_id;
    RTE_ETH_FOREACH_DEV(port_id) {
        port_ids_.push_back(port_id);
        
        struct rte_eth_dev_info dev_info;
        int ret = rte_eth_dev_info_get(port_id, &dev_info);
        if (ret != 0) {
            std::cerr << "Failed to get device info for port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
            continue;
        }

        std::cout << "Port " << port_id << ": " << dev_info.driver_name << std::endl;
    }

    return 0;
}

uint16_t DPDKManager::getPortId(uint16_t index) const {
    if (index >= port_ids_.size()) {
        throw std::out_of_range("Port index out of range");
    }
    return port_ids_[index];
}

int DPDKManager::configurePorts() {
    if (!initialized_) {
        std::cerr << "DPDK Manager not initialized" << std::endl;
        return -1;
    }

    for (uint16_t port_id : port_ids_) {
        struct rte_eth_dev_info dev_info;
        int ret = rte_eth_dev_info_get(port_id, &dev_info);
        if (ret != 0) {
            std::cerr << "Failed to get device info for port " << port_id << std::endl;
            continue;
        }

        struct rte_eth_conf port_conf = port_conf_default_;
        port_conf.rxmode.offloads &= dev_info.rx_offload_capa;
        port_conf.txmode.offloads &= dev_info.tx_offload_capa;

        ret = rte_eth_dev_configure(port_id, 1, 1, &port_conf);
        if (ret < 0) {
            std::cerr << "Failed to configure port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
            continue;
        }

        ret = rte_eth_rx_queue_setup(port_id, 0, config_.nb_rxd,
                                     rte_eth_dev_socket_id(port_id),
                                     nullptr, mbuf_pool_);
        if (ret < 0) {
            std::cerr << "Failed to setup RX queue for port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
            continue;
        }

        ret = rte_eth_tx_queue_setup(port_id, 0, config_.nb_txd,
                                     rte_eth_dev_socket_id(port_id), nullptr);
        if (ret < 0) {
            std::cerr << "Failed to setup TX queue for port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
            continue;
        }

        std::cout << "Port " << port_id << " configured successfully" << std::endl;
    }

    return 0;
}

int DPDKManager::startPorts() {
    if (!initialized_) {
        std::cerr << "DPDK Manager not initialized" << std::endl;
        return -1;
    }

    for (uint16_t port_id : port_ids_) {
        int ret = rte_eth_dev_start(port_id);
        if (ret < 0) {
            std::cerr << "Failed to start port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
            continue;
        }

        ret = rte_eth_promiscuous_enable(port_id);
        if (ret != 0) {
            std::cerr << "Failed to enable promiscuous mode for port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
        }

        std::cout << "Port " << port_id << " started successfully" << std::endl;
    }

    return 0;
}

void DPDKManager::stopPorts() {
    for (uint16_t port_id : port_ids_) {
        int ret = rte_eth_dev_stop(port_id);
        if (ret != 0) {
            std::cerr << "Failed to stop port " << port_id 
                      << ": " << rte_strerror(-ret) << std::endl;
        }
        
        rte_eth_dev_close(port_id);
        std::cout << "Port " << port_id << " stopped" << std::endl;
    }
}

void DPDKManager::printPortStats(uint16_t port_id) {
    struct rte_eth_stats stats;
    int ret = rte_eth_stats_get(port_id, &stats);
    if (ret != 0) {
        std::cerr << "Failed to get stats for port " << port_id << std::endl;
        return;
    }

    std::cout << "Port " << port_id << " Stats:" << std::endl;
    std::cout << "  RX packets: " << stats.ipackets << std::endl;
    std::cout << "  TX packets: " << stats.opackets << std::endl;
    std::cout << "  RX bytes: " << stats.ibytes << std::endl;
    std::cout << "  TX bytes: " << stats.obytes << std::endl;
    std::cout << "  RX errors: " << stats.ierrors << std::endl;
    std::cout << "  TX errors: " << stats.oerrors << std::endl;
}

void DPDKManager::printEthStats() {
    for (uint16_t port_id : port_ids_) {
        printPortStats(port_id);
    }
}

} // namespace binance_stream