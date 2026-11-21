#include "MtkEngine.h"
#include <thread>
#include <chrono>
#include <sstream>
#include <iomanip>

namespace BSLab {

MtkEngine::MtkEngine(BSLab_LogCallback log_cb)
    : m_log_cb(log_cb) {
}

MtkEngine::~MtkEngine() {
    if (m_port.IsOpen()) {
        m_port.Close();
    }
}

void MtkEngine::Log(BSLab_LogLevel level, const std::string& msg) {
    if (m_log_cb) {
        m_log_cb(static_cast<int>(level), msg.c_str());
    }
}

bool MtkEngine::ConnectAndSync(const std::string& port_name, int timeout_ms, MtkChipInfo& out_info) {
    Log(BSLAB_LOG_BROM, "Opening native COM port: " + port_name + " [Win32 Overlapped Async I/O]...");

    // Standard MTK initial baudrate is 115200 for BROM / Preloader initial sync
    if (!m_port.Open(port_name, 115200)) {
        Log(BSLAB_LOG_ERROR, "Failed to open port " + port_name + " (Port may be locked or busy).");
        return false;
    }

    Log(BSLAB_LOG_INFO, "Port opened. Asserting hardware control lines (DTR/RTS) to wake Preloader...");
    m_port.SetDTR(true);
    m_port.SetRTS(true);
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    m_port.Purge();

    Log(BSLAB_LOG_BROM, "Starting 4-Phase Synchronization (0xA0 / 0x0A / 0x50 / 0x05)...");
    if (!Execute4PhaseHandshake(35)) {
        Log(BSLAB_LOG_ERROR, "4-Phase Handshake failed. Device did not respond with expected echo sequence.");
        m_port.Close();
        return false;
    }

    Log(BSLAB_LOG_SUCCESS, "[+] 4-Phase Handshake verified successfully! Link synchronized.");

    // Query Chipset Information
    if (!GetChipInfo(out_info)) {
        Log(BSLAB_LOG_WARN, "Handshake passed but failed to read Chip ID registers.");
        return false;
    }

    std::stringstream ss;
    ss << "[+] Target Hardware Identified: " << out_info.chip_name
       << " [HW Code: 0x" << std::hex << std::uppercase << std::setfill('0') << std::setw(4) << out_info.hw_code
       << ", SubCode: 0x" << std::setw(4) << out_info.hw_sub_code
       << ", HW Ver: 0x" << std::setw(4) << out_info.hw_ver << "]";
    Log(BSLAB_LOG_SUCCESS, ss.str());

    return true;
}

bool MtkEngine::Execute4PhaseHandshake(int max_retries) {
    // Phase Definition: { Tx_Byte, Expected_Rx_Byte }
    const uint8_t phase_tx[4] = { 0xA0, 0x0A, 0x50, 0x05 };
    const uint8_t phase_rx[4] = { 0x5F, 0xF5, 0xAF, 0xFA };

    for (int retry = 0; retry < max_retries; ++retry) {
        m_port.Purge(); // Clear driver RX/TX buffers before each synchronization burst

        bool sync_ok = true;
        for (int phase = 0; phase < 4; ++phase) {
            uint8_t tx = phase_tx[phase];
            uint8_t expected = phase_rx[phase];

            if (m_port.WriteByte(tx) != 1) {
                sync_ok = false;
                break;
            }

            // High-speed read with 100ms timeout
            int rx = m_port.ReadByte(100);
            if (rx < 0 || static_cast<uint8_t>(rx) != expected) {
                sync_ok = false;
                break;
            }
        }

        if (sync_ok) {
            return true;
        }

        // Delay 15ms before retrying synchronization cycle
        std::this_thread::sleep_for(std::chrono::milliseconds(15));
    }

    return false;
}

bool MtkEngine::SendCmd16(MtkCmd cmd, uint16_t& out_val) {
    uint8_t c = static_cast<uint8_t>(cmd);
    if (m_port.WriteByte(c) != 1) return false;

    // Echo check: MTK device echoes back command byte or ACK
    int echo = m_port.ReadByte(100);
    if (echo < 0 || echo != c) return false;

    // Read 2-byte response (Big Endian)
    std::vector<uint8_t> resp;
    if (m_port.Read(resp, 2, 200) != 2) return false;

    out_val = (static_cast<uint16_t>(resp[0]) << 8) | resp[1];

    // Read trailing status (typically 0x0000 = OK)
    std::vector<uint8_t> status;
    m_port.Read(status, 2, 100);

    return true;
}

bool MtkEngine::GetChipInfo(MtkChipInfo& out_info) {
    if (!SendCmd16(MtkCmd::GET_HW_CODE, out_info.hw_code)) return false;
    SendCmd16(MtkCmd::GET_HW_SUB_CODE, out_info.hw_sub_code);
    SendCmd16(MtkCmd::GET_HW_VER, out_info.hw_ver);
    SendCmd16(MtkCmd::GET_SW_VER, out_info.sw_ver);

    out_info.chip_name = ResolveChipName(out_info.hw_code);
    return true;
}

bool MtkEngine::Read32(uint32_t addr, uint32_t& out_val) {
    uint8_t cmd_buf[5];
    cmd_buf[0] = static_cast<uint8_t>(MtkCmd::READ32);
    cmd_buf[1] = (addr >> 24) & 0xFF;
    cmd_buf[2] = (addr >> 16) & 0xFF;
    cmd_buf[3] = (addr >> 8) & 0xFF;
    cmd_buf[4] = addr & 0xFF;

    if (m_port.Write(cmd_buf, 5) != 5) return false;

    // Expect echo of command
    int echo = m_port.ReadByte(100);
    if (echo != static_cast<int>(MtkCmd::READ32)) return false;

    // Read 4-byte response
    std::vector<uint8_t> resp;
    if (m_port.Read(resp, 4, 200) != 4) return false;

    out_val = (static_cast<uint32_t>(resp[0]) << 24) |
              (static_cast<uint32_t>(resp[1]) << 16) |
              (static_cast<uint32_t>(resp[2]) << 8)  |
               static_cast<uint32_t>(resp[3]);

    // Read status code (2 bytes)
    std::vector<uint8_t> status;
    m_port.Read(status, 2, 100);

    return true;
}

bool MtkEngine::Write32(uint32_t addr, uint32_t val) {
    uint8_t buf[9];
    buf[0] = static_cast<uint8_t>(MtkCmd::WRITE32);
    buf[1] = (addr >> 24) & 0xFF;
    buf[2] = (addr >> 16) & 0xFF;
    buf[3] = (addr >> 8) & 0xFF;
    buf[4] = addr & 0xFF;
    buf[5] = (val >> 24) & 0xFF;
    buf[6] = (val >> 16) & 0xFF;
    buf[7] = (val >> 8) & 0xFF;
    buf[8] = val & 0xFF;

    if (m_port.Write(buf, 9) != 9) return false;

    int echo = m_port.ReadByte(100);
    if (echo != static_cast<int>(MtkCmd::WRITE32)) return false;

    std::vector<uint8_t> status;
    if (m_port.Read(status, 2, 100) != 2) return false;

    return (status[0] == 0 && status[1] == 0);
}

bool MtkEngine::ForceBromFromPreloader(const std::string& port_name) {
    Log(BSLAB_LOG_BROM, "[*] Transmitting Watchdog BROM Crash Vector to Preloader on " + port_name + "...");
    WinSerialPort port;
    if (!port.Open(port_name, 115200)) {
        Log(BSLAB_LOG_ERROR, "Failed to open Preloader port: " + port_name);
        return false;
    }

    port.SetDTR(true);
    port.SetRTS(true);
    std::this_thread::sleep_for(std::chrono::milliseconds(20));

    // 1. Send Preloader WDT Reboot Vector: WDT_BASE = 0x10007000
    // CMD_WRITE32 (0xD4): 0x10007000 = 0x22000014 (MODE_EN | DUAL_CORE)
    uint8_t wdt_mode[9] = { 0xD4, 0x10, 0x00, 0x70, 0x00, 0x22, 0x00, 0x00, 0x14 };
    port.Write(wdt_mode, 9);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    // CMD_WRITE32: 0x10007014 (WDT_SWRST) = 0x1209 (Reset Key)
    uint8_t wdt_rst[9] = { 0xD4, 0x10, 0x00, 0x70, 0x14, 0x00, 0x00, 0x12, 0x09 };
    port.Write(wdt_rst, 9);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    // 2. Pulse METAMETA / ADVEMETA payloads (Forces BROM instead of Preloader reboot)
    const char* meta = "ADVEMETA";
    port.Write(reinterpret_cast<const uint8_t*>(meta), 8);

    port.Close();
    Log(BSLAB_LOG_SUCCESS, "[+] Preloader Glitch Dispatched! Device power-cycling into BROM mode without testpoint...");
    return true;
}

std::string MtkEngine::ResolveChipName(uint16_t hw_code) {
    switch (hw_code) {
        case 0x6768: return "MediaTek Helio G85 / G88 (MT6769)";
        case 0x6765: return "MediaTek Helio G25 / G35 (MT6765)";
        case 0x6761: return "MediaTek Helio A22 (MT6761)";
        case 0x6771: return "MediaTek Helio P60 / P70 (MT6771)";
        case 0x6779: return "MediaTek Helio P90 (MT6779)";
        case 0x6785: return "MediaTek Helio G90 / G95 (MT6785)";
        case 0x6833: return "MediaTek Dimensity 700 / 6020 (MT6833)";
        case 0x6853: return "MediaTek Dimensity 720 (MT6853)";
        case 0x6873: return "MediaTek Dimensity 800 (MT6873)";
        case 0x6877: return "MediaTek Dimensity 900 (MT6877)";
        case 0x6885: return "MediaTek Dimensity 1000 (MT6885)";
        case 0x6893: return "MediaTek Dimensity 1200 (MT6893)";
        case 0x6983: return "MediaTek Dimensity 9000 (MT6983)";
        case 0x6985: return "MediaTek Dimensity 9200 (MT6985)";
        default: {
            std::stringstream ss;
            ss << "MediaTek SoC (HW Code: 0x" << std::hex << std::uppercase << hw_code << ")";
            return ss.str();
        }
    }
}

} // namespace BSLab
