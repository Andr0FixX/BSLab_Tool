#pragma once

#include <string>
#include <vector>
#include <mutex>
#include <atomic>
#include <functional>
#include <cstdint>

namespace BSLab {

struct HuaweiPortInfo {
    std::string port;
    std::string description;
    std::string hwid;
    std::string type; // "USB COM 1.0", "PCUI", "Modem", "Unknown"
};

class KirinRescueEngine {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;
    using ProgressCallback = std::function<void(int overall_pct, int file_pct, const std::string& stage, const std::string& status)>;

    explicit KirinRescueEngine(LogCallback logger = nullptr);
    ~KirinRescueEngine() = default;

    void SetLogger(LogCallback logger) { m_logger = logger; }
    void Abort() { m_abortRequested = true; }
    bool IsAborted() const { return m_abortRequested; }

    /**
     * Scans for Huawei serial ports (USB COM 1.0, PCUI, DBAdapter).
     */
    static std::vector<HuaweiPortInfo> ScanHuaweiPorts();

    /**
     * Finds active HUAWEI USB COM 1.0 port (VID: 0x12D1, PID: 0x3609).
     */
    static std::string FindUsbCom10Port();

    /**
     * Resolves canonical Kirin chipset folder from user hint / model code.
     */
    static std::string ResolveChipset(const std::string& hint);

    /**
     * Locates the root directory containing Kirin stage loaders.
     */
    static std::string FindLoadersDir();

    /**
     * Injects multi-stage Kirin Bootloader into HUAWEI USB COM 1.0 device.
     * Wakes up CPU and reboots device into Fastboot Rescue Mode.
     */
    bool BootRescueMode(
        const std::string& port,
        const std::string& chipset,
        ProgressCallback progress_cb = nullptr
    );

private:
    void Log(int level, const std::string& msg);

    LogCallback m_logger;
    std::atomic<bool> m_abortRequested{false};
    std::mutex m_engineMutex;
};

} // namespace BSLab
