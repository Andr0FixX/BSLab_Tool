#include "HuaweiFastboot.h"
#include <windows.h>
#include <filesystem>
#include <sstream>
#include <iostream>
#include <algorithm>

namespace BSLab {

namespace fs = std::filesystem;

HuaweiFastboot::HuaweiFastboot(LogCallback logger)
    : m_logger(std::move(logger)) {
}

void HuaweiFastboot::Log(int level, const std::string& msg) {
    if (m_logger) {
        m_logger(level, msg);
    }
}

std::string HuaweiFastboot::FindFastbootBinary() {
    std::vector<std::string> candidates = {
        "tools/adb/fastboot.exe",
        "tools\\adb\\fastboot.exe",
        "platform-tools/fastboot.exe",
        "platform-tools\\fastboot.exe",
        "C:\\BSLab_Tool\\tools\\adb\\fastboot.exe",
        "C:\\BSLab_Tool\\platform-tools\\fastboot.exe"
    };

    for (const auto& path : candidates) {
        if (fs::exists(path)) {
            return path;
        }
    }
    return "fastboot.exe";
}

std::string HuaweiFastboot::ExecuteCommand(const std::string& args, const std::string& target_serial) {
    std::string binPath = FindFastbootBinary();
    std::string cmdLine = "\"" + binPath + "\"";
    if (!target_serial.empty()) {
        cmdLine += " -s " + target_serial;
    }
    cmdLine += " " + args;

    SECURITY_ATTRIBUTES sa;
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = nullptr;

    HANDLE hReadPipe = nullptr;
    HANDLE hWritePipe = nullptr;
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        return "ERROR: Failed to create stdout/stderr pipe";
    }

    SetHandleInformation(hReadPipe, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.hStdOutput = hWritePipe;
    si.hStdError = hWritePipe;
    si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi;
    ZeroMemory(&pi, sizeof(pi));

    std::vector<char> cmdVec(cmdLine.begin(), cmdLine.end());
    cmdVec.push_back('\0');

    BOOL success = CreateProcessA(
        nullptr,
        cmdVec.data(),
        nullptr,
        nullptr,
        TRUE,
        CREATE_NO_WINDOW,
        nullptr,
        nullptr,
        &si,
        &pi
    );

    CloseHandle(hWritePipe);

    if (!success) {
        CloseHandle(hReadPipe);
        return "ERROR: Failed to launch fastboot process: " + cmdLine;
    }

    std::string output;
    char buffer[4096];
    DWORD bytesRead = 0;

    // Wait with a strict 2.5s timeout so fastboot never hangs waiting for a device
    DWORD waitRes = WaitForSingleObject(pi.hProcess, 2500);
    if (waitRes == WAIT_TIMEOUT) {
        TerminateProcess(pi.hProcess, 1);
        WaitForSingleObject(pi.hProcess, 200);
    }

    DWORD avail = 0;
    while (PeekNamedPipe(hReadPipe, nullptr, 0, nullptr, &avail, nullptr) && avail > 0) {
        DWORD toRead = std::min(avail, static_cast<DWORD>(sizeof(buffer) - 1));
        if (ReadFile(hReadPipe, buffer, toRead, &bytesRead, nullptr) && bytesRead > 0) {
            buffer[bytesRead] = '\0';
            output.append(buffer, bytesRead);
        } else {
            break;
        }
    }

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hReadPipe);

    return output;
}

bool HuaweiFastboot::IsDeviceConnected(const std::string& target_serial) {
    std::string out = ExecuteCommand("devices", target_serial);
    std::istringstream stream(out);
    std::string line;
    while (std::getline(stream, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (!line.empty() && line.find("fastboot") != std::string::npos) {
            return true;
        }
    }
    return false;
}

std::string HuaweiFastboot::GetVar(const std::string& var_name, const std::string& target_serial) {
    return ExecuteCommand("getvar " + var_name, target_serial);
}

bool HuaweiFastboot::ResetFRP(const std::string& target_serial) {
    Log(0, "Executing Huawei 1-Click FRP Reset in Rescue / Fastboot...");

    // Step 1: Check fastboot presence
    if (!IsDeviceConnected(target_serial)) {
        Log(4, "[Huawei FRP] No phone detected in Fastboot / Rescue Mode!");
        Log(0, "Tip: First run 'Boot Kirin Rescue Mode' or hold (Vol- + Power) to enter Fastboot.");
        return false;
    }

    // Step 2: Try OEM frp-erase
    Log(0, "[*] Dispatching 'fastboot oem frp-erase'...");
    std::string res1 = ExecuteCommand("oem frp-erase", target_serial);
    std::string r1Lower = res1;
    std::transform(r1Lower.begin(), r1Lower.end(), r1Lower.begin(), ::tolower);

    if (res1.find("OKAY") != std::string::npos || r1Lower.find("success") != std::string::npos) {
        Log(2, "[✓] Huawei FRP Token Erased via OEM command!");
        ExecuteCommand("reboot", target_serial);
        Log(2, "[✓] Device rebooted into normal Android OS without FRP lock.");
        return true;
    }

    // Step 3: Try standard fastboot erase frp
    Log(0, "[*] Trying standard 'fastboot erase frp'...");
    std::string res2 = ExecuteCommand("erase frp", target_serial);
    std::string r2Lower = res2;
    std::transform(r2Lower.begin(), r2Lower.end(), r2Lower.begin(), ::tolower);

    if (res2.find("OKAY") != std::string::npos || r2Lower.find("success") != std::string::npos) {
        Log(2, "[✓] Huawei FRP Partition Wiped Successfully!");
        ExecuteCommand("reboot", target_serial);
        return true;
    }

    // Step 4: Try oem frp-unlock
    Log(0, "[*] Trying 'fastboot oem frp-unlock'...");
    std::string res3 = ExecuteCommand("oem frp-unlock", target_serial);
    std::string r3Lower = res3;
    std::transform(r3Lower.begin(), r3Lower.end(), r3Lower.begin(), ::tolower);

    if (res3.find("OKAY") != std::string::npos || r3Lower.find("success") != std::string::npos) {
        Log(2, "[✓] Huawei FRP Lock Bypassed Successfully!");
        ExecuteCommand("reboot", target_serial);
        return true;
    }

    Log(3, "[Huawei FRP] Execution result: " + res1 + " | " + res2 + " | " + res3);
    return false;
}

bool HuaweiFastboot::Reboot(const std::string& target_serial) {
    std::string res = ExecuteCommand("reboot", target_serial);
    return res.find("OKAY") != std::string::npos;
}

} // namespace BSLab
