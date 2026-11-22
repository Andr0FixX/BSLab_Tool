#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

constexpr uint32_t PIT_MAGIC_SIG = 0x12349876;
constexpr uint32_t PIT_MAGIC_LE_SIG = 0x76983412;

struct SamsungNativePitEntry {
    uint32_t binary_type{0};
    uint32_t device_type{0};
    uint32_t partition_id{0};
    uint32_t partition_type{0};
    std::string partition_name;
    std::string flash_filename;
    uint32_t block_start{0};
    uint32_t block_count{0};
    double size_mb{0.0};
    std::string filesystem;
};

class SamsungPitReader {
public:
    SamsungPitReader() = default;
    ~SamsungPitReader() = default;

    /**
     * Parses raw PIT binary data into structured partition entries.
     */
    static bool ParsePitBytes(
        const uint8_t* data,
        size_t length,
        std::vector<SamsungNativePitEntry>& outEntries,
        std::string& outError
    );

    /**
     * Parses a PIT file directly from disk.
     */
    static bool ParsePitFile(
        const std::string& filePath,
        std::vector<SamsungNativePitEntry>& outEntries,
        std::string& outError
    );

    /**
     * Serializes partition entries to a JSON string for C# interop.
     */
    static std::string ToJson(const std::vector<SamsungNativePitEntry>& entries);

private:
    static std::vector<SamsungNativePitEntry> ParsePitStringsFallback(const uint8_t* data, size_t length);
};

} // namespace BSLab
