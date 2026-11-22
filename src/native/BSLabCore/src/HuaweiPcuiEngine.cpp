#include "HuaweiPcuiEngine.h"
#include "KirinRescueEngine.h"
#include "WinSerialPort.h"
#include <chrono>
#include <thread>
#include <sstream>
#include <algorithm>

namespace BSLab {

HuaweiPcuiEngine::HuaweiPcuiEngine(LogCallback logger)
    : m_logger(std::move(logger)) {
}

void HuaweiPcuiEngine::Log(int level, const std::string& msg) {
    if (m_logger) {
        m_logger(level, msg);
    }
}

std::string HuaweiPcuiEngine::FindPcuiPort() {
    auto ports = KirinRescueEngine::ScanHuaweiPorts();

    // 1. Strictly prioritize genuine PCUI port
    for (const auto& p : ports) {
        if (p.type == "PCUI") {
            return p.port;
        }
    }

    // 2. Fallback to any Huawei serial / modem port except DBAdapter
    for (const auto& p : ports) {
        std::string descLower = p.description;
        std::transform(descLower.begin(), descLower.end(), descLower.begin(), ::tolower);
        if (descLower.find("dbadapter") == std::string::npos &&
            (p.type == "Modem" || descLower.find("serial") != std::string::npos)) {
            return p.port;
        }
    }

    return "";
}

std::string HuaweiPcuiEngine::SendAtCommand(
    const std::string& port,
    const std::string& cmd,
    uint32_t timeout_ms
) {
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

    std::string response;
    auto startTime = std::chrono::steady_clock::now();
    uint8_t ch = 0;

    while (true) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - startTime).count();
        if (elapsed > timeout_ms) {
            break;
        }

        if (serial.ReadByte(ch, 50)) {
            response += static_cast<char>(ch);

            // Check terminators
            if (response.find("\r\nOK\r\n") != std::string::npos ||
                response.find("\r\nERROR\r\n") != std::string::npos ||
                response.find("+CME ERROR") != std::string::npos ||
                response.find("+CMS ERROR") != std::string::npos) {
                break;
            }
        }
    }

    serial.Close();
    return response;
}

bool HuaweiPcuiEngine::ReadDeviceInfo(
    const std::string& port,
    HuaweiDeviceInfo& out_info
) {
    std::string targetPort = port.empty() ? FindPcuiPort() : port;
    if (targetPort.empty()) {
        Log(4, "[Huawei PCUI] No active PCUI COM port found. Enable Manufacture Mode (*#*#2846579#*#*).");
        return false;
    }

    Log(0, "[Huawei PCUI] Probing AT Command Interface on " + targetPort + "...");

    // 1. Handshake
    std::string ping = SendAtCommand(targetPort, "AT", 1000);
    if (ping.find("ERROR: Failed to open port") != std::string::npos) {
        Log(4, "[Huawei PCUI] Failed to open port: " + targetPort);
        return false;
    }
    if (ping.find("OK") == std::string::npos) {
        Log(3, "[Huawei PCUI] Device did not acknowledge AT ping.");
    }

    // 2. Query Model
    std::string modelResp = SendAtCommand(targetPort, "AT+CGMM", 1500);
    if (modelResp.find("OK") != std::string::npos) {
        std::istringstream stream(modelResp);
        std::string line;
        while (std::getline(stream, line)) {
            while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
            if (!line.empty() && line.find("AT") == std::string::npos && line.find("OK") == std::string::npos) {
                out_info.model = line;
                break;
            }
        }
    }

    // 3. Query IMEI
    std::string imeiResp = SendAtCommand(targetPort, "AT+CGSN", 1500);
    if (imeiResp.find("OK") != std::string::npos) {
        std::istringstream stream(imeiResp);
        std::string line;
        while (std::getline(stream, line)) {
            while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
            if (!line.empty() && line.find("AT") == std::string::npos && line.find("OK") == std::string::npos) {
                out_info.imei = line;
                break;
            }
        }
    }

    // 4. Query Version
    std::string verResp = SendAtCommand(targetPort, "AT^VERSION", 1500);
    if (verResp.find("OK") == std::string::npos) {
        verResp = SendAtCommand(targetPort, "AT+CGMR", 1500);
    }
    if (verResp.find("OK") != std::string::npos) {
        std::istringstream stream(verResp);
        std::string line;
        while (std::getline(stream, line)) {
            while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
            if (!line.empty() && line.find("AT") == std::string::npos && line.find("OK") == std::string::npos) {
                out_info.build_version = line;
                break;
            }
        }
    }

    // 5. Query Battery Level
    std::string batResp = SendAtCommand(targetPort, "AT+CBC", 1000);
    if (batResp.find("+CBC:") != std::string::npos) {
        size_t pos = batResp.find("+CBC:");
        size_t endLine = batResp.find("\r", pos);
        if (endLine != std::string::npos) {
            out_info.battery_level = batResp.substr(pos, endLine - pos);
        }
    }

    if (out_info.model.empty() && out_info.imei.empty() && out_info.build_version.empty()) {
        Log(3, "[Huawei PCUI] No telemetry data returned from " + targetPort);
        return false;
    }

    out_info.raw_responses = "MODEL: " + out_info.model + " | IMEI: " + out_info.imei +
                            " | BUILD: " + out_info.build_version;

    Log(2, "[✓] Huawei Manufacture Mode Telemetry Acquired: " + out_info.raw_responses);
    return true;
}

bool HuaweiPcuiEngine::RebootToFastboot(const std::string& port) {
    std::string targetPort = port.empty() ? FindPcuiPort() : port;
    if (targetPort.empty()) {
        Log(4, "[Huawei PCUI] No port specified for reboot command.");
        return false;
    }

    Log(0, "[Huawei PCUI] Sending Fastboot Rescue Reboot command (AT^BOOT_RESCUE)...");
    std::string resp = SendAtCommand(targetPort, "AT^BOOT_RESCUE", 2000);
    if (resp.find("OK") == std::string::npos) {
        resp = SendAtCommand(targetPort, "AT^REBOOT=1", 2000);
    }

    Log(2, "[+] Reboot command dispatched. Device will enter Fastboot Rescue Mode.");
    return true;
}

} // namespace BSLab
