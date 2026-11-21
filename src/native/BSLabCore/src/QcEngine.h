#pragma once

#include "WinSerialPort.h"
#include "QcSahara.h"
#include "QcFirehose.h"
#include "GptParser.h"
#include "../include/BSLabCore.h"
#include <string>
#include <vector>

namespace BSLab {

class QcEngine {
public:
    QcEngine(BSLab_LogCallback log_cb = nullptr);
    ~QcEngine();

    // Connects to COM port, executes Sahara handshake, and injects Firehose Programmer
    bool ConnectAndBootFirehose(
        const std::string& port_name,
        const std::wstring& programmer_path,
        BSLab_ProgressCallback progress_cb = nullptr
    );

    // Reads Live GPT from LUN 0
    bool ReadGPT(std::vector<GptPartition>& out_partitions, int lun = 0);

    // 1-Click Service Operations
    bool ResetFRP(BSLab_ProgressCallback progress_cb = nullptr);
    bool FactoryReset(bool wipe_frp, BSLab_ProgressCallback progress_cb = nullptr);
    bool FlashPartition(const std::string& name, uint64_t start_lba, uint64_t sector_count, const std::wstring& image_path, BSLab_ProgressCallback progress_cb = nullptr);
    bool ErasePartition(const std::string& name, uint64_t start_lba, uint64_t sector_count, BSLab_ProgressCallback progress_cb = nullptr);
    bool Reboot();

    WinSerialPort& GetPort() { return m_port; }

private:
    BSLab_LogCallback m_log_cb;
    WinSerialPort m_port;
    QcSahara m_sahara;
    QcFirehose m_firehose;
    std::vector<GptPartition> m_cached_partitions;

    void Log(BSLab_LogLevel level, const std::string& msg);
};

} // namespace BSLab
