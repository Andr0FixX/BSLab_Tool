#include <windows.h>
#include <shellapi.h>
#include <iostream>
#include <string>
#include <vector>
#include <sstream>

// BSLab Tool - High Performance Standalone Windows Updater
// Autonomous file-lock safe extractor & restarter

static std::wstring StringToWString(const std::string& str) {
    if (str.empty()) return std::wstring();
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), (int)str.size(), NULL, 0);
    std::wstring wstr(size_needed, 0);
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), (int)str.size(), &wstr[0], size_needed);
    return wstr;
}

static bool RunCommandHidden(const std::wstring& cmd) {
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags |= STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    ZeroMemory(&pi, sizeof(pi));

    std::vector<wchar_t> cmdBuf(cmd.begin(), cmd.end());
    cmdBuf.push_back(0);

    if (CreateProcessW(NULL, cmdBuf.data(), NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, 180000); // 3 minutes max for large updates
        DWORD exitCode = 0;
        GetExitCodeProcess(pi.hProcess, &exitCode);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return (exitCode == 0);
    }
    return false;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    int argc = 0;
    LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!argv) return 1;

    std::wstring zipPath = L"";
    std::wstring targetDir = L"";
    std::wstring exeName = L"BSLab_Tool.exe";
    DWORD waitPid = 0;

    for (int i = 1; i < argc; ++i) {
        std::wstring arg = argv[i];
        if (arg == L"--zip" && i + 1 < argc) {
            zipPath = argv[++i];
        } else if (arg == L"--target" && i + 1 < argc) {
            targetDir = argv[++i];
        } else if (arg == L"--exe" && i + 1 < argc) {
            exeName = argv[++i];
        } else if (arg == L"--pid" && i + 1 < argc) {
            waitPid = (DWORD)_wtoi(argv[++i]);
        }
    }
    LocalFree(argv);

    if (zipPath.empty() || targetDir.empty()) {
        MessageBoxW(NULL, 
            L"BSLab Tool Updater (Standalone)\n\nUsage: BSLabUpdater.exe --zip <path> --target <dir> [--exe <name>] [--pid <id>]", 
            L"BSLab Tool Auto-Update", MB_OK | MB_ICONINFORMATION);
        return 0;
    }

    // Step 1: Wait for main BSLab Tool process to terminate so file locks are released
    if (waitPid > 0) {
        HANDLE hProcess = OpenProcess(SYNCHRONIZE, FALSE, waitPid);
        if (hProcess != NULL) {
            WaitForSingleObject(hProcess, 15000); // Wait up to 15 seconds
            CloseHandle(hProcess);
        }
    }
    Sleep(1200); // Safety margin for OS kernel to release file handles

    // Step 2: Extract update package over target directory
    // Strategy A: Native Windows tar.exe (fastest, built into Windows 10/11)
    std::wstring tarCmd = L"tar.exe -xf \"" + zipPath + L"\" -C \"" + targetDir + L"\"";
    bool extracted = RunCommandHidden(tarCmd);

    // Strategy B: Fallback to PowerShell Expand-Archive
    if (!extracted) {
        std::wstring psCmd = L"powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "
                             L"\"Expand-Archive -Path '" + zipPath + L"' -DestinationPath '" + targetDir + L"' -Force\"";
        extracted = RunCommandHidden(psCmd);
    }

    if (!extracted) {
        MessageBoxW(NULL, 
            L"Failed to extract update package!\nPlease make sure BSLab Tool is completely closed and try again.", 
            L"Update Extraction Error", MB_OK | MB_ICONERROR);
        return 2;
    }

    // Step 3: Delete temporary update zip
    DeleteFileW(zipPath.c_str());

    // Step 4: Launch updated BSLab Tool executable
    std::wstring fullExePath = targetDir;
    if (!fullExePath.empty() && fullExePath.back() != L'\\' && fullExePath.back() != L'/') {
        fullExePath += L"\\";
    }
    fullExePath += exeName;

    ShellExecuteW(NULL, L"open", fullExePath.c_str(), NULL, targetDir.c_str(), SW_SHOWNORMAL);

    return 0;
}
