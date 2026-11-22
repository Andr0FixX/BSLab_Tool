#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <fstream>
#include <cassert>
#include <windows.h>
#include "include/BSLabCore.h"

int main() {
    std::cout << "====================================================\n";
    std::cout << " BSLabCore Native C++ Samsung/Odin Verification Suite\n";
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

    // 3. Scan Devices
    char devJson[4096] = {0};
    int devCount = 0;
    bool scanOk = BSLab_Samsung_ScanDevices(devJson, sizeof(devJson), &devCount);
    std::cout << "[TEST 3] BSLab_Samsung_ScanDevices(): Count=" << devCount << ", JSON=" << devJson << "\n";
    assert(scanOk);
    assert(devJson[0] == '[');
    std::cout << "  -> PASSED\n";

    // 4. Parse PIT
    const char* samplePit = "resources\\loaders\\samsung\\pit\\A032FXXU2AVH4_PIT_f59d4ccf.pit";
    char pitJson[32768] = {0};
    int pitCount = 0;
    bool pitOk = BSLab_Samsung_ParsePit(samplePit, pitJson, sizeof(pitJson), &pitCount);
    std::cout << "[TEST 4] BSLab_Samsung_ParsePit(): Result=" << (pitOk ? "TRUE" : "FALSE") 
              << ", Count=" << pitCount << "\n";
    if (pitOk) {
        assert(pitCount > 0);
        assert(std::strstr(pitJson, "\"name\":") != nullptr);
        std::cout << "  First 120 chars of PIT JSON: " << std::string(pitJson).substr(0, 120) << "...\n";
        std::cout << "  -> PASSED\n";
    } else {
        std::cout << "  [!] Sample PIT not at relative path, trying absolute path...\n";
        samplePit = "C:\\BSLab_Tool\\resources\\loaders\\samsung\\pit\\A032FXXU2AVH4_PIT_f59d4ccf.pit";
        pitOk = BSLab_Samsung_ParsePit(samplePit, pitJson, sizeof(pitJson), &pitCount);
        assert(pitOk && pitCount > 0);
        std::cout << "  Parsed " << pitCount << " partitions from absolute path.\n";
        std::cout << "  -> PASSED\n";
    }

    // 5. Verify TAR.MD5
    std::string tempFile = "temp_test_samsung.tar.md5";
    {
        std::ofstream out(tempFile, std::ios::binary);
        std::string payload = "BS_LAB_TOOL_SAMSUNG_FIRMWARE_PAYLOAD_TEST_DATA";
        out.write(payload.data(), payload.size());
        // Exact MD5 of "BS_LAB_TOOL_SAMSUNG_FIRMWARE_PAYLOAD_TEST_DATA" is 114a7ca6dd81928511d2db4c4513f10a
        out << "\r\n114a7ca6dd81928511d2db4c4513f10a\r\n";
    }

    char md5Msg[256] = {0};
    bool md5Ok = BSLab_Samsung_VerifyTarMd5(tempFile.c_str(), nullptr, md5Msg, sizeof(md5Msg));
    std::cout << "[TEST 5] BSLab_Samsung_VerifyTarMd5(): " << (md5Ok ? "TRUE" : "FALSE") 
              << ", Msg=" << md5Msg << "\n";
    assert(md5Ok);
    std::remove(tempFile.c_str());
    std::cout << "  -> PASSED\n";

    // 6. Test Handshake on invalid port (graceful error handling)
    bool hsOk = BSLab_Samsung_Handshake("COM999_NON_EXISTENT");
    std::cout << "[TEST 6] BSLab_Samsung_Handshake(COM999): " << (hsOk ? "TRUE" : "FALSE (Expected)") << "\n";
    assert(!hsOk);
    std::cout << "  -> PASSED\n";

    // 7. Abort Flash
    std::cout << "[TEST 7] BSLab_Samsung_Abort()...\n";
    BSLab_Samsung_Abort();
    std::cout << "  -> PASSED\n";

    // 8. Shutdown
    BSLab_Shutdown();
    std::cout << "[TEST 8] BSLab_Shutdown()...\n";
    std::cout << "  -> PASSED\n";

    std::cout << "\n>>> ALL NATIVE SAMSUNG / ODIN C++ TESTS PASSED WITH 0 ERRORS! <<<\n";
    return 0;
}
