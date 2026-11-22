#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <functional>
#include "WinSerialPort.h"

namespace BSLab {

class SpdFdlEngine {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;
    using ProgressCallback = std::function<void(float pct, const std::string& status)>;

    // Default RAM execution addresses for modern Unisoc chipsets (T606, T612, T616, SC9863A)
    static constexpr uint32_t FDL1_ADDR_TIGER = 0x00005000;
    static constexpr uint32_t FDL2_ADDR_TIGER = 0x9E000000;
    static constexpr size_t FDL_CHUNK_SIZE    = 2048; // 2KB chunks for BSL MID_DATA

    explicit SpdFdlEngine(WinSerialPort& serialPort, LogCallback logger = nullptr);
    ~SpdFdlEngine() = default;

    /**
     * Streams FDL binary into target RAM and triggers CPU execution.
     */
    bool LoadFdl(
        const uint8_t* fdlData,
        size_t fdlSize,
        uint32_t loadAddr,
        const std::string& fdlName = "FDL1",
        ProgressCallback progressCb = nullptr
    );

    /**
     * Queries hardware chip type or SoC ID from device.
     */
    std::string ReadChipInfo();

    /**
     * Erases a specific partition on the target eMMC/UFS storage (e.g. persist, misc, userdata).
     */
    bool ErasePartition(const std::string& partitionName);

    /**
     * Writes raw partition data in high-speed chunked blocks.
     */
    bool WritePartition(
        const std::string& partitionName,
        const uint8_t* data,
        size_t length,
        ProgressCallback progressCb = nullptr
    );

    /**
     * Sends system reset / reboot command.
     */
    bool RebootDevice();

private:
    void Log(int level, const std::string& msg);

    WinSerialPort& m_port;
    LogCallback m_logger;
};

} // namespace BSLab
