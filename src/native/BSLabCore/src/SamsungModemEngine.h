#pragma once

#include <string>
#include <map>
#include <mutex>
#include <functional>
#include "WinSerialPort.h"

namespace BSLab {

struct SamsungDeviceInfo {
    std::string port;
    std::string description;
    std::string hwid;
    std::string mode; // "Download Mode (Odin)" or "Modem / CDC Port"
};

struct SamsungModemInfo {
    std::string model;
    std::string serial_imei;
    std::string baseband_ap;
    std::string devcon_info;
    std::string csc;
    std::string knox_guard;
    std::string knox_warranty;
    std::string frp_status;
};

class SamsungModemEngine {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;

    explicit SamsungModemEngine(LogCallback logger = nullptr);
    ~SamsungModemEngine() = default;

    void SetLogger(LogCallback logger) { m_logger = logger; }

    /**
     * Enumerate all connected Samsung Serial & Modem COM ports.
     */
    static std::vector<SamsungDeviceInfo> ScanSamsungPorts();

    /**
     * Finds active Samsung Mobile USB Modem port.
     */
    static std::string FindModemPort();

    /**
     * Sends an AT command with CR/LF framing and captures response until OK/ERROR or timeout.
     */
    std::string SendAtCommand(const std::string& port, const std::string& cmd, uint32_t timeoutMs = 2000);

    /**
     * Harvests full device telemetry via Modem AT diagnostic interface.
     */
    bool ReadDeviceInfo(const std::string& port, SamsungModemInfo& outInfo);

    /**
     * Activates Samsung Factory Test Mode (*#0*#) service sequence.
     */
    bool TriggerTestMode(const std::string& port);

    /**
     * Signals device to reboot directly into Odin Download Mode.
     */
    bool RebootToDownloadMode(const std::string& port);

    /**
     * Reads active CSC and Sales Code.
     */
    bool ReadCscStatus(const std::string& port, std::string& outCsc, std::string& outSalesCode);

    /**
     * 1-Click CSC carrier & feature change without data loss.
     */
    bool ChangeCsc(const std::string& port, const std::string& targetCsc, bool rebootAfter = true);

    /**
     * Audits Samsung Knox Guard (KG), Knox Warranty Bit, and FRP status.
     */
    bool ReadKnoxSecurity(const std::string& port, std::string& outKnoxGuard, std::string& outWarranty, std::string& outFrp);

private:
    void Log(int level, const std::string& msg);

    std::mutex m_portMutex;
    LogCallback m_logger;
};

} // namespace BSLab
