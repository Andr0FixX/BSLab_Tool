#include "QcDiagQcnEngine.h"
#include "WinSerialPort.h"

#include <fstream>
#include <sstream>
#include <chrono>
#include <thread>
#include <cstring>
#include <algorithm>

namespace BSLab {

// =========================================================================
// CRC16-CCITT & HDLC FRAMING IMPLEMENTATION
// =========================================================================

uint16_t QcDiagQcnEngine::CalculateCrc16(const uint8_t* data, size_t length) {
    if (!data || length == 0) return 0;
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; ++bit) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0x8408;
            } else {
                crc >>= 1;
            }
        }
    }
    return crc ^ 0xFFFF;
}

std::vector<uint8_t> QcDiagQcnEngine::EscapeDiagData(const uint8_t* data, size_t length) {
    std::vector<uint8_t> out;
    if (!data || length == 0) return out;
    out.reserve(length + 32);

    for (size_t i = 0; i < length; ++i) {
        uint8_t b = data[i];
        if (b == FRAME_DELIMITER) { // 0x7E
            out.push_back(ESCAPE_BYTE); // 0x7D
            out.push_back(0x5E);
        } else if (b == ESCAPE_BYTE) { // 0x7D
            out.push_back(ESCAPE_BYTE); // 0x7D
            out.push_back(0x5D);
        } else {
            out.push_back(b);
        }
    }
    return out;
}

std::vector<uint8_t> QcDiagQcnEngine::UnescapeDiagData(const uint8_t* data, size_t length) {
    std::vector<uint8_t> out;
    if (!data || length == 0) return out;
    out.reserve(length);

    bool escaped = false;
    for (size_t i = 0; i < length; ++i) {
        uint8_t b = data[i];
        if (escaped) {
            if (b == 0x5E) {
                out.push_back(FRAME_DELIMITER);
            } else if (b == 0x5D) {
                out.push_back(ESCAPE_BYTE);
            } else {
                out.push_back(b);
            }
            escaped = false;
        } else if (b == ESCAPE_BYTE) {
            escaped = true;
        } else {
            out.push_back(b);
        }
    }
    return out;
}

std::vector<uint8_t> QcDiagQcnEngine::BuildFrame(const uint8_t* payload, size_t length) {
    std::vector<uint8_t> frame;
    if (!payload || length == 0) return frame;

    uint16_t crc = CalculateCrc16(payload, length);
    std::vector<uint8_t> raw(payload, payload + length);
    raw.push_back(static_cast<uint8_t>(crc & 0xFF));
    raw.push_back(static_cast<uint8_t>((crc >> 8) & 0xFF));

    std::vector<uint8_t> escaped = EscapeDiagData(raw.data(), raw.size());
    frame.reserve(escaped.size() + 2);
    frame.push_back(FRAME_DELIMITER);
    frame.insert(frame.end(), escaped.begin(), escaped.end());
    frame.push_back(FRAME_DELIMITER);
    return frame;
}

// =========================================================================
// IMEI / LUHN ALGORITHM & QUALCOMM BCD
// =========================================================================

char QcDiagQcnEngine::CalculateLuhnCheckDigit(const std::string& imei14) {
    int total = 0;
    int count = 0;
    for (char c : imei14) {
        if (c >= '0' && c <= '9') {
            int d = c - '0';
            if (count % 2 == 1) { // 2nd, 4th, 6th... digit doubled
                int doubled = d * 2;
                total += (doubled > 9) ? (doubled - 9) : doubled;
            } else {
                total += d;
            }
            count++;
            if (count == 14) break;
        }
    }
    if (count < 14) return '0';
    int check = (10 - (total % 10)) % 10;
    return static_cast<char>('0' + check);
}

bool QcDiagQcnEngine::ValidateImei(const std::string& imei, std::string& outFullImei, std::string& outError) {
    std::string clean;
    for (char c : imei) {
        if (c >= '0' && c <= '9') clean += c;
    }

    if (clean.length() == 14) {
        char ch = CalculateLuhnCheckDigit(clean);
        outFullImei = clean + ch;
        outError = "Auto-computed Luhn check digit: " + std::string(1, ch);
        return true;
    } else if (clean.length() == 15) {
        char expected = CalculateLuhnCheckDigit(clean.substr(0, 14));
        if (clean[14] != expected) {
            outFullImei = clean;
            outError = "Invalid check digit (expected " + std::string(1, expected) + ", got " + std::string(1, clean[14]) + ")";
            return false;
        }
        outFullImei = clean;
        outError = "Valid 15-digit IMEI";
        return true;
    }

    outFullImei = clean;
    outError = "Invalid IMEI length (" + std::to_string(clean.length()) + " digits, required 14 or 15)";
    return false;
}

bool QcDiagQcnEngine::EncodeImeiQcBcd(const std::string& imei15, std::vector<uint8_t>& outBcd9) {
    std::string fullImei, err;
    if (!ValidateImei(imei15, fullImei, err) && fullImei.length() != 15) {
        return false;
    }

    outBcd9.assign(9, 0);
    outBcd9[0] = 0x08; // Length prefix per 3GPP TS 24.008

    int d1 = fullImei[0] - '0';
    outBcd9[1] = static_cast<uint8_t>((d1 << 4) | 0x0A); // Odd digits indicator

    for (int i = 1; i <= 7; ++i) {
        int d_low = fullImei[2 * i - 1] - '0';
        int d_high = fullImei[2 * i] - '0';
        outBcd9[i + 1] = static_cast<uint8_t>((d_high << 4) | (d_low & 0x0F));
    }
    return true;
}

bool QcDiagQcnEngine::DecodeImeiQcBcd(const uint8_t* bcd9, size_t length, std::string& outImei15) {
    if (!bcd9 || length < 9) {
        outImei15.clear();
        return false;
    }

    outImei15.clear();
    // Byte 1: upper nibble is first digit
    int d1 = (bcd9[1] >> 4) & 0x0F;
    if (d1 > 9) return false;
    outImei15 += static_cast<char>('0' + d1);

    // Bytes 2 through 8: lower nibble then upper nibble
    for (size_t i = 2; i <= 8; ++i) {
        int d_low = bcd9[i] & 0x0F;
        int d_high = (bcd9[i] >> 4) & 0x0F;
        if (d_low > 9 || d_high > 9) return false;
        outImei15 += static_cast<char>('0' + d_low);
        outImei15 += static_cast<char>('0' + d_high);
    }
    return (outImei15.length() == 15);
}

// =========================================================================
// QCN / XQCN FILE PARSING & CREATION
// =========================================================================

bool QcDiagQcnEngine::ParseQcnFile(const std::string& qcnPath, std::vector<QcnNvRecord>& outRecords, std::string& outError) {
    outRecords.clear();
    std::ifstream file(qcnPath, std::ios::binary);
    if (!file.is_open()) {
        outError = "Failed to open QCN file: " + qcnPath;
        return false;
    }

    file.seekg(0, std::ios::end);
    size_t fileSize = static_cast<size_t>(file.tellg());
    file.seekg(0, std::ios::beg);

    if (fileSize < 4) {
        outError = "QCN file too small to contain valid NV data.";
        return false;
    }

    std::vector<uint8_t> buffer(fileSize);
    file.read(reinterpret_cast<char*>(buffer.data()), fileSize);
    file.close();

    size_t idx = 0;
    // Check for container header signature
    if (fileSize >= 32 && (std::memcmp(buffer.data(), "QCN_FILE", 8) == 0 ||
                           std::memcmp(buffer.data(), "QCN\0", 4) == 0)) {
        idx = 32;
    } else if (fileSize >= 16 && std::memcmp(buffer.data(), "QCN_FILE\x01", 9) == 0) {
        idx = 16;
    }

    while (idx + 4 <= fileSize) {
        uint16_t itemId = static_cast<uint16_t>(buffer[idx] | (buffer[idx + 1] << 8));
        uint16_t itemLen = static_cast<uint16_t>(buffer[idx + 2] | (buffer[idx + 3] << 8));

        if (itemLen > 0 && itemLen <= 1024 && (idx + 4 + itemLen <= fileSize)) {
            QcnNvRecord rec;
            rec.itemId = itemId;
            rec.data.assign(buffer.begin() + (idx + 4), buffer.begin() + (idx + 4 + itemLen));
            outRecords.push_back(std::move(rec));
            idx += 4 + itemLen;
        } else if (idx + 130 <= fileSize) {
            // Legacy fixed 128-byte record format
            QcnNvRecord rec;
            rec.itemId = itemId;
            rec.data.assign(buffer.begin() + (idx + 2), buffer.begin() + (idx + 130));
            outRecords.push_back(std::move(rec));
            idx += 130;
        } else {
            break;
        }
    }

    if (outRecords.empty()) {
        outError = "No valid NV calibration records found in QCN file.";
        return false;
    }
    return true;
}

bool QcDiagQcnEngine::CreateQcnFile(const std::string& outQcnPath, const std::vector<QcnNvRecord>& records) {
    std::ofstream out(outQcnPath, std::ios::binary);
    if (!out.is_open()) return false;

    // Standard QCN 32-byte header container
    uint8_t header[32] = { 0 };
    std::memcpy(header, "QCN_FILE\x01\x00\x00\x00\x10\x00\x00\x00", 16);
    out.write(reinterpret_cast<const char*>(header), sizeof(header));

    for (const auto& rec : records) {
        uint16_t id = rec.itemId;
        uint16_t len = static_cast<uint16_t>(rec.data.size());
        out.write(reinterpret_cast<const char*>(&id), sizeof(id));
        out.write(reinterpret_cast<const char*>(&len), sizeof(len));
        if (len > 0) {
            out.write(reinterpret_cast<const char*>(rec.data.data()), len);
        }
    }
    return true;
}

bool QcDiagQcnEngine::PatchQcnFile(const std::string& inQcnPath, const std::string& outQcnPath,
                                   const std::string& imei1, const std::string& imei2,
                                   int& outPatchedCount, std::string& outMsg) {
    outPatchedCount = 0;
    std::vector<QcnNvRecord> records;
    std::string err;
    if (!ParseQcnFile(inQcnPath, records, err)) {
        outMsg = "Failed to parse input QCN: " + err;
        return false;
    }

    std::vector<uint8_t> bcd1, bcd2;
    bool hasImei1 = !imei1.empty();
    bool hasImei2 = !imei2.empty();

    if (hasImei1) {
        if (!EncodeImeiQcBcd(imei1, bcd1)) {
            outMsg = "Invalid IMEI 1 format or checksum";
            return false;
        }
    }
    if (hasImei2) {
        if (!EncodeImeiQcBcd(imei2, bcd2)) {
            outMsg = "Invalid IMEI 2 format or checksum";
            return false;
        }
    }

    bool found550 = false;
    bool found650 = false;

    for (auto& rec : records) {
        if (rec.itemId == NV_UE_IMEI_I && hasImei1) {
            if (rec.data.size() < 128) rec.data.resize(128, 0);
            std::memcpy(rec.data.data(), bcd1.data(), 9);
            found550 = true;
            outPatchedCount++;
        } else if (rec.itemId == NV_UE_IMEI2_I && hasImei2) {
            if (rec.data.size() < 128) rec.data.resize(128, 0);
            std::memcpy(rec.data.data(), bcd2.data(), 9);
            found650 = true;
            outPatchedCount++;
        }
    }

    // If IMEI items were not in input file, append them
    if (hasImei1 && !found550) {
        QcnNvRecord rec;
        rec.itemId = NV_UE_IMEI_I;
        rec.data.resize(128, 0);
        std::memcpy(rec.data.data(), bcd1.data(), 9);
        records.push_back(std::move(rec));
        outPatchedCount++;
    }
    if (hasImei2 && !found650) {
        QcnNvRecord rec;
        rec.itemId = NV_UE_IMEI2_I;
        rec.data.resize(128, 0);
        std::memcpy(rec.data.data(), bcd2.data(), 9);
        records.push_back(std::move(rec));
        outPatchedCount++;
    }

    if (!CreateQcnFile(outQcnPath, records)) {
        outMsg = "Failed to write patched QCN to destination: " + outQcnPath;
        return false;
    }

    outMsg = "Successfully patched " + std::to_string(outPatchedCount) + " IMEI NV item(s) into QCN container.";
    return true;
}

// =========================================================================
// HARDWARE DIAGNOSTIC SERIAL COMMUNICATION ENGINE
// =========================================================================

QcDiagQcnEngine::QcDiagQcnEngine()
    : m_serial(std::make_unique<WinSerialPort>()) {
}

QcDiagQcnEngine::~QcDiagQcnEngine() {
    Disconnect();
}

bool QcDiagQcnEngine::Connect(const std::string& portName, uint32_t baudRate) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_abort = false;
    if (m_serial->IsOpen()) {
        m_serial->Close();
    }

    if (!m_serial->Open(portName, baudRate)) {
        m_lastError = "Cannot open Qualcomm Diagnostic COM port: " + portName;
        return false;
    }
    m_serial->Purge();
    return true;
}

void QcDiagQcnEngine::Disconnect() {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_serial && m_serial->IsOpen()) {
        m_serial->Close();
    }
}

bool QcDiagQcnEngine::IsConnected() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_serial && m_serial->IsOpen();
}

bool QcDiagQcnEngine::SendDiagCmd(const uint8_t* reqPayload, size_t reqLen,
                                  std::vector<uint8_t>& outRespBody, uint32_t timeoutMs) {
    outRespBody.clear();
    if (!m_serial || !m_serial->IsOpen()) {
        m_lastError = "Serial port not open.";
        return false;
    }

    std::vector<uint8_t> frame = BuildFrame(reqPayload, reqLen);
    m_serial->Purge();
    size_t written = m_serial->Write(frame.data(), frame.size());
    if (written != frame.size()) {
        m_lastError = "Failed to write full Diag frame.";
        return false;
    }

    // Read response with HDLC delimiter framing
    auto start = std::chrono::steady_clock::now();
    std::vector<uint8_t> rawBuf;
    bool foundStart = false;

    while (!m_abort) {
        auto now = std::chrono::steady_clock::now();
        if (std::chrono::duration_cast<std::chrono::milliseconds>(now - start).count() > timeoutMs) {
            break;
        }

        uint8_t ch = 0;
        if (m_serial->ReadByte(ch, 50)) {
            if (ch == FRAME_DELIMITER) {
                if (!foundStart) {
                    foundStart = true;
                    rawBuf.clear();
                } else if (!rawBuf.empty()) {
                    // Frame completed
                    break;
                }
            } else if (foundStart) {
                rawBuf.push_back(ch);
            }
        }
    }

    if (rawBuf.empty()) {
        m_lastError = "Diag response timed out.";
        return false;
    }

    std::vector<uint8_t> unescaped = UnescapeDiagData(rawBuf.data(), rawBuf.size());
    if (unescaped.size() < 3) {
        m_lastError = "Diag response packet too short.";
        return false;
    }

    // Verify CRC16
    size_t bodyLen = unescaped.size() - 2;
    uint16_t recvCrc = static_cast<uint16_t>(unescaped[bodyLen] | (unescaped[bodyLen + 1] << 8));
    uint16_t calcCrc = CalculateCrc16(unescaped.data(), bodyLen);

    if (recvCrc != calcCrc) {
        m_lastError = "CRC16 checksum mismatch in Diag packet.";
        // Some modems respond with non-standard checksums, still return body if command matches
    }

    outRespBody.assign(unescaped.begin(), unescaped.begin() + bodyLen);
    return true;
}

bool QcDiagQcnEngine::SendSPC(const std::string& spcCode, bool* outUnlocked) {
    if (outUnlocked) *outUnlocked = false;
    std::string spc = spcCode;
    while (spc.length() < 6) spc += '0';
    if (spc.length() > 6) spc = spc.substr(0, 6);

    uint8_t req[7];
    req[0] = CMD_DIAG_SPC; // 0x41
    std::memcpy(&req[1], spc.data(), 6);

    std::vector<uint8_t> resp;
    if (!SendDiagCmd(req, sizeof(req), resp, 1500)) {
        return false;
    }

    if (!resp.empty() && resp[0] == CMD_DIAG_SPC) {
        bool unlocked = (resp.size() > 1 && resp[1] == 0x01);
        if (outUnlocked) *outUnlocked = unlocked;
        return true;
    }
    return false;
}

bool QcDiagQcnEngine::ReadNvItem(uint16_t itemId, std::vector<uint8_t>& outData128) {
    outData128.clear();
    uint8_t req[131] = { 0 };
    req[0] = CMD_DIAG_NV_READ; // 0x26
    req[1] = static_cast<uint8_t>(itemId & 0xFF);
    req[2] = static_cast<uint8_t>((itemId >> 8) & 0xFF);

    std::vector<uint8_t> resp;
    if (!SendDiagCmd(req, sizeof(req), resp, 1500)) {
        return false;
    }

    if (resp.size() >= 3 && resp[0] == CMD_DIAG_NV_READ) {
        // resp[1..2] is item id, payload follows
        size_t payloadLen = resp.size() - 3;
        outData128.assign(resp.begin() + 3, resp.end());
        if (outData128.size() < 128) {
            outData128.resize(128, 0);
        }
        return true;
    }
    return false;
}

bool QcDiagQcnEngine::WriteNvItem(uint16_t itemId, const uint8_t* data128) {
    if (!data128) return false;
    uint8_t req[131] = { 0 };
    req[0] = CMD_DIAG_NV_WRITE; // 0x27
    req[1] = static_cast<uint8_t>(itemId & 0xFF);
    req[2] = static_cast<uint8_t>((itemId >> 8) & 0xFF);
    std::memcpy(&req[3], data128, 128);

    std::vector<uint8_t> resp;
    if (!SendDiagCmd(req, sizeof(req), resp, 1500)) {
        return false;
    }

    return (!resp.empty() && resp[0] == CMD_DIAG_NV_WRITE);
}

bool QcDiagQcnEngine::ReadImei(std::string& outImei1, std::string& outImei2) {
    outImei1.clear();
    outImei2.clear();

    std::vector<uint8_t> data1;
    if (ReadNvItem(NV_UE_IMEI_I, data1)) {
        DecodeImeiQcBcd(data1.data(), data1.size(), outImei1);
    }

    std::vector<uint8_t> data2;
    if (ReadNvItem(NV_UE_IMEI2_I, data2)) {
        DecodeImeiQcBcd(data2.data(), data2.size(), outImei2);
    }

    return !outImei1.empty();
}

bool QcDiagQcnEngine::WriteImei(const std::string& imei1, const std::string& imei2) {
    std::vector<uint8_t> bcd1, bcd2;
    if (!EncodeImeiQcBcd(imei1, bcd1)) {
        m_lastError = "Invalid IMEI 1";
        return false;
    }

    bool hasImei2 = !imei2.empty();
    if (hasImei2 && !EncodeImeiQcBcd(imei2, bcd2)) {
        m_lastError = "Invalid IMEI 2";
        return false;
    }

    // Unlock SPC before writing
    SendSPC("000000");

    uint8_t buf1[128] = { 0 };
    std::memcpy(buf1, bcd1.data(), 9);
    if (!WriteNvItem(NV_UE_IMEI_I, buf1)) {
        m_lastError = "Failed to write Primary IMEI (NV 550)";
        return false;
    }

    if (hasImei2) {
        uint8_t buf2[128] = { 0 };
        std::memcpy(buf2, bcd2.data(), 9);
        if (!WriteNvItem(NV_UE_IMEI2_I, buf2)) {
            m_lastError = "Failed to write Secondary IMEI (NV 650)";
            return false;
        }
    }

    return true;
}

bool QcDiagQcnEngine::RestoreQcn(const std::string& qcnPath,
                                 const std::string& customImei1,
                                 const std::string& customImei2,
                                 std::function<void(float, const std::string&)> progressCb) {
    m_abort = false;
    std::vector<QcnNvRecord> records;
    std::string err;
    if (!ParseQcnFile(qcnPath, records, err)) {
        m_lastError = "Failed to parse QCN: " + err;
        return false;
    }

    std::vector<uint8_t> bcd1, bcd2;
    bool hasImei1 = !customImei1.empty() && EncodeImeiQcBcd(customImei1, bcd1);
    bool hasImei2 = !customImei2.empty() && EncodeImeiQcBcd(customImei2, bcd2);

    // Unlock NVRAM write access
    SendSPC("000000");

    size_t total = records.size();
    size_t written = 0;

    for (size_t i = 0; i < total; ++i) {
        if (m_abort) {
            m_lastError = "QCN write aborted by technician.";
            return false;
        }

        auto& rec = records[i];
        if (rec.data.size() < 128) {
            rec.data.resize(128, 0);
        }

        // On-the-fly custom IMEI injection
        if (rec.itemId == NV_UE_IMEI_I && hasImei1) {
            std::memcpy(rec.data.data(), bcd1.data(), 9);
        } else if (rec.itemId == NV_UE_IMEI2_I && hasImei2) {
            std::memcpy(rec.data.data(), bcd2.data(), 9);
        }

        if (WriteNvItem(rec.itemId, rec.data.data())) {
            written++;
        }

        if (progressCb && (i % 5 == 0 || i == total - 1)) {
            float pct = static_cast<float>(i + 1) / static_cast<float>(total);
            std::string status = "Writing NV Item " + std::to_string(rec.itemId) + " (" +
                                 std::to_string(i + 1) + "/" + std::to_string(total) + ")";
            progressCb(pct, status);
        }
    }

    // Reset phone modem calibration
    RebootPhone();
    return (written > 0);
}

bool QcDiagQcnEngine::BackupQcn(const std::string& outQcnPath,
                                const std::vector<uint16_t>& itemIds,
                                std::function<void(float, const std::string&)> progressCb) {
    m_abort = false;
    std::vector<uint16_t> targetIds = itemIds;
    if (targetIds.empty()) {
        // Standard essential RF & Calibration NV items
        targetIds = {
            NV_UE_IMEI_I, NV_UE_IMEI2_I, NV_FACTORY_DATA_1, NV_FACTORY_DATA_2,
            NV_LTE_BC_CONFIG_I, 10, 11, 71, 169, 170, 171, 172, 173, 174,
            553, 560, 561, 562, 574, 575, 576, 577, 850, 851, 852
        };
    }

    SendSPC("000000");

    std::vector<QcnNvRecord> records;
    size_t total = targetIds.size();

    for (size_t i = 0; i < total; ++i) {
        if (m_abort) {
            m_lastError = "Backup aborted.";
            return false;
        }

        uint16_t id = targetIds[i];
        std::vector<uint8_t> data;
        if (ReadNvItem(id, data) && !data.empty()) {
            QcnNvRecord rec;
            rec.itemId = id;
            rec.data = std::move(data);
            records.push_back(std::move(rec));
        }

        if (progressCb && (i % 3 == 0 || i == total - 1)) {
            float pct = static_cast<float>(i + 1) / static_cast<float>(total);
            std::string status = "Backing up NV " + std::to_string(id) + " (" +
                                 std::to_string(i + 1) + "/" + std::to_string(total) + ")";
            progressCb(pct, status);
        }
    }

    return CreateQcnFile(outQcnPath, records);
}

bool QcDiagQcnEngine::RebootPhone() {
    uint8_t req[2];
    req[0] = CMD_DIAG_PHONE_MODE; // 0x29
    req[1] = 0x01;                // 0x01 = Reset / Reboot to normal mode

    std::vector<uint8_t> resp;
    return SendDiagCmd(req, sizeof(req), resp, 1000);
}

void QcDiagQcnEngine::Abort() {
    m_abort = true;
    Disconnect();
}

std::string QcDiagQcnEngine::GetLastError() const {
    return m_lastError;
}

} // namespace BSLab
