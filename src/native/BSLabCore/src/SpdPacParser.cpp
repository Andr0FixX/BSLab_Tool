#include "SpdPacParser.h"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstring>
#include <algorithm>

namespace BSLab {

static inline uint32_t ReadU32LE(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
          (static_cast<uint32_t>(p[1]) << 8) |
          (static_cast<uint32_t>(p[2]) << 16) |
          (static_cast<uint32_t>(p[3]) << 24);
}

std::string SpdPacParser::DecodeUtf16OrAscii(const uint8_t* data, size_t maxLen) {
    if (!data || maxLen == 0) return "";

    // Check if looks like UTF-16LE (alternating nulls)
    bool isUtf16 = false;
    if (maxLen >= 2 && data[1] == 0) {
        isUtf16 = true;
    }

    std::string result;
    if (isUtf16) {
        for (size_t i = 0; i + 1 < maxLen; i += 2) {
            uint16_t ch = static_cast<uint16_t>(data[i]) | (static_cast<uint16_t>(data[i + 1]) << 8);
            if (ch == 0) break;
            if (ch < 128) {
                result.push_back(static_cast<char>(ch));
            } else {
                result.push_back('?');
            }
        }
    } else {
        for (size_t i = 0; i < maxLen; ++i) {
            if (data[i] == 0) break;
            result.push_back(static_cast<char>(data[i]));
        }
    }

    while (!result.empty() && (result.back() == '\0' || result.back() == ' ')) {
        result.pop_back();
    }
    return result;
}

bool SpdPacParser::Parse(const std::string& pacPath, SpdPacInfo& outInfo, std::string& outError) {
    outInfo.partitions.clear();
    outInfo.file_count = 0;

    std::ifstream file(pacPath, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        outError = "Failed to open PAC archive: " + pacPath;
        return false;
    }

    uint64_t fileSize = static_cast<uint64_t>(file.tellg());
    if (fileSize < 2048) {
        outError = "File is too small to be a valid PAC archive (<2048 bytes)";
        return false;
    }

    file.seekg(0, std::ios::beg);

    // 1. Version tag (first 48 bytes)
    uint8_t verRaw[48];
    file.read(reinterpret_cast<char*>(verRaw), sizeof(verRaw));
    outInfo.version = DecodeUtf16OrAscii(verRaw, sizeof(verRaw));
    if (outInfo.version.empty()) {
        outInfo.version = "PAC_FORMAT_V1.0";
    }

    // 2. Product Name (512 bytes UTF-16LE at offset 52)
    file.seekg(52, std::ios::beg);
    uint8_t prdNameRaw[512];
    file.read(reinterpret_cast<char*>(prdNameRaw), sizeof(prdNameRaw));
    outInfo.product_name = DecodeUtf16OrAscii(prdNameRaw, sizeof(prdNameRaw));
    if (outInfo.product_name.empty()) {
        outInfo.product_name = "Unisoc Device";
    }

    // 3. Product Version (512 bytes UTF-16LE at offset 564)
    file.seekg(564, std::ios::beg);
    uint8_t prdVerRaw[512];
    file.read(reinterpret_cast<char*>(prdVerRaw), sizeof(prdVerRaw));
    outInfo.product_version = DecodeUtf16OrAscii(prdVerRaw, sizeof(prdVerRaw));
    if (outInfo.product_version.empty()) {
        outInfo.product_version = "Unknown";
    }

    // 4. File Count
    uint32_t fileCount = 0;
    static const uint64_t countOffsets[] = { 2096, 2100, 2124 };
    for (uint64_t off : countOffsets) {
        if (off + 4 <= fileSize) {
            file.seekg(off, std::ios::beg);
            uint8_t cBuf[4];
            file.read(reinterpret_cast<char*>(cBuf), 4);
            uint32_t cnt = ReadU32LE(cBuf);
            if (cnt > 0 && cnt <= 256) {
                fileCount = cnt;
                break;
            }
        }
    }

    if (fileCount == 0 || fileCount > 256) {
        fileCount = 32; // Standard fallback estimate
    }

    // 5. File Entries (Starting offset 2124, entry size 2560 bytes)
    constexpr size_t ENTRY_SIZE = 2560;
    std::vector<uint8_t> entryBuf(ENTRY_SIZE);

    for (uint32_t i = 0; i < fileCount; ++i) {
        uint64_t entryStart = 2124 + (static_cast<uint64_t>(i) * ENTRY_SIZE);
        if (entryStart + ENTRY_SIZE > fileSize) break;

        file.seekg(entryStart, std::ios::beg);
        file.read(reinterpret_cast<char*>(entryBuf.data()), ENTRY_SIZE);
        if (file.gcount() < static_cast<std::streamsize>(ENTRY_SIZE)) break;

        // FileID (Partition name, 512 bytes UTF-16LE at offset 4)
        std::string fileId = DecodeUtf16OrAscii(entryBuf.data() + 4, 512);

        // FileName (Image name, 512 bytes UTF-16LE at offset 516)
        std::string fileName = DecodeUtf16OrAscii(entryBuf.data() + 516, 512);

        if (fileId.empty()) {
            continue;
        }

        // Offset 1128 contains: nFileSize(4), nFileFlag(4), nCheckFlag(4), dwDataOffset(4)
        const uint8_t* sizeMeta = entryBuf.data() + 1128;
        uint32_t nFileSize = ReadU32LE(sizeMeta + 0);
        uint32_t nFileFlag = ReadU32LE(sizeMeta + 4);
        uint32_t dwDataOffset = ReadU32LE(sizeMeta + 12);

        if (dwDataOffset < fileSize && nFileSize > 0) {
            SpdPacPartition part;
            part.name = fileId;
            part.filename = fileName.empty() ? (fileId + ".bin") : fileName;
            part.file_size = nFileSize;
            part.size_mb = static_cast<double>(nFileSize) / (1024.0 * 1024.0);
            part.data_offset = dwDataOffset;
            part.is_download = (nFileFlag != 0);
            part.is_checked = part.is_download && (nFileSize > 0);

            outInfo.partitions.push_back(part);
        }
    }

    outInfo.file_count = static_cast<uint32_t>(outInfo.partitions.size());
    return !outInfo.partitions.empty();
}

bool SpdPacParser::ExtractPartition(
    const std::string& pacPath,
    const SpdPacPartition& partition,
    std::vector<uint8_t>& outBuffer,
    std::string& outError
) {
    outBuffer.clear();
    std::ifstream file(pacPath, std::ios::binary);
    if (!file.is_open()) {
        outError = "Failed to open PAC file: " + pacPath;
        return false;
    }

    file.seekg(partition.data_offset, std::ios::beg);
    outBuffer.resize(partition.file_size);
    file.read(reinterpret_cast<char*>(outBuffer.data()), partition.file_size);

    if (file.gcount() != static_cast<std::streamsize>(partition.file_size)) {
        outError = "Read mismatch extracting partition " + partition.name;
        outBuffer.clear();
        return false;
    }

    return true;
}

std::string SpdPacParser::ToJson(const SpdPacInfo& info) {
    std::ostringstream ss;
    ss << "{";
    ss << "\"version\":\"" << info.version << "\",";
    ss << "\"product_name\":\"" << info.product_name << "\",";
    ss << "\"product_version\":\"" << info.product_version << "\",";
    ss << "\"file_count\":" << info.file_count << ",";
    ss << "\"partitions\":[";
    for (size_t i = 0; i < info.partitions.size(); ++i) {
        const auto& p = info.partitions[i];
        if (i > 0) ss << ",";
        ss << "{";
        ss << "\"name\":\"" << p.name << "\",";
        ss << "\"filename\":\"" << p.filename << "\",";
        ss << "\"file_size\":" << p.file_size << ",";
        ss << "\"size_mb\":" << std::fixed << std::setprecision(2) << p.size_mb << ",";
        ss << "\"data_offset\":" << p.data_offset << ",";
        ss << "\"is_download\":" << (p.is_download ? "true" : "false") << ",";
        ss << "\"is_checked\":" << (p.is_checked ? "true" : "false");
        ss << "}";
    }
    ss << "]}";
    return ss.str();
}

} // namespace BSLab
