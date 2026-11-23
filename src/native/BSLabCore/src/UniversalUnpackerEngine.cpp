#include "UniversalUnpackerEngine.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <memory>

namespace BSLab {

// =========================================================================
// PROTOBUF LIGHTWEIGHT HELPER FOR ANDROID OTA PAYLOAD.BIN
// =========================================================================

namespace {

bool ReadVarint(const uint8_t*& ptr, const uint8_t* end, uint64_t& val) {
    val = 0;
    int shift = 0;
    while (ptr < end) {
        uint8_t b = *ptr++;
        val |= static_cast<uint64_t>(b & 0x7F) << shift;
        if ((b & 0x80) == 0) return true;
        shift += 7;
        if (shift > 64) return false;
    }
    return false;
}

struct RawExtent {
    uint64_t start_block = 0;
    uint64_t num_blocks = 0;
};

struct RawOperation {
    uint32_t type = 0;
    uint64_t data_offset = 0;
    uint64_t data_length = 0;
    uint64_t dst_length = 0;
    std::vector<RawExtent> extents;
};

struct RawPartition {
    std::string name;
    uint64_t size = 0;
    std::vector<RawOperation> operations;
};

RawExtent ParseExtentMsg(const uint8_t* data, size_t length) {
    RawExtent ext;
    const uint8_t* ptr = data;
    const uint8_t* end = data + length;
    while (ptr < end) {
        uint64_t tag = 0;
        if (!ReadVarint(ptr, end, tag)) break;
        uint32_t field = static_cast<uint32_t>(tag >> 3);
        uint32_t wire = static_cast<uint32_t>(tag & 7);

        if (wire == 0) { // Varint
            uint64_t val = 0;
            if (!ReadVarint(ptr, end, val)) break;
            if (field == 1) ext.start_block = val;
            else if (field == 2) ext.num_blocks = val;
        } else if (wire == 2) { // Length-delimited
            uint64_t len = 0;
            if (!ReadVarint(ptr, end, len) || ptr + len > end) break;
            ptr += len;
        } else if (wire == 5) { // 32-bit
            ptr += 4;
        } else if (wire == 1) { // 64-bit
            ptr += 8;
        } else {
            break;
        }
    }
    return ext;
}

RawOperation ParseOperationMsg(const uint8_t* data, size_t length) {
    RawOperation op;
    const uint8_t* ptr = data;
    const uint8_t* end = data + length;
    while (ptr < end) {
        uint64_t tag = 0;
        if (!ReadVarint(ptr, end, tag)) break;
        uint32_t field = static_cast<uint32_t>(tag >> 3);
        uint32_t wire = static_cast<uint32_t>(tag & 7);

        if (wire == 0) { // Varint
            uint64_t val = 0;
            if (!ReadVarint(ptr, end, val)) break;
            if (field == 1) op.type = static_cast<uint32_t>(val);
            else if (field == 2) op.data_offset = val;
            else if (field == 3) op.data_length = val;
            else if (field == 7) op.dst_length = val;
        } else if (wire == 2) { // Length-delimited (extents)
            uint64_t len = 0;
            if (!ReadVarint(ptr, end, len) || ptr + len > end) break;
            if (field == 6) { // dst_extents
                op.extents.push_back(ParseExtentMsg(ptr, static_cast<size_t>(len)));
            }
            ptr += len;
        } else if (wire == 5) {
            ptr += 4;
        } else if (wire == 1) {
            ptr += 8;
        } else {
            break;
        }
    }
    return op;
}

RawPartition ParsePartitionMsg(const uint8_t* data, size_t length) {
    RawPartition p;
    const uint8_t* ptr = data;
    const uint8_t* end = data + length;
    while (ptr < end) {
        uint64_t tag = 0;
        if (!ReadVarint(ptr, end, tag)) break;
        uint32_t field = static_cast<uint32_t>(tag >> 3);
        uint32_t wire = static_cast<uint32_t>(tag & 7);

        if (wire == 0) {
            uint64_t val = 0;
            if (!ReadVarint(ptr, end, val)) break;
        } else if (wire == 2) {
            uint64_t len = 0;
            if (!ReadVarint(ptr, end, len) || ptr + len > end) break;
            if (field == 1) { // partition_name
                p.name.assign(reinterpret_cast<const char*>(ptr), static_cast<size_t>(len));
            } else if (field == 4) { // PartitionInfo
                const uint8_t* infoPtr = ptr;
                const uint8_t* infoEnd = ptr + len;
                while (infoPtr < infoEnd) {
                    uint64_t infoTag = 0;
                    if (!ReadVarint(infoPtr, infoEnd, infoTag)) break;
                    if ((infoTag >> 3) == 1 && (infoTag & 7) == 0) {
                        ReadVarint(infoPtr, infoEnd, p.size);
                    } else if ((infoTag & 7) == 2) {
                        uint64_t skipLen = 0;
                        if (ReadVarint(infoPtr, infoEnd, skipLen)) infoPtr += skipLen;
                    }
                }
            } else if (field == 5) { // operations
                p.operations.push_back(ParseOperationMsg(ptr, static_cast<size_t>(len)));
            }
            ptr += len;
        } else if (wire == 5) {
            ptr += 4;
        } else if (wire == 1) {
            ptr += 8;
        } else {
            break;
        }
    }
    return p;
}

} // anonymous namespace

// =========================================================================
// UNIVERSAL UNPACKER ENGINE CORE IMPLEMENTATION
// =========================================================================

FirmwareContainerType UniversalUnpackerEngine::IdentifyFileType(const std::string& filePath) {
    std::ifstream file(filePath, std::ios::binary);
    if (!file.is_open()) return FirmwareContainerType::UNKNOWN;

    uint32_t magic = 0;
    file.read(reinterpret_cast<char*>(&magic), sizeof(magic));
    if (file.gcount() < 4) return FirmwareContainerType::UNKNOWN;

    if (magic == PAYLOAD_MAGIC) {
        return FirmwareContainerType::PAYLOAD_BIN;
    }
    if (magic == SPARSE_HEADER_MAGIC) {
        return FirmwareContainerType::ANDROID_SPARSE;
    }
    if (magic == HUAWEI_APP_MAGIC) {
        return FirmwareContainerType::HUAWEI_UPDATE_APP;
    }

    // Check at offset 4096 (0x1000) for Android Super / Logical Partition header
    file.seekg(4096, std::ios::beg);
    uint32_t lpMagic = 0;
    file.read(reinterpret_cast<char*>(&lpMagic), sizeof(lpMagic));
    if (file.gcount() == 4 && lpMagic == LP_METADATA_MAGIC) {
        return FirmwareContainerType::ANDROID_SUPER;
    }

    return FirmwareContainerType::GENERIC_ARCHIVE;
}

const char* UniversalUnpackerEngine::FirmwareTypeToString(FirmwareContainerType type) {
    switch (type) {
        case FirmwareContainerType::PAYLOAD_BIN:       return "Android OTA Payload.bin";
        case FirmwareContainerType::ANDROID_SPARSE:     return "Android Sparse Image (simg2img)";
        case FirmwareContainerType::ANDROID_SUPER:      return "Android Dynamic Super Partition (super.img)";
        case FirmwareContainerType::HUAWEI_UPDATE_APP:  return "Huawei Official UPDATE.APP";
        case FirmwareContainerType::GENERIC_ARCHIVE:    return "Generic Firmware Archive";
        default:                                        return "Unknown Format";
    }
}

bool UniversalUnpackerEngine::IsSparseImage(const std::string& filePath) {
    std::ifstream file(filePath, std::ios::binary);
    if (!file.is_open()) return false;
    uint32_t magic = 0;
    file.read(reinterpret_cast<char*>(&magic), sizeof(magic));
    return (file.gcount() == 4 && magic == SPARSE_HEADER_MAGIC);
}

bool UniversalUnpackerEngine::UnsparseImage(
    const std::string& sparsePath,
    const std::string& outRawPath,
    std::function<void(float, const std::string&)> progressCb
) {
    s_abortRequested = false;
    std::ifstream in(sparsePath, std::ios::binary);
    if (!in.is_open()) return false;

    std::ofstream out(outRawPath, std::ios::binary);
    if (!out.is_open()) return false;

    uint8_t header[28] = { 0 };
    in.read(reinterpret_cast<char*>(header), sizeof(header));
    if (in.gcount() < 28) return false;

    uint32_t magic = *reinterpret_cast<uint32_t*>(&header[0]);
    if (magic != SPARSE_HEADER_MAGIC) {
        // Not sparse, copy flat file
        in.seekg(0, std::ios::beg);
        std::vector<uint8_t> buffer(4 * 1024 * 1024); // 4MB buffer
        while (in && !s_abortRequested) {
            in.read(reinterpret_cast<char*>(buffer.data()), buffer.size());
            std::streamsize bytes = in.gcount();
            if (bytes <= 0) break;
            out.write(reinterpret_cast<const char*>(buffer.data()), bytes);
        }
        return true;
    }

    uint16_t fileHdrSz   = *reinterpret_cast<uint16_t*>(&header[6]);
    uint16_t chunkHdrSz  = *reinterpret_cast<uint16_t*>(&header[8]);
    uint32_t blkSz       = *reinterpret_cast<uint32_t*>(&header[10]);
    uint32_t totalChunks = *reinterpret_cast<uint32_t*>(&header[18]);

    if (fileHdrSz > 28) {
        in.seekg(fileHdrSz - 28, std::ios::cur);
    }

    std::vector<uint8_t> ioBuffer(4 * 1024 * 1024);
    std::vector<uint8_t> zeroBuffer(1024 * 1024, 0);

    for (uint32_t i = 0; i < totalChunks && !s_abortRequested; ++i) {
        uint8_t chunkHdr[12] = { 0 };
        in.read(reinterpret_cast<char*>(chunkHdr), sizeof(chunkHdr));
        if (in.gcount() < 12) break;

        uint16_t chunkType = *reinterpret_cast<uint16_t*>(&chunkHdr[0]);
        uint32_t chunkSz   = *reinterpret_cast<uint32_t*>(&chunkHdr[4]); // in blocks
        uint32_t totalSz   = *reinterpret_cast<uint32_t*>(&chunkHdr[8]);

        if (chunkHdrSz > 12) {
            in.seekg(chunkHdrSz - 12, std::ios::cur);
        }

        uint64_t dataBytes = static_cast<uint64_t>(chunkSz) * blkSz;

        if (chunkType == CHUNK_TYPE_RAW) {
            uint64_t remaining = dataBytes;
            while (remaining > 0 && !s_abortRequested) {
                size_t toRead = static_cast<size_t>(std::min<uint64_t>(remaining, ioBuffer.size()));
                in.read(reinterpret_cast<char*>(ioBuffer.data()), toRead);
                std::streamsize readBytes = in.gcount();
                if (readBytes <= 0) break;
                out.write(reinterpret_cast<const char*>(ioBuffer.data()), readBytes);
                remaining -= readBytes;
            }
        } else if (chunkType == CHUNK_TYPE_FILL) {
            uint32_t fillPattern = 0;
            in.read(reinterpret_cast<char*>(&fillPattern), sizeof(fillPattern));
            // Fill 64KB block pattern
            std::vector<uint32_t> fillBlock(blkSz / 4, fillPattern);
            for (uint32_t b = 0; b < chunkSz && !s_abortRequested; ++b) {
                out.write(reinterpret_cast<const char*>(fillBlock.data()), blkSz);
            }
        } else if (chunkType == CHUNK_TYPE_DONT_CARE) {
            uint64_t remaining = dataBytes;
            while (remaining > 0 && !s_abortRequested) {
                size_t toWrite = static_cast<size_t>(std::min<uint64_t>(remaining, zeroBuffer.size()));
                out.write(reinterpret_cast<const char*>(zeroBuffer.data()), toWrite);
                remaining -= toWrite;
            }
        } else if (chunkType == CHUNK_TYPE_CRC32) {
            in.seekg(4, std::ios::cur);
        }

        if (progressCb && (i % 20 == 0 || i == totalChunks - 1)) {
            float pct = static_cast<float>(i + 1) / static_cast<float>(totalChunks);
            std::string status = "Unsparsing chunk " + std::to_string(i + 1) + "/" + std::to_string(totalChunks);
            progressCb(pct, status);
        }
    }

    out.flush();
    return !s_abortRequested;
}

bool UniversalUnpackerEngine::UnpackSuperImage(
    const std::string& superPath,
    const std::string& outDir,
    std::vector<ExtractedPartitionInfo>& outFiles,
    std::function<void(float, const std::string&)> progressCb
) {
    s_abortRequested = false;
    outFiles.clear();
    std::filesystem::create_directories(outDir);

    std::string workingSuper = superPath;
    bool wasUnsparsed = false;

    if (IsSparseImage(superPath)) {
        std::string rawSuperPath = (std::filesystem::path(outDir) / "super_raw.img").string();
        if (progressCb) progressCb(0.05f, "Decompressing sparse super.img container...");
        if (!UnsparseImage(superPath, rawSuperPath, progressCb)) {
            return false;
        }
        workingSuper = rawSuperPath;
        wasUnsparsed = true;
    }

    std::ifstream f(workingSuper, std::ios::binary);
    if (!f.is_open()) return false;

    f.seekg(0, std::ios::end);
    uint64_t fileSize = static_cast<uint64_t>(f.tellg());
    f.seekg(0, std::ios::beg);

    // Standard Android Dynamic Partitions
    const std::vector<std::string> knownParts = {
        "system", "vendor", "product", "system_ext", "odm", "system_dlkm", "vendor_dlkm"
    };

    uint64_t offset = 1048576; // Start after LP geometry header
    std::vector<uint8_t> ioBuf(2 * 1024 * 1024);

    for (size_t i = 0; i < knownParts.size() && offset < fileSize && !s_abortRequested; ++i) {
        const std::string& pName = knownParts[i];
        std::string outPath = (std::filesystem::path(outDir) / (pName + ".img")).string();

        f.seekg(offset, std::ios::beg);
        uint8_t sample[4096] = { 0 };
        f.read(reinterpret_cast<char*>(sample), sizeof(sample));
        
        bool allZero = true;
        for (int b = 0; b < 4096; ++b) {
            if (sample[b] != 0) { allZero = false; break; }
        }

        if (allZero) {
            offset += 1048576;
            continue;
        }

        uint64_t extentSize = std::min<uint64_t>(1073741824ULL, fileSize - offset); // 1GB chunk max
        std::ofstream partF(outPath, std::ios::binary);
        if (partF.is_open()) {
            partF.write(reinterpret_cast<const char*>(sample), sizeof(sample));
            uint64_t copied = sizeof(sample);

            while (copied < extentSize && !s_abortRequested) {
                size_t toRead = static_cast<size_t>(std::min<uint64_t>(extentSize - copied, ioBuf.size()));
                f.read(reinterpret_cast<char*>(ioBuf.data()), toRead);
                std::streamsize n = f.gcount();
                if (n <= 0) break;
                partF.write(reinterpret_cast<const char*>(ioBuf.data()), n);
                copied += n;
            }
            partF.close();

            ExtractedPartitionInfo info;
            info.name = pName + ".img";
            info.path = outPath;
            info.size = copied;
            outFiles.push_back(std::move(info));
        }

        offset += extentSize;
        if (progressCb) {
            float pct = static_cast<float>(offset) / static_cast<float>(fileSize);
            progressCb(std::min(1.0f, pct), "Extracted " + pName + ".img");
        }
    }

    f.close();

    // Clean up temporary raw super if created
    if (wasUnsparsed && std::filesystem::exists(workingSuper)) {
        std::error_code ec;
        std::filesystem::remove(workingSuper, ec);
    }

    return !outFiles.empty();
}

bool UniversalUnpackerEngine::InspectPayloadBin(
    const std::string& payloadPath,
    std::vector<PayloadPartition>& outPartitions,
    std::string& outError
) {
    outPartitions.clear();
    std::ifstream f(payloadPath, std::ios::binary);
    if (!f.is_open()) {
        outError = "Failed to open payload.bin file.";
        return false;
    }

    uint32_t magic = 0;
    f.read(reinterpret_cast<char*>(&magic), 4);
    if (magic != PAYLOAD_MAGIC) {
        outError = "Invalid OTA payload header magic (Expected 'CrAU').";
        return false;
    }

    // Read big-endian uint64 file format version
    uint8_t vBytes[8];
    f.read(reinterpret_cast<char*>(vBytes), 8);
    uint64_t version = 0;
    for (int i = 0; i < 8; ++i) version = (version << 8) | vBytes[i];

    // Read big-endian uint64 manifest size
    uint8_t mBytes[8];
    f.read(reinterpret_cast<char*>(mBytes), 8);
    uint64_t manifestSize = 0;
    for (int i = 0; i < 8; ++i) manifestSize = (manifestSize << 8) | mBytes[i];

    if (manifestSize == 0 || manifestSize > 100 * 1024 * 1024) {
        outError = "Corrupted or oversized payload manifest.";
        return false;
    }

    uint32_t metadataSigSize = 0;
    if (version >= 2) {
        uint8_t sBytes[4];
        f.read(reinterpret_cast<char*>(sBytes), 4);
        for (int i = 0; i < 4; ++i) metadataSigSize = (metadataSigSize << 8) | sBytes[i];
    }

    std::vector<uint8_t> manifest(manifestSize);
    f.read(reinterpret_cast<char*>(manifest.data()), manifestSize);
    if (f.gcount() < static_cast<std::streamsize>(manifestSize)) {
        outError = "Truncated payload manifest.";
        return false;
    }

    // Parse top-level protobuf manifest
    const uint8_t* ptr = manifest.data();
    const uint8_t* end = manifest.data() + manifest.size();
    uint32_t blockSize = 4096;

    while (ptr < end) {
        uint64_t tag = 0;
        if (!ReadVarint(ptr, end, tag)) break;
        uint32_t field = static_cast<uint32_t>(tag >> 3);
        uint32_t wire = static_cast<uint32_t>(tag & 7);

        if (wire == 0) { // Varint
            uint64_t val = 0;
            if (!ReadVarint(ptr, end, val)) break;
            if (field == 3) blockSize = static_cast<uint32_t>(val);
        } else if (wire == 2) { // Length-delimited
            uint64_t len = 0;
            if (!ReadVarint(ptr, end, len) || ptr + len > end) break;
            if (field == 1) { // PartitionUpdate
                RawPartition rp = ParsePartitionMsg(ptr, static_cast<size_t>(len));
                PayloadPartition pp;
                pp.name = rp.name;
                pp.size = rp.size;
                pp.block_size = blockSize;
                outPartitions.push_back(std::move(pp));
            }
            ptr += len;
        } else if (wire == 5) {
            ptr += 4;
        } else if (wire == 1) {
            ptr += 8;
        } else {
            break;
        }
    }

    return !outPartitions.empty();
}

bool UniversalUnpackerEngine::UnpackPayloadBin(
    const std::string& payloadPath,
    const std::string& outDir,
    const std::vector<std::string>& targetPartitions,
    std::vector<ExtractedPartitionInfo>& outFiles,
    std::function<void(float, const std::string&)> progressCb
) {
    s_abortRequested = false;
    outFiles.clear();
    std::filesystem::create_directories(outDir);

    std::ifstream f(payloadPath, std::ios::binary);
    if (!f.is_open()) return false;

    uint32_t magic = 0;
    f.read(reinterpret_cast<char*>(&magic), 4);
    if (magic != PAYLOAD_MAGIC) return false;

    uint8_t vBytes[8];
    f.read(reinterpret_cast<char*>(vBytes), 8);
    uint64_t version = 0;
    for (int i = 0; i < 8; ++i) version = (version << 8) | vBytes[i];

    uint8_t mBytes[8];
    f.read(reinterpret_cast<char*>(mBytes), 8);
    uint64_t manifestSize = 0;
    for (int i = 0; i < 8; ++i) manifestSize = (manifestSize << 8) | mBytes[i];

    uint32_t metadataSigSize = 0;
    if (version >= 2) {
        uint8_t sBytes[4];
        f.read(reinterpret_cast<char*>(sBytes), 4);
        for (int i = 0; i < 4; ++i) metadataSigSize = (metadataSigSize << 8) | sBytes[i];
    }

    std::vector<uint8_t> manifest(manifestSize);
    f.read(reinterpret_cast<char*>(manifest.data()), manifestSize);
    f.seekg(metadataSigSize, std::ios::cur);
    uint64_t dataStartOffset = static_cast<uint64_t>(f.tellg());

    // Parse partitions
    const uint8_t* ptr = manifest.data();
    const uint8_t* end = manifest.data() + manifest.size();
    uint32_t blockSize = 4096;
    std::vector<RawPartition> partitions;

    while (ptr < end) {
        uint64_t tag = 0;
        if (!ReadVarint(ptr, end, tag)) break;
        uint32_t field = static_cast<uint32_t>(tag >> 3);
        uint32_t wire = static_cast<uint32_t>(tag & 7);

        if (wire == 0) {
            uint64_t val = 0;
            if (!ReadVarint(ptr, end, val)) break;
            if (field == 3) blockSize = static_cast<uint32_t>(val);
        } else if (wire == 2) {
            uint64_t len = 0;
            if (!ReadVarint(ptr, end, len) || ptr + len > end) break;
            if (field == 1) {
                partitions.push_back(ParsePartitionMsg(ptr, static_cast<size_t>(len)));
            }
            ptr += len;
        } else if (wire == 5) {
            ptr += 4;
        } else if (wire == 1) {
            ptr += 8;
        } else {
            break;
        }
    }

    std::vector<RawPartition> selected;
    if (!targetPartitions.empty()) {
        for (auto& p : partitions) {
            for (const auto& t : targetPartitions) {
                if (_stricmp(p.name.c_str(), t.c_str()) == 0) {
                    selected.push_back(std::move(p));
                    break;
                }
            }
        }
    } else {
        selected = std::move(partitions);
    }

    size_t total = selected.size();
    std::vector<uint8_t> chunkBuf;

    for (size_t i = 0; i < total && !s_abortRequested; ++i) {
        const auto& part = selected[i];
        std::string outPath = (std::filesystem::path(outDir) / (part.name + ".img")).string();
        std::ofstream outF(outPath, std::ios::binary);
        if (!outF.is_open()) continue;

        for (const auto& op : part.operations) {
            if (s_abortRequested) break;

            if (op.data_length > 0) {
                f.seekg(dataStartOffset + op.data_offset, std::ios::beg);
                if (chunkBuf.size() < op.data_length) chunkBuf.resize(op.data_length);
                f.read(reinterpret_cast<char*>(chunkBuf.data()), op.data_length);
            }

            for (const auto& ext : op.extents) {
                uint64_t writeOffset = ext.start_block * blockSize;
                uint64_t writeBytes = ext.num_blocks * blockSize;
                outF.seekp(writeOffset, std::ios::beg);

                if (op.type == 6) { // OP_ZERO
                    std::vector<uint8_t> zeros(65536, 0);
                    uint64_t rem = writeBytes;
                    while (rem > 0) {
                        size_t toWrite = static_cast<size_t>(std::min<uint64_t>(rem, zeros.size()));
                        outF.write(reinterpret_cast<const char*>(zeros.data()), toWrite);
                        rem -= toWrite;
                    }
                } else {
                    size_t toWrite = static_cast<size_t>(std::min<uint64_t>(writeBytes, op.data_length));
                    if (toWrite > 0) {
                        outF.write(reinterpret_cast<const char*>(chunkBuf.data()), toWrite);
                    }
                }
            }
        }
        outF.close();

        ExtractedPartitionInfo info;
        info.name = part.name + ".img";
        info.path = outPath;
        info.size = std::filesystem::file_size(outPath);
        outFiles.push_back(std::move(info));

        if (progressCb) {
            float pct = static_cast<float>(i + 1) / static_cast<float>(total);
            progressCb(pct, "Extracted " + part.name + ".img");
        }
    }

    return !outFiles.empty();
}

bool UniversalUnpackerEngine::UnpackHuaweiUpdateApp(
    const std::string& appPath,
    const std::string& outDir,
    std::vector<ExtractedPartitionInfo>& outFiles,
    std::function<void(float, const std::string&)> progressCb
) {
    s_abortRequested = false;
    outFiles.clear();
    std::filesystem::create_directories(outDir);

    std::ifstream f(appPath, std::ios::binary);
    if (!f.is_open()) return false;

    struct AppEntry {
        std::string name;
        uint64_t offset = 0;
        uint32_t size = 0;
    };
    std::vector<AppEntry> entries;

    // Scan headers (0x55, 0xAA, 0x5A, 0xA5)
    while (!s_abortRequested) {
        uint32_t magic = 0;
        f.read(reinterpret_cast<char*>(&magic), 4);
        if (f.gcount() < 4) break;

        if (magic != HUAWEI_APP_MAGIC) {
            // Seek ahead 1 byte
            f.seekg(-3, std::ios::cur);
            continue;
        }

        uint32_t headerSize = 0;
        f.read(reinterpret_cast<char*>(&headerSize), 4);
        if (headerSize < 76 || headerSize > 2048) continue;

        f.seekg(16, std::ios::cur);

        uint32_t payloadSize = 0;
        f.read(reinterpret_cast<char*>(&payloadSize), 4);

        f.seekg(32, std::ios::cur);

        char rawName[16] = { 0 };
        f.read(rawName, 16);
        std::string cleanName;
        for (int c = 0; c < 16 && rawName[c] != '\0'; ++c) {
            if (rawName[c] >= 32 && rawName[c] <= 126) cleanName += rawName[c];
        }
        if (cleanName.empty()) {
            cleanName = "PARTITION_" + std::to_string(entries.size() + 1);
        }

        uint32_t alreadyRead = 4 + 4 + 16 + 4 + 32 + 16;
        if (headerSize > alreadyRead) {
            f.seekg(headerSize - alreadyRead, std::ios::cur);
        }

        AppEntry entry;
        entry.name = cleanName;
        entry.offset = static_cast<uint64_t>(f.tellg());
        entry.size = payloadSize;
        entries.push_back(std::move(entry));

        // Skip payload & 4-byte alignment padding
        f.seekg(payloadSize, std::ios::cur);
        uint32_t rem = payloadSize % 4;
        if (rem > 0) f.seekg(4 - rem, std::ios::cur);
    }

    if (entries.empty()) return false;

    f.clear(); // Clear EOF flag from first scanning pass

    size_t total = entries.size();
    std::vector<uint8_t> buffer(1024 * 1024); // 1MB buffer

    for (size_t i = 0; i < total && !s_abortRequested; ++i) {
        const auto& e = entries[i];
        std::string filename = e.name;
        if (filename.length() < 4 || filename.substr(filename.length() - 4) != ".img") {
            filename += ".img";
        }

        std::string outPath = (std::filesystem::path(outDir) / filename).string();
        f.seekg(e.offset, std::ios::beg);

        std::ofstream outF(outPath, std::ios::binary);
        if (outF.is_open()) {
            uint32_t remaining = e.size;
            while (remaining > 0 && !s_abortRequested) {
                size_t toRead = std::min<size_t>(remaining, buffer.size());
                f.read(reinterpret_cast<char*>(buffer.data()), toRead);
                std::streamsize n = f.gcount();
                if (n <= 0) break;
                outF.write(reinterpret_cast<const char*>(buffer.data()), n);
                remaining -= static_cast<uint32_t>(n);
            }
            outF.close();

            ExtractedPartitionInfo info;
            info.name = filename;
            info.path = outPath;
            info.size = e.size;
            outFiles.push_back(std::move(info));
        }

        if (progressCb) {
            float pct = static_cast<float>(i + 1) / static_cast<float>(total);
            progressCb(pct, "Extracted " + filename);
        }
    }

    return !outFiles.empty();
}

void UniversalUnpackerEngine::Abort() {
    s_abortRequested = true;
}

} // namespace BSLab
