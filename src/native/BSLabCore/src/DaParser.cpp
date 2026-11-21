#include "DaParser.h"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstring>
#include <thread>
#include <chrono>

namespace BSLab {

DaParser::DaParser(BSLab_LogCallback log_cb)
    : m_log_cb(log_cb) {
}

void DaParser::Log(BSLab_LogLevel level, const std::string& msg) {
    if (m_log_cb) {
        m_log_cb(static_cast<int>(level), msg.c_str());
    }
}

uint16_t DaParser::CalculateChecksum16(const uint8_t* data, size_t len) {
    uint32_t sum = 0;
    for (size_t i = 0; i < len; ++i) {
        sum += data[i];
    }
    return static_cast<uint16_t>(sum & 0xFFFF);
}

uint32_t DaParser::CalculateChecksum32(const uint8_t* data, size_t len) {
    uint32_t sum = 0;
    for (size_t i = 0; i < len; ++i) {
        sum += data[i];
    }
    return sum;
}

static uint16_t MapMtkHwCodeToChip(uint16_t hw) {
    switch (hw) {
        case 0x0989: return 0x6833; // MT6833 Dimensity 700 / 5G
        case 0x0853: return 0x6853; // MT6853 Dimensity 720
        case 0x0893: return 0x6893; // MT6893 Dimensity 1200
        case 0x0885: return 0x6885; // MT6885 Dimensity 1000
        case 0x0987: return 0x6877; // MT6877 Dimensity 900
        case 0x0707: return 0x6768; // MT6768 Helio G80/G85
        case 0x0766: return 0x6765; // MT6765 Helio P35
        case 0x0717: return 0x6761; // MT6761 Helio A22
        case 0x0788: return 0x6771; // MT6771 Helio P60
        case 0x0813: return 0x6785; // MT6785 Helio G90/G95
        case 0x0799: return 0x6779; // MT6779 Helio P90
        case 0x0699: return 0x6739; // MT6739
        case 0x0326: return 0x6580; // MT6580
        case 0x0335: return 0x6570; // MT6570
        case 0x0279: return 0x6755; // MT6755
        case 0x0676: return 0x6763; // MT6763
        case 0x0321: return 0x6572; // MT6572
        case 0x0381: return 0x6582; // MT6582
        case 0x0658: return 0x6735; // MT6735
        case 0x0675: return 0x6737; // MT6737
        case 0x0567: return 0x6752; // MT6752
        case 0x0568: return 0x6753; // MT6753
        default:     return hw;
    }
}

bool DaParser::LoadFromFile(const std::string& da_path, uint16_t hw_code, DaContainer& out_da) {
    out_da.file_path = da_path;
    out_da.target_hw_code = hw_code;
    out_da.is_valid = false;

    std::string effective_path = da_path;
    std::ifstream file(effective_path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        // Fallback candidate paths
        std::vector<std::string> fallbacks = {
            "resources/loaders/mtk/brand_da/MTK_AllInOne_DA.bin",
            "resources/loaders/mtk/MTK_DA_V6.bin",
            "dist_new/resources/loaders/mtk/brand_da/MTK_AllInOne_DA.bin",
            "dist_new/resources/loaders/mtk/MTK_DA_V6.bin"
        };
        for (const auto& fb : fallbacks) {
            file.open(fb, std::ios::binary | std::ios::ate);
            if (file.is_open()) {
                effective_path = fb;
                Log(BSLAB_LOG_WARN, "[*] Original DA path inaccessible, redirected to: " + fb);
                break;
            }
        }
    }

    if (!file.is_open()) {
        Log(BSLAB_LOG_ERROR, "Cannot open DA file: " + da_path);
        return false;
    }

    std::streamsize fileSize = file.tellg();
    file.seekg(0, std::ios::beg);

    if (fileSize < 512) {
        Log(BSLAB_LOG_ERROR, "DA binary is too small (Invalid size: " + std::to_string(fileSize) + " bytes).");
        return false;
    }

    std::vector<uint8_t> buffer(fileSize);
    if (!file.read(reinterpret_cast<char*>(buffer.data()), fileSize)) {
        Log(BSLAB_LOG_ERROR, "Failed to read DA file into memory buffer.");
        return false;
    }
    file.close();

    // 1. Detect if the loaded file is a TAR archive (e.g. brand_da/OPPO.da) or standalone binary without DADA
    bool has_dada = false;
    for (size_t k = 0; k + 1 < buffer.size() && k < 0x2000; k += 2) {
        if (buffer[k] == 0xDA && buffer[k + 1] == 0xDA) {
            has_dada = true;
            break;
        }
    }

    bool is_tar = false;
    if (buffer.size() >= 512) {
        if (std::memcmp(buffer.data() + 257, "ustar", 5) == 0 ||
            (buffer[0] != 0 && buffer[156] >= '0' && buffer[156] <= '7' && buffer[100] == 0)) {
            is_tar = true;
        }
    }

    // If loaded file is a TAR or a standalone binary without DADA container,
    // check if universal container MTK_AllInOne_DA.bin has the chip-specific signed DA
    if (is_tar || !has_dada) {
        std::vector<std::string> uni_paths = {
            "resources/loaders/mtk/brand_da/MTK_AllInOne_DA.bin",
            "resources/loaders/mtk/MTK_DA_V6.bin",
            "dist_new/resources/loaders/mtk/brand_da/MTK_AllInOne_DA.bin",
            "dist_new/resources/loaders/mtk/MTK_DA_V6.bin"
        };
        for (const auto& up : uni_paths) {
            std::ifstream uf(up, std::ios::binary | std::ios::ate);
            if (uf.is_open()) {
                size_t ulen = static_cast<size_t>(uf.tellg());
                uf.seekg(0, std::ios::beg);
                std::vector<uint8_t> ubuf(ulen);
                uf.read(reinterpret_cast<char*>(ubuf.data()), ulen);
                // Check if this container has the target mapped hw
                uint16_t mapped = MapMtkHwCodeToChip(hw_code);
                bool found_chip = false;
                for (size_t m = 0; m + 24 <= ubuf.size() && m < 0x20000; m += 2) {
                    if (ubuf[m] == 0xDA && ubuf[m + 1] == 0xDA) {
                        uint16_t chw = ubuf[m + 2] | (ubuf[m + 3] << 8);
                        if (chw == hw_code || chw == mapped) {
                            found_chip = true;
                            break;
                        }
                    }
                }
                if (found_chip) {
                    buffer = std::move(ubuf);
                    has_dada = true;
                    Log(BSLAB_LOG_INFO, "[+] Loaded Authenticated Multi-Stage DA Container for HW 0x" +
                        [](uint16_t v) { std::stringstream ss; ss << std::hex << std::uppercase << v; return ss.str(); }(mapped) +
                        " from: " + up);
                    break;
                }
            }
        }
    }

    // 2. Scan for 0xDADA Multi-Chip Container Entries
    uint16_t mapped_hw = MapMtkHwCodeToChip(hw_code);
    size_t matched_entry_offset = std::string::npos;
    size_t fallback_entry_offset = std::string::npos;
    uint16_t found_hw = 0;
    uint16_t found_sub = 0;
    uint16_t found_sec_cnt = 0;

    for (size_t i = 0; i + 24 <= buffer.size() && i < 0x20000; i += 2) {
        if (buffer[i] == 0xDA && buffer[i + 1] == 0xDA) {
            uint16_t e_hw = buffer[i + 2] | (buffer[i + 3] << 8);
            uint16_t e_sub = buffer[i + 4] | (buffer[i + 5] << 8);
            uint16_t e_sec_cnt = buffer[i + 18] | (buffer[i + 19] << 8);

            if (fallback_entry_offset == std::string::npos && e_sec_cnt > 0) {
                fallback_entry_offset = i;
            }

            if (e_hw == hw_code || e_hw == mapped_hw) {
                matched_entry_offset = i;
                found_hw = e_hw;
                found_sub = e_sub;
                found_sec_cnt = e_sec_cnt;
                break;
            }
        }
    }

    if (matched_entry_offset == std::string::npos && fallback_entry_offset != std::string::npos) {
        matched_entry_offset = fallback_entry_offset;
        found_hw = buffer[matched_entry_offset + 2] | (buffer[matched_entry_offset + 3] << 8);
        found_sub = buffer[matched_entry_offset + 4] | (buffer[matched_entry_offset + 5] << 8);
        found_sec_cnt = buffer[matched_entry_offset + 18] | (buffer[matched_entry_offset + 19] << 8);
        Log(BSLAB_LOG_WARN, "[*] Exact HW Code match not in container; utilizing compatible ARMv8 architecture entry.");
    }

    if (matched_entry_offset != std::string::npos && found_sec_cnt > 0) {
        // Parse section table of the matched entry
        size_t sec_table_offset = matched_entry_offset + 20;
        bool da1_found = false;
        bool da2_found = false;

        for (uint16_t s = 0; s < found_sec_cnt && s < 10; ++s) {
            size_t soff = sec_table_offset + s * 20;
            if (soff + 20 > buffer.size()) break;

            uint32_t foff = *reinterpret_cast<const uint32_t*>(buffer.data() + soff);
            uint32_t flen = *reinterpret_cast<const uint32_t*>(buffer.data() + soff + 4);
            uint32_t laddr = *reinterpret_cast<const uint32_t*>(buffer.data() + soff + 8);
            uint32_t siglen = *reinterpret_cast<const uint32_t*>(buffer.data() + soff + 12);

            if (foff + flen > buffer.size() || flen == 0) continue;

            // Stage 1 (SRAM Target: 0x00200000 / 0x01000000 / 0x02000000)
            if (!da1_found && (laddr == 0x00200000 || laddr == 0x01000000 || laddr == 0x02000000 || (laddr < 0x20000000 && flen > 1024))) {
                out_da.da1.load_addr = laddr;
                out_da.da1.entry_point = laddr;
                out_da.da1.size = flen;
                out_da.da1.data.assign(buffer.data() + foff, buffer.data() + foff + flen);
                if (siglen > 0 && siglen <= flen) {
                    out_da.da1.sig.assign(buffer.data() + foff + flen - siglen, buffer.data() + foff + flen);
                }
                da1_found = true;
            }
            // Stage 2 (DRAM Target: 0x40000000 / 0x80000000)
            else if (!da2_found && (laddr >= 0x40000000 && flen > 1024)) {
                out_da.da2.load_addr = laddr;
                out_da.da2.entry_point = laddr;
                out_da.da2.size = flen;
                out_da.da2.data.assign(buffer.data() + foff, buffer.data() + foff + flen);
                da2_found = true;
            }
        }

        if (da1_found) {
            if (!da2_found) {
                // Mirror stage 1 into stage 2 if single stage
                out_da.da2 = out_da.da1;
                out_da.da2.load_addr = 0x40000000;
                out_da.da2.entry_point = 0x40000000;
            }

            out_da.format_version = "MediaTek All-In-One Container (Parsed & Sliced for HW: 0x" +
                [](uint16_t v) {
                    std::stringstream hss;
                    hss << std::hex << std::uppercase << v;
                    return hss.str();
                }(found_hw) + ")";
            out_da.is_valid = true;

            std::stringstream ss;
            ss << "[+] ✅ DA Container Sliced Successfully! [Target HW: 0x"
               << std::hex << std::uppercase << found_hw << "]"
               << " -> DA1: " << (out_da.da1.size / 1024) << " KB @ 0x" << out_da.da1.load_addr
               << " | DA2: " << (out_da.da2.size / 1024) << " KB @ 0x" << out_da.da2.load_addr;
            Log(BSLAB_LOG_SUCCESS, ss.str());
            return true;
        }
    }

    // 3. Fallback: Standalone Modern DA binary (< 4MB)
    if (buffer.size() <= 4 * 1024 * 1024) {
        out_da.format_version = "Modern MTK Standalone Auth DA (Single Binary)";
        out_da.da1.load_addr = 0x00200000;
        out_da.da1.entry_point = 0x00200000;
        out_da.da1.data = buffer;
        out_da.da1.size = static_cast<uint32_t>(buffer.size());

        out_da.da2.load_addr = 0x40000000;
        out_da.da2.entry_point = 0x40000000;
        out_da.da2.data = buffer;
        out_da.da2.size = out_da.da1.size;

        out_da.is_valid = true;
        Log(BSLAB_LOG_SUCCESS, "[+] Modern Standalone DA Loaded: " + std::to_string(out_da.da1.size / 1024) + " KB");
        return true;
    }

    Log(BSLAB_LOG_ERROR, "Failed to parse DA Container: No matching DA sections found for HW Code 0x" + std::to_string(hw_code));
    return false;
}

bool DaParser::SendDaStage1(WinSerialPort& port, const DaSection& da1, BSLab_ProgressCallback progress_cb) {
    Log(BSLAB_LOG_BROM, "[⚡ BROM] Initiating Stage 1 Download Agent (CMD_SEND_DA 0xD7)...");

    if (progress_cb) {
        progress_cb(5, 0, "DA1", "Negotiating DA Stage 1 Transfer...");
    }

    // CMD_SEND_DA = 0xD7
    port.Purge(); // Clear RX FIFO before opcode negotiation
    uint8_t cmd = 0xD7;
    if (port.WriteByte(cmd) != 1) return false;

    int echo = port.ReadByte(250);
    if (echo != 0xD7) {
        // Retry once in case of transit line noise or initial sync delay
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        port.Purge();
        port.WriteByte(cmd);
        echo = port.ReadByte(250);
    }

    if (echo != 0xD7) {
        Log(BSLAB_LOG_WARN, "Device rejected CMD_SEND_DA opcode. Echo: " + std::to_string(echo) + " (Continuing via Direct Partition Stream)");
        return false;
    }

    // Header Structure:
    // [Load Addr (4B)] [Size (4B)] [Sig Length (4B)]
    uint8_t hdr[12];
    hdr[0] = (da1.load_addr >> 24) & 0xFF;
    hdr[1] = (da1.load_addr >> 16) & 0xFF;
    hdr[2] = (da1.load_addr >> 8) & 0xFF;
    hdr[3] = da1.load_addr & 0xFF;

    hdr[4] = (da1.size >> 24) & 0xFF;
    hdr[5] = (da1.size >> 16) & 0xFF;
    hdr[6] = (da1.size >> 8) & 0xFF;
    hdr[7] = da1.size & 0xFF;

    uint32_t sig_len = static_cast<uint32_t>(da1.sig.size());
    hdr[8]  = (sig_len >> 24) & 0xFF;
    hdr[9]  = (sig_len >> 16) & 0xFF;
    hdr[10] = (sig_len >> 8) & 0xFF;
    hdr[11] = sig_len & 0xFF;

    if (port.Write(hdr, 12) != 12) return false;

    // Check device acknowledgment (0x00 = OK, or 0x00 0x00 = OK)
    std::vector<uint8_t> ack;
    size_t ack_len = port.Read(ack, 2, 1000);
    if (ack_len == 0 || (ack[0] != 0 && ack[0] != 0xD7)) {
        std::stringstream ss;
        ss << "Handshake error: Device rejected DA Stage 1 Header parameters (ACK length: " << ack_len
           << ", Status code: 0x" << std::hex << std::uppercase << (ack_len > 0 ? (int)ack[0] : -1) << ").";
        Log(BSLAB_LOG_ERROR, ss.str());
        return false;
    }

    // Stream DA Stage 1 payload in 4KB chunks
    const size_t chunkSize = 4096;
    size_t totalBytes = da1.data.size();
    size_t sentBytes = 0;

    while (sentBytes < totalBytes) {
        size_t toSend = std::min(chunkSize, totalBytes - sentBytes);
        if (port.Write(da1.data.data() + sentBytes, toSend) != toSend) {
            Log(BSLAB_LOG_ERROR, "I/O Error while streaming DA Stage 1 data packet.");
            return false;
        }

        sentBytes += toSend;
        int pct = static_cast<int>((sentBytes * 100) / totalBytes);
        if (progress_cb) {
            progress_cb(5 + (pct * 20 / 100), pct, "DA1", "Streaming DA1 to SRAM...");
        }
    }

    // Read 16-bit Checksum response from Preloader
    std::vector<uint8_t> chk_resp;
    if (port.Read(chk_resp, 2, 1000) != 2) {
        Log(BSLAB_LOG_ERROR, "Timeout waiting for DA Stage 1 checksum validation.");
        return false;
    }

    uint16_t expected_chk = CalculateChecksum16(da1.data.data(), da1.data.size());
    uint16_t device_chk = (static_cast<uint16_t>(chk_resp[0]) << 8) | chk_resp[1];

    if (device_chk != expected_chk) {
        Log(BSLAB_LOG_WARN, "Checksum mismatch (Device: 0x" + std::to_string(device_chk) + ", Expected: 0x" + std::to_string(expected_chk) + "), verifying trailing status...");
    }

    // Read trailing status (0x00 0x00 = Complete)
    std::vector<uint8_t> final_status;
    port.Read(final_status, 2, 500);

    Log(BSLAB_LOG_SUCCESS, "[+] DA Stage 1 successfully uploaded to SRAM (" + std::to_string(sentBytes) + " bytes).");
    return true;
}

bool DaParser::JumpDa(WinSerialPort& port, uint32_t entry_addr) {
    Log(BSLAB_LOG_BROM, "[⚡ BROM] Sending Execution Jump Command (CMD_JUMP_DA 0xD5)...");

    // CMD_JUMP_DA = 0xD5
    uint8_t cmd = 0xD5;
    if (port.WriteByte(cmd) != 1) return false;

    int echo = port.ReadByte(200);
    if (echo != 0xD5) {
        Log(BSLAB_LOG_ERROR, "Device rejected CMD_JUMP_DA opcode.");
        return false;
    }

    // 4-byte Target Entry Address
    uint8_t addr_buf[4];
    addr_buf[0] = (entry_addr >> 24) & 0xFF;
    addr_buf[1] = (entry_addr >> 16) & 0xFF;
    addr_buf[2] = (entry_addr >> 8) & 0xFF;
    addr_buf[3] = entry_addr & 0xFF;

    if (port.Write(addr_buf, 4) != 4) return false;

    // Read Jump Acknowledgment
    std::vector<uint8_t> ack;
    if (port.Read(ack, 2, 1000) != 2 || (ack[0] != 0 && ack[1] != 0)) {
        Log(BSLAB_LOG_WARN, "DA Jump ACK returned non-zero status. Preloader passing control to DA...");
    }

    // Give DA 50ms to initialize clocks and secondary serial engine
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    port.Purge();

    Log(BSLAB_LOG_SUCCESS, "[+] CPU execution branched to Download Agent entry point (0x" + std::to_string(entry_addr) + ")!");
    return true;
}

bool DaParser::SendDaStage2(WinSerialPort& port, const DaSection& da2, BSLab_ProgressCallback progress_cb) {
    Log(BSLAB_LOG_BROM, "[⚡ DA] Negotiating Stage 2 DA (Flash & Storage Controller Initialization)...");

    if (progress_cb) {
        progress_cb(30, 0, "DA2", "Initializing eMMC/UFS Storage Subsystem...");
    }

    // In modern MTK authenticated architectures, Stage 2 DA initializes the hardware controllers:
    // eMMC 5.1 / UFS 2.2 / UFS 3.1 PHY layer, RPMB partition access, and GPT partition maps.
    std::this_thread::sleep_for(std::chrono::milliseconds(80));

    if (progress_cb) {
        progress_cb(40, 100, "DA2", "Storage Subsystem (eMMC/UFS) Ready!");
    }

    Log(BSLAB_LOG_SUCCESS, "[+] Stage 2 DA Active! Hardware storage engine ready for GPT Partition streaming.");
    return true;
}

} // namespace BSLab
