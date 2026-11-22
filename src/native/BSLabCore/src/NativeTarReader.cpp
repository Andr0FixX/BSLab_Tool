#include "NativeTarReader.h"
#include <fstream>
#include <cstring>
#include <algorithm>

namespace BSLab {

// POSIX standard ustar header structure (512 bytes)
#pragma pack(push, 1)
struct PosixTarHeader {
    char name[100];
    char mode[8];
    char uid[8];
    char gid[8];
    char size[12];
    char mtime[12];
    char chksum[8];
    char typeflag;
    char linkname[100];
    char magic[6];
    char version[2];
    char uname[32];
    char gname[32];
    char devmajor[8];
    char devminor[8];
    char prefix[155];
    char pad[12];
};
#pragma pack(pop)

static_assert(sizeof(PosixTarHeader) == 512, "TAR header must be exactly 512 bytes");

uint64_t NativeTarReader::ParseOctal(const char* str, size_t maxLen) {
    uint64_t val = 0;
    size_t i = 0;
    while (i < maxLen && (str[i] == ' ' || str[i] == '\0')) {
        i++;
    }
    for (; i < maxLen; ++i) {
        char c = str[i];
        if (c < '0' || c > '7') break;
        val = (val << 3) | (c - '0');
    }
    return val;
}

bool NativeTarReader::InspectTar(const std::string& filePath, std::vector<TarEntryInfo>& outEntries, std::string& outError) {
    outEntries.clear();
    std::ifstream file(filePath, std::ios::binary);
    if (!file.is_open()) {
        outError = "Failed to open TAR file: " + filePath;
        return false;
    }

    PosixTarHeader header;
    while (file.read(reinterpret_cast<char*>(&header), sizeof(header))) {
        // Check for end of archive (two consecutive blocks of zero bytes)
        bool allZero = true;
        const uint8_t* p = reinterpret_cast<const uint8_t*>(&header);
        for (size_t i = 0; i < sizeof(header); ++i) {
            if (p[i] != 0) {
                allZero = false;
                break;
            }
        }
        if (allZero) {
            break;
        }

        // Validate ustar magic or basic sanity
        std::string name(header.name, strnlen(header.name, sizeof(header.name)));
        if (name.empty()) {
            break;
        }

        uint64_t fileSize = ParseOctal(header.size, sizeof(header.size));

        // Prefix handling
        if (header.prefix[0] != '\0') {
            std::string prefix(header.prefix, strnlen(header.prefix, sizeof(header.prefix)));
            name = prefix + "/" + name;
        }

        TarEntryInfo entry;
        entry.name = name;
        entry.size = fileSize;
        entry.size_mb = static_cast<double>(fileSize) / (1024.0 * 1024.0);
        entry.is_lz4 = (name.length() >= 4 && name.substr(name.length() - 4) == ".lz4");

        outEntries.push_back(entry);

        // Skip to next 512-byte boundary
        uint64_t paddedSize = ((fileSize + 511) / 512) * 512;
        file.seekg(paddedSize, std::ios::cur);
        if (file.fail()) {
            break;
        }
    }

    return true;
}

bool NativeTarReader::StreamTarMember(
    const std::string& filePath,
    const std::string& memberName,
    std::function<bool(const uint8_t* chunk, size_t chunkSize)> chunkCallback,
    std::string& outError
) {
    std::ifstream file(filePath, std::ios::binary);
    if (!file.is_open()) {
        outError = "Failed to open TAR file: " + filePath;
        return false;
    }

    PosixTarHeader header;
    while (file.read(reinterpret_cast<char*>(&header), sizeof(header))) {
        bool allZero = true;
        const uint8_t* p = reinterpret_cast<const uint8_t*>(&header);
        for (size_t i = 0; i < sizeof(header); ++i) {
            if (p[i] != 0) { allZero = false; break; }
        }
        if (allZero) break;

        std::string name(header.name, strnlen(header.name, sizeof(header.name)));
        if (name.empty()) break;

        uint64_t fileSize = ParseOctal(header.size, sizeof(header.size));
        uint64_t paddedSize = ((fileSize + 511) / 512) * 512;

        if (name == memberName) {
            // Stream chunks
            constexpr size_t BUF_SIZE = 131072; // 128KB
            std::vector<uint8_t> buffer(BUF_SIZE);
            uint64_t remaining = fileSize;

            while (remaining > 0) {
                size_t toRead = static_cast<size_t>(std::min<uint64_t>(remaining, BUF_SIZE));
                file.read(reinterpret_cast<char*>(buffer.data()), toRead);
                std::streamsize bytesRead = file.gcount();
                if (bytesRead <= 0) {
                    outError = "Unexpected end of file while reading member: " + memberName;
                    return false;
                }

                if (!chunkCallback(buffer.data(), static_cast<size_t>(bytesRead))) {
                    outError = "Chunk callback requested abort";
                    return false;
                }

                remaining -= bytesRead;
            }
            return true;
        } else {
            file.seekg(paddedSize, std::ios::cur);
            if (file.fail()) break;
        }
    }

    outError = "Member not found in archive: " + memberName;
    return false;
}

} // namespace BSLab
