#include <iostream>
#include <cassert>
#include <cstring>
#include <vector>
#include <cstdint>
#include <filesystem>
#include "QcDiagQcnEngine.h"
#include "../include/BSLabCore.h"

int main() {
    std::cout << "====================================================\n";
    std::cout << "   BSLabCore Native Unit Test: Qualcomm Diag & QCN  \n";
    std::cout << "====================================================\n";

    // ----------------------------------------------------
    // TEST 1: CRC16-CCITT Calculation
    // ----------------------------------------------------
    std::cout << "[*] Test 1: Testing Qualcomm Diag CRC16-CCITT... ";
    {
        uint8_t sample[] = { 0x26, 0x26, 0x02 }; // Diag Read NV 550
        uint16_t crc = BSLab::QcDiagQcnEngine::CalculateCrc16(sample, sizeof(sample));
        assert(crc != 0);
        // Verify consistency with same payload
        uint16_t crc2 = BSLab::QcDiagQcnEngine::CalculateCrc16(sample, sizeof(sample));
        assert(crc == crc2);
        std::cout << "PASSED (CRC: 0x" << std::hex << crc << std::dec << ")\n";
    }

    // ----------------------------------------------------
    // TEST 2: HDLC Framing & Byte Stuffing
    // ----------------------------------------------------
    std::cout << "[*] Test 2: Testing HDLC Framing (0x7E / 0x7D stuffing)... ";
    {
        uint8_t payload[] = { 0x01, 0x7E, 0x02, 0x7D, 0x03, 0x7E, 0x7D };
        auto escaped = BSLab::QcDiagQcnEngine::EscapeDiagData(payload, sizeof(payload));
        // Escaped output should not have raw 0x7E or unescaped 0x7D
        for (size_t i = 0; i < escaped.size(); ++i) {
            assert(escaped[i] != 0x7E);
        }
        auto unescaped = BSLab::QcDiagQcnEngine::UnescapeDiagData(escaped.data(), escaped.size());
        assert(unescaped.size() == sizeof(payload));
        assert(std::memcmp(unescaped.data(), payload, sizeof(payload)) == 0);

        // Test BuildFrame
        auto frame = BSLab::QcDiagQcnEngine::BuildFrame(payload, sizeof(payload));
        assert(frame.front() == 0x7E);
        assert(frame.back() == 0x7E);
        std::cout << "PASSED (Framed size: " << frame.size() << ")\n";
    }

    // ----------------------------------------------------
    // TEST 3: Luhn Check Digit Algorithm
    // ----------------------------------------------------
    std::cout << "[*] Test 3: Testing Luhn Algorithm for 14/15-digit IMEI... ";
    {
        // Known valid IMEI: 86512304567890?
        std::string imei14 = "86512304567890";
        char ch = BSLab::QcDiagQcnEngine::CalculateLuhnCheckDigit(imei14);
        assert(ch >= '0' && ch <= '9');

        std::string full15 = imei14 + ch;
        std::string outImei, outErr;
        bool valid = BSLab::QcDiagQcnEngine::ValidateImei(full15, outImei, outErr);
        assert(valid);
        assert(outImei == full15);

        // Test with invalid check digit
        std::string badImei = imei14 + (ch == '9' ? '0' : static_cast<char>(ch + 1));
        bool invalid = BSLab::QcDiagQcnEngine::ValidateImei(badImei, outImei, outErr);
        assert(!invalid);
        std::cout << "PASSED (Luhn check digit: " << ch << ")\n";
    }

    // ----------------------------------------------------
    // TEST 4: Qualcomm 9-byte BCD Encoding & Decoding
    // ----------------------------------------------------
    std::cout << "[*] Test 4: Testing 3GPP TS 24.008 9-byte BCD Parity... ";
    {
        std::string testImei = "860123456789018";
        std::vector<uint8_t> bcd;
        bool okEnc = BSLab::QcDiagQcnEngine::EncodeImeiQcBcd(testImei, bcd);
        assert(okEnc);
        assert(bcd.size() == 9);
        assert(bcd[0] == 0x08); // Length prefix
        assert((bcd[1] & 0x0F) == 0x0A); // Odd indicator
        assert(((bcd[1] >> 4) & 0x0F) == 8); // First digit is '8'

        std::string decoded;
        bool okDec = BSLab::QcDiagQcnEngine::DecodeImeiQcBcd(bcd.data(), bcd.size(), decoded);
        assert(okDec);
        assert(decoded == testImei);
        std::cout << "PASSED (" << testImei << " <-> BCD <-> " << decoded << ")\n";
    }

    // ----------------------------------------------------
    // TEST 5: QCN Binary Container Creation & Parsing
    // ----------------------------------------------------
    std::cout << "[*] Test 5: Testing QCN Binary Container Parse & Create... ";
    {
        std::vector<BSLab::QcnNvRecord> sampleRecords;
        
        // Record 1: NV 550 (IMEI 1)
        BSLab::QcnNvRecord r1;
        r1.itemId = 550;
        r1.data.assign(128, 0xAA);
        sampleRecords.push_back(r1);

        // Record 2: NV 650 (IMEI 2)
        BSLab::QcnNvRecord r2;
        r2.itemId = 650;
        r2.data.assign(128, 0xBB);
        sampleRecords.push_back(r2);

        // Record 3: NV 6828 (Carrier Aggregation)
        BSLab::QcnNvRecord r3;
        r3.itemId = 6828;
        r3.data.assign(64, 0xCC);
        sampleRecords.push_back(r3);

        std::string testQcn = "test_sample.qcn";
        bool okCreate = BSLab::QcDiagQcnEngine::CreateQcnFile(testQcn, sampleRecords);
        assert(okCreate);

        std::vector<BSLab::QcnNvRecord> parsed;
        std::string err;
        bool okParse = BSLab::QcDiagQcnEngine::ParseQcnFile(testQcn, parsed, err);
        assert(okParse);
        assert(parsed.size() == 3);
        assert(parsed[0].itemId == 550 && parsed[0].data.size() == 128);
        assert(parsed[1].itemId == 650 && parsed[1].data.size() == 128);
        assert(parsed[2].itemId == 6828 && parsed[2].data.size() == 64);
        std::cout << "PASSED (3 NV items created and verified)\n";
    }

    // ----------------------------------------------------
    // TEST 6: QCN On-the-fly IMEI Patching
    // ----------------------------------------------------
    std::cout << "[*] Test 6: Testing QCN On-the-fly IMEI Injection... ";
    {
        std::string inQcn = "test_sample.qcn";
        std::string outQcn = "test_patched.qcn";
        std::string newImei1 = "867777012345674";
        std::string newImei2 = "868888012345672";
        int patchedCount = 0;
        std::string patchMsg;

        bool okPatch = BSLab::QcDiagQcnEngine::PatchQcnFile(inQcn, outQcn, newImei1, newImei2, patchedCount, patchMsg);
        assert(okPatch);
        assert(patchedCount == 2);

        // Parse patched file and verify decoded IMEIs
        std::vector<BSLab::QcnNvRecord> patchedRecords;
        std::string err;
        assert(BSLab::QcDiagQcnEngine::ParseQcnFile(outQcn, patchedRecords, err));

        std::string readImei1, readImei2;
        assert(BSLab::QcDiagQcnEngine::DecodeImeiQcBcd(patchedRecords[0].data.data(), 9, readImei1));
        assert(BSLab::QcDiagQcnEngine::DecodeImeiQcBcd(patchedRecords[1].data.data(), 9, readImei2));
        assert(readImei1 == newImei1);
        assert(readImei2 == newImei2);
        std::cout << "PASSED (Injected IMEI 1: " << readImei1 << ", IMEI 2: " << readImei2 << ")\n";

        // Cleanup temp files
        std::filesystem::remove("test_sample.qcn");
        std::filesystem::remove("test_patched.qcn");
    }

    // ----------------------------------------------------
    // TEST 7: C-ABI Exports Verification
    // ----------------------------------------------------
    std::cout << "[*] Test 7: Testing C-ABI DLL Export Functions... ";
    {
        char outFull[32] = { 0 };
        char outErr[256] = { 0 };
        assert(BSLab_QC_Diag_ValidateImei("86512304567890", outFull, sizeof(outFull), outErr, sizeof(outErr)));
        assert(std::strlen(outFull) == 15);

        uint8_t bcd[9];
        assert(BSLab_QC_Diag_EncodeImeiBcd(outFull, bcd, sizeof(bcd)));

        char decoded[32] = { 0 };
        assert(BSLab_QC_Diag_DecodeImeiBcd(bcd, sizeof(bcd), decoded, sizeof(decoded)));
        assert(std::strcmp(outFull, decoded) == 0);
        std::cout << "PASSED (All C-ABI interfaces operational)\n";
    }

    std::cout << "\n====================================================\n";
    std::cout << " ✅ ALL 7 QUALCOMM DIAG & QCN TESTS PASSED (0 ERRORS)\n";
    std::cout << "====================================================\n";
    return 0;
}
