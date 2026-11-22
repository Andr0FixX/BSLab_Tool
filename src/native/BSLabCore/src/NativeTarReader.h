#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <functional>

namespace BSLab {

struct TarEntryInfo {
    std::string name;
    uint64_t size{0};
    double size_mb{0.0};
    bool is_lz4{false};
};

class NativeTarReader {
public:
    NativeTarReader() = default;
    ~NativeTarReader() = default;

    /**
     * Inspects a TAR or TAR.MD5 archive and returns file members list.
     * Header-only streaming parse: does not load payloads into RAM.
     */
    static bool InspectTar(const std::string& filePath, std::vector<TarEntryInfo>& outEntries, std::string& outError);

    /**
     * Streams a specific member file or sequential blocks directly to a chunk callback.
     */
    static bool StreamTarMember(
        const std::string& filePath,
        const std::string& memberName,
        std::function<bool(const uint8_t* chunk, size_t chunkSize)> chunkCallback,
        std::string& outError
    );

private:
    static uint64_t ParseOctal(const char* str, size_t maxLen);
};

} // namespace BSLab
