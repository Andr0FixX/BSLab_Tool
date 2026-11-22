#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <mutex>
#include <atomic>
#include <memory>
#include <functional>

namespace BSLab {

class WinSerialPort;

struct QcnNvRecord {
    uint16_t itemId = 0;
    std::vector<uint8_t> data;
};

class QcDiagQcnEngine {
public:
    // Qualcomm HDLC Framing Constants
    static constexpr uint8_t FRAME_DELIMITER = 0x7E;
    static constexpr uint8_t ESCAPE_BYTE     = 0x7D;

    // Qualcomm Diagnostic Command Codes
    static constexpr uint8_t CMD_DIAG_VERNO      = 0x00;
    static constexpr uint8_t CMD_DIAG_ESN        = 0x01;
    static constexpr uint8_t CMD_DIAG_NV_READ    = 0x26;
    static constexpr uint8_t CMD_DIAG_NV_WRITE   = 0x27;
    static constexpr uint8_t CMD_DIAG_PHONE_MODE = 0x29;
    static constexpr uint8_t CMD_DIAG_SPC        = 0x41;
    static constexpr uint8_t CMD_DIAG_SUBSYS_CMD = 0x4B;

    // Common NV Item IDs
    static constexpr uint16_t NV_UE_IMEI_I        = 550;   // Primary IMEI
    static constexpr uint16_t NV_UE_IMEI2_I       = 650;   // Secondary / Dual-SIM IMEI
    static constexpr uint16_t NV_FACTORY_DATA_1   = 2497;  // Factory RF Data 1
    static constexpr uint16_t NV_FACTORY_DATA_2   = 2498;  // Factory RF Data 2
    static constexpr uint16_t NV_LTE_BC_CONFIG_I  = 6828;  // Carrier Aggregation / Band Config

    QcDiagQcnEngine();
    ~QcDiagQcnEngine();

    // Non-copyable
    QcDiagQcnEngine(const QcDiagQcnEngine&) = delete;
    QcDiagQcnEngine& operator=(const QcDiagQcnEngine&) = delete;

    // =========================================================================
    // STATIC ALGORITHMS & CONTAINER PARSING
    // =========================================================================

    // CRC16-CCITT for Qualcomm Diag (Polynomial 0x8408 reversed)
    static uint16_t CalculateCrc16(const uint8_t* data, size_t length);

    // HDLC Framing: Byte Stuffing (0x7E -> 0x7D 0x5E, 0x7D -> 0x7D 0x5D)
    static std::vector<uint8_t> EscapeDiagData(const uint8_t* data, size_t length);

    // HDLC Framing: Reversing Byte Stuffing
    static std::vector<uint8_t> UnescapeDiagData(const uint8_t* data, size_t length);

    // Build complete framed packet: Payload + CRC16 -> Escape -> Delimiters
    static std::vector<uint8_t> BuildFrame(const uint8_t* payload, size_t length);

    // Luhn Algorithm: Computes 15th check digit for 14-digit prefix
    static char CalculateLuhnCheckDigit(const std::string& imei14);

    // Validates IMEI string (14 or 15 digits) and returns sanitized 15-digit string
    static bool ValidateImei(const std::string& imei, std::string& outFullImei, std::string& outError);

    // Encodes 15-digit IMEI into Qualcomm 9-byte BCD (3GPP TS 24.008 format)
    static bool EncodeImeiQcBcd(const std::string& imei15, std::vector<uint8_t>& outBcd9);

    // Decodes Qualcomm 9-byte BCD into 15-digit IMEI string
    static bool DecodeImeiQcBcd(const uint8_t* bcd9, size_t length, std::string& outImei15);

    // Parses a binary QCN / XQCN calibration file into individual NV items
    static bool ParseQcnFile(const std::string& qcnPath, std::vector<QcnNvRecord>& outRecords, std::string& outError);

    // Injects custom IMEI 1 and optional IMEI 2 into QCN file on disk
    static bool PatchQcnFile(const std::string& inQcnPath, const std::string& outQcnPath,
                             const std::string& imei1, const std::string& imei2,
                             int& outPatchedCount, std::string& outMsg);

    // Creates a valid QCN binary container from a list of NV items
    static bool CreateQcnFile(const std::string& outQcnPath, const std::vector<QcnNvRecord>& records);

    // =========================================================================
    // HARDWARE DIAGNOSTIC SERIAL COMMUNICATION
    // =========================================================================

    // Opens Qualcomm Diagnostic Port (e.g. "COM3" or "\\\\.\\COM14")
    bool Connect(const std::string& portName, uint32_t baudRate = 115200);

    // Closes port
    void Disconnect();

    // Check connection status
    bool IsConnected() const;

    // Sends raw diag payload and receives unescaped response body
    bool SendDiagCmd(const uint8_t* reqPayload, size_t reqLen,
                     std::vector<uint8_t>& outRespBody, uint32_t timeoutMs = 2000);

    // Unlocks NVRAM write access with 6-digit SPC (default "000000")
    bool SendSPC(const std::string& spcCode = "000000", bool* outUnlocked = nullptr);

    // Reads standard 128-byte NV Item
    bool ReadNvItem(uint16_t itemId, std::vector<uint8_t>& outData128);

    // Writes standard 128-byte NV Item
    bool WriteNvItem(uint16_t itemId, const uint8_t* data128);

    // Reads IMEI 1 (NV 550) and IMEI 2 (NV 650) from live device
    bool ReadImei(std::string& outImei1, std::string& outImei2);

    // Directly writes IMEI 1 and optional IMEI 2 to device NV
    bool WriteImei(const std::string& imei1, const std::string& imei2 = "");

    // Restores complete QCN file with optional on-the-fly IMEI injection
    bool RestoreQcn(const std::string& qcnPath,
                    const std::string& customImei1 = "",
                    const std::string& customImei2 = "",
                    std::function<void(float, const std::string&)> progressCb = nullptr);

    // Reads essential/calibration NV items from live device and saves as QCN file
    bool BackupQcn(const std::string& outQcnPath,
                   const std::vector<uint16_t>& itemIds,
                   std::function<void(float, const std::string&)> progressCb = nullptr);

    // Reboots phone by sending Phone Mode Reset (CMD 0x29, mode 0x01)
    bool RebootPhone();

    // Abort active transfer
    void Abort();

    std::string GetLastError() const;

private:
    std::unique_ptr<WinSerialPort> m_serial;
    mutable std::mutex m_mutex;
    std::atomic<bool> m_abort{false};
    std::string m_lastError;
};

} // namespace BSLab
