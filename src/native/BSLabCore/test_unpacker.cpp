#include <iostream>
#include <cassert>
#include <cstring>
#include <vector>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include "UniversalUnpackerEngine.h"
#include "../include/BSLabCore.h"

int main() {
    std::cout << "====================================================\n";
    std::cout << "   BSLabCore Native Unit Test: Universal Unpacker   \n";
    std::cout << "====================================================\n";

    // ----------------------------------------------------
    // TEST 1: Android Sparse Image (simg2img) Decompression
    // ----------------------------------------------------
    std::cout << "[*] Test 1: Testing Android Sparse Decompression (simg2img)... ";
    {
        std::string testSparse = "test_sample.sparse";
        std::string testRaw = "test_sample_out.raw";

        std::ofstream out(testSparse, std::ios::binary);
        assert(out.is_open());

        // 28-byte Sparse Header
        uint8_t hdr[28] = { 0 };
        *reinterpret_cast<uint32_t*>(&hdr[0])  = 0xED26FF3A; // magic
        *reinterpret_cast<uint16_t*>(&hdr[4])  = 1;          // major
        *reinterpret_cast<uint16_t*>(&hdr[6])  = 28;         // file_hdr_sz
        *reinterpret_cast<uint16_t*>(&hdr[8])  = 12;         // chunk_hdr_sz
        *reinterpret_cast<uint32_t*>(&hdr[10]) = 4096;       // blk_sz (4KB)
        *reinterpret_cast<uint32_t*>(&hdr[14]) = 4;          // total_blks (4 blocks = 16KB)
        *reinterpret_cast<uint32_t*>(&hdr[18]) = 2;          // total_chunks
        out.write(reinterpret_cast<char*>(hdr), 28);

        // Chunk 1: RAW (2 blocks = 8192 bytes)
        uint8_t ch1[12] = { 0 };
        *reinterpret_cast<uint16_t*>(&ch1[0]) = 0xCAC1; // CHUNK_TYPE_RAW
        *reinterpret_cast<uint32_t*>(&ch1[4]) = 2;      // chunk_sz (2 blocks)
        *reinterpret_cast<uint32_t*>(&ch1[8]) = 12 + 8192; // total_sz
        out.write(reinterpret_cast<char*>(ch1), 12);
        std::vector<uint8_t> rawData(8192, 0xAB);
        out.write(reinterpret_cast<char*>(rawData.data()), 8192);

        // Chunk 2: FILL (2 blocks = 8192 bytes)
        uint8_t ch2[12] = { 0 };
        *reinterpret_cast<uint16_t*>(&ch2[0]) = 0xCAC2; // CHUNK_TYPE_FILL
        *reinterpret_cast<uint32_t*>(&ch2[4]) = 2;      // chunk_sz (2 blocks)
        *reinterpret_cast<uint32_t*>(&ch2[8]) = 12 + 4; // total_sz
        out.write(reinterpret_cast<char*>(ch2), 12);
        uint32_t fillVal = 0x12345678;
        out.write(reinterpret_cast<char*>(&fillVal), 4);
        out.close();

        // Verify IsSparseImage
        assert(BSLab::UniversalUnpackerEngine::IsSparseImage(testSparse));

        // Unsparse
        bool ok = BSLab::UniversalUnpackerEngine::UnsparseImage(testSparse, testRaw);
        assert(ok);
        assert(std::filesystem::exists(testRaw));
        assert(std::filesystem::file_size(testRaw) == 16384); // 4 blocks * 4096 = 16KB

        // Verify contents
        std::ifstream rawIn(testRaw, std::ios::binary);
        std::vector<uint8_t> readBack(16384);
        rawIn.read(reinterpret_cast<char*>(readBack.data()), 16384);
        rawIn.close();

        // First 8192 bytes must be 0xAB
        for (int i = 0; i < 8192; ++i) {
            assert(readBack[i] == 0xAB);
        }
        // Second 8192 bytes must be 0x12345678 repeated
        uint32_t* pWords = reinterpret_cast<uint32_t*>(&readBack[8192]);
        for (int i = 0; i < 2048; ++i) {
            assert(pWords[i] == 0x12345678);
        }

        std::filesystem::remove(testSparse);
        std::filesystem::remove(testRaw);
        std::cout << "PASSED (16KB sparse -> raw decompressed with 100% integrity)\n";
    }

    // ----------------------------------------------------
    // TEST 2: Firmware Container Type Identification
    // ----------------------------------------------------
    std::cout << "[*] Test 2: Testing Container Magic Identification... ";
    {
        // Sparse
        {
            std::ofstream f("test_magic.sparse", std::ios::binary);
            uint32_t m = 0xED26FF3A;
            f.write(reinterpret_cast<char*>(&m), 4);
            f.close();
            auto t = BSLab::UniversalUnpackerEngine::IdentifyFileType("test_magic.sparse");
            assert(t == BSLab::FirmwareContainerType::ANDROID_SPARSE);
            std::filesystem::remove("test_magic.sparse");
        }
        // Huawei
        {
            std::ofstream f("test_magic.app", std::ios::binary);
            uint32_t m = 0xA55AAA55; // 0x55, 0xAA, 0x5A, 0xA5
            f.write(reinterpret_cast<char*>(&m), 4);
            f.close();
            auto t = BSLab::UniversalUnpackerEngine::IdentifyFileType("test_magic.app");
            assert(t == BSLab::FirmwareContainerType::HUAWEI_UPDATE_APP);
            std::filesystem::remove("test_magic.app");
        }
        // Payload.bin
        {
            std::ofstream f("test_magic.bin", std::ios::binary);
            uint32_t m = 0x55417243; // "CrAU"
            f.write(reinterpret_cast<char*>(&m), 4);
            f.close();
            auto t = BSLab::UniversalUnpackerEngine::IdentifyFileType("test_magic.bin");
            assert(t == BSLab::FirmwareContainerType::PAYLOAD_BIN);
            std::filesystem::remove("test_magic.bin");
        }
        std::cout << "PASSED (Sparse, Huawei APP, and Payload.bin detected)\n";
    }

    // ----------------------------------------------------
    // TEST 3: Huawei UPDATE.APP Extraction
    // ----------------------------------------------------
    std::cout << "[*] Test 3: Testing Huawei UPDATE.APP Extractor... ";
    {
        std::string testApp = "test_update.app";
        std::string outDir = "test_huawei_extracted";

        std::ofstream out(testApp, std::ios::binary);
        // Header
        uint32_t magic = 0xA55AAA55;
        out.write(reinterpret_cast<char*>(&magic), 4);
        uint32_t hdrSize = 98;
        out.write(reinterpret_cast<char*>(&hdrSize), 4);
        // 16 dummy bytes
        uint8_t d16[16] = { 0 };
        out.write(reinterpret_cast<char*>(d16), 16);
        // Payload size: 512 bytes
        uint32_t payloadSize = 512;
        out.write(reinterpret_cast<char*>(&payloadSize), 4);
        // 32 dummy bytes
        uint8_t d32[32] = { 0 };
        out.write(reinterpret_cast<char*>(d32), 32);
        // 16 bytes partition name: "BOOT"
        char name[16] = { 0 };
        std::memcpy(name, "BOOT", 4);
        out.write(name, 16);
        // Remainder of header (98 - 76 = 22 bytes)
        uint8_t d22[22] = { 0 };
        out.write(reinterpret_cast<char*>(d22), 22);

        // Payload
        std::vector<uint8_t> payload(512, 0x77);
        out.write(reinterpret_cast<char*>(payload.data()), 512);
        out.close();

        std::vector<BSLab::ExtractedPartitionInfo> files;
        bool ok = BSLab::UniversalUnpackerEngine::UnpackHuaweiUpdateApp(testApp, outDir, files);
        assert(ok);
        assert(files.size() == 1);
        assert(files[0].name == "BOOT.img");
        assert(files[0].size == 512);

        // Verify extracted file content
        std::string bootImgPath = (std::filesystem::path(outDir) / "BOOT.img").string();
        assert(std::filesystem::exists(bootImgPath));
        std::ifstream bf(bootImgPath, std::ios::binary);
        std::vector<uint8_t> bootBytes(512);
        bf.read(reinterpret_cast<char*>(bootBytes.data()), 512);
        bf.close();
        for (int i = 0; i < 512; ++i) {
            assert(bootBytes[i] == 0x77);
        }

        std::filesystem::remove(testApp);
        std::filesystem::remove_all(outDir);
        std::cout << "PASSED (BOOT.img correctly parsed and extracted)\n";
    }

    // ----------------------------------------------------
    // TEST 4: C-ABI Exports Verification
    // ----------------------------------------------------
    std::cout << "[*] Test 4: Testing C-ABI Unpacker Export APIs... ";
    {
        char typeName[64] = { 0 };
        int typeId = BSLab_Unpacker_IdentifyType("non_existent.bin", typeName, sizeof(typeName));
        assert(typeId == 0); // UNKNOWN

        // Test abort
        BSLab_Unpacker_Abort();
        std::cout << "PASSED (C-ABI interfaces verified)\n";
    }

    std::cout << "\n====================================================\n";
    std::cout << " ✅ ALL UNIVERSAL UNPACKER TESTS PASSED (0 ERRORS)\n";
    std::cout << "====================================================\n";
    return 0;
}
