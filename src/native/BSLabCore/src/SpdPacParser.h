#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

struct SpdPacPartition {
    std::string name;            // e.g. "FDL1", "FDL2", "boot", "recovery", "super"
    std::string filename;        // e.g. "fdl1.bin", "boot.img"
    uint64_t file_size{0};
    double size_mb{0.0};
    uint64_t data_offset{0};
    bool is_download{true};
    bool is_checked{true};
};

struct SpdPacInfo {
    std::string version;
    std::string product_name;
    std::string product_version;
    uint32_t file_count{0};
    std::vector<SpdPacPartition> partitions;
};

class SpdPacParser {
public:
    SpdPacParser() = default;
    ~SpdPacParser() = default;

    /**
     * Parses the header and partition entries from a Spreadtrum / Unisoc .PAC archive.
     * Header-only streaming parse: does NOT load multi-gigabyte payloads into RAM.
     */
    static bool Parse(const std::string& pacPath, SpdPacInfo& outInfo, std::string& outError);

    /**
     * Extracts a specific partition payload from the PAC archive into memory.
     */
    static bool ExtractPartition(
        const std::string& pacPath,
        const SpdPacPartition& partition,
        std::vector<uint8_t>& outBuffer,
        std::string& outError
    );

    /**
     * Serializes parsed PAC metadata and partitions to JSON for C# interop.
     */
    static std::string ToJson(const SpdPacInfo& info);

private:
    static std::string DecodeUtf16OrAscii(const uint8_t* data, size_t maxLen);
};

} // namespace BSLab
