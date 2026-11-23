#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <atomic>

namespace BSLab {

enum class FirmwareContainerType {
    UNKNOWN = 0,
    PAYLOAD_BIN,
    ANDROID_SPARSE,
    ANDROID_SUPER,
    HUAWEI_UPDATE_APP,
    GENERIC_ARCHIVE
};

struct ExtractedPartitionInfo {
    std::string name;
    std::string path;
    uint64_t size = 0;
};

struct PayloadPartition {
    std::string name;
    uint64_t size = 0;
    uint32_t block_size = 4096;
};

class UniversalUnpackerEngine {
public:
    // Standard AOSP and Container Magics
    static constexpr uint32_t SPARSE_HEADER_MAGIC   = 0xED26FF3A;
    static constexpr uint32_t LP_METADATA_MAGIC     = 0x616C6F30; // "0loa"
    static constexpr uint32_t HUAWEI_APP_MAGIC      = 0xA55AAA55; // 0x55, 0xAA, 0x5A, 0xA5 little-endian
    static constexpr uint32_t PAYLOAD_MAGIC         = 0x55417243; // "CrAU" little-endian

    // Sparse chunk types
    static constexpr uint16_t CHUNK_TYPE_RAW        = 0xCAC1;
    static constexpr uint16_t CHUNK_TYPE_FILL       = 0xCAC2;
    static constexpr uint16_t CHUNK_TYPE_DONT_CARE  = 0xCAC3;
    static constexpr uint16_t CHUNK_TYPE_CRC32      = 0xCAC4;

    // Detects container type by reading file signature
    static FirmwareContainerType IdentifyFileType(const std::string& filePath);
    static const char* FirmwareTypeToString(FirmwareContainerType type);

    // Checks if file is Android Sparse image
    static bool IsSparseImage(const std::string& filePath);

    // Converts Android Sparse image to raw flat linear image (simg2img)
    static bool UnsparseImage(
        const std::string& sparsePath,
        const std::string& outRawPath,
        std::function<void(float, const std::string&)> progressCb = nullptr
    );

    // Unpacks dynamic partitions from Android super.img (lpunpack)
    static bool UnpackSuperImage(
        const std::string& superPath,
        const std::string& outDir,
        std::vector<ExtractedPartitionInfo>& outFiles,
        std::function<void(float, const std::string&)> progressCb = nullptr
    );

    // Inspects Android OTA payload.bin header and returns partition directory
    static bool InspectPayloadBin(
        const std::string& payloadPath,
        std::vector<PayloadPartition>& outPartitions,
        std::string& outError
    );

    // Extracts target or all partitions from Android OTA payload.bin
    static bool UnpackPayloadBin(
        const std::string& payloadPath,
        const std::string& outDir,
        const std::vector<std::string>& targetPartitions,
        std::vector<ExtractedPartitionInfo>& outFiles,
        std::function<void(float, const std::string&)> progressCb = nullptr
    );

    // Unpacks partition images from Huawei UPDATE.APP container
    static bool UnpackHuaweiUpdateApp(
        const std::string& appPath,
        const std::string& outDir,
        std::vector<ExtractedPartitionInfo>& outFiles,
        std::function<void(float, const std::string&)> progressCb = nullptr
    );

    // Abort active unpacking operation
    static void Abort();

private:
    static inline std::atomic<bool> s_abortRequested{false};
};

} // namespace BSLab
