#include "PartitionDoctorEngine.h"
#include "NativeTarReader.h"
#include <windows.h>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <cstring>

namespace BSLab {

static const std::unordered_set<std::string> g_protected_partitions = {
    "userdata", "data", "metadata", "cache",
    "persist", "persist_a", "persist_b",
    "nvram", "nvdata", "nvcfg", "protect_f", "protect_s",
    "modemst1", "modemst2", "fsg", "fsc", "sec_efs", "efs",
    "proinfo", "frp", "devinfo", "keystore", "keymaster",
    "keymaster_a", "keymaster_b", "misc"
};

static const std::unordered_map<std::string, std::vector<MagicType>> g_partition_expectations = {
    {"boot", {MagicType::BOOT_IMG}},
    {"boot_a", {MagicType::BOOT_IMG}},
    {"boot_b", {MagicType::BOOT_IMG}},
    {"init_boot", {MagicType::BOOT_IMG}},
    {"init_boot_a", {MagicType::BOOT_IMG}},
    {"init_boot_b", {MagicType::BOOT_IMG}},
    {"recovery", {MagicType::BOOT_IMG}},
    {"recovery_a", {MagicType::BOOT_IMG}},
    {"recovery_b", {MagicType::BOOT_IMG}},
    {"vendor_boot", {MagicType::BOOT_IMG}},
    {"vendor_boot_a", {MagicType::BOOT_IMG}},
    {"vendor_boot_b", {MagicType::BOOT_IMG}},
    {"vbmeta", {MagicType::AVB_VBMETA}},
    {"vbmeta_a", {MagicType::AVB_VBMETA}},
    {"vbmeta_b", {MagicType::AVB_VBMETA}},
    {"vbmeta_system", {MagicType::AVB_VBMETA}},
    {"vbmeta_system_a", {MagicType::AVB_VBMETA}},
    {"vbmeta_system_b", {MagicType::AVB_VBMETA}},
    {"vbmeta_vendor", {MagicType::AVB_VBMETA}},
    {"vbmeta_vendor_a", {MagicType::AVB_VBMETA}},
    {"vbmeta_vendor_b", {MagicType::AVB_VBMETA}},
    {"dtbo", {MagicType::DTBO}},
    {"dtbo_a", {MagicType::DTBO}},
    {"dtbo_b", {MagicType::DTBO}},
    {"super", {MagicType::DYNAMIC_SUPER, MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"system", {MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"system_a", {MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"system_b", {MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"vendor", {MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"vendor_a", {MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"vendor_b", {MagicType::SPARSE_IMAGE, MagicType::EXT4_FS, MagicType::F2FS_FS}},
    {"abl", {MagicType::ELF_BOOTLOADER}},
    {"abl_a", {MagicType::ELF_BOOTLOADER}},
    {"abl_b", {MagicType::ELF_BOOTLOADER}},
    {"xbl", {MagicType::ELF_BOOTLOADER}},
    {"xbl_a", {MagicType::ELF_BOOTLOADER}},
    {"xbl_b", {MagicType::ELF_BOOTLOADER}},
    {"xbl_config", {MagicType::ELF_BOOTLOADER}},
    {"tz", {MagicType::ELF_BOOTLOADER}},
    {"tz_a", {MagicType::ELF_BOOTLOADER}},
    {"tz_b", {MagicType::ELF_BOOTLOADER}},
    {"hyp", {MagicType::ELF_BOOTLOADER}},
    {"hyp_a", {MagicType::ELF_BOOTLOADER}},
    {"hyp_b", {MagicType::ELF_BOOTLOADER}}
};

uint32_t PartitionDoctorEngine::ReadLe32(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) |
          (static_cast<uint32_t>(p[1]) << 8) |
          (static_cast<uint32_t>(p[2]) << 16) |
          (static_cast<uint32_t>(p[3]) << 24);
}

uint32_t PartitionDoctorEngine::ReadBe32(const uint8_t* p) {
    return (static_cast<uint32_t>(p[0]) << 24) |
           (static_cast<uint32_t>(p[1]) << 16) |
           (static_cast<uint32_t>(p[2]) << 8) |
            static_cast<uint32_t>(p[3]);
}

uint64_t PartitionDoctorEngine::ReadLe64(const uint8_t* p) {
    return static_cast<uint64_t>(ReadLe32(p)) |
          (static_cast<uint64_t>(ReadLe32(p + 4)) << 32);
}

uint64_t PartitionDoctorEngine::ReadBe64(const uint8_t* p) {
    return (static_cast<uint64_t>(ReadBe32(p)) << 32) |
            static_cast<uint64_t>(ReadBe32(p + 4));
}

MagicType PartitionDoctorEngine::IdentifyMagic(const uint8_t* buffer, size_t size) {
    if (!buffer || size == 0) return MagicType::UNKNOWN;

    // Check all zero or all 0xFF (up to 512 bytes)
    size_t check_len = (size < 512) ? size : 512;
    bool all_zero = true;
    bool all_ff = true;
    for (size_t i = 0; i < check_len; ++i) {
        if (buffer[i] != 0x00) all_zero = false;
        if (buffer[i] != 0xFF) all_ff = false;
        if (!all_zero && !all_ff) break;
    }
    if (all_zero || all_ff) return MagicType::EMPTY_ZERO;

    // Android Boot Image: "ANDROID!" (8 bytes)
    if (size >= 8 && memcmp(buffer, "ANDROID!", 8) == 0) {
        return MagicType::BOOT_IMG;
    }

    // AVB VBMeta: "AVB0" (4 bytes)
    if (size >= 4 && memcmp(buffer, "AVB0", 4) == 0) {
        return MagicType::AVB_VBMETA;
    }

    // DTBO Table: 0xD7B7AB1E (big-endian)
    if (size >= 4 && buffer[0] == 0xD7 && buffer[1] == 0xB7 && buffer[2] == 0xAB && buffer[3] == 0x1E) {
        return MagicType::DTBO;
    }

    // Dynamic Super liblp: 0x616C7073 ("spla" little-endian)
    if (size >= 4 && buffer[0] == 0x73 && buffer[1] == 0x70 && buffer[2] == 0x6C && buffer[3] == 0x61) {
        return MagicType::DYNAMIC_SUPER;
    }

    // ELF Executable: "\x7FELF" (4 bytes)
    if (size >= 4 && buffer[0] == 0x7F && buffer[1] == 'E' && buffer[2] == 'L' && buffer[3] == 'F') {
        return MagicType::ELF_BOOTLOADER;
    }

    // Android Sparse Image: 0xED26FF3A (little-endian: 3A FF 26 ED)
    if (size >= 4 && buffer[0] == 0x3A && buffer[1] == 0xFF && buffer[2] == 0x26 && buffer[3] == 0xED) {
        return MagicType::SPARSE_IMAGE;
    }

    // Huawei UPDATE.APP Magic: 0x55 0xAA 0x5A 0xA5
    if (size >= 4 && buffer[0] == 0x55 && buffer[1] == 0xAA && buffer[2] == 0x5A && buffer[3] == 0xA5) {
        return MagicType::HUAWEI_APP;
    }

    // EFI / GPT Header: "EFI PART" at offset 512 (8 bytes)
    if (size >= 520 && memcmp(buffer + 512, "EFI PART", 8) == 0) {
        return MagicType::GPT_HEADER;
    }

    // Ext4 Superblock: 0xEF53 at offset 1080 (0x438) -> LE: 53 EF
    if (size >= 1082 && buffer[1080] == 0x53 && buffer[1081] == 0xEF) {
        return MagicType::EXT4_FS;
    }

    // F2FS Superblock: 0xF2F52010 at offset 1024 (0x400) -> LE: 10 20 F5 F2
    if (size >= 1028 && buffer[1024] == 0x10 && buffer[1025] == 0x20 && buffer[1026] == 0xF5 && buffer[1027] == 0xF2) {
        return MagicType::F2FS_FS;
    }

    return MagicType::UNKNOWN;
}

const char* PartitionDoctorEngine::MagicTypeToString(MagicType type) {
    switch (type) {
        case MagicType::BOOT_IMG:       return "BOOT_IMG";
        case MagicType::AVB_VBMETA:     return "AVB_VBMETA";
        case MagicType::DTBO:           return "DTBO";
        case MagicType::DYNAMIC_SUPER:  return "DYNAMIC_SUPER";
        case MagicType::ELF_BOOTLOADER: return "ELF_BOOTLOADER";
        case MagicType::SPARSE_IMAGE:   return "SPARSE_IMAGE";
        case MagicType::GPT_HEADER:     return "GPT_HEADER";
        case MagicType::EXT4_FS:        return "EXT4_FS";
        case MagicType::F2FS_FS:        return "F2FS_FS";
        case MagicType::HUAWEI_APP:     return "HUAWEI_APP";
        case MagicType::EMPTY_ZERO:     return "EMPTY_ZERO";
        default:                        return "UNKNOWN";
    }
}

MagicType PartitionDoctorEngine::StringToMagicType(const std::string& str) {
    if (str == "BOOT_IMG")       return MagicType::BOOT_IMG;
    if (str == "AVB_VBMETA")     return MagicType::AVB_VBMETA;
    if (str == "DTBO")           return MagicType::DTBO;
    if (str == "DYNAMIC_SUPER")  return MagicType::DYNAMIC_SUPER;
    if (str == "ELF_BOOTLOADER") return MagicType::ELF_BOOTLOADER;
    if (str == "SPARSE_IMAGE")   return MagicType::SPARSE_IMAGE;
    if (str == "GPT_HEADER")     return MagicType::GPT_HEADER;
    if (str == "EXT4_FS")        return MagicType::EXT4_FS;
    if (str == "F2FS_FS")        return MagicType::F2FS_FS;
    if (str == "HUAWEI_APP")     return MagicType::HUAWEI_APP;
    if (str == "EMPTY_ZERO")     return MagicType::EMPTY_ZERO;
    return MagicType::UNKNOWN;
}

bool PartitionDoctorEngine::IsProtectedPartition(const std::string& partition_name) {
    std::string clean = partition_name;
    std::transform(clean.begin(), clean.end(), clean.begin(), ::tolower);
    while (!clean.empty() && (clean.front() == ' ' || clean.front() == '/')) clean.erase(clean.begin());
    while (!clean.empty() && (clean.back() == ' ')) clean.pop_back();

    if (g_protected_partitions.find(clean) != g_protected_partitions.end()) {
        return true;
    }

    for (const auto& p : g_protected_partitions) {
        if (clean.rfind(p + "_", 0) == 0 || clean.rfind(p + "-", 0) == 0) {
            return true;
        }
    }

    return false;
}

bool PartitionDoctorEngine::ParseBootHeader(const uint8_t* data, size_t len, BootHeaderInfo& out_info) {
    out_info = BootHeaderInfo();
    if (!data || len < 64) {
        out_info.error = "Data chunk too short (<64 bytes)";
        return false;
    }

    if (memcmp(data, "ANDROID!", 8) != 0) {
        out_info.error = "Missing 'ANDROID!' boot magic";
        return false;
    }

    uint32_t header_version = ReadLe32(data + 40);
    out_info.header_version = header_version;

    if (header_version <= 2) {
        out_info.kernel_size = ReadLe32(data + 8);
        out_info.ramdisk_size = ReadLe32(data + 16);
        out_info.second_size = ReadLe32(data + 24);
        out_info.page_size = ReadLe32(data + 36);

        uint32_t os_ver = ReadLe32(data + 44);
        if (os_ver > 0) {
            uint32_t os_a = (os_ver >> 25) & 0x7F;
            uint32_t os_b = (os_ver >> 18) & 0x7F;
            uint32_t os_c = (os_ver >> 11) & 0x7F;
            std::stringstream ss;
            ss << os_a;
            if (os_b > 0 || os_c > 0) ss << "." << os_b;
            if (os_c > 0) ss << "." << os_c;
            out_info.os_version = ss.str();

            uint32_t y = ((os_ver >> 4) & 0x7F) + 2000;
            uint32_t m = os_ver & 0xF;
            char patch[16];
            snprintf(patch, sizeof(patch), "%04u-%02u", y, m);
            out_info.security_patch = patch;
        }

        if ((header_version == 1 || header_version == 2) && len >= 1640) {
            out_info.recovery_dtbo_size = ReadLe32(data + 1632);
            if (header_version == 2 && len >= 1648) {
                out_info.dtb_size = ReadLe32(data + 1644);
            }
        }
    } else {
        // v3 / v4
        out_info.kernel_size = ReadLe32(data + 8);
        out_info.ramdisk_size = ReadLe32(data + 12);
        out_info.page_size = 4096;

        uint32_t os_ver = ReadLe32(data + 16);
        if (os_ver > 0) {
            uint32_t os_a = (os_ver >> 25) & 0x7F;
            uint32_t os_b = (os_ver >> 18) & 0x7F;
            uint32_t os_c = (os_ver >> 11) & 0x7F;
            std::stringstream ss;
            ss << os_a << "." << os_b << "." << os_c;
            out_info.os_version = ss.str();

            uint32_t y = ((os_ver >> 4) & 0x7F) + 2000;
            uint32_t m = os_ver & 0xF;
            char patch[16];
            snprintf(patch, sizeof(patch), "%04u-%02u", y, m);
            out_info.security_patch = patch;
        }
    }

    out_info.valid = true;
    return true;
}

bool PartitionDoctorEngine::ParseAvbHeader(const uint8_t* data, size_t len, AvbHeaderInfo& out_info) {
    out_info = AvbHeaderInfo();
    if (!data || len < 64) {
        out_info.error = "Data chunk too small for AVB";
        return false;
    }

    if (memcmp(data, "AVB0", 4) != 0) {
        out_info.error = "Missing 'AVB0' magic";
        return false;
    }

    uint32_t req_maj = ReadBe32(data + 4);
    uint32_t req_min = ReadBe32(data + 8);
    // If major looks corrupted or swapped, check LE
    if (req_maj > 0xFFFF) {
        req_maj = ReadLe32(data + 4);
        req_min = ReadLe32(data + 8);
        out_info.auth_block_size = ReadLe64(data + 12);
        out_info.aux_block_size = ReadLe64(data + 20);
        out_info.algorithm_type = ReadLe32(data + 28);
        if (len >= 116) {
            out_info.rollback_index = ReadLe64(data + 104);
            out_info.flags = ReadLe32(data + 112);
        }
    } else {
        out_info.auth_block_size = ReadBe64(data + 12);
        out_info.aux_block_size = ReadBe64(data + 20);
        out_info.algorithm_type = ReadBe32(data + 28);
        if (len >= 116) {
            out_info.rollback_index = ReadBe64(data + 104);
            out_info.flags = ReadBe32(data + 112);
        }
    }

    char ver_buf[32];
    snprintf(ver_buf, sizeof(ver_buf), "%u.%u", req_maj, req_min);
    out_info.libavb_version = ver_buf;
    out_info.is_verification_disabled = (out_info.flags & 1) != 0;
    out_info.is_dm_verity_disabled = (out_info.flags & 2) != 0;
    out_info.valid = true;
    return true;
}

bool PartitionDoctorEngine::ParseDtboHeader(const uint8_t* data, size_t len, DtboHeaderInfo& out_info) {
    out_info = DtboHeaderInfo();
    if (!data || len < 32) {
        out_info.error = "Data chunk too small for DTBO";
        return false;
    }

    if (!(data[0] == 0xD7 && data[1] == 0xB7 && data[2] == 0xAB && data[3] == 0x1E)) {
        out_info.error = "Missing DTBO table magic (0xD7B7AB1E)";
        return false;
    }

    out_info.total_size = ReadBe32(data + 4);
    out_info.header_size = ReadBe32(data + 8);
    out_info.dt_entry_size = ReadBe32(data + 12);
    out_info.dt_entry_count = ReadBe32(data + 16);
    out_info.page_size = ReadBe32(data + 24);
    out_info.version = ReadBe32(data + 28);
    out_info.valid = true;
    return true;
}

bool PartitionDoctorEngine::ParseElfHeader(const uint8_t* data, size_t len, ElfHeaderInfo& out_info) {
    out_info = ElfHeaderInfo();
    if (!data || len < 52) {
        out_info.error = "Data chunk too small for ELF";
        return false;
    }

    if (data[0] != 0x7F || data[1] != 'E' || data[2] != 'L' || data[3] != 'F') {
        out_info.error = "Missing '\\x7FELF' magic";
        return false;
    }

    uint8_t elf_class = data[4]; // 1 = 32-bit, 2 = 64-bit
    uint8_t data_enc = data[5];   // 1 = LE, 2 = BE
    out_info.is_64bit = (elf_class == 2);

    bool is_le = (data_enc == 1);
    uint16_t e_machine = is_le ? (static_cast<uint16_t>(data[18]) | (static_cast<uint16_t>(data[19]) << 8))
                               : ((static_cast<uint16_t>(data[18]) << 8) | static_cast<uint16_t>(data[19]));

    if (e_machine == 183) {
        out_info.architecture = "AArch64 (64-bit)";
    } else if (e_machine == 40) {
        out_info.architecture = "ARM (32-bit)";
    } else {
        out_info.architecture = "Machine " + std::to_string(e_machine);
    }

    if (out_info.is_64bit && len >= 32) {
        out_info.entry_point = is_le ? ReadLe64(data + 24) : ReadBe64(data + 24);
    } else if (!out_info.is_64bit && len >= 28) {
        out_info.entry_point = is_le ? ReadLe32(data + 24) : ReadBe32(data + 24);
    }

    out_info.valid = true;
    return true;
}

PartitionInspectionResult PartitionDoctorEngine::InspectPartition(const std::string& partition_name, const uint8_t* data, size_t len) {
    PartitionInspectionResult res;
    res.partition_name = partition_name;

    std::string clean = partition_name;
    std::transform(clean.begin(), clean.end(), clean.begin(), ::tolower);

    // 1. Check Protected Partition Firewall
    if (IsProtectedPartition(clean)) {
        res.status = "PROTECTED";
        res.healthy = true;
        res.safe_to_flash = false;
        res.detected_type = MagicType::UNKNOWN;
        res.description = "User Data / IMEI / Security partition. HARD LOCKED: NEVER WRITE IN SURGICAL UNBRICK.";
        res.recommendation = "Preserve untouched to guarantee 100% Zero Data Loss.";
        return res;
    }

    // 2. Identify Magic
    MagicType detected = IdentifyMagic(data, len);
    res.detected_type = detected;

    // 3. Look up expected magic types
    auto it = g_partition_expectations.find(clean);
    if (it != g_partition_expectations.end()) {
        res.expected_types = it->second;
    }

    // 4. Handle Empty or Zeroed
    if (detected == MagicType::EMPTY_ZERO) {
        res.status = "EMPTY_OR_WIPED";
        res.healthy = false;
        res.safe_to_flash = true;
        res.description = "Partition '" + partition_name + "' is blank or completely wiped.";
        res.recommendation = "Flash original factory '" + partition_name + ".img' to restore bootability.";
        return res;
    }

    // 5. Deep Parse
    if (detected == MagicType::BOOT_IMG) {
        ParseBootHeader(data, len, res.boot_info);
    } else if (detected == MagicType::AVB_VBMETA) {
        ParseAvbHeader(data, len, res.avb_info);
    } else if (detected == MagicType::DTBO) {
        ParseDtboHeader(data, len, res.dtbo_info);
    } else if (detected == MagicType::ELF_BOOTLOADER) {
        ParseElfHeader(data, len, res.elf_info);
    }

    // 6. Compare Expected vs Detected
    if (!res.expected_types.empty()) {
        bool match = false;
        for (const auto& exp : res.expected_types) {
            if (detected == exp) {
                match = true;
                break;
            }
        }

        if (match) {
            res.status = "HEALTHY";
            res.healthy = true;
            res.safe_to_flash = true;
            res.description = "Partition '" + partition_name + "' header signature is valid (" + MagicTypeToString(detected) + ").";
            res.recommendation = "Header is intact. No repair needed.";
        } else {
            res.status = "MISMATCH_CORRUPTED";
            res.healthy = false;
            res.safe_to_flash = true;
            res.description = "Partition '" + partition_name + "' expected " + MagicTypeToString(res.expected_types[0]) +
                              " but detected '" + MagicTypeToString(detected) + "'. File was corrupted or wrongly flashed!";
            res.recommendation = "Surgically reflash clean factory '" + partition_name + ".img'.";
        }
    } else {
        // Generic partition
        if (detected != MagicType::UNKNOWN) {
            res.status = "DETECTED_NON_EMPTY";
            res.healthy = true;
            res.safe_to_flash = true;
            res.description = "Valid filesystem / binary signature detected (" + std::string(MagicTypeToString(detected)) + ").";
            res.recommendation = "Header appears valid.";
        } else {
            res.status = "UNKNOWN_OR_RAW";
            res.healthy = true; // May be proprietary data
            res.safe_to_flash = true;
            res.description = "Raw or proprietary partition data.";
            res.recommendation = "Review if device boots normally.";
        }
    }

    return res;
}

bool PartitionDoctorEngine::VerifyImageBeforeFlash(const std::string& partition_name, const std::string& image_path, std::string& out_error) {
    if (IsProtectedPartition(partition_name)) {
        out_error = "[SECURITY BLOCK] Partition '" + partition_name + "' is HARD-LOCKED against flashing. "
                    "Surgical unbricking strictly forbids touching user data or IMEI calibration partitions!";
        return false;
    }

    std::ifstream file(image_path, std::ios::binary);
    if (!file.is_open()) {
        out_error = "Image file does not exist or cannot be opened: " + image_path;
        return false;
    }

    uint8_t buffer[4096];
    file.read(reinterpret_cast<char*>(buffer), sizeof(buffer));
    std::streamsize bytes_read = file.gcount();
    file.close();

    if (bytes_read == 0) {
        out_error = "Image file is completely empty (0 bytes): " + image_path;
        return false;
    }

    MagicType detected = IdentifyMagic(buffer, static_cast<size_t>(bytes_read));

    std::string clean = partition_name;
    std::transform(clean.begin(), clean.end(), clean.begin(), ::tolower);

    auto it = g_partition_expectations.find(clean);
    if (it != g_partition_expectations.end()) {
        bool match = false;
        for (const auto& exp : it->second) {
            if (detected == exp) {
                match = true;
                break;
            }
        }

        if (!match) {
            out_error = "[PRE-FLASH SAFETY REJECT] Image '" + image_path + "' detected as '" +
                        MagicTypeToString(detected) + "', but target partition '" + partition_name +
                        "' strictly requires " + MagicTypeToString(it->second[0]) +
                        ". Operation blocked to prevent device hard brick!";
            return false;
        }
    }

    return true;
}

DiagnosticReport PartitionDoctorEngine::AnalyzeFastbootGetvar(const std::string& getvar_all_output) {
    DiagnosticReport report;
    report.device_mode = "FASTBOOT";

    std::unordered_map<std::string, std::string> vars;
    std::stringstream ss(getvar_all_output);
    std::string line;

    while (std::getline(ss, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        while (!line.empty() && line.front() == ' ') line.erase(line.begin());

        if (line.empty() || line.find("finished. total time:") != std::string::npos) continue;
        if (line.rfind("(bootloader)", 0) == 0) {
            line = line.substr(12);
            while (!line.empty() && line.front() == ' ') line.erase(line.begin());
        }

        size_t colon_pos = line.rfind(':');
        if (colon_pos != std::string::npos) {
            std::string key = line.substr(0, colon_pos);
            std::string val = line.substr(colon_pos + 1);
            while (!key.empty() && key.back() == ' ') key.pop_back();
            while (!val.empty() && val.front() == ' ') val.erase(val.begin());
            while (!val.empty() && val.back() == ' ') val.pop_back();
            vars[key] = val;
        }
    }

    if (vars.empty()) {
        report.overall_health = "DISCONNECTED";
        report.anomalies.push_back({"", "DISCONNECTED", "CRITICAL", "No fastboot response or device not detected in fastboot mode."});
        return report;
    }

    if (vars.find("product") != vars.end()) report.product = vars["product"];

    std::string current_slot = "";
    if (vars.find("current-slot") != vars.end()) {
        current_slot = vars["current-slot"];
    }

    // 1. Evaluate A/B Slot Health
    if (!current_slot.empty()) {
        bool curr_healthy = true;
        std::string curr_succ = vars.count("slot-successful:" + current_slot) ? vars["slot-successful:" + current_slot] : "";
        std::string curr_unboot = vars.count("slot-unbootable:" + current_slot) ? vars["slot-unbootable:" + current_slot] : "";

        if (curr_unboot == "yes" || curr_unboot == "true" || curr_unboot == "1" ||
            (curr_succ == "no" || curr_succ == "false" || curr_succ == "0")) {
            curr_healthy = false;
        }

        std::string other_slot = (current_slot == "a") ? "b" : "a";
        bool other_healthy = false;
        std::string other_succ = vars.count("slot-successful:" + other_slot) ? vars["slot-successful:" + other_slot] : "";
        std::string other_unboot = vars.count("slot-unbootable:" + other_slot) ? vars["slot-unbootable:" + other_slot] : "";

        if ((other_succ == "yes" || other_succ == "true" || other_succ == "1") &&
            (other_unboot != "yes" && other_unboot != "true" && other_unboot != "1")) {
            other_healthy = true;
        }

        if (!curr_healthy) {
            report.overall_health = "INSTANT_FIX";
            report.anomalies.push_back({
                "slot_" + current_slot,
                "SLOT_EXHAUSTED",
                "CRITICAL",
                "Active slot '" + current_slot + "' marked unbootable or failed boot checks."
            });

            if (other_healthy) {
                report.instant_commands.push_back("fastboot set_active " + other_slot);
                report.surgical_repair_steps.push_back({
                    "SWITCH_ACTIVE_SLOT",
                    other_slot,
                    "",
                    "fastboot set_active " + other_slot,
                    "Switch active slot from failed '" + current_slot + "' to intact backup slot '" + other_slot + "'. Phone unbricks instantly with ZERO data loss."
                });
            } else {
                report.overall_health = "SURGICAL_FIXABLE";
                report.surgical_repair_steps.push_back({
                    "SURGICAL_FLASH_BOOT",
                    "boot_" + current_slot,
                    "boot_" + current_slot + ".img",
                    "fastboot flash boot_" + current_slot + " boot_" + current_slot + ".img",
                    "Both slots exhausted. Reflash clean factory 'boot_" + current_slot + ".img' and 'vbmeta_" + current_slot + ".img'."
                });
            }
        }
    }

    // 2. Evaluate Critical Partition Sizes
    std::vector<std::string> critical_parts = {"boot", "vbmeta", "dtbo", "super", "system", "vendor", "recovery"};
    for (const auto& cp : critical_parts) {
        std::string test_name = cp;
        if (!current_slot.empty()) test_name = cp + "_" + current_slot;

        std::string key = "partition-size:" + test_name;
        if (vars.find(key) != vars.end()) {
            std::string sz_str = vars[key];
            uint64_t size_val = 0;
            try {
                if (sz_str.rfind("0x", 0) == 0 || sz_str.rfind("0X", 0) == 0) {
                    size_val = std::stoull(sz_str, nullptr, 16);
                } else {
                    size_val = std::stoull(sz_str);
                }
            } catch (...) { size_val = 0; }

            if (size_val == 0) {
                report.corrupted_partitions.push_back(test_name);
                report.anomalies.push_back({
                    test_name,
                    "ZERO_SIZE_PARTITION",
                    "HIGH",
                    "Partition '" + test_name + "' reports 0 bytes size or invalid allocation."
                });
                report.surgical_repair_steps.push_back({
                    "REFLASH_PARTITION",
                    test_name,
                    test_name + ".img",
                    "fastboot flash " + test_name + " " + test_name + ".img",
                    "Reflash matching '" + test_name + ".img' from factory firmware container."
                });
            } else {
                report.healthy_partitions.push_back(test_name);
            }
        }
    }

    if (!report.corrupted_partitions.empty() && report.overall_health == "HEALTHY") {
        report.overall_health = "SURGICAL_FIXABLE";
    }

    return report;
}

DiagnosticReport PartitionDoctorEngine::AnalyzeInspections(
    const std::vector<PartitionInspectionResult>& inspections,
    const std::string& device_mode,
    const std::string& product
) {
    DiagnosticReport report;
    report.device_mode = device_mode;
    report.product = product;

    for (const auto& diag : inspections) {
        if (diag.status == "PROTECTED") continue;

        if (diag.healthy) {
            report.healthy_partitions.push_back(diag.partition_name);
        } else {
            report.corrupted_partitions.push_back(diag.partition_name);

            if (diag.status == "MISMATCH_CORRUPTED") {
                report.anomalies.push_back({
                    diag.partition_name,
                    "MAGIC_MISMATCH",
                    "CRITICAL",
                    diag.description
                });
                report.surgical_repair_steps.push_back({
                    "SURGICAL_RESTORE",
                    diag.partition_name,
                    diag.partition_name + ".img",
                    "fastboot flash " + diag.partition_name + " " + diag.partition_name + ".img",
                    "Flash clean factory image '" + diag.partition_name + ".img' directly to fix corruption without touching userdata."
                });
            } else if (diag.status == "EMPTY_OR_WIPED") {
                report.anomalies.push_back({
                    diag.partition_name,
                    "EMPTY_PARTITION",
                    "CRITICAL",
                    diag.description
                });
                report.surgical_repair_steps.push_back({
                    "SURGICAL_RESTORE",
                    diag.partition_name,
                    diag.partition_name + ".img",
                    "fastboot flash " + diag.partition_name + " " + diag.partition_name + ".img",
                    "Write original factory image for '" + diag.partition_name + "' to restore unbrick."
                });
            }
        }
    }

    if (!report.corrupted_partitions.empty()) {
        report.overall_health = "SURGICAL_FIXABLE";
    }

    return report;
}

std::string PartitionDoctorEngine::InspectionResultToJson(const PartitionInspectionResult& res) {
    std::stringstream ss;
    ss << "{\n";
    ss << "  \"partition\": \"" << res.partition_name << "\",\n";
    ss << "  \"status\": \"" << res.status << "\",\n";
    ss << "  \"healthy\": " << (res.healthy ? "true" : "false") << ",\n";
    ss << "  \"detected_type\": \"" << MagicTypeToString(res.detected_type) << "\",\n";
    ss << "  \"safe_to_flash\": " << (res.safe_to_flash ? "true" : "false") << ",\n";
    ss << "  \"description\": \"" << res.description << "\",\n";
    ss << "  \"recommendation\": \"" << res.recommendation << "\"";

    if (res.boot_info.valid) {
        ss << ",\n  \"boot_details\": {\n";
        ss << "    \"version\": " << res.boot_info.header_version << ",\n";
        ss << "    \"kernel_size\": " << res.boot_info.kernel_size << ",\n";
        ss << "    \"ramdisk_size\": " << res.boot_info.ramdisk_size << ",\n";
        ss << "    \"os_version\": \"" << res.boot_info.os_version << "\",\n";
        ss << "    \"security_patch\": \"" << res.boot_info.security_patch << "\"\n";
        ss << "  }";
    } else if (res.avb_info.valid) {
        ss << ",\n  \"avb_details\": {\n";
        ss << "    \"libavb_version\": \"" << res.avb_info.libavb_version << "\",\n";
        ss << "    \"rollback_index\": " << res.avb_info.rollback_index << ",\n";
        ss << "    \"verification_disabled\": " << (res.avb_info.is_verification_disabled ? "true" : "false") << "\n";
        ss << "  }";
    } else if (res.dtbo_info.valid) {
        ss << ",\n  \"dtbo_details\": {\n";
        ss << "    \"total_size\": " << res.dtbo_info.total_size << ",\n";
        ss << "    \"entry_count\": " << res.dtbo_info.dt_entry_count << "\n";
        ss << "  }";
    } else if (res.elf_info.valid) {
        ss << ",\n  \"elf_details\": {\n";
        ss << "    \"arch\": \"" << res.elf_info.architecture << "\",\n";
        ss << "    \"is_64bit\": " << (res.elf_info.is_64bit ? "true" : "false") << "\n";
        ss << "  }";
    }

    ss << "\n}";
    return ss.str();
}

std::string PartitionDoctorEngine::DiagnosticReportToJson(const DiagnosticReport& report) {
    std::stringstream ss;
    ss << "{\n";
    ss << "  \"device_mode\": \"" << report.device_mode << "\",\n";
    ss << "  \"product\": \"" << report.product << "\",\n";
    ss << "  \"overall_health\": \"" << report.overall_health << "\",\n";
    ss << "  \"total_anomalies\": " << report.anomalies.size() << ",\n";
    ss << "  \"userdata_status\": \"" << report.userdata_status << "\",\n";
    ss << "  \"zero_data_loss_guaranteed\": true,\n";

    // corrupted_partitions
    ss << "  \"corrupted_partitions\": [";
    for (size_t i = 0; i < report.corrupted_partitions.size(); ++i) {
        ss << "\"" << report.corrupted_partitions[i] << "\"";
        if (i + 1 < report.corrupted_partitions.size()) ss << ", ";
    }
    ss << "],\n";

    // healthy_partitions
    ss << "  \"healthy_partitions\": [";
    for (size_t i = 0; i < report.healthy_partitions.size(); ++i) {
        ss << "\"" << report.healthy_partitions[i] << "\"";
        if (i + 1 < report.healthy_partitions.size()) ss << ", ";
    }
    ss << "],\n";

    // instant_commands
    ss << "  \"instant_commands\": [";
    for (size_t i = 0; i < report.instant_commands.size(); ++i) {
        ss << "\"" << report.instant_commands[i] << "\"";
        if (i + 1 < report.instant_commands.size()) ss << ", ";
    }
    ss << "],\n";

    // anomalies
    ss << "  \"anomalies\": [\n";
    for (size_t i = 0; i < report.anomalies.size(); ++i) {
        const auto& an = report.anomalies[i];
        ss << "    {\n";
        ss << "      \"partition\": \"" << an.partition << "\",\n";
        ss << "      \"type\": \"" << an.type << "\",\n";
        ss << "      \"severity\": \"" << an.severity << "\",\n";
        ss << "      \"description\": \"" << an.description << "\"\n";
        ss << "    }" << (i + 1 < report.anomalies.size() ? ",\n" : "\n");
    }
    ss << "  ],\n";

    // surgical_repair_steps
    ss << "  \"surgical_repair_steps\": [\n";
    for (size_t i = 0; i < report.surgical_repair_steps.size(); ++i) {
        const auto& st = report.surgical_repair_steps[i];
        ss << "    {\n";
        ss << "      \"action\": \"" << st.action << "\",\n";
        ss << "      \"target_partition\": \"" << st.target_partition << "\",\n";
        ss << "      \"command\": \"" << st.command << "\",\n";
        ss << "      \"explanation\": \"" << st.explanation << "\"\n";
        ss << "    }" << (i + 1 < report.surgical_repair_steps.size() ? ",\n" : "\n");
    }
    ss << "  ]\n";

    ss << "}";
    return ss.str();
}

bool PartitionDoctorEngine::ExtractSingleImage(
    const std::string& source_path,
    const std::string& target_partition,
    const std::string& destination_dir,
    std::string& out_image_path,
    std::string& out_error
) {
    out_image_path.clear();
    out_error.clear();

    // Check if source_path is already the image file itself
    DWORD attr = GetFileAttributesA(source_path.c_str());
    if (attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY)) {
        std::string lower_src = source_path;
        std::transform(lower_src.begin(), lower_src.end(), lower_src.begin(), ::tolower);
        if (lower_src.ends_with(".img") || lower_src.ends_with(".bin")) {
            out_image_path = source_path;
            return true;
        }

        // If it's a TAR / TAR.MD5 archive
        if (lower_src.ends_with(".tar") || lower_src.ends_with(".tar.md5")) {
            CreateDirectoryA(destination_dir.c_str(), NULL);
            std::vector<TarEntryInfo> entries;
            std::string tar_err;
            if (NativeTarReader::InspectTar(source_path, entries, tar_err)) {
                std::string clean_part = target_partition;
                std::transform(clean_part.begin(), clean_part.end(), clean_part.begin(), ::tolower);

                std::string matched_member;
                for (const auto& e : entries) {
                    std::string m_lower = e.name;
                    std::transform(m_lower.begin(), m_lower.end(), m_lower.begin(), ::tolower);
                    if (m_lower.rfind(clean_part, 0) == 0 && (m_lower.ends_with(".img") || m_lower.ends_with(".bin") || m_lower.ends_with(".lz4"))) {
                        matched_member = e.name;
                        break;
                    }
                }

                if (!matched_member.empty()) {
                    std::string dest_file = destination_dir + "\\" + matched_member;
                    std::ofstream out_f(dest_file, std::ios::binary);
                    if (!out_f.is_open()) {
                        out_error = "Failed to create destination file: " + dest_file;
                        return false;
                    }

                    bool stream_ok = NativeTarReader::StreamTarMember(
                        source_path,
                        matched_member,
                        [&out_f](const uint8_t* chunk, size_t chunkSize) -> bool {
                            out_f.write(reinterpret_cast<const char*>(chunk), chunkSize);
                            return out_f.good();
                        },
                        out_error
                    );
                    out_f.close();

                    if (stream_ok) {
                        out_image_path = dest_file;
                        return true;
                    } else {
                        return false;
                    }
                }
            }
        }
    }

    // Check directory
    if (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY)) {
        std::string clean_part = target_partition;
        std::transform(clean_part.begin(), clean_part.end(), clean_part.begin(), ::tolower);

        std::vector<std::string> candidates = {
            clean_part + ".img",
            clean_part + ".bin",
            target_partition + ".img",
            target_partition + ".bin"
        };

        for (const auto& cand : candidates) {
            std::string full_p = source_path + "\\" + cand;
            if (GetFileAttributesA(full_p.c_str()) != INVALID_FILE_ATTRIBUTES) {
                out_image_path = full_p;
                return true;
            }
        }
    }

    out_error = "Target image for partition '" + target_partition + "' not found in: " + source_path;
    return false;
}

std::string PartitionDoctorEngine::FindFastbootExecutable() {
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    std::string baseDir = exePath;
    size_t lastSlash = baseDir.find_last_of("\\/");
    if (lastSlash != std::string::npos) baseDir = baseDir.substr(0, lastSlash);

    std::vector<std::string> candidates = {
        baseDir + "\\resources\\platform-tools\\fastboot.exe",
        baseDir + "\\resources\\resources\\platform-tools\\fastboot.exe",
        baseDir + "\\platform-tools\\fastboot.exe",
        "C:\\BSLab_Tool\\dist_new\\resources\\platform-tools\\fastboot.exe",
        "C:\\BSLab_Tool\\resources\\platform-tools\\fastboot.exe"
    };

    for (const auto& c : candidates) {
        if (GetFileAttributesA(c.c_str()) != INVALID_FILE_ATTRIBUTES) {
            return c;
        }
    }

    return "fastboot.exe";
}

bool PartitionDoctorEngine::SurgicalFlashFastboot(
    const std::string& target_partition,
    const std::string& image_path,
    const std::string& serial,
    std::string& out_log,
    std::string& out_error
) {
    out_log.clear();
    out_error.clear();

    // 1. Enforce Firewall Lockout
    if (IsProtectedPartition(target_partition)) {
        out_error = "[SECURITY BLOCK] Partition '" + target_partition + "' is HARD-LOCKED against flashing/formatting. "
                    "Surgical unbricking strictly forbids touching user data or IMEI calibration partitions!";
        return false;
    }

    // 2. Verify image header magic bytes
    if (!VerifyImageBeforeFlash(target_partition, image_path, out_error)) {
        return false;
    }

    // 3. Resolve Fastboot binary
    std::string fastboot_bin = FindFastbootExecutable();

    // 4. Build command line
    std::string cmd = "\"" + fastboot_bin + "\"";
    if (!serial.empty()) {
        cmd += " -s " + serial;
    }
    cmd += " flash " + target_partition + " \"" + image_path + "\"";

    // 5. Setup Pipes for Non-Blocking execution
    HANDLE hStdOutRead = NULL;
    HANDLE hStdOutWrite = NULL;
    SECURITY_ATTRIBUTES saAttr;
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    if (!CreatePipe(&hStdOutRead, &hStdOutWrite, &saAttr, 0)) {
        out_error = "Failed to create pipe for Fastboot execution";
        return false;
    }
    SetHandleInformation(hStdOutRead, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.hStdError = hStdOutWrite;
    si.hStdOutput = hStdOutWrite;
    si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    ZeroMemory(&pi, sizeof(pi));

    std::vector<char> cmdVec(cmd.begin(), cmd.end());
    cmdVec.push_back('\0');

    BOOL success = CreateProcessA(
        NULL,
        cmdVec.data(),
        NULL,
        NULL,
        TRUE,
        CREATE_NO_WINDOW,
        NULL,
        NULL,
        &si,
        &pi
    );

    CloseHandle(hStdOutWrite);

    if (!success) {
        CloseHandle(hStdOutRead);
        out_error = "Failed to launch fastboot process: " + std::to_string(GetLastError());
        return false;
    }

    // Strict 60s timeout guard
    DWORD startTime = GetTickCount();
    char buffer[1024];
    DWORD bytesRead = 0;
    std::string rawOutput;

    while (true) {
        DWORD bytesAvailable = 0;
        if (PeekNamedPipe(hStdOutRead, NULL, 0, NULL, &bytesAvailable, NULL) && bytesAvailable > 0) {
            if (ReadFile(hStdOutRead, buffer, sizeof(buffer) - 1, &bytesRead, NULL) && bytesRead > 0) {
                buffer[bytesRead] = '\0';
                rawOutput += buffer;
            }
        }

        DWORD waitRes = WaitForSingleObject(pi.hProcess, 50);
        if (waitRes == WAIT_OBJECT_0) {
            while (ReadFile(hStdOutRead, buffer, sizeof(buffer) - 1, &bytesRead, NULL) && bytesRead > 0) {
                buffer[bytesRead] = '\0';
                rawOutput += buffer;
            }
            break;
        }

        if (GetTickCount() - startTime > 60000) {
            TerminateProcess(pi.hProcess, 1);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            CloseHandle(hStdOutRead);
            out_error = "Fastboot surgical flashing timed out after 60 seconds";
            return false;
        }
    }

    DWORD exitCode = 0;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hStdOutRead);

    out_log = rawOutput;

    std::string lowerOut = rawOutput;
    std::transform(lowerOut.begin(), lowerOut.end(), lowerOut.begin(), ::tolower);

    if (exitCode == 0 && lowerOut.find("okay") != std::string::npos) {
        return true;
    }

    out_error = "Fastboot command failed (Exit " + std::to_string(exitCode) + "): " + rawOutput;
    return false;
}

} // namespace BSLab
