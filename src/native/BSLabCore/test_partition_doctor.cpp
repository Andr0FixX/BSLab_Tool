#include <iostream>
#include <vector>
#include <cstring>
#include <cassert>
#include <cstdint>
#include <windows.h>

typedef bool (*fn_IdentifyMagic)(const uint8_t*, int, char*, int);
typedef bool (*fn_IsProtected)(const char*);
typedef bool (*fn_InspectHeader)(const char*, const uint8_t*, int, char*, int);
typedef bool (*fn_VerifyImageBeforeFlash)(const char*, const char*, char*, int);
typedef bool (*fn_AnalyzeFastbootGetvar)(const char*, char*, int);
typedef bool (*fn_ExtractSingleImage)(const char*, const char*, const char*, char*, int, char*, int);

int main() {
    std::cout << "====================================================\n";
    std::cout << "BSLab Core - Native Partition Doctor Verification\n";
    std::cout << "====================================================\n";

    HMODULE hDll = LoadLibraryA("dist_new\\BSLabCore.dll");
    if (!hDll) {
        std::cerr << "[-] Failed to load dist_new\\BSLabCore.dll! Error: " << GetLastError() << "\n";
        return 1;
    }
    std::cout << "[+] Successfully loaded dist_new\\BSLabCore.dll\n";

    auto pIdentifyMagic = (fn_IdentifyMagic)GetProcAddress(hDll, "BSLab_PartitionDoctor_IdentifyMagic");
    auto pIsProtected = (fn_IsProtected)GetProcAddress(hDll, "BSLab_PartitionDoctor_IsProtected");
    auto pInspectHeader = (fn_InspectHeader)GetProcAddress(hDll, "BSLab_PartitionDoctor_InspectHeader");
    auto pVerifyImage = (fn_VerifyImageBeforeFlash)GetProcAddress(hDll, "BSLab_PartitionDoctor_VerifyImageBeforeFlash");
    auto pAnalyzeGetvar = (fn_AnalyzeFastbootGetvar)GetProcAddress(hDll, "BSLab_PartitionDoctor_AnalyzeFastbootGetvar");
    auto pExtractImage = (fn_ExtractSingleImage)GetProcAddress(hDll, "BSLab_PartitionDoctor_ExtractSingleImage");

    if (!pIdentifyMagic || !pIsProtected || !pInspectHeader || !pVerifyImage || !pAnalyzeGetvar || !pExtractImage) {
        std::cerr << "[-] Missing exported function pointers!\n";
        return 2;
    }
    std::cout << "[+] All 6 Partition Doctor exports resolved successfully!\n";

    // Test 1: IdentifyMagic
    char magicName[64];
    uint8_t bootHeader[1024];
    std::memset(bootHeader, 0, sizeof(bootHeader));
    std::memcpy(bootHeader, "ANDROID!", 8);
    // Write header version 2 at offset 40
    bootHeader[40] = 2;
    // Write kernel size 0x10000 at offset 8
    bootHeader[8] = 0x00; bootHeader[9] = 0x00; bootHeader[10] = 0x01; bootHeader[11] = 0x00;

    bool idOk = pIdentifyMagic(bootHeader, sizeof(bootHeader), magicName, sizeof(magicName));
    assert(idOk);
    std::cout << "[+] Test 1 (Magic Identification - Boot): " << magicName << " (Expected: BOOT_IMG)\n";
    assert(std::string(magicName) == "BOOT_IMG");

    // Test 2: IdentifyMagic - AVB VBMeta
    uint8_t avbHeader[256];
    std::memset(avbHeader, 0, sizeof(avbHeader));
    std::memcpy(avbHeader, "AVB0", 4);
    pIdentifyMagic(avbHeader, sizeof(avbHeader), magicName, sizeof(magicName));
    std::cout << "[+] Test 2 (Magic Identification - AVB0): " << magicName << " (Expected: AVB_VBMETA)\n";
    assert(std::string(magicName) == "AVB_VBMETA");

    // Test 3: IdentifyMagic - DTBO table
    uint8_t dtboHeader[64];
    std::memset(dtboHeader, 0, sizeof(dtboHeader));
    dtboHeader[0] = 0xD7; dtboHeader[1] = 0xB7; dtboHeader[2] = 0xAB; dtboHeader[3] = 0x1E;
    pIdentifyMagic(dtboHeader, sizeof(dtboHeader), magicName, sizeof(magicName));
    std::cout << "[+] Test 3 (Magic Identification - DTBO): " << magicName << " (Expected: DTBO)\n";
    assert(std::string(magicName) == "DTBO");

    // Test 4: IsProtected
    assert(pIsProtected("userdata") == true);
    assert(pIsProtected("userdata_a") == true);
    assert(pIsProtected("nvram") == true);
    assert(pIsProtected("sec_efs") == true);
    assert(pIsProtected("persist") == true);
    assert(pIsProtected("boot") == false);
    assert(pIsProtected("boot_a") == false);
    assert(pIsProtected("recovery") == false);
    assert(pIsProtected("system") == false);
    std::cout << "[+] Test 4 (Data Loss Firewall Verification): All protected partitions correctly hard-locked!\n";

    // Test 5: InspectHeader - Boot Image
    char jsonBuf[4096];
    bool inspOk = pInspectHeader("boot_a", bootHeader, sizeof(bootHeader), jsonBuf, sizeof(jsonBuf));
    assert(inspOk);
    std::cout << "[+] Test 5 (Forensic Inspection - Boot Header):\n" << jsonBuf << "\n";
    assert(std::string(jsonBuf).find("\"status\": \"HEALTHY\"") != std::string::npos);

    // Test 6: InspectHeader - Protected Partition Lock
    inspOk = pInspectHeader("userdata", bootHeader, sizeof(bootHeader), jsonBuf, sizeof(jsonBuf));
    assert(inspOk);
    std::cout << "[+] Test 6 (Forensic Inspection - Protected Lock):\n" << jsonBuf << "\n";
    assert(std::string(jsonBuf).find("\"status\": \"PROTECTED\"") != std::string::npos);

    // Test 7: Fastboot Getvar Health Analysis & INSTANT_FIX
    std::string mockGetvar = 
        "(bootloader) product: sweet\n"
        "(bootloader) current-slot: a\n"
        "(bootloader) slot-successful:a: no\n"
        "(bootloader) slot-unbootable:a: yes\n"
        "(bootloader) slot-retry-count:a: 0\n"
        "(bootloader) slot-successful:b: yes\n"
        "(bootloader) slot-unbootable:b: no\n"
        "(bootloader) partition-size:boot_a: 0x4000000\n"
        "(bootloader) partition-size:dtbo_a: 0x800000\n"
        "(bootloader) partition-size:super: 0x1E0000000\n";

    char reportJson[8192];
    bool repOk = pAnalyzeGetvar(mockGetvar.c_str(), reportJson, sizeof(reportJson));
    assert(repOk);
    std::cout << "[+] Test 7 (Fastboot A/B Slot Forensic Analysis):\n" << reportJson << "\n";
    assert(std::string(reportJson).find("\"overall_health\": \"INSTANT_FIX\"") != std::string::npos);
    assert(std::string(reportJson).find("fastboot set_active b") != std::string::npos);

    FreeLibrary(hDll);
    std::cout << "\n====================================================\n";
    std::cout << "SUCCESS: All 7 Native Partition Doctor tests PASSED!\n";
    std::cout << "====================================================\n";
    return 0;
}
