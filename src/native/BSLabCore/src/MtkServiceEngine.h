#pragma once

#include "MtkEngine.h"
#include "DaParser.h"
#include "GptParser.h"
#include "MtkStreamFlasher.h"
#include "../include/BSLabCore.h"
#include <string>
#include <vector>
#include <functional>

namespace BSLab {

enum class ServiceOpType {
    RESET_FRP,
    RESET_MI_ACCOUNT,
    FACTORY_RESET_SAFE,
    BACKUP_NVRAM,
    RESTORE_NVRAM,
    UNLOCK_BOOTLOADER
};

class MtkServiceEngine {
public:
    MtkServiceEngine(BSLab_LogCallback log_cb = nullptr);
    ~MtkServiceEngine() = default;

    // 1-Click FRP Lock Bypass (Erases 'frp', 'persistent', and 'config' LBA ranges)
    bool ResetFRP(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // 1-Click Mi Account / Xiaomi Cloud Lock Bypass (Formats/patches 'persist' partition)
    bool ResetMiAccount(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // 1-Click Factory Reset + Safe Format (Formats 'userdata' + 'metadata' + 'cache')
    bool FactoryResetSafe(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        bool wipe_frp,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // 1-Click NVRAM / NVDATA / EFS Backup (Dumps 'nvram', 'nvdata', 'protect1', 'protect2')
    bool BackupNVRAM(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        const std::wstring& backup_folder,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // 1-Click NVRAM / NVDATA / EFS Restore
    bool RestoreNVRAM(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        const std::wstring& backup_folder,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // 1-Click Bootloader Unlock (Patches 'seccfg' security configuration)
    bool UnlockBootloader(
        WinSerialPort& port,
        const std::vector<GptPartition>& partitions,
        BSLab_ProgressCallback progress_cb = nullptr
    );

private:
    BSLab_LogCallback m_log_cb;
    MtkStreamFlasher m_flasher;

    void Log(BSLab_LogLevel level, const std::string& msg);
    const GptPartition* LocatePartition(const std::vector<GptPartition>& partitions, const std::vector<std::string>& possible_names);
};

} // namespace BSLab
