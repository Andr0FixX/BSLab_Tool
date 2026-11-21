#pragma once

#include "WinSerialPort.h"
#include "../include/BSLabCore.h"
#include <string>
#include <vector>
#include <cstdint>
#include <functional>

namespace BSLab {

// Standard MTK Protocol Opcodes
enum class MtkCmd : uint8_t {
    GET_HW_CODE     = 0xFD,
    GET_HW_SUB_CODE = 0xFC,
    GET_HW_VER      = 0xFB,
    GET_SW_VER      = 0xFA,
    READ16          = 0xA2,
    WRITE16         = 0xA1,
    READ32          = 0xD1,
    WRITE32         = 0xD0,
    JUMP_DA         = 0xD5,
    SEND_DA         = 0xD7,
    GET_TARGET_CONFIG = 0xD8
};

struct MtkChipInfo {
    uint16_t hw_code = 0;
    uint16_t hw_sub_code = 0;
    uint16_t hw_ver = 0;
    uint16_t sw_ver = 0;
    std::string chip_name;
};

class MtkEngine {
public:
    MtkEngine(BSLab_LogCallback log_cb = nullptr);
    ~MtkEngine();

    // High-speed Win32 handshake with sub-millisecond precision
    bool ConnectAndSync(const std::string& port_name, int timeout_ms, MtkChipInfo& out_info);

    // Read Hardware registers
    bool GetChipInfo(MtkChipInfo& out_info);

    // Direct Preloader / BROM Handshake Sequence
    bool Execute4PhaseHandshake(int max_retries = 25);

    // Send single MTK protocol command with 16-bit response
    bool SendCmd16(MtkCmd cmd, uint16_t& out_val);

    // Send 32-bit memory read/write
    bool Read32(uint32_t addr, uint32_t& out_val);
    bool Write32(uint32_t addr, uint32_t val);

    // Preloader-to-BROM Force Glitch Vector (Without Testpoint)
    bool ForceBromFromPreloader(const std::string& port_name);

    // Logging helper
    void Log(BSLab_LogLevel level, const std::string& msg);

    // Port handle
    WinSerialPort& GetPort() { return m_port; }

private:
    WinSerialPort m_port;
    BSLab_LogCallback m_log_cb;

    std::string ResolveChipName(uint16_t hw_code);
};

} // namespace BSLab
