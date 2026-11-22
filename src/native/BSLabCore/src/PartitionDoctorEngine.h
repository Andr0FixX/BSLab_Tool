#pragma once

#include <string>
#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <cstdint>
#include <memory>

namespace BSLab {

enum class MagicType {
    BOOT_IMG,
    AVB_VBMETA,
    DTBO,
    DYNAMIC_SUPER,
    ELF_BOOTLOADER,
    SPARSE_IMAGE,
    GPT_HEADER,
    EXT4_FS,
    F2FS_FS,
    HUAWEI_APP,
    EMPTY_ZERO,
    UNKNOWN
};

enum class FaultSeverity {
    HEALTHY,
    INSTANT_FIX,
    SURGICAL_FIXABLE,
    SECURITY_AVB_FAULT,
    SYSTEM_FAULT,
    DATA_PRESERVED_SAFE,
    DISCONNECTED
};

struct BootHeaderInfo {
    bool valid = false;
    uint32_t header_version = 0;
    uint32_t page_size = 0;
    uint32_t kernel_size = 0;
    uint32_t ramdisk_size = 0;
    uint32_t second_size = 0;
    uint32_t recovery_dtbo_size = 0;
    uint32_t dtb_size = 0;
    std::string os_version = "Unknown";
    std::string security_patch = "Unknown";
    std::string error;
};

struct AvbHeaderInfo {
    bool valid = false;
    std::string libavb_version = "Unknown";
    uint64_t auth_block_size = 0;
    uint64_t aux_block_size = 0;
    uint32_t algorithm_type = 0;
    uint64_t rollback_index = 0;
    uint32_t flags = 0;
    bool is_verification_disabled = false;
    bool is_dm_verity_disabled = false;
    std::string error;
};

struct DtboHeaderInfo {
    bool valid = false;
    uint32_t total_size = 0;
    uint32_t header_size = 0;
    uint32_t dt_entry_count = 0;
    uint32_t dt_entry_size = 0;
    uint32_t page_size = 0;
    uint32_t version = 0;
    std::string error;
};

struct ElfHeaderInfo {
    bool valid = false;
    bool is_64bit = false;
    std::string architecture = "Unknown";
    uint64_t entry_point = 0;
    std::string error;
};

struct PartitionInspectionResult {
    std::string partition_name;
    std::string status; // "HEALTHY", "PROTECTED", "EMPTY_OR_WIPED", "MISMATCH_CORRUPTED", "DETECTED_NON_EMPTY", "UNKNOWN_OR_RAW"
    bool healthy = false;
    MagicType detected_type = MagicType::UNKNOWN;
    std::vector<MagicType> expected_types;
    std::string description;
    std::string recommendation;
    bool safe_to_flash = false;

    // Detailed header info if parsed
    BootHeaderInfo boot_info;
    AvbHeaderInfo avb_info;
    DtboHeaderInfo dtbo_info;
    ElfHeaderInfo elf_info;
};

struct AnomalyItem {
    std::string partition;
    std::string type;
    std::string severity;
    std::string description;
};

struct SurgicalStep {
    std::string action;
    std::string target_partition;
    std::string source_file;
    std::string command;
    std::string explanation;
};

struct DiagnosticReport {
    std::string device_mode = "FASTBOOT";
    std::string product = "Unknown";
    std::string overall_health = "HEALTHY";
    std::vector<std::string> corrupted_partitions;
    std::vector<std::string> healthy_partitions;
    std::vector<AnomalyItem> anomalies;
    std::vector<SurgicalStep> surgical_repair_steps;
    std::vector<std::string> instant_commands;
    std::string userdata_status = "100% PROTECTED & UNTOUCHED";
    bool zero_data_loss_guaranteed = true;
};

class PartitionDoctorEngine {
public:
    // Magic Identification & Signatures
    static MagicType IdentifyMagic(const uint8_t* buffer, size_t size);
    static const char* MagicTypeToString(MagicType type);
    static MagicType StringToMagicType(const std::string& str);
    static bool IsProtectedPartition(const std::string& partition_name);

    // Deep Header Forensic Parsing
    static bool ParseBootHeader(const uint8_t* data, size_t len, BootHeaderInfo& out_info);
    static bool ParseAvbHeader(const uint8_t* data, size_t len, AvbHeaderInfo& out_info);
    static bool ParseDtboHeader(const uint8_t* data, size_t len, DtboHeaderInfo& out_info);
    static bool ParseElfHeader(const uint8_t* data, size_t len, ElfHeaderInfo& out_info);

    // Forensic Partition Inspection & Pre-Flash Verification
    static PartitionInspectionResult InspectPartition(const std::string& partition_name, const uint8_t* data, size_t len);
    static bool VerifyImageBeforeFlash(const std::string& partition_name, const std::string& image_path, std::string& out_error);

    // Diagnostic Brain & Surgical Unbrick Formulation
    static DiagnosticReport AnalyzeFastbootGetvar(const std::string& getvar_all_output);
    static DiagnosticReport AnalyzeInspections(const std::vector<PartitionInspectionResult>& inspections,
                                              const std::string& device_mode = "EDL_9008",
                                              const std::string& product = "Unknown");

    // JSON Serialization for C# WPF DataGrid
    static std::string InspectionResultToJson(const PartitionInspectionResult& res);
    static std::string DiagnosticReportToJson(const DiagnosticReport& report);

    // Single-Partition Image Extractor
    static bool ExtractSingleImage(const std::string& source_path,
                                  const std::string& target_partition,
                                  const std::string& destination_dir,
                                  std::string& out_image_path,
                                  std::string& out_error);

    // Surgical Fastboot Flasher with Zero-Data-Loss Firewall
    static bool SurgicalFlashFastboot(const std::string& target_partition,
                                     const std::string& image_path,
                                     const std::string& serial,
                                     std::string& out_log,
                                     std::string& out_error);

private:
    static std::string FindFastbootExecutable();
    static uint32_t ReadBe32(const uint8_t* p);
    static uint32_t ReadLe32(const uint8_t* p);
    static uint64_t ReadLe64(const uint8_t* p);
    static uint64_t ReadBe64(const uint8_t* p);
};

} // namespace BSLab
