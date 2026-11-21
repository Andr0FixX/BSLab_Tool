#include "GptParser.h"
#include <cstring>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace BSLab {

std::string GptParser::Utf16ToAscii(const uint16_t* utf16_str, size_t max_chars) {
    std::string res;
    for (size_t i = 0; i < max_chars; ++i) {
        uint16_t c = utf16_str[i];
        if (c == 0) break; // Null terminator
        if (c < 128) {
            res.push_back(static_cast<char>(c));
        } else {
            res.push_back('?');
        }
    }
    return res;
}

std::string GptParser::GuidToString(const uint8_t* g) {
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    // Data1 (4B LE)
    ss << std::setw(2) << (int)g[3] << std::setw(2) << (int)g[2] << std::setw(2) << (int)g[1] << std::setw(2) << (int)g[0] << "-";
    // Data2 (2B LE)
    ss << std::setw(2) << (int)g[5] << std::setw(2) << (int)g[4] << "-";
    // Data3 (2B LE)
    ss << std::setw(2) << (int)g[7] << std::setw(2) << (int)g[6] << "-";
    // Data4 (2B BE)
    ss << std::setw(2) << (int)g[8] << std::setw(2) << (int)g[9] << "-";
    // Data5 (6B BE)
    for (int i = 10; i < 16; ++i) {
        ss << std::setw(2) << (int)g[i];
    }
    return ss.str();
}

std::string GptParser::FormatSize(uint64_t bytes) {
    std::stringstream ss;
    ss << std::fixed << std::setprecision(2);
    if (bytes >= (1024ULL * 1024ULL * 1024ULL)) {
        double gb = static_cast<double>(bytes) / (1024.0 * 1024.0 * 1024.0);
        ss << gb << " GB";
    } else if (bytes >= (1024ULL * 1024ULL)) {
        double mb = static_cast<double>(bytes) / (1024.0 * 1024.0);
        ss << mb << " MB";
    } else if (bytes >= 1024ULL) {
        double kb = static_cast<double>(bytes) / 1024.0;
        ss << kb << " KB";
    } else {
        ss << bytes << " Bytes";
    }
    return ss.str();
}

bool GptParser::Parse(const uint8_t* raw_buffer, size_t buffer_size, std::vector<GptPartition>& out_partitions, uint32_t sector_size) {
    out_partitions.clear();

    // LBA 1 begins at sector_size (typically offset 512)
    size_t header_offset = sector_size;
    if (buffer_size < header_offset + sizeof(GptHeaderRaw)) {
        return false;
    }

    const GptHeaderRaw* header = reinterpret_cast<const GptHeaderRaw*>(raw_buffer + header_offset);

    // Verify "EFI PART" signature: 0x5452415020494645ULL
    if (header->signature != 0x5452415020494645ULL) {
        return false;
    }

    uint32_t num_entries = header->num_partition_entries;
    uint32_t entry_size = header->sizeof_partition_entry;
    if (entry_size < sizeof(GptEntryRaw) || num_entries == 0 || num_entries > 512) {
        return false;
    }

    // Partition array begins at partition_entry_lba (typically LBA 2 = offset 1024)
    size_t entries_offset = static_cast<size_t>(header->partition_entry_lba * sector_size);
    if (buffer_size < entries_offset + (num_entries * entry_size)) {
        return false;
    }

    int part_index = 0;
    for (uint32_t i = 0; i < num_entries; ++i) {
        const uint8_t* entry_ptr = raw_buffer + entries_offset + (i * entry_size);
        const GptEntryRaw* raw_entry = reinterpret_cast<const GptEntryRaw*>(entry_ptr);

        // Check if entry is unused (Type GUID all zeros)
        bool is_empty = true;
        for (int b = 0; b < 16; ++b) {
            if (raw_entry->partition_type_guid[b] != 0) {
                is_empty = false;
                break;
            }
        }
        if (is_empty) continue;

        GptPartition part;
        part.index = part_index++;
        part.name = Utf16ToAscii(raw_entry->partition_name, 36);
        part.start_lba = raw_entry->starting_lba;
        part.end_lba = raw_entry->ending_lba;
        part.sector_count = (part.end_lba >= part.start_lba) ? (part.end_lba - part.start_lba + 1) : 0;
        part.size_bytes = part.sector_count * sector_size;
        part.size_str = FormatSize(part.size_bytes);
        part.type_guid = GuidToString(raw_entry->partition_type_guid);

        // Slot Awareness detection (e.g. boot_a vs boot_b)
        if (part.name.length() > 2) {
            if (part.name.rfind("_a") == part.name.length() - 2) {
                part.is_slot_a = true;
            } else if (part.name.rfind("_b") == part.name.length() - 2) {
                part.is_slot_b = true;
            }
        }

        out_partitions.push_back(part);
    }

    return !out_partitions.empty();
}

std::string GptParser::ToJson(const std::vector<GptPartition>& partitions) {
    std::stringstream ss;
    ss << "[\n";
    for (size_t i = 0; i < partitions.size(); ++i) {
        const auto& p = partitions[i];
        ss << "  {\n"
           << "    \"index\": " << p.index << ",\n"
           << "    \"name\": \"" << p.name << "\",\n"
           << "    \"start_lba\": " << p.start_lba << ",\n"
           << "    \"end_lba\": " << p.end_lba << ",\n"
           << "    \"sector_count\": " << p.sector_count << ",\n"
           << "    \"size_bytes\": " << p.size_bytes << ",\n"
           << "    \"size_str\": \"" << p.size_str << "\",\n"
           << "    \"is_slot_a\": " << (p.is_slot_a ? "true" : "false") << ",\n"
           << "    \"is_slot_b\": " << (p.is_slot_b ? "true" : "false") << "\n"
           << "  }" << (i + 1 < partitions.size() ? "," : "") << "\n";
    }
    ss << "]";
    return ss.str();
}

const GptPartition* GptParser::FindPartition(const std::vector<GptPartition>& partitions, const std::string& name) {
    for (const auto& p : partitions) {
        if (p.name == name) return &p;
    }
    return nullptr;
}

} // namespace BSLab
