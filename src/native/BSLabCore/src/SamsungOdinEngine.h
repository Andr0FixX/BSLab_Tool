#pragma once

#include <string>
#include <vector>
#include <map>
#include <atomic>
#include <mutex>
#include <functional>
#include "WinSerialPort.h"
#include "NativeTarReader.h"
#include "NativeMd5.h"
#include "SamsungPitReader.h"
#include "SamsungModemEngine.h"

namespace BSLab {

struct SamsungFlashSlots {
    std::string bl_path;
    std::string ap_path;
    std::string cp_path;
    std::string csc_path;
    std::string pit_path;
};

class SamsungOdinEngine {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;
    using ProgressCallback = std::function<void(int overall_pct, int file_pct, const char* part_name, const char* status_text)>;

    static constexpr size_t ODIN_CHUNK_SIZE = 131072; // 128 KB

    explicit SamsungOdinEngine(LogCallback logger = nullptr);
    ~SamsungOdinEngine();

    void SetLogger(LogCallback logger) { m_logger = logger; }

    /**
     * Executes Odin protocol handshake over target COM port.
     */
    bool PerformHandshake(const std::string& portName);

    /**
     * Flashes 4-File Samsung firmware (BL, AP, CP, CSC, PIT) with live progress feedback.
     */
    bool FlashFirmware(
        const std::string& portName,
        const SamsungFlashSlots& slots,
        bool repartition,
        bool autoReboot,
        ProgressCallback progressCb
    );

    /**
     * Requests immediate cancellation of an active flashing session.
     */
    void Abort();

    /**
     * Locates and launches the bundled official Samsung Odin3 executable with dynamically configured Odin3.ini.
     */
    bool LaunchOfficialOdin(
        const SamsungFlashSlots& slots,
        bool repartition,
        bool autoReboot
    );

    /**
     * Helper to locate Odin3 executable on disk.
     */
    static std::string FindOdinExecutable();

private:
    void Log(int level, const std::string& msg);

    std::atomic<bool> m_abortRequested{false};
    std::mutex m_flashMutex;
    WinSerialPort m_serial;
    LogCallback m_logger;
};

} // namespace BSLab
