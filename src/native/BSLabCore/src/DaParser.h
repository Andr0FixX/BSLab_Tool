#pragma once

#include "WinSerialPort.h"
#include "../include/BSLabCore.h"
#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

struct DaSection {
    uint32_t load_addr = 0;
    uint32_t entry_point = 0;
    uint32_t size = 0;
    std::vector<uint8_t> data;
    std::vector<uint8_t> sig;
};

struct DaContainer {
    std::string file_path;
    uint16_t target_hw_code = 0;
    std::string format_version;
    DaSection da1; // Stage 1 (Initial Loader)
    DaSection da2; // Stage 2 (Flash Engine for eMMC / UFS / NAND)
    bool is_valid = false;
};

class DaParser {
public:
    DaParser(BSLab_LogCallback log_cb = nullptr);
    ~DaParser() = default;

    // Parse DA binary (supports MTK_AllInOne_DA_v5 and standalone modern 2025 DA containers)
    bool LoadFromFile(const std::string& da_path, uint16_t hw_code, DaContainer& out_da);

    // Stream DA Stage 1 into Target SoC SRAM
    bool SendDaStage1(WinSerialPort& port, const DaSection& da1, BSLab_ProgressCallback progress_cb = nullptr);

    // Jump execution to DA Entrypoint
    bool JumpDa(WinSerialPort& port, uint32_t entry_addr);

    // Stream DA Stage 2 into DRAM and initialize Storage Subsystem (eMMC / UFS)
    bool SendDaStage2(WinSerialPort& port, const DaSection& da2, BSLab_ProgressCallback progress_cb = nullptr);

private:
    BSLab_LogCallback m_log_cb;

    void Log(BSLab_LogLevel level, const std::string& msg);
    uint16_t CalculateChecksum16(const uint8_t* data, size_t len);
    uint32_t CalculateChecksum32(const uint8_t* data, size_t len);
};

} // namespace BSLab
