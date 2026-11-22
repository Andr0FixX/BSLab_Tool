#include "SamsungPitReader.h"
#include <fstream>
#include <cstring>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace BSLab {

static inline uint32_t ReadU32LE(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
          (static_cast<uint32_t>(p[1]) << 8) |
          (static_cast<uint32_t>(p[2]) << 16) |
          (static_cast<uint32_t>(p[3]) << 24);
}

static inline uint32_t ReadU32BE(const uint8_t* p) {
    return (static_cast<uint32_t>(p[0]) << 24) |
           (static_cast<uint32_t>(p[1]) << 16) |
           (static_cast<uint32_t>(p[2]) << 8) |
            static_cast<uint32_t>(p[3]);
}

bool SamsungPitReader::ParsePitBytes(
    const uint8_t* data,
    size_t length,
    std::vector<SamsungNativePitEntry>& outEntries,
    std::string& outError
) {
    outEntries.clear();
    if (!data || length < 28) {
        outError = "PIT data too short (< 28 bytes)";
        return false;
    }

    uint32_t magic = ReadU32LE(data);
    bool isBigEndian = false;

    if (magic != PIT_MAGIC_SIG && magic != PIT_MAGIC_LE_SIG) {
        uint32_t magicBe = ReadU32BE(data);
        if (magicBe == PIT_MAGIC_SIG) {
            isBigEndian = true;
        } else {
            // Check fallback string scan
            auto fallback = ParsePitStringsFallback(data, length);
            if (!fallback.empty()) {
                outEntries = std::move(fallback);
                return true;
            }
            std::ostringstream ss;
            ss << "Invalid PIT Magic: 0x" << std::hex << magic << " (expected 0x12349876)";
            outError = ss.str();
            return false;
        }
    }

    uint32_t entryCount = isBigEndian ? ReadU32BE(data + 4) : ReadU32LE(data + 4);
    if (entryCount <= 0 || entryCount > 256) {
        entryCount = isBigEndian ? ReadU32BE(data + 8) : ReadU32LE(data + 8);
        entryCount = std::min<uint32_t>(128, std::max<uint32_t>(1, entryCount));
    }

    size_t offset = 28; // Standard Samsung PIT header size
    size_t entrySize = 132;
    if (length >= 28 + entryCount * 136) {
        entrySize = 136;
    }

    while (offset + entrySize <= length && outEntries.size() < entryCount) {
        const uint8_t* block = data + offset;

        uint32_t bType = isBigEndian ? ReadU32BE(block + 0) : ReadU32LE(block + 0);
        uint32_t dType = isBigEndian ? ReadU32BE(block + 4) : ReadU32LE(block + 4);
        uint32_t pId   = isBigEndian ? ReadU32BE(block + 8) : ReadU32LE(block + 8);
        uint32_t pType = isBigEndian ? ReadU32BE(block + 12) : ReadU32LE(block + 12);

        // Partition name (up to 32 chars)
        char nameBuf[33] = {0};
        std::memcpy(nameBuf, block + 16, 32);
        std::string partName(nameBuf);
        while (!partName.empty() && (partName.back() == '\0' || partName.back() == ' ')) {
            partName.pop_back();
        }

        // Filename (up to 32 chars)
        char fnBuf[33] = {0};
        std::memcpy(fnBuf, block + 48, 32);
        std::string fileName(fnBuf);
        while (!fileName.empty() && (fileName.back() == '\0' || fileName.back() == ' ')) {
            fileName.pop_back();
        }

        uint32_t blkStart = isBigEndian ? ReadU32BE(block + 80) : ReadU32LE(block + 80);
        uint32_t blkCount = isBigEndian ? ReadU32BE(block + 84) : ReadU32LE(block + 84);

        if (!partName.empty()) {
            SamsungNativePitEntry entry;
            entry.binary_type = bType;
            entry.device_type = dType;
            entry.partition_id = pId;
            entry.partition_type = pType;
            entry.partition_name = partName;

            if (fileName.empty()) {
                std::string lowerName = partName;
                std::transform(lowerName.begin(), lowerName.end(), lowerName.begin(), ::tolower);
                entry.flash_filename = lowerName + ".img";
            } else {
                entry.flash_filename = fileName;
            }

            entry.block_start = blkStart;
            entry.block_count = blkCount;
            entry.size_mb = (static_cast<double>(blkCount) * 512.0) / (1024.0 * 1024.0);
            entry.filesystem = (pType == 0) ? "Raw / Binary" : (pType == 2 ? "EXT4 / F2FS" : "Partition");

            outEntries.push_back(entry);
        }

        offset += entrySize;
    }

    if (outEntries.empty()) {
        outEntries = ParsePitStringsFallback(data, length);
    }

    return !outEntries.empty();
}

bool SamsungPitReader::ParsePitFile(
    const std::string& filePath,
    std::vector<SamsungNativePitEntry>& outEntries,
    std::string& outError
) {
    std::ifstream file(filePath, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        outError = "PIT file not found: " + filePath;
        return false;
    }

    std::streamsize size = file.tellg();
    if (size <= 0) {
        outError = "PIT file is empty: " + filePath;
        return false;
    }

    file.seekg(0, std::ios::beg);
    std::vector<uint8_t> buffer(static_cast<size_t>(size));
    if (!file.read(reinterpret_cast<char*>(buffer.data()), size)) {
        outError = "Failed to read PIT file contents: " + filePath;
        return false;
    }

    return ParsePitBytes(buffer.data(), buffer.size(), outEntries, outError);
}

std::vector<SamsungNativePitEntry> SamsungPitReader::ParsePitStringsFallback(const uint8_t* data, size_t length) {
    std::vector<SamsungNativePitEntry> list;
    if (!data || length == 0) return list;

    static const char* knownParts[] = {
        "BOOT", "RECOVERY", "SYSTEM", "USERDATA", "CACHE", "EFS", "RADIO",
        "PARAM", "PERSISTENT", "MISC", "MODEM", "SUPER", "DTBO", "VBMETA"
    };

    uint32_t idx = 1;
    for (const char* part : knownParts) {
        size_t pLen = std::strlen(part);
        for (size_t i = 0; i + pLen <= length; ++i) {
            if (std::memcmp(data + i, part, pLen) == 0) {
                SamsungNativePitEntry entry;
                entry.binary_type = 0;
                entry.device_type = 2; // eMMC/UFS
                entry.partition_id = idx;
                entry.partition_type = 0;
                entry.partition_name = part;

                std::string lower = part;
                std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
                entry.flash_filename = lower + ".img";
                entry.block_start = idx * 0x8000;
                entry.block_count = 0x10000; // 32MB default chunk
                entry.size_mb = (static_cast<double>(entry.block_count) * 512.0) / (1024.0 * 1024.0);
                entry.filesystem = "EXT4 / Raw";

                list.push_back(entry);
                idx++;
                break;
            }
        }
    }
    return list;
}

std::string SamsungPitReader::ToJson(const std::vector<SamsungNativePitEntry>& entries) {
    std::ostringstream ss;
    ss << "[";
    for (size_t i = 0; i < entries.size(); ++i) {
        const auto& e = entries[i];
        if (i > 0) ss << ",";
        ss << "{";
        ss << "\"index\":" << (i + 1) << ",";
        ss << "\"name\":\"" << e.partition_name << "\",";
        ss << "\"filename\":\"" << e.flash_filename << "\",";
        ss << "\"binary_type\":" << e.binary_type << ",";
        ss << "\"device_type\":" << e.device_type << ",";
        ss << "\"partition_id\":" << e.partition_id << ",";
        ss << "\"partition_type\":" << e.partition_type << ",";
        ss << "\"block_start\":" << e.block_start << ",";
        ss << "\"block_count\":" << e.block_count << ",";
        ss << "\"size_mb\":" << std::fixed << std::setprecision(2) << e.size_mb << ",";
        ss << "\"filesystem\":\"" << e.filesystem << "\"";
        ss << "}";
    }
    ss << "]";
    return ss.str();
}

} // namespace BSLab
