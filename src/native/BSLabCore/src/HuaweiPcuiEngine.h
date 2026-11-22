#pragma once

#include <string>
#include <vector>
#include <mutex>
#include <functional>
#include <cstdint>

namespace BSLab {

struct HuaweiDeviceInfo {
    std::string model;
    std::string imei;
    std::string build_version;
    std::string battery_level;
    std::string serial_number;
    std::string raw_responses;
};

class HuaweiPcuiEngine {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;

    explicit HuaweiPcuiEngine(LogCallback logger = nullptr);
    ~HuaweiPcuiEngine() = default;

    void SetLogger(LogCallback logger) { m_logger = logger; }

    /**
     * Finds active Huawei PCUI COM port.
     */
    static std::string FindPcuiPort();

    /**
     * Transmits raw AT command over PCUI port and captures response.
     */
    std::string SendAtCommand(
        const std::string& port,
        const std::string& cmd,
        uint32_t timeout_ms = 3000
    );

    /**
     * Performs deep Manufacture Mode telemetry reading.
     */
    bool ReadDeviceInfo(
        const std::string& port,
        HuaweiDeviceInfo& out_info
    );

    /**
     * Triggers hardware reboot from Manufacture Mode into Fastboot Rescue Mode.
     */
    bool RebootToFastboot(const std::string& port);

private:
    void Log(int level, const std::string& msg);

    LogCallback m_logger;
    std::mutex m_portMutex;
};

} // namespace BSLab
