#include "SpdFdlEngine.h"
#include "SpdBslProtocol.h"
#include <chrono>
#include <thread>
#include <algorithm>

namespace BSLab {

SpdFdlEngine::SpdFdlEngine(WinSerialPort& serialPort, LogCallback logger)
    : m_port(serialPort), m_logger(std::move(logger)) {}

void SpdFdlEngine::Log(int level, const std::string& msg) {
    if (m_logger) {
        m_logger(level, msg);
    }
}

bool SpdFdlEngine::LoadFdl(
    const uint8_t* fdlData,
    size_t fdlSize,
    uint32_t loadAddr,
    const std::string& fdlName,
    ProgressCallback progressCb
) {
    if (!fdlData || fdlSize == 0 || !m_port.IsOpen()) {
        Log(4, fdlName + " Load Error: Empty data or closed COM port.");
        return false;
    }

    Log(0, "Initiating " + fdlName + " Transfer (" + std::to_string(fdlSize) + " bytes at RAM: 0x" + std::to_string(loadAddr) + ")...");

    // 1. START DATA: [addr: uint32 BE, length: uint32 BE]
    uint8_t startPayload[8];
    startPayload[0] = static_cast<uint8_t>((loadAddr >> 24) & 0xFF);
    startPayload[1] = static_cast<uint8_t>((loadAddr >> 16) & 0xFF);
    startPayload[2] = static_cast<uint8_t>((loadAddr >> 8) & 0xFF);
    startPayload[3] = static_cast<uint8_t>(loadAddr & 0xFF);

    startPayload[4] = static_cast<uint8_t>((fdlSize >> 24) & 0xFF);
    startPayload[5] = static_cast<uint8_t>((fdlSize >> 16) & 0xFF);
    startPayload[6] = static_cast<uint8_t>((fdlSize >> 8) & 0xFF);
    startPayload[7] = static_cast<uint8_t>(fdlSize & 0xFF);

    uint16_t respType = 0;
    std::vector<uint8_t> respPayload;
    if (!SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_START_DATA, startPayload, 8, respType, respPayload, 5000)) {
        Log(4, fdlName + " Start Data rejected by device.");
        return false;
    }

    // 2. MID DATA: send chunks
    size_t offset = 0;
    while (offset < fdlSize) {
        size_t chunkSize = std::min<size_t>(FDL_CHUNK_SIZE, fdlSize - offset);
        if (!SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_MID_DATA, fdlData + offset, chunkSize, respType, respPayload, 4000)) {
            Log(4, "Error streaming " + fdlName + " chunk at offset " + std::to_string(offset));
            return false;
        }

        offset += chunkSize;
        if (progressCb) {
            float pct = static_cast<float>(offset) / static_cast<float>(fdlSize);
            progressCb(pct, "Streaming " + fdlName + " to RAM...");
        }
    }

    // 3. END DATA
    if (!SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_END_DATA, nullptr, 0, respType, respPayload, 4000)) {
        Log(4, fdlName + " End Data rejected.");
        return false;
    }

    // 4. EXEC DATA: Execute FDL in RAM
    Log(0, "Executing " + fdlName + " in target RAM...");
    if (SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_EXEC_DATA, nullptr, 0, respType, respPayload, 5000)) {
        Log(2, "[✓] " + fdlName + " Executed Successfully!");
        std::this_thread::sleep_for(std::chrono::milliseconds(300));
        return true;
    } else {
        Log(3, fdlName + " Exec Data reported warning.");
        return false;
    }
}

std::string SpdFdlEngine::ReadChipInfo() {
    uint16_t respType = 0;
    std::vector<uint8_t> respPayload;
    if (SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_READ_CHIP_TYPE, nullptr, 0, respType, respPayload, 3000)) {
        if (!respPayload.empty()) {
            std::string chip;
            for (size_t i = 0; i < respPayload.size(); ++i) {
                if (respPayload[i] != 0) chip.push_back(static_cast<char>(respPayload[i]));
            }
            if (!chip.empty()) return chip;
        }
    }
    return "Unisoc Universal (Tiger/SC)";
}

bool SpdFdlEngine::ErasePartition(const std::string& partitionName) {
    Log(0, "Erasing Unisoc partition '" + partitionName + "'...");

    // Encode partition name as UTF-16LE + 2 null bytes
    std::vector<uint8_t> nameBuf;
    nameBuf.reserve((partitionName.size() + 1) * 2);
    for (char c : partitionName) {
        nameBuf.push_back(static_cast<uint8_t>(c));
        nameBuf.push_back(0);
    }
    nameBuf.push_back(0);
    nameBuf.push_back(0);

    uint16_t respType = 0;
    std::vector<uint8_t> respPayload;
    if (SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_ERASE_PARTITION, nameBuf.data(), nameBuf.size(), respType, respPayload, 8000)) {
        Log(2, "[✓] Partition '" + partitionName + "' Erased Successfully!");
        return true;
    } else {
        Log(4, "[!] Failed to erase partition '" + partitionName + "'.");
        return false;
    }
}

bool SpdFdlEngine::WritePartition(
    const std::string& partitionName,
    const uint8_t* data,
    size_t length,
    ProgressCallback progressCb
) {
    if (!data || length == 0) return false;

    Log(0, "Writing partition '" + partitionName + "' (" + std::to_string(length) + " bytes)...");

    // Partition write init packet: UTF-16LE name + length[4]
    std::vector<uint8_t> initPayload;
    for (char c : partitionName) {
        initPayload.push_back(static_cast<uint8_t>(c));
        initPayload.push_back(0);
    }
    initPayload.push_back(0);
    initPayload.push_back(0);

    // Append length (uint32 BE)
    initPayload.push_back(static_cast<uint8_t>((length >> 24) & 0xFF));
    initPayload.push_back(static_cast<uint8_t>((length >> 16) & 0xFF));
    initPayload.push_back(static_cast<uint8_t>((length >> 8) & 0xFF));
    initPayload.push_back(static_cast<uint8_t>(length & 0xFF));

    uint16_t respType = 0;
    std::vector<uint8_t> respPayload;
    if (!SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_START_DATA, initPayload.data(), initPayload.size(), respType, respPayload, 5000)) {
        Log(4, "Partition write start failed for " + partitionName);
        return false;
    }

    size_t offset = 0;
    while (offset < length) {
        size_t chunkSize = std::min<size_t>(FDL_CHUNK_SIZE, length - offset);
        if (!SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_MID_DATA, data + offset, chunkSize, respType, respPayload, 4000)) {
            Log(4, "Partition write failed at offset " + std::to_string(offset));
            return false;
        }

        offset += chunkSize;
        if (progressCb) {
            float pct = static_cast<float>(offset) / static_cast<float>(length);
            progressCb(pct, "Writing " + partitionName + "...");
        }
    }

    if (!SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_END_DATA, nullptr, 0, respType, respPayload, 4000)) {
        Log(4, "Partition write end failed for " + partitionName);
        return false;
    }

    Log(2, "[✓] Partition '" + partitionName + "' Written Successfully!");
    return true;
}

bool SpdFdlEngine::RebootDevice() {
    Log(0, "Dispatching Normal Reset / Reboot to Unisoc device...");
    uint16_t respType = 0;
    std::vector<uint8_t> respPayload;
    return SpdBslProtocol::SendCommand(m_port, SpdBslProtocol::CMD_NORMAL_RESET, nullptr, 0, respType, respPayload, 2000);
}

} // namespace BSLab
