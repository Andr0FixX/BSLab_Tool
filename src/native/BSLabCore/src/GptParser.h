#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

#pragma pack(push, 1)
// Standard UEFI / Android GPT Header (LBA 1, 92 bytes)
struct GptHeaderRaw {
    uint64_t signature;                    // 0x5452415020494645 ("EFI PART")
    uint32_t revision;                     // 0x00010000
    uint32_t header_size;                  // 92 bytes
    uint32_t header_crc32;
    uint32_t reserved;
    uint64_t my_lba;                       // 1
    uint64_t alternate_lba;                // Backup GPT LBA at disk end
    uint64_t first_usable_lba;             // Typically 34
    uint64_t last_usable_lba;
    uint8_t  disk_guid[16];
    uint64_t partition_entry_lba;          // Typically 2
    uint32_t num_partition_entries;        // Typically 128
    uint32_t sizeof_partition_entry;       // Typically 128 bytes
    uint32_t partition_entry_array_crc32;
};

// Standard GPT Partition Entry (128 bytes each, LBA 2..33)
struct GptEntryRaw {
    uint8_t  partition_type_guid[16];
    uint8_t  unique_partition_guid[16];
    uint64_t starting_lba;
    uint64_t ending_lba;
    uint64_t attributes;
    uint16_t partition_name[36];           // UTF-16LE Partition Name
};
#pragma pack(pop)

// Structured High-Level Representation for C# UI & Flasher
struct GptPartition {
    int index = 0;
    std::string name;
    uint64_t start_lba = 0;
    uint64_t end_lba = 0;
    uint64_t sector_count = 0;
    uint64_t size_bytes = 0;
    std::string size_str;                  // e.g. "4.25 GB", "64.0 MB"
    std::string type_guid;
    bool is_slot_a = false;
    bool is_slot_b = false;
};

class GptParser {
public:
    GptParser() = default;
    ~GptParser() = default;

    // Parse raw sector stream (typically 17KB = 34 sectors * 512 bytes)
    static bool Parse(const uint8_t* raw_buffer, size_t buffer_size, std::vector<GptPartition>& out_partitions, uint32_t sector_size = 512);

    // Format partition list as fast JSON string for C# WPF DataGrid binding
    static std::string ToJson(const std::vector<GptPartition>& partitions);

    // Search helper
    static const GptPartition* FindPartition(const std::vector<GptPartition>& partitions, const std::string& name);

    // Format human readable size (KB, MB, GB)
    static std::string FormatSize(uint64_t bytes);

private:
    static std::string Utf16ToAscii(const uint16_t* utf16_str, size_t max_chars);
    static std::string GuidToString(const uint8_t* guid_bytes);
};

} // namespace BSLab
