#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <cassert>
#include <filesystem>
#include "include/BSLabCore.h"

namespace fs = std::filesystem;

int main() {
    std::cout << "====================================================\n";
    std::cout << " BSLabCore Native C++ Huawei/Kirin Verification Suite\n";
    std::cout << "====================================================\n";

    // 1. Version Check
    const char* ver = BSLab_GetVersion();
    std::cout << "[TEST 1] BSLab_GetVersion(): " << ver << "\n";
    assert(ver != nullptr && std::strlen(ver) > 0);
    std::cout << "  -> PASSED\n";

    // 2. Initialize
    auto logCb = [](int lvl, const char* msg) {
        std::cout << "  [DLL LOG " << lvl << "] " << msg << "\n";
    };
    bool initOk = BSLab_Initialize(logCb);
    std::cout << "[TEST 2] BSLab_Initialize(): " << (initOk ? "TRUE" : "FALSE") << "\n";
    assert(initOk);
    std::cout << "  -> PASSED\n";

    // 3. Scan Huawei Ports
    char portsJson[4096] = {0};
    int portCount = 0;
    bool scanOk = BSLab_Huawei_ScanPorts(portsJson, sizeof(portsJson), &portCount);
    std::cout << "[TEST 3] BSLab_Huawei_ScanPorts(): Count=" << portCount << ", JSON=" << portsJson << "\n";
    assert(scanOk);
    assert(portsJson[0] == '[');
    std::cout << "  -> PASSED\n";

    // 4. Verify Kirin Stage Loaders Existence on Disk
    std::vector<std::string> chipsets = {
        "KIRIN_65x", "KIRIN_710A", "KIRIN_810", "KIRIN_820", "KIRIN_970", "KIRIN_980", "KIRIN_990"
    };
    int foundLoaders = 0;
    for (const auto& chip : chipsets) {
        fs::path p1 = fs::path("resources/loaders/kirin") / chip;
        fs::path p2 = fs::path("C:/BSLab_Tool/resources/loaders/kirin") / chip;
        if (fs::exists(p1) || fs::exists(p2)) {
            foundLoaders++;
        }
    }
    std::cout << "[TEST 4] Verified " << foundLoaders << "/" << chipsets.size() << " Kirin loader architectures.\n";
    assert(foundLoaders > 0);
    std::cout << "  -> PASSED\n";

    // 5. Kirin Rescue Boot on invalid port (graceful error handling)
    bool rescueOk = BSLab_Huawei_Kirin_BootRescue("COM999_NON_EXISTENT", "KIRIN_710A", nullptr);
    std::cout << "[TEST 5] BSLab_Huawei_Kirin_BootRescue(COM999): " << (rescueOk ? "TRUE" : "FALSE (Expected)") << "\n";
    assert(!rescueOk);
    std::cout << "  -> PASSED\n";

    // 6. PCUI Read Info on invalid port (graceful error handling)
    char pcuiJson[4096] = {0};
    bool pcuiOk = BSLab_Huawei_PCUI_ReadInfo("COM999_NON_EXISTENT", pcuiJson, sizeof(pcuiJson));
    std::cout << "[TEST 6] BSLab_Huawei_PCUI_ReadInfo(COM999): " << (pcuiOk ? "TRUE" : "FALSE (Expected)") << "\n";
    assert(!pcuiOk);
    std::cout << "  -> PASSED\n";

    // 7. Fastboot GetVar invocation
    char fbResp[4096] = {0};
    bool fbOk = BSLab_Huawei_Fastboot_GetVar("version", "DUMMY_SERIAL_999", fbResp, sizeof(fbResp));
    std::cout << "[TEST 7] BSLab_Huawei_Fastboot_GetVar(version): Result=" << (fbOk ? "TRUE" : "FALSE")
              << ", Response: " << (fbResp[0] ? fbResp : "(No device connected)") << "\n";
    assert(fbOk);
    std::cout << "  -> PASSED\n";

    // 8. Abort and Shutdown
    std::cout << "[TEST 8] BSLab_Huawei_Abort() & BSLab_Shutdown()...\n";
    BSLab_Huawei_Abort();
    BSLab_Shutdown();
    std::cout << "  -> PASSED\n";

    std::cout << "\n>>> ALL NATIVE HUAWEI / KIRIN C++ TESTS PASSED WITH 0 ERRORS! <<<\n";
    return 0;
}
