#include "QcEngine.h"

namespace BSLab {

QcEngine::QcEngine(BSLab_LogCallback log_cb)
    : m_log_cb(log_cb), m_sahara(log_cb), m_firehose(log_cb) {
}

QcEngine::~QcEngine() {
    if (m_port.IsOpen()) {
        m_port.Close();
    }
}

void QcEngine::Log(BSLab_LogLevel level, const std::string& msg) {
    if (m_log_cb) {
        m_log_cb(static_cast<int>(level), msg.c_str());
    }
}

bool QcEngine::ConnectAndBootFirehose(
    const std::string& port_name,
    const std::wstring& programmer_path,
    BSLab_ProgressCallback progress_cb
) {
    Log(BSLAB_LOG_BROM, "Opening Qualcomm HS-USB QDLoader 9008 Port: " + port_name + "...");

    if (!m_port.Open(port_name, 115200)) {
        Log(BSLAB_LOG_ERROR, "[-] Failed to open " + port_name + " (Port may be locked or device disconnected).");
        return false;
    }

    // 1. Execute Sahara Handshake
    if (!m_sahara.Handshake(m_port, 8000)) {
        m_port.Close();
        return false;
    }

    // 2. Upload Firehose Programmer into SoC DRAM
    if (!m_sahara.UploadProgrammer(m_port, programmer_path, progress_cb)) {
        m_port.Close();
        return false;
    }

    // 3. Configure Firehose Storage Mode
    if (!m_firehose.Configure(m_port, QcStorageType::EMMC)) {
        Log(BSLAB_LOG_WARN, "Notice: Storage configure completed with defaults.");
    }

    Log(BSLAB_LOG_SUCCESS, "[+] Qualcomm Snapdragon Engine Ready! Storage & Partition Doctor Active.");
    return true;
}

bool QcEngine::ReadGPT(std::vector<GptPartition>& out_partitions, int lun) {
    bool ok = m_firehose.ReadGPT(m_port, out_partitions, lun);
    if (ok) {
        m_cached_partitions = out_partitions;
    }
    return ok;
}

bool QcEngine::ResetFRP(BSLab_ProgressCallback progress_cb) {
    if (m_cached_partitions.empty()) {
        ReadGPT(m_cached_partitions);
    }
    return m_firehose.ResetFRP(m_port, m_cached_partitions, progress_cb);
}

bool QcEngine::FactoryReset(bool wipe_frp, BSLab_ProgressCallback progress_cb) {
    if (m_cached_partitions.empty()) {
        ReadGPT(m_cached_partitions);
    }
    return m_firehose.FactoryResetSafe(m_port, m_cached_partitions, wipe_frp, progress_cb);
}

bool QcEngine::FlashPartition(
    const std::string& name,
    uint64_t start_lba,
    uint64_t sector_count,
    const std::wstring& image_path,
    BSLab_ProgressCallback progress_cb
) {
    return m_firehose.FlashPartition(m_port, name, start_lba, sector_count, image_path, progress_cb);
}

bool QcEngine::ErasePartition(
    const std::string& name,
    uint64_t start_lba,
    uint64_t sector_count,
    BSLab_ProgressCallback progress_cb
) {
    return m_firehose.ErasePartition(m_port, name, start_lba, sector_count, progress_cb);
}

bool QcEngine::Reboot() {
    return m_firehose.Reboot(m_port);
}

} // namespace BSLab
