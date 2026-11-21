#pragma once

#include "WinSerialPort.h"
#include "../include/BSLabCore.h"
#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

// Standard Qualcomm Sahara Protocol Command IDs
enum class SaharaCmd : uint32_t {
    HELLO          = 0x01,
    HELLO_RESP     = 0x02,
    READ_DATA      = 0x03,
    END_IMAGE_TX   = 0x04,
    DONE           = 0x05,
    DONE_RESP      = 0x06,
    RESET          = 0x07,
    RESET_RESP     = 0x08,
    MEMORY_DEBUG   = 0x09,
    CMD_EXEC       = 0x0B,
    CMD_EXEC_RESP  = 0x0C,
    CMD_EXEC_DATA  = 0x0D,
    MEMORY_READ    = 0x0E
};

#pragma pack(push, 1)
struct SaharaPktHdr {
    uint32_t cmd;       // Command ID
    uint32_t length;    // Packet size in bytes
};

struct SaharaHelloPkt {
    SaharaPktHdr hdr;
    uint32_t version;
    uint32_t min_version;
    uint32_t max_cmd_len;
    uint32_t mode;
    uint32_t reserved[6];
};

struct SaharaReadDataPkt {
    SaharaPktHdr hdr;
    uint32_t image_id;
    uint32_t data_offset;
    uint32_t data_length;
};

struct SaharaEndImageTxPkt {
    SaharaPktHdr hdr;
    uint32_t image_id;
    uint32_t status;
};

struct SaharaDonePkt {
    SaharaPktHdr hdr;
};
#pragma pack(pop)

class QcSahara {
public:
    QcSahara(BSLab_LogCallback log_cb = nullptr);
    ~QcSahara() = default;

    // Connects to HS-USB QDLoader 9008 and executes Sahara Handshake
    bool Handshake(WinSerialPort& port, int timeout_ms = 8000);

    // Uploads Qualcomm Firehose ELF/MBN Programmer into SoC RAM
    bool UploadProgrammer(
        WinSerialPort& port,
        const std::wstring& programmer_path,
        BSLab_ProgressCallback progress_cb = nullptr
    );

private:
    BSLab_LogCallback m_log_cb;

    void Log(BSLab_LogLevel level, const std::string& msg);
    bool SendHelloResponse(WinSerialPort& port);
    bool SendDone(WinSerialPort& port);
};

} // namespace BSLab
