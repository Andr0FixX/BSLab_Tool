#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <fstream>
#include <cassert>
#include "include/BSLabCore.h"

int main() {
    std::cout << "====================================================\n";
    std::cout << " BSLabCore Native C++ Unisoc/SPD Verification Suite\n";
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

    // 3. Scan Unisoc Ports
    char portsJson[4096] = {0};
    int portCount = 0;
    bool scanOk = BSLab_Unisoc_ScanPorts(portsJson, sizeof(portsJson), &portCount);
    std::cout << "[TEST 3] BSLab_Unisoc_ScanPorts(): Count=" << portCount << ", JSON=" << portsJson << "\n";
    assert(scanOk);
    assert(portsJson[0] == '[');
    std::cout << "  -> PASSED\n";

    // 4. Test PAC Parser with non-existent file (Graceful error handling)
    char pacJson[4096] = {0};
    int pacFiles = 0;
    bool pacFailOk = !BSLab_Unisoc_ParsePac("non_existent_file.pac", pacJson, sizeof(pacJson), &pacFiles);
    std::cout << "[TEST 4] BSLab_Unisoc_ParsePac(invalid): " << (pacFailOk ? "FALSE (Expected graceful failure)" : "UNEXPECTED") << "\n";
    assert(pacFailOk);
    std::cout << "  -> PASSED\n";

    // 5. Connect on Invalid Port (Graceful failure)
    bool connOk = BSLab_Unisoc_Connect("COM999_NON_EXISTENT", nullptr, nullptr);
    std::cout << "[TEST 5] BSLab_Unisoc_Connect(COM999): " << (connOk ? "TRUE" : "FALSE (Expected)") << "\n";
    assert(!connOk);
    std::cout << "  -> PASSED\n";

    // 6. Test FRP Reset on Invalid Port (Graceful failure)
    bool frpOk = BSLab_Unisoc_ResetFRP("COM999_NON_EXISTENT", nullptr, nullptr);
    std::cout << "[TEST 6] BSLab_Unisoc_ResetFRP(COM999): " << (frpOk ? "TRUE" : "FALSE (Expected)") << "\n";
    assert(!frpOk);
    std::cout << "  -> PASSED\n";

    // 7. Abort Operation
    std::cout << "[TEST 7] BSLab_Unisoc_Abort()...\n";
    BSLab_Unisoc_Abort();
    std::cout << "  -> PASSED\n";

    // 8. Shutdown
    BSLab_Shutdown();
    std::cout << "[TEST 8] BSLab_Shutdown()...\n";
    std::cout << "  -> PASSED\n";

    std::cout << "\n>>> ALL NATIVE UNISOC / SPD C++ TESTS PASSED WITH 0 ERRORS! <<<\n";
    return 0;
}
