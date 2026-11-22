/**
 * BS Lab Tool v2.0 PRO — Enterprise Native Core Engine
 * Architecture: C++20 Win32 High-Speed Hardware Abstraction Layer
 * Exports standard C-ABI interface for C# WPF (.NET) P/Invoke Interop
 * 
 * Proprietary to: BS Lab & Mobile Traders (Syed Bisharat Ali)
 */

#pragma once

#ifdef _WIN32
    #ifdef BSLABCORE_EXPORTS
        #define BSLAB_API extern "C" __declspec(dllexport)
    #else
        #define BSLAB_API extern "C" __declspec(dllimport)
    #endif
#else
    #define BSLAB_API extern "C"
#endif

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Log Levels matching C# UI Console
typedef enum {
    BSLAB_LOG_INFO    = 0,
    BSLAB_LOG_BROM    = 1,
    BSLAB_LOG_SUCCESS = 2,
    BSLAB_LOG_WARN    = 3,
    BSLAB_LOG_ERROR   = 4,
    BSLAB_LOG_DEBUG   = 5
} BSLab_LogLevel;

// Callback Signatures for Non-Blocking C# WPF Telemetry
typedef void (*BSLab_ProgressCallback)(int overall_pct, int file_pct, const char* part_name, const char* status_text);
typedef void (*BSLab_LogCallback)(int log_level, const char* message);

// ============================================================================
// SYSTEM & CORE ENGINE INITIALIZATION
// ============================================================================

BSLAB_API const char* BSLab_GetVersion(void);
BSLAB_API bool BSLab_Initialize(BSLab_LogCallback log_cb);
BSLAB_API void BSLab_Shutdown(void);

// ============================================================================
// MEDIATEK (MTK) HIGH-SPEED PROTOCOL ENGINE
// ============================================================================

/**
 * Executes sub-millisecond 4-Phase MTK BROM/Preloader Hardware Synchronization.
 * @param port_name e.g. "COM12"
 * @param timeout_ms Max milliseconds to wait for connection
 * @param out_hw_code Pointer to store detected Chipset ID (e.g. 0x6768 for Helio G85)
 * @return true if 4-Phase handshake verified
 */
BSLAB_API bool BSLab_MTK_SyncHandshake(
    const char* port_name,
    int timeout_ms,
    uint16_t* out_hw_code
);

/**
 * High-Speed Slot-Aware Firmware Flasher via authenticated Download Agent (DA).
 */
BSLAB_API bool BSLab_MTK_LoadDA(
    const char* port_name,
    const char* da_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Reads Live GPT Partition Table from eMMC / UFS storage.
 * Returns UTF-8 JSON representation in out_json_buffer.
 */
BSLAB_API bool BSLab_MTK_ReadGPT(
    const char* port_name,
    char* out_json_buffer,
    int max_buffer_len,
    int* out_partition_count
);

/**
 * High-Speed Zero-Copy Partition Flasher via Win32 MapViewOfFile.
 */
BSLAB_API bool BSLab_MTK_FlashPartition(
    const char* port_name,
    const char* partition_name,
    uint64_t start_lba,
    const wchar_t* image_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Dumps a raw partition image to disk.
 */
BSLAB_API bool BSLab_MTK_DumpPartition(
    const char* port_name,
    const char* partition_name,
    uint64_t start_lba,
    uint64_t sector_count,
    const wchar_t* output_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Erases/Formats an LBA block range (e.g. frp, userdata, metadata).
 */
BSLAB_API bool BSLab_MTK_ErasePartition(
    const char* port_name,
    const char* partition_name,
    uint64_t start_lba,
    uint64_t sector_count,
    BSLab_ProgressCallback progress_cb
);

BSLAB_API bool BSLab_MTK_FlashFirmware(
    const char* port_name,
    const char* scatter_path,
    const char* da_path,
    const char* preloader_path,
    const char* auth_path,
    bool force_brom,
    bool reboot_after,
    BSLab_ProgressCallback progress_cb
);

/**
 * One-Click Service Operations
 */
BSLAB_API bool BSLab_MTK_ResetFRP(
    const char* port_name,
    const char* da_path,
    BSLab_ProgressCallback progress_cb
);

BSLAB_API bool BSLab_MTK_FactoryReset(
    const char* port_name,
    const char* da_path,
    bool wipe_frp,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Xiaomi / Redmi / POCO Mi Account Cloud Lock Bypass.
 */
BSLAB_API bool BSLab_MTK_ResetMiAccount(
    const char* port_name,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Network & IMEI Safeguard: Dumps NVRAM, NVDATA, protect1, protect2.
 */
BSLAB_API bool BSLab_MTK_BackupNVRAM(
    const char* port_name,
    const wchar_t* backup_folder,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Network & IMEI Safeguard: Restores NVRAM, NVDATA, protect1, protect2.
 */
BSLAB_API bool BSLab_MTK_RestoreNVRAM(
    const char* port_name,
    const wchar_t* backup_folder,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Instant Bootloader Unlock (seccfg patch).
 */
BSLAB_API bool BSLab_MTK_UnlockBootloader(
    const char* port_name,
    BSLab_ProgressCallback progress_cb
);

/**
 * Preloader-to-BROM Force Glitch: Forces locked preloader into BROM without testpoint.
 */
BSLAB_API bool BSLab_MTK_ForceBROM(
    const char* port_name
);

BSLAB_API bool BSLab_MTK_Reboot(
    const char* port_name,
    int reboot_mode // 0=Normal, 1=Fastboot, 2=Recovery
);

// ============================================================================
// PHASE 4: QUALCOMM SNAPDRAGON EDL 9008 SAHARA & FIREHOSE ENGINE
// ============================================================================

/**
 * Connects to Qualcomm HS-USB QDLoader 9008, negotiates Sahara, and injects Firehose.
 */
BSLAB_API bool BSLab_QC_ConnectEDL(
    const char* port_name,
    const wchar_t* programmer_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Reads Live GPT from Snapdragon Storage via Firehose XML.
 */
BSLAB_API bool BSLab_QC_ReadGPT(
    const char* port_name,
    char* out_json_buffer,
    int max_buffer_len,
    int* out_partition_count
);

/**
 * High-Speed Zero-Copy Flashing on Qualcomm EDL.
 */
BSLAB_API bool BSLab_QC_FlashPartition(
    const char* port_name,
    const char* partition_name,
    uint64_t start_lba,
    uint64_t sector_count,
    const wchar_t* image_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Erases Flash sector range on Qualcomm EDL.
 */
BSLAB_API bool BSLab_QC_ErasePartition(
    const char* port_name,
    const char* partition_name,
    uint64_t start_lba,
    uint64_t sector_count,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Qualcomm FRP Reset.
 */
BSLAB_API bool BSLab_QC_ResetFRP(
    const char* port_name,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Qualcomm Safe Factory Reset.
 */
BSLAB_API bool BSLab_QC_FactoryReset(
    const char* port_name,
    bool wipe_frp,
    BSLab_ProgressCallback progress_cb
);

/**
 * Reboot Qualcomm Device to System.
 */
BSLAB_API bool BSLab_QC_Reboot(
    const char* port_name
);

// ============================================================================
// PHASE 5: SAMSUNG ODIN & MODEM PROTOCOL ENGINE
// ============================================================================

/**
 * Scans connected Samsung devices (Modem, CDC, and Download Mode ports).
 * Returns JSON array in out_json_buffer.
 */
BSLAB_API bool BSLab_Samsung_ScanDevices(
    char* out_json_buffer,
    int max_buffer_len,
    int* out_device_count
);

/**
 * Verifies Samsung .tar.md5 file integrity.
 */
BSLAB_API bool BSLab_Samsung_VerifyTarMd5(
    const char* file_path,
    BSLab_ProgressCallback progress_cb,
    char* out_status_msg,
    int max_msg_len
);

/**
 * Inspects members inside a Samsung TAR or TAR.MD5 archive without unpacking.
 * Returns JSON array in out_json_buffer.
 */
BSLAB_API bool BSLab_Samsung_InspectTar(
    const char* file_path,
    char* out_json_buffer,
    int max_buffer_len,
    int* out_member_count
);

/**
 * Parses binary Samsung PIT file and returns structured partitions JSON.
 */
BSLAB_API bool BSLab_Samsung_ParsePit(
    const char* pit_path,
    char* out_json_buffer,
    int max_buffer_len,
    int* out_entry_count
);

/**
 * Executes Odin Download Mode hardware sync handshake.
 */
BSLAB_API bool BSLab_Samsung_Handshake(
    const char* port_name
);

/**
 * Flashes 4-File Samsung firmware (BL, AP, CP, CSC, PIT) in high-speed hardware mode.
 */
BSLAB_API bool BSLab_Samsung_FlashFirmware(
    const char* port_name,
    const char* bl_path,
    const char* ap_path,
    const char* cp_path,
    const char* csc_path,
    const char* pit_path,
    bool repartition,
    bool auto_reboot,
    BSLab_ProgressCallback progress_cb
);

/**
 * Aborts any ongoing Samsung flashing operation.
 */
BSLAB_API void BSLab_Samsung_Abort(void);

/**
 * Launches Official Samsung Odin3 with pre-configured slots and options.
 */
BSLAB_API bool BSLab_Samsung_LaunchOfficialOdin(
    const char* bl_path,
    const char* ap_path,
    const char* cp_path,
    const char* csc_path,
    const char* pit_path,
    bool repartition,
    bool auto_reboot
);

/**
 * Reads detailed Samsung device info via Modem AT port (Model, IMEI, Baseband, CSC).
 * Returns JSON in out_json_buffer.
 */
BSLAB_API bool BSLab_Samsung_Modem_ReadInfo(
    const char* port_name,
    char* out_json_buffer,
    int max_buffer_len
);

/**
 * Triggers reboot to Odin Download Mode from Modem / MTP mode.
 */
BSLAB_API bool BSLab_Samsung_Modem_RebootDownload(
    const char* port_name
);

/**
 * Executes 1-Click CSC carrier change via Modem AT commands.
 */
BSLAB_API bool BSLab_Samsung_Modem_ChangeCSC(
    const char* port_name,
    const char* target_csc,
    bool reboot_after
);

/**
 * Reads Knox Guard, Knox Warranty bit, and FRP lock status.
 * Returns JSON in out_json_buffer.
 */
BSLAB_API bool BSLab_Samsung_Modem_ReadKnoxSecurity(
    const char* port_name,
    char* out_json_buffer,
    int max_buffer_len
);

// ============================================================================
// PHASE 6: UNISOC / SPREADTRUM (SPD) PROTOCOL ENGINE
// ============================================================================

/**
 * Scans connected Unisoc / Spreadtrum COM ports.
 * Returns JSON array in out_json_buffer.
 */
BSLAB_API bool BSLab_Unisoc_ScanPorts(
    char* out_json_buffer,
    int max_buffer_len,
    int* out_count
);

/**
 * Parses a Unisoc .PAC firmware archive.
 * Returns JSON object with version, product name, and partitions in out_json_buffer.
 */
BSLAB_API bool BSLab_Unisoc_ParsePac(
    const char* pac_path,
    char* out_json_buffer,
    int max_buffer_len,
    int* out_count
);

/**
 * Connects to Unisoc BROM (0x7E sync) and optionally loads FDL1/FDL2 from PAC.
 */
BSLAB_API bool BSLab_Unisoc_Connect(
    const char* port_name,
    const char* pac_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Flashes complete PAC firmware archive to Unisoc device.
 */
BSLAB_API bool BSLab_Unisoc_FlashFirmware(
    const char* port_name,
    const char* pac_path,
    bool reboot_after,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Unisoc FRP Reset (erases persist / misc / frp).
 */
BSLAB_API bool BSLab_Unisoc_ResetFRP(
    const char* port_name,
    const char* pac_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * 1-Click Unisoc Safe Factory Reset (erases userdata & cache).
 */
BSLAB_API bool BSLab_Unisoc_FactoryReset(
    const char* port_name,
    const char* pac_path,
    BSLab_ProgressCallback progress_cb
);

/**
 * Reboots Unisoc device to system.
 */
BSLAB_API bool BSLab_Unisoc_Reboot(
    const char* port_name
);

/**
 * Aborts ongoing Unisoc operation.
 */
BSLAB_API void BSLab_Unisoc_Abort(void);

#ifdef __cplusplus
}
#endif
