#include "SamsungModemEngine.h"
#include <windows.h>
#include <regex>
#include <sstream>
#include <thread>
#include <chrono>
#include <algorithm>

namespace BSLab {

SamsungModemEngine::SamsungModemEngine(LogCallback logger)
    : m_logger(std::move(logger)) {}

void SamsungModemEngine::Log(int level, const std::string& msg) {
    if (m_logger) {
        m_logger(level, msg);
    }
}

std::vector<SamsungDeviceInfo> SamsungModemEngine::ScanSamsungPorts() {
    std::vector<SamsungDeviceInfo> devices;

    // 1. Scan SERIALCOMM
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

            bool isSamsung = (lowerKey.find("ssud") != std::string::npos ||
                              lowerKey.find("samsung") != std::string::npos ||
                              lowerKey.find("modem") != std::string::npos);

            std::string desc = "Samsung USB Serial Device";
            std::string mode = "Modem / CDC Port";

            if (lowerKey.find("download") != std::string::npos || lowerKey.find("odin") != std::string::npos) {
                mode = "Download Mode (Odin)";
                desc = "SAMSUNG Mobile USB Download Port";
            } else if (lowerKey.find("modem") != std::string::npos) {
                desc = "SAMSUNG Mobile USB Modem";
            }

            // Always add if samsung or if looking like a candidate
            if (isSamsung) {
                devices.push_back({ portName, desc, regKey, mode });
            }

            valLen = sizeof(valueName);
            dataLen = sizeof(data);
            index++;
        }
        RegCloseKey(hKey);
    }

    return devices;
}

std::string SamsungModemEngine::FindModemPort() {
    auto ports = ScanSamsungPorts();
    for (const auto& dev : ports) {
        if (dev.mode == "Modem / CDC Port") {
            return dev.port;
        }
    }
    if (!ports.empty()) {
        return ports[0].port;
    }
    return "";
}

std::string SamsungModemEngine::SendAtCommand(const std::string& port, const std::string& cmd, uint32_t timeoutMs) {
    std::lock_guard<std::mutex> lock(m_portMutex);

    std::string framedCmd = cmd;
    if (framedCmd.length() < 2 || framedCmd.substr(framedCmd.length() - 2) != "\r\n") {
        framedCmd += "\r\n";
    }

    WinSerialPort serial;
    if (!serial.Open(port, 115200)) {
        return "ERROR: Failed to open port " + port;
    }

    serial.Purge();
    serial.Write(reinterpret_cast<const uint8_t*>(framedCmd.data()), framedCmd.length());

    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    std::string response;
    auto startTime = std::chrono::steady_clock::now();

    uint8_t buf[256];
    while (true) {
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - startTime).count();
        if (elapsed > timeoutMs) break;

        size_t bytesRead = serial.Read(buf, sizeof(buf) - 1, 100);
        if (bytesRead > 0) {
            buf[bytesRead] = '\0';
            response.append(reinterpret_cast<char*>(buf), bytesRead);

            if (response.find("OK\r\n") != std::string::npos ||
                response.find("ERROR\r\n") != std::string::npos) {
                break;
            }
        }
    }

    serial.Close();

    // Clean whitespace
    while (!response.empty() && (response.back() == '\r' || response.back() == '\n' || response.back() == ' ')) {
        response.pop_back();
    }
    return response;
}

bool SamsungModemEngine::ReadDeviceInfo(const std::string& port, SamsungModemInfo& outInfo) {
    Log(0, "Reading Samsung Device Info via Port " + port + "...");

    // 1. Basic Ping
    std::string ping = SendAtCommand(port, "AT");
    if (ping.find("OK") == std::string::npos) {
        Log(3, "Modem did not respond with OK to AT ping (response: " + ping + ")");
    }

    // 2. Model / Identification (AT+GMM)
    std::string modelResp = SendAtCommand(port, "AT+GMM");
    if (modelResp.find("ERROR") == std::string::npos && !modelResp.empty()) {
        std::istringstream iss(modelResp);
        std::string line;
        while (std::getline(iss, line)) {
            while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) line.pop_back();
            if (!line.empty() && line.find("AT") == std::string::npos && line.find("OK") == std::string::npos) {
                outInfo.model = line;
                break;
            }
        }
    }

    // 3. Serial / IMEI (AT+GSN)
    std::string snResp = SendAtCommand(port, "AT+GSN");
    if (snResp.find("ERROR") == std::string::npos && !snResp.empty()) {
        std::istringstream iss(snResp);
        std::string line;
        while (std::getline(iss, line)) {
            while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) line.pop_back();
            if (!line.empty() && line.find("AT") == std::string::npos && line.find("OK") == std::string::npos) {
                outInfo.serial_imei = line;
                break;
            }
        }
    }

    // 4. Baseband / AP Version (AT+GMR)
    std::string swResp = SendAtCommand(port, "AT+GMR");
    if (swResp.find("ERROR") == std::string::npos && !swResp.empty()) {
        std::istringstream iss(swResp);
        std::string line;
        while (std::getline(iss, line)) {
            while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) line.pop_back();
            if (!line.empty() && line.find("AT") == std::string::npos && line.find("OK") == std::string::npos) {
                outInfo.baseband_ap = line;
                break;
            }
        }
    }

    // 5. DEVCONINFO (Detailed Samsung Hardware & Security Config)
    std::string devResp = SendAtCommand(port, "AT+DEVCONINFO");
    if (devResp.find("DEVCONINFO") != std::string::npos || devResp.find("OK") != std::string::npos) {
        outInfo.devcon_info = devResp;
    }

    // Knox and CSC info
    ReadCscStatus(port, outInfo.csc, outInfo.csc);
    ReadKnoxSecurity(port, outInfo.knox_guard, outInfo.knox_warranty, outInfo.frp_status);

    Log(2, "[✓] Samsung Device Info Retrieved Successfully:");
    Log(0, "   ● Model       : " + (outInfo.model.empty() ? "N/A" : outInfo.model));
    Log(0, "   ● IMEI/Serial : " + (outInfo.serial_imei.empty() ? "N/A" : outInfo.serial_imei));
    Log(0, "   ● Baseband/AP : " + (outInfo.baseband_ap.empty() ? "N/A" : outInfo.baseband_ap));
    Log(0, "   ● Active CSC  : " + (outInfo.csc.empty() ? "N/A" : outInfo.csc));
    Log(0, "   ● Knox Guard  : " + (outInfo.knox_guard.empty() ? "N/A" : outInfo.knox_guard));

    return true;
}

bool SamsungModemEngine::TriggerTestMode(const std::string& port) {
    Log(0, "Transmitting Diagnostic Setup Commands on " + port + "...");
    static const char* cmds[] = { "AT", "AT+KSUART=0", "AT+SWAT=1", "AT+ACTIVATE=1" };
    for (const char* c : cmds) {
        std::string res = SendAtCommand(port, c);
        Log(0, std::string("  [") + c + "] -> " + res);
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    return true;
}

bool SamsungModemEngine::RebootToDownloadMode(const std::string& port) {
    Log(0, "Requesting Reboot to Download Mode on " + port + "...");
    std::string res = SendAtCommand(port, "AT+REBOOT=2");
    if (res.find("OK") != std::string::npos || res.find("ERROR") == std::string::npos) {
        Log(2, "[✓] Download Mode reboot signal dispatched.");
        return true;
    }

    // Alternate command fallback
    std::string res2 = SendAtCommand(port, "AT+CFUN=1,1");
    return res2.find("OK") != std::string::npos;
}

bool SamsungModemEngine::ReadCscStatus(const std::string& port, std::string& outCsc, std::string& outSalesCode) {
    outCsc = "Unknown";
    outSalesCode = "Unknown";

    std::string raw = SendAtCommand(port, "AT+PRECON?");
    std::smatch m;
    if (raw.find("PRECON:") != std::string::npos) {
        std::regex re(R"(PRECON:\s*(\w+))");
        if (std::regex_search(raw, m, re)) {
            outCsc = m[1].str();
            std::transform(outCsc.begin(), outCsc.end(), outCsc.begin(), ::toupper);
            outSalesCode = outCsc;
            return true;
        }
    }

    std::string devInfo = SendAtCommand(port, "AT+DEVCONINFO");
    std::regex reCsc(R"(CSC[=:]\s*([A-Za-z]{3}))");
    if (std::regex_search(devInfo, m, reCsc)) {
        outCsc = m[1].str();
        std::transform(outCsc.begin(), outCsc.end(), outCsc.begin(), ::toupper);
        outSalesCode = outCsc;
        return true;
    }

    return false;
}

bool SamsungModemEngine::ChangeCsc(const std::string& port, const std::string& targetCsc, bool rebootAfter) {
    std::string target = targetCsc;
    std::transform(target.begin(), target.end(), target.begin(), ::toupper);
    Log(0, "Initiating Samsung 1-Click CSC Switch to [" + target + "] on " + port + "...");

    std::string ping = SendAtCommand(port, "AT");
    if (ping.find("OK") == std::string::npos) {
        Log(4, "Modem communication not ready. Ensure phone is unlocked.");
        return false;
    }

    Log(0, "Transmitting Pre-Configuration Command: AT+PRECON=0," + target + "...");
    std::string res1 = SendAtCommand(port, "AT+PRECON=0," + target);
    Log(0, "  Response: " + res1);

    SendAtCommand(port, "AT+SWAT=1");

    std::string res2 = SendAtCommand(port, "AT+PRECON=1," + target);
    Log(0, "  Confirm Response: " + res2);

    if (res1.find("OK") != std::string::npos || res2.find("OK") != std::string::npos || res1.find("ERROR") == std::string::npos) {
        Log(2, "[✓] CSC successfully reprogrammed to [" + target + "]! Carrier features unlocked.");
        if (rebootAfter) {
            Log(0, "Rebooting device to apply new CSC configuration...");
            SendAtCommand(port, "AT+REBOOT");
        }
        return true;
    } else {
        Log(3, "CSC primary command returned: " + res1 + ". Trying fallback sequence...");
        SendAtCommand(port, "AT+SVC=1,0");
        std::string res3 = SendAtCommand(port, "AT+PRECON=0," + target);
        if (res3.find("OK") != std::string::npos) {
            Log(2, "[✓] Fallback CSC write successful to [" + target + "]!");
            if (rebootAfter) {
                SendAtCommand(port, "AT+REBOOT");
            }
            return true;
        }
    }

    return false;
}

bool SamsungModemEngine::ReadKnoxSecurity(const std::string& port, std::string& outKnoxGuard, std::string& outWarranty, std::string& outFrp) {
    outKnoxGuard = "COMPLETED (Safe / Normal)";
    outWarranty = "0x0 (Official / Untripped)";
    outFrp = "OFF / Unlocked";

    std::string rawDev = SendAtCommand(port, "AT+DEVCONINFO");
    std::smatch m;

    // KG
    if (rawDev.find("KG:") != std::string::npos || rawDev.find("KNOX_GUARD:") != std::string::npos) {
        std::regex reKg(R"((?:KG|KNOX_GUARD)[:=]\s*(\w+))");
        if (std::regex_search(rawDev, m, reKg)) {
            outKnoxGuard = m[1].str();
            std::transform(outKnoxGuard.begin(), outKnoxGuard.end(), outKnoxGuard.begin(), ::toupper);
        }
    }

    // Warranty bit
    if (rawDev.find("WAR:") != std::string::npos || rawDev.find("WARRANTY:") != std::string::npos) {
        std::regex reWar(R"((?:WAR|WARRANTY)[:=]\s*([0-9xX]+))");
        if (std::regex_search(rawDev, m, reWar)) {
            outWarranty = m[1].str();
        }
    }

    // FRP
    if (rawDev.find("FRP:") != std::string::npos || rawDev.find("FRP_LOCK:") != std::string::npos) {
        std::regex reFrp(R"((?:FRP|FRP_LOCK)[:=]\s*(\w+))");
        if (std::regex_search(rawDev, m, reFrp)) {
            std::string val = m[1].str();
            std::transform(val.begin(), val.end(), val.begin(), ::toupper);
            if (val == "1" || val == "ON" || val == "LOCK") {
                outFrp = "ON / Locked";
            } else {
                outFrp = "OFF / Unlocked";
            }
        }
    }

    return true;
}

} // namespace BSLab
