#include "KirinRescueEngine.h"
#include "WinSerialPort.h"
#include <windows.h>
#include <setupapi.h>
#include <devguid.h>
#include <initguid.h>
#include <fstream>
#include <filesystem>
#include <algorithm>
#include <chrono>
#include <thread>
#include <sstream>

#pragma comment(lib, "setupapi.lib")

namespace BSLab {

namespace fs = std::filesystem;

KirinRescueEngine::KirinRescueEngine(LogCallback logger)
    : m_logger(std::move(logger)) {
}

void KirinRescueEngine::Log(int level, const std::string& msg) {
    if (m_logger) {
        m_logger(level, msg);
    }
}

// Ports Device Class GUID: {4D36E978-E325-11CE-BFC1-08002BE10318}
static const GUID GUID_DEVCLASS_PORTS_LOCAL = {
    0x4d36e978, 0xe325, 0x11ce, { 0xbf, 0xc1, 0x08, 0x00, 0x2b, 0xe1, 0x03, 0x18 }
};

std::vector<HuaweiPortInfo> KirinRescueEngine::ScanHuaweiPorts() {
    std::vector<HuaweiPortInfo> portList;

    // 1. Scan via SetupAPI for rich hardware descriptors (VID/PID)
    HDEVINFO hDevInfo = SetupDiGetClassDevsA(&GUID_DEVCLASS_PORTS_LOCAL, nullptr, nullptr, DIGCF_PRESENT);
    if (hDevInfo != INVALID_HANDLE_VALUE) {
        SP_DEVINFO_DATA devInfoData;
        devInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

        for (DWORD i = 0; SetupDiEnumDeviceInfo(hDevInfo, i, &devInfoData); i++) {
            char friendlyName[256] = {0};
            char hwId[512] = {0};

            SetupDiGetDeviceRegistryPropertyA(hDevInfo, &devInfoData, SPDRP_FRIENDLYNAME,
                nullptr, reinterpret_cast<PBYTE>(friendlyName), sizeof(friendlyName), nullptr);
            SetupDiGetDeviceRegistryPropertyA(hDevInfo, &devInfoData, SPDRP_HARDWAREID,
                nullptr, reinterpret_cast<PBYTE>(hwId), sizeof(hwId), nullptr);

            std::string nameStr(friendlyName);
            std::string hwStr(hwId);
            std::string nameLower = nameStr;
            std::string hwLower = hwStr;
            std::transform(nameLower.begin(), nameLower.end(), nameLower.begin(), ::tolower);
            std::transform(hwLower.begin(), hwLower.end(), hwLower.begin(), ::tolower);

            // Extract COM port name (e.g. COM12)
            std::string comPort;
            size_t openParen = nameStr.rfind('(');
            size_t closeParen = nameStr.rfind(')');
            if (openParen != std::string::npos && closeParen != std::string::npos && closeParen > openParen) {
                comPort = nameStr.substr(openParen + 1, closeParen - openParen - 1);
            }

            if (comPort.empty() || comPort.find("COM") == std::string::npos) {
                continue;
            }

            bool isHuawei = (hwLower.find("vid_12d1") != std::string::npos ||
                             nameLower.find("huawei") != std::string::npos ||
                             nameLower.find("hisilicon") != std::string::npos);

            if (isHuawei) {
                std::string pType = "Unknown";
                if (hwLower.find("pid_3609") != std::string::npos || nameLower.find("usb com 1.0") != std::string::npos) {
                    pType = "USB COM 1.0";
                } else if (nameLower.find("pcui") != std::string::npos) {
                    pType = "PCUI";
                } else if (nameLower.find("modem") != std::string::npos) {
                    pType = "Modem";
                }

                portList.push_back({ comPort, nameStr, hwStr, pType });
            }
        }
        SetupDiDestroyDeviceInfoList(hDevInfo);
    }

    // 2. Scan Registry SERIALCOMM as fallback
    HKEY hKey;
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM", 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        char valName[256];
        char data[256];
        DWORD index = 0;
        DWORD valLen = sizeof(valName);
        DWORD dataLen = sizeof(data);

        while (RegEnumValueA(hKey, index, valName, &valLen, nullptr, nullptr,
                             reinterpret_cast<LPBYTE>(data), &dataLen) == ERROR_SUCCESS) {
            std::string port(data, dataLen > 0 ? (data[dataLen - 1] == '\0' ? dataLen - 1 : dataLen) : 0);
            std::string key(valName, valLen);
            std::string keyLower = key;
            std::transform(keyLower.begin(), keyLower.end(), keyLower.begin(), ::tolower);

            // Check if not already in portList
            bool alreadyAdded = false;
            for (const auto& p : portList) {
                if (p.port == port) {
                    alreadyAdded = true;
                    break;
                }
            }

            if (!alreadyAdded) {
                if (keyLower.find("huawei") != std::string::npos || keyLower.find("hw_") != std::string::npos) {
                    std::string pType = "Unknown";
                    if (keyLower.find("pcui") != std::string::npos) pType = "PCUI";
                    else if (keyLower.find("modem") != std::string::npos) pType = "Modem";
                    portList.push_back({ port, "Huawei Serial Port", key, pType });
                }
            }

            valLen = sizeof(valName);
            dataLen = sizeof(data);
            index++;
        }
        RegCloseKey(hKey);
    }

    return portList;
}

std::string KirinRescueEngine::FindUsbCom10Port() {
    auto ports = ScanHuaweiPorts();
    for (const auto& p : ports) {
        if (p.type == "USB COM 1.0") {
            return p.port;
        }
    }
    return "";
}

std::string KirinRescueEngine::ResolveChipset(const std::string& hint) {
    std::string h = hint;
    std::transform(h.begin(), h.end(), h.begin(), ::toupper);

    if (h.find("659") != std::string::npos || h.find("650") != std::string::npos ||
        h.find("655") != std::string::npos || h.find("658") != std::string::npos ||
        h.find("65X") != std::string::npos || h.find("RNE") != std::string::npos ||
        h.find("LLD") != std::string::npos || h.find("FIG") != std::string::npos) {
        return "KIRIN_65x";
    }
    if (h.find("710") != std::string::npos || h.find("JSN") != std::string::npos ||
        h.find("POT") != std::string::npos || h.find("STK") != std::string::npos ||
        h.find("MAR") != std::string::npos) {
        return "KIRIN_710A";
    }
    if (h.find("810") != std::string::npos) {
        return "KIRIN_810";
    }
    if (h.find("820") != std::string::npos) {
        return "KIRIN_820";
    }
    if (h.find("970") != std::string::npos || h.find("BKL") != std::string::npos ||
        h.find("CLT") != std::string::npos || h.find("EML") != std::string::npos) {
        return "KIRIN_970";
    }
    if (h.find("980") != std::string::npos || h.find("VOG") != std::string::npos ||
        h.find("ELE") != std::string::npos || h.find("HMA") != std::string::npos ||
        h.find("LYA") != std::string::npos) {
        return "KIRIN_980";
    }
    if (h.find("990") != std::string::npos) {
        return "KIRIN_990";
    }
    return "KIRIN_65x";
}

std::string KirinRescueEngine::FindLoadersDir() {
    std::vector<std::string> candidates = {
        "resources/loaders/kirin",
        "resources\\loaders\\kirin",
        "C:\\BSLab_Tool\\resources\\loaders\\kirin",
        "../resources/loaders/kirin",
        "../../resources/loaders/kirin"
    };

    for (const auto& path : candidates) {
        if (fs::exists(path) && fs::is_directory(path)) {
            return path;
        }
    }
    return "resources/loaders/kirin";
}

bool KirinRescueEngine::BootRescueMode(
    const std::string& port,
    const std::string& chipset,
    ProgressCallback progress_cb
) {
    std::lock_guard<std::mutex> lock(m_engineMutex);
    m_abortRequested = false;

    std::string targetPort = port.empty() ? FindUsbCom10Port() : port;
    if (targetPort.empty()) {
        Log(4, "[Huawei Kirin] No HUAWEI USB COM 1.0 port detected! Connect phone via Test Point to GND.");
        return false;
    }

    std::string chipFolder = ResolveChipset(chipset);
    std::string loadersRoot = FindLoadersDir();
    fs::path chipDir = fs::path(loadersRoot) / chipFolder;

    if (!fs::exists(chipDir)) {
        Log(4, "[Huawei Kirin] Loader directory not found for: " + chipFolder + " at " + chipDir.string());
        return false;
    }

    // Identify stage files in ordered sequence
    std::vector<std::pair<std::string, fs::path>> stageFiles;
    const std::vector<std::string> stageNames = {
        "xloader_1.bin",
        "xloader_2.bin",
        "bl2.bin",
        "fastboot.bin"
    };

    for (const auto& name : stageNames) {
        fs::path p = chipDir / name;
        if (fs::exists(p) && fs::is_regular_file(p)) {
            stageFiles.emplace_back(name, p);
        }
    }

    if (stageFiles.empty()) {
        Log(4, "[Huawei Kirin] No valid binary loaders found inside " + chipDir.string());
        return false;
    }

    std::ostringstream stagesSummary;
    for (size_t i = 0; i < stageFiles.size(); ++i) {
        if (i > 0) stagesSummary << ", ";
        stagesSummary << stageFiles[i].first;
    }

    Log(0, "Targeting Port: " + targetPort + " | Chipset: " + chipFolder);
    Log(0, "Loaded " + std::to_string(stageFiles.size()) + " injection stages: " + stagesSummary.str());

    WinSerialPort serial;
    if (!serial.Open(targetPort, 115200)) {
        Log(4, "[Huawei Kirin] Failed to open port: " + targetPort);
        return false;
    }

    serial.Purge();

    const size_t totalStages = stageFiles.size();
    const size_t chunkSize = 4096;

    for (size_t idx = 0; idx < totalStages; ++idx) {
        if (m_abortRequested) {
            Log(3, "[Huawei Kirin] Operation aborted by user.");
            serial.Close();
            return false;
        }

        const auto& [stageName, stagePath] = stageFiles[idx];
        std::ifstream file(stagePath, std::ios::binary | std::ios::ate);
        if (!file.is_open()) {
            Log(4, "[Huawei Kirin] Failed to open stage file: " + stagePath.string());
            serial.Close();
            return false;
        }

        std::streamsize fileSize = file.tellg();
        file.seekg(0, std::ios::beg);

        std::vector<uint8_t> buffer(static_cast<size_t>(fileSize));
        if (!file.read(reinterpret_cast<char*>(buffer.data()), fileSize)) {
            Log(4, "[Huawei Kirin] Error reading file data: " + stagePath.string());
            serial.Close();
            return false;
        }
        file.close();

        Log(0, "[*] Dispatching Stage " + std::to_string(idx + 1) + "/" +
               std::to_string(totalStages) + ": " + stageName + " (" +
               std::to_string(fileSize) + " bytes)...");

        size_t sent = 0;
        while (sent < buffer.size()) {
            if (m_abortRequested) {
                Log(3, "[Huawei Kirin] Aborted during stage dispatch.");
                serial.Close();
                return false;
            }

            size_t toSend = std::min(chunkSize, buffer.size() - sent);
            size_t written = serial.Write(buffer.data() + sent, toSend);
            if (written != toSend) {
                Log(4, "[Huawei Kirin] Serial write failed at offset " + std::to_string(sent));
                serial.Close();
                return false;
            }

            sent += written;
            int filePct = static_cast<int>((sent * 100) / buffer.size());
            int overallPct = static_cast<int>(((idx * 100) + filePct) / totalStages);

            if (progress_cb) {
                progress_cb(overallPct, filePct, stageName, "Injecting " + stageName);
            }

            // Brief inter-chunk pause for ROM handshake
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }

        // Inter-stage pause
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
        Log(2, "[✓] Stage " + std::to_string(idx + 1) + " (" + stageName + ") injected successfully!");
    }

    serial.Close();

    Log(2, "==================================================");
    Log(2, "🎉 KIRIN RESCUE BOOTLOADER INJECTED SUCCESSFULLY!");
    Log(2, "==================================================");
    Log(0, "[*] Phone is now rebooting into Fastboot Rescue Mode...");
    Log(0, "[*] Screen will turn white showing 'FASTBOOT & RESCUE MODE'.");

    if (progress_cb) {
        progress_cb(100, 100, "COMPLETE", "Rescue Mode Active");
    }

    return true;
}

} // namespace BSLab
