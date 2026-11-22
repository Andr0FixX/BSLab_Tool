#pragma once

#include <string>
#include <vector>
#include <atomic>
#include <mutex>
#include <functional>
#include "WinSerialPort.h"
#include "SpdBslProtocol.h"
#include "SpdPacParser.h"
#include "SpdFdlEngine.h"

namespace BSLab {

struct UnisocPortInfo {
    std::string port;
    std::string description;
    std::string hwid;
};

class UnisocEngine {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;
    using ProgressCallback = std::function<void(int overall_pct, int file_pct, const char* part_name, const char* status_text)>;

    explicit UnisocEngine(LogCallback logger = nullptr);
    ~UnisocEngine();

    void SetLogger(LogCallback logger) { m_logger = logger; }

    /**
     * Enumerate all connected Unisoc / Spreadtrum COM ports.
     */
    static std::vector<UnisocPortInfo> ScanPorts();

    /**
     * Connects to device, traps BSL 0x7E sync, and loads FDL1/FDL2 from PAC if provided.
     */
    bool Connect(
        const std::string& portName,
        const std::string& pacPath = "",
        ProgressCallback progressCb = nullptr
    );

    /**
     * Flashes complete PAC firmware archive to target device.
     */
    bool FlashFirmware(
        const std::string& portName,
        const std::string& pacPath,
        bool rebootAfter = true,
        ProgressCallback progressCb = nullptr
    );

    /**
     * 1-Click FRP Unlock for Unisoc devices (erases persist / misc).
     */
    bool ResetFRP(
        const std::string& portName,
        const std::string& pacPath = "",
        ProgressCallback progressCb = nullptr
    );

    /**
     * 1-Click Factory Reset for Unisoc devices (erases userdata & cache).
     */
    bool FactoryReset(
        const std::string& portName,
        const std::string& pacPath = "",
        ProgressCallback progressCb = nullptr
    );

    /**
     * Reboots device to system.
     */
    bool Reboot(const std::string& portName);

    /**
     * Aborts any ongoing Unisoc operation.
     */
    void Abort();

private:
    void Log(int level, const std::string& msg);

    std::atomic<bool> m_abortRequested{false};
    std::mutex m_mutex;
    WinSerialPort m_serial;
    LogCallback m_logger;
};

} // namespace BSLab
