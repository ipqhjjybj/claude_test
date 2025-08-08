cmake_minimum_required(VERSION 3.16)
project(BinanceDPDKStream)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)

# Find DPDK
pkg_check_modules(DPDK REQUIRED libdpdk)

# Find websocketpp (header-only library)
find_path(WEBSOCKETPP_INCLUDE_DIR websocketpp/config.hpp)

# Find OpenSSL
find_package(OpenSSL REQUIRED)

# Find Boost
find_package(Boost REQUIRED COMPONENTS system thread chrono random)

# Find nlohmann_json
find_package(nlohmann_json REQUIRED)

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=native -O3 -g")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")

# Include directories
include_directories(include)
include_directories(${DPDK_INCLUDE_DIRS})
include_directories(${WEBSOCKETPP_INCLUDE_DIR})
include_directories(${Boost_INCLUDE_DIRS})

# Add compile definitions
add_definitions(${DPDK_CFLAGS_OTHER})

# Source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Create library
add_library(binance_dpdk_stream SHARED ${SOURCES})

# Link libraries
target_link_libraries(binance_dpdk_stream
    ${DPDK_LIBRARIES}
    ${Boost_LIBRARIES}
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
    pthread
)

# Examples
add_subdirectory(examples)

# Install
install(TARGETS binance_dpdk_stream
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include
    FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp"
)