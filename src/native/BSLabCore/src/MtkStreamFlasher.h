#pragma once

#include "WinSerialPort.h"
#include "GptParser.h"
#include "../include/BSLabCore.h"
#include <string>
#include <cstdint>
#include <windows.h>

namespace BSLab {

class MtkStreamFlasher {
public:
    MtkStreamFlasher(BSLab_LogCallback log_cb = nullptr);
    ~MtkStreamFlasher() = default;

    // Flash raw partition image using Zero-Copy Windows Memory Mapping
    bool FlashPartitionImage(
        WinSerialPort& port,
        const std::string& partition_name,
        uint64_t start_lba,
        const std::wstring& image_file_path,
        BSLab_ProgressCallback progress_cb = nullptr,
        int base_overall_pct = 0,
        int overall_weight = 100
    );

    // Flash Android Sparse Image chunk-by-chunk (skips DONT_CARE blocks with zero RAM bloat)
    bool FlashSparseImage(
        WinSerialPort& port,
        const std::string& partition_name,
        uint64_t start_lba,
        const uint8_t* pData,
        uint64_t totalBytes,
        BSLab_ProgressCallback progress_cb = nullptr,
        int base_overall_pct = 0,
        int overall_weight = 100
    );

    // Flash multi-partition firmware from MediaTek Scatter Descriptor
    bool FlashScatterFirmware(
        WinSerialPort& port,
        const std::string& scatter_path,
        const std::vector<GptPartition>& partitions,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // Direct Erase / Format partition (Zero out LBA range)
    bool ErasePartition(
        WinSerialPort& port,
        const std::string& partition_name,
        uint64_t start_lba,
        uint64_t sector_count,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // Dump partition to disk
    bool DumpPartitionImage(
        WinSerialPort& port,
        const std::string& partition_name,
        uint64_t start_lba,
        uint64_t sector_count,
        const std::wstring& output_file_path,
        BSLab_ProgressCallback progress_cb = nullptr
    );

private:
    BSLab_LogCallback m_log_cb;

    void Log(BSLab_LogLevel level, const std::string& msg);
    uint32_t CalculateCRC32(const uint8_t* data, size_t length);
};

} // namespace BSLab
