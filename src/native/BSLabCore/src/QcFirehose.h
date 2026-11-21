#pragma once

#include "WinSerialPort.h"
#include "GptParser.h"
#include "../include/BSLabCore.h"
#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

enum class QcStorageType {
    EMMC,
    UFS
};

class QcFirehose {
public:
    QcFirehose(BSLab_LogCallback log_cb = nullptr);
    ~QcFirehose() = default;

    // Send XML Configuration packet to running Firehose (eMMC vs UFS)
    bool Configure(WinSerialPort& port, QcStorageType storage = QcStorageType::EMMC);

    // Read Live GPT Partition Table from Qualcomm Storage LUN
    bool ReadGPT(
        WinSerialPort& port,
        std::vector<GptPartition>& out_partitions,
        int physical_partition_lun = 0
    );

    // Stream partition image using Zero-Copy Memory Mapping via Firehose XML
    bool FlashPartition(
        WinSerialPort& port,
        const std::string& partition_name,
        uint64_t start_sector,
        uint64_t sector_count,
        const std::wstring& image_path,
        BSLab_ProgressCallback progress_cb = nullptr,
        int physical_partition_lun = 0
    );

    // 1-Click Erase Sector Range
    bool ErasePartition(
        WinSerialPort& port,
        const std::string& partition_name,
        uint64_t start_sector,
        uint64_t sector_count,
        BSLab_ProgressCallback progress_cb = nullptr,
        int physical_partition_lun = 0
    );

    // 1-Click Qualcomm Reset FRP (LBA erase of 'frp' / 'config')
    bool ResetFRP(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // 1-Click Qualcomm Safe Factory Reset (LBA erase of 'userdata' + 'metadata')
    bool FactoryResetSafe(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        bool wipe_frp,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // Reboot Device to Android System
    bool Reboot(WinSerialPort& port);

private:
    BSLab_LogCallback m_log_cb;

    void Log(BSLab_LogLevel level, const std::string& msg);
    bool SendXmlCommand(WinSerialPort& port, const std::string& xml, std::string& out_resp, int timeout_ms = 4000);
};

} // namespace BSLab
