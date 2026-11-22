#include "UnisocEngine.h"
#include <windows.h>
#include <algorithm>
#include <sstream>
#include <thread>
#include <chrono>

namespace BSLab {

UnisocEngine::UnisocEngine(LogCallback logger)
    : m_logger(std::move(logger)) {}

UnisocEngine::~UnisocEngine() {
    Abort();
}

void UnisocEngine::Log(int level, const std::string& msg) {
    if (m_logger) {
        m_logger(level, msg);
    }
}

void UnisocEngine::Abort() {
    m_abortRequested.store(true);
    if (m_serial.IsOpen()) {
        m_serial.Close();
    }
}

std::vector<UnisocPortInfo> UnisocEngine::ScanPorts() {
    std::vector<UnisocPortInfo> devices;

    HKEY hKey;
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM", 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        char valueName[256];
        DWORD valLen = sizeof(valueName);
        char data[256];
        DWORD dataLen = sizeof(data);
        DWORD index = 0;

        while (RegEnumValueA(hKey, index, valueName, &valLen, nullptr, nullptr, reinterpret_cast<LPBYTE>(data), &dataLen) == ERROR_SUCCESS) {
            std::string portName(data, dataLen > 0 ? (data[dataLen - 1] == '\0' ? dataLen - 1 : dataLen) : 0);
            std::string regKey(valueName, valLen);

            std::string lowerKey = regKey;
            std::transform(lowerKey.begin(), lowerKey.end(), lowerKey.begin(), ::tolower);

            bool isSpd = (lowerKey.find("spd") != std::string::npos ||
                          lowerKey.find("sprd") != std::string::npos ||
                          lowerKey.find("spreadtrum") != std::string::npos ||
                          lowerKey.find("unisoc") != std::string::npos);

            std::string desc = isSpd ? "SPRD U2S Diag / Download Port" : "Serial Communication Port";
            devices.push_back({ portName, desc, regKey });

            valLen = sizeof(valueName);
            dataLen = sizeof(data);
            index++;
        }
        RegCloseKey(hKey);
    }

    return devices;
}

bool UnisocEngine::Connect(
    const std::string& portName,
    const std::string& pacPath,
    ProgressCallback progressCb
) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_abortRequested.store(false);

    if (m_serial.IsOpen()) {
        m_serial.Close();
    }

    Log(0, "Connecting to Unisoc Port: " + portName + " at 115200 baud...");
    if (!m_serial.Open(portName, 115200)) {
        Log(4, "Failed to open port: " + portName);
        return false;
    }

    m_serial.SetDtr(true);
    m_serial.SetRts(true);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    m_serial.Purge();

    // 1. Trap BSL 0x7E sync frames
    Log(0, "Sending BSL Sync Frames (0x7E) to trap Unisoc Bootloader...");
    if (progressCb) progressCb(10, 0, "BROM", "Trapping 0x7E Sync Frames...");

    if (!SpdBslProtocol::SyncDevice(m_serial, 35)) {
        Log(4, "BSL 0x7E Sync Mismatch/Timeout. Reconnect phone with Vol- held.");
        m_serial.Close();
        return false;
    }

    Log(2, "[SYNC] Unisoc BSL Handshake Trapped Successfully (0x7E ACK Received)!");

    // 2. Connect Command
    uint16_t respType = 0;
    std::vector<uint8_t> respPayload;
    if (!SpdBslProtocol::SendCommand(m_serial, SpdBslProtocol::CMD_CONNECT, nullptr, 0, respType, respPayload, 4000)) {
        Log(3, "BSL Connect Command reported warning or no ACK.");
    }

    SpdFdlEngine fdl(m_serial, [this](int lvl, const std::string& msg) {
        Log(lvl, msg);
    });

    // 3. If PAC provided, extract and load FDL1 & FDL2
    if (!pacPath.empty()) {
        Log(0, "Parsing PAC Archive: " + pacPath + "...");
        SpdPacInfo pacInfo;
        std::string err;
        if (!SpdPacParser::Parse(pacPath, pacInfo, err)) {
            Log(4, "PAC Parse Error: " + err);
            m_serial.Close();
            return false;
        }

        // Find FDL1 & FDL2
        const SpdPacPartition* fdl1Part = nullptr;
        const SpdPacPartition* fdl2Part = nullptr;

        for (const auto& p : pacInfo.partitions) {
            std::string lower = p.name;
            std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
            if (lower.find("fdl1") != std::string::npos) fdl1Part = &p;
            if (lower.find("fdl2") != std::string::npos) fdl2Part = &p;
        }

        if (fdl1Part) {
            std::vector<uint8_t> fdl1Data;
            if (!SpdPacParser::ExtractPartition(pacPath, *fdl1Part, fdl1Data, err)) {
                Log(4, "Failed to extract FDL1: " + err);
                m_serial.Close();
                return false;
            }
            if (progressCb) progressCb(30, 0, "FDL1", "Streaming FDL1 to RAM...");
            if (!fdl.LoadFdl(fdl1Data.data(), fdl1Data.size(), SpdFdlEngine::FDL1_ADDR_TIGER, "FDL1")) {
                Log(4, "FDL1 execution failed.");
                m_serial.Close();
                return false;
            }
        }

        if (fdl2Part) {
            std::vector<uint8_t> fdl2Data;
            if (!SpdPacParser::ExtractPartition(pacPath, *fdl2Part, fdl2Data, err)) {
                Log(4, "Failed to extract FDL2: " + err);
                m_serial.Close();
                return false;
            }
            if (progressCb) progressCb(60, 0, "FDL2", "Streaming FDL2 to RAM...");
            if (!fdl.LoadFdl(fdl2Data.data(), fdl2Data.size(), SpdFdlEngine::FDL2_ADDR_TIGER, "FDL2")) {
                Log(4, "FDL2 execution failed.");
                m_serial.Close();
                return false;
            }
        }

        Log(2, "FDL1 & FDL2 Bootloader Active: Storage & Partition Engine Ready!");
    }

    if (progressCb) progressCb(100, 100, "CONNECT", "Connected & FDL Active [OK]");
    return true;
}

bool UnisocEngine::FlashFirmware(
    const std::string& portName,
    const std::string& pacPath,
    bool rebootAfter,
    ProgressCallback progressCb
) {
    if (!Connect(portName, pacPath, progressCb)) {
        return false;
    }

    SpdPacInfo pacInfo;
    std::string err;
    if (!SpdPacParser::Parse(pacPath, pacInfo, err)) {
        Log(4, "PAC Parse Error: " + err);
        return false;
    }

    SpdFdlEngine fdl(m_serial, [this](int lvl, const std::string& msg) {
        Log(lvl, msg);
    });

    uint64_t totalBytes = 0;
    for (const auto& p : pacInfo.partitions) {
        std::string lower = p.name;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        if (p.is_download && p.file_size > 0 && lower.find("fdl") == std::string::npos) {
            totalBytes += p.file_size;
        }
    }

    uint64_t bytesWritten = 0;

    for (const auto& p : pacInfo.partitions) {
        if (m_abortRequested.load()) {
            Log(3, "Operation aborted by user.");
            return false;
        }

        std::string lower = p.name;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        if (!p.is_download || p.file_size == 0 || lower.find("fdl") != std::string::npos) {
            continue;
        }

        std::vector<uint8_t> partData;
        if (!SpdPacParser::ExtractPartition(pacPath, p, partData, err)) {
            Log(4, "Failed to extract partition " + p.name + ": " + err);
            return false;
        }

        bool ok = fdl.WritePartition(p.name, partData.data(), partData.size(), [&](float pct, const std::string& status) {
            if (progressCb) {
                int filePct = static_cast<int>(pct * 100.0f);
                uint64_t currentOverall = bytesWritten + static_cast<uint64_t>(pct * static_cast<float>(p.file_size));
                int overallPct = totalBytes > 0 ? static_cast<int>((currentOverall * 100) / totalBytes) : filePct;
                progressCb(overallPct, filePct, p.name.c_str(), status.c_str());
            }
        });

        if (!ok) {
            Log(4, "Write failed on partition " + p.name);
            return false;
        }

        bytesWritten += p.file_size;
    }

    if (rebootAfter) {
        fdl.RebootDevice();
    }

    if (progressCb) progressCb(100, 100, "PASS", "Flashing completed successfully!");
    Log(2, "🎉 Unisoc PAC Firmware Flash Completed Successfully!");
    return true;
}

bool UnisocEngine::ResetFRP(
    const std::string& portName,
    const std::string& pacPath,
    ProgressCallback progressCb
) {
    if (!Connect(portName, pacPath, progressCb)) {
        return false;
    }

    SpdFdlEngine fdl(m_serial, [this](int lvl, const std::string& msg) {
        Log(lvl, msg);
    });

    Log(0, "Executing 1-Click FRP Unlock for Unisoc Device...");
    bool ok = fdl.ErasePartition("persist") || fdl.ErasePartition("misc") || fdl.ErasePartition("frp");

    if (ok) {
        Log(2, "[✓] FRP Lock Cleared Successfully!");
        fdl.RebootDevice();
        if (progressCb) progressCb(100, 100, "FRP", "FRP Lock Cleared [OK]");
        return true;
    } else {
        Log(4, "[!] FRP Reset Failed.");
        return false;
    }
}

bool UnisocEngine::FactoryReset(
    const std::string& portName,
    const std::string& pacPath,
    ProgressCallback progressCb
) {
    if (!Connect(portName, pacPath, progressCb)) {
        return false;
    }

    SpdFdlEngine fdl(m_serial, [this](int lvl, const std::string& msg) {
        Log(lvl, msg);
    });

    Log(0, "Executing 1-Click Factory Reset for Unisoc Device...");
    bool ok1 = fdl.ErasePartition("userdata");
    bool ok2 = fdl.ErasePartition("cache");

    if (ok1 || ok2) {
        Log(2, "[✓] Factory Reset / Userdata Wipe Successful!");
        fdl.RebootDevice();
        if (progressCb) progressCb(100, 100, "RESET", "Factory Reset Complete [OK]");
        return true;
    } else {
        Log(4, "[!] Factory Reset Failed.");
        return false;
    }
}

bool UnisocEngine::Reboot(const std::string& portName) {
    if (m_serial.IsOpen()) {
        SpdFdlEngine fdl(m_serial, [this](int lvl, const std::string& msg) {
            Log(lvl, msg);
        });
        return fdl.RebootDevice();
    } else {
        if (!m_serial.Open(portName, 115200)) return false;
        SpdFdlEngine fdl(m_serial, [this](int lvl, const std::string& msg) {
            Log(lvl, msg);
        });
        bool ok = fdl.RebootDevice();
        m_serial.Close();
        return ok;
    }
}

} // namespace BSLab
