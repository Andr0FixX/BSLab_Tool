"""
BSLab Tool PRO - Partition Doctor: Binary Magic Signatures & Fingerprints Library
Defines binary magic signatures for Android partitions, boot headers, filesystems, and loaders.
"""

from enum import Enum
from typing import Dict, Any, List

class MagicType(Enum):
    BOOT_IMG = "BOOT_IMG"
    AVB_VBMETA = "AVB_VBMETA"
    DTBO = "DTBO"
    DYNAMIC_SUPER = "DYNAMIC_SUPER"
    ELF_BOOTLOADER = "ELF_BOOTLOADER"
    SPARSE_IMAGE = "SPARSE_IMAGE"
    GPT_HEADER = "GPT_HEADER"
    EXT4_FS = "EXT4_FS"
    F2FS_FS = "F2FS_FS"
    HUAWEI_APP = "HUAWEI_APP"
    EMPTY_ZERO = "EMPTY_ZERO"
    UNKNOWN = "UNKNOWN"

class PartitionSignatures:
    """
    Standard binary signatures used for partition header verification.
    """
    # Android Boot Image Magic: "ANDROID!" (8 bytes)
    BOOT_MAGIC = b"ANDROID!"
    
    # Android Verified Boot 2.0 (AVB) Magic: "AVB0" (4 bytes)
    AVB_MAGIC = b"AVB0"
    
    # Device Tree Blob Overlay (DTBO) Table Magic: 0xD7B7AB1E (big-endian)
    DTBO_MAGIC = b"\xD7\xB7\xAB\x1E"
    
    # Dynamic Super Partition (liblp) Magic: 0x616C7073 ("spla" little-endian)
    LP_METADATA_GEOMETRY_MAGIC = b"\x73\x70\x6c\x61" # 0x616C7073
    
    # Linux ELF Executable Header for Bootloaders (xbl, abl, tz, hyp, sbl1)
    ELF_MAGIC = b"\x7FELF"
    
    # Android Sparse Image Format Magic: 0xED26FF3A
    SPARSE_MAGIC = b"\x3A\xFF\x26\xED"
    
    # EFI / GPT Partition Table Magic: "EFI PART" (8 bytes at LBA 1 / offset 512)
    GPT_MAGIC = b"EFI PART"
    
    # Ext4 Superblock Magic: 0xEF53 at offset 1080 (0x438)
    EXT4_MAGIC = b"\x53\xEF"
    
    # F2FS Superblock Magic: 0xF2F52010 at offset 1024 (0x400)
    F2FS_MAGIC = b"\x10\x20\xF5\xF2"
    
    # Huawei UPDATE.APP Magic: 0x55 0xAA 0x5A 0xA5
    HUAWEI_APP_MAGIC = b"\x55\xAA\x5A\xA5"

    # Mapping of partition names to their expected primary magic types
    PARTITION_EXPECTATION_MAP: Dict[str, List[MagicType]] = {
        "boot": [MagicType.BOOT_IMG],
        "boot_a": [MagicType.BOOT_IMG],
        "boot_b": [MagicType.BOOT_IMG],
        "init_boot": [MagicType.BOOT_IMG],
        "init_boot_a": [MagicType.BOOT_IMG],
        "init_boot_b": [MagicType.BOOT_IMG],
        "recovery": [MagicType.BOOT_IMG],
        "recovery_a": [MagicType.BOOT_IMG],
        "recovery_b": [MagicType.BOOT_IMG],
        "vendor_boot": [MagicType.BOOT_IMG],
        "vendor_boot_a": [MagicType.BOOT_IMG],
        "vendor_boot_b": [MagicType.BOOT_IMG],
        "vbmeta": [MagicType.AVB_VBMETA],
        "vbmeta_a": [MagicType.AVB_VBMETA],
        "vbmeta_b": [MagicType.AVB_VBMETA],
        "vbmeta_system": [MagicType.AVB_VBMETA],
        "vbmeta_system_a": [MagicType.AVB_VBMETA],
        "vbmeta_system_b": [MagicType.AVB_VBMETA],
        "vbmeta_vendor": [MagicType.AVB_VBMETA],
        "vbmeta_vendor_a": [MagicType.AVB_VBMETA],
        "vbmeta_vendor_b": [MagicType.AVB_VBMETA],
        "dtbo": [MagicType.DTBO],
        "dtbo_a": [MagicType.DTBO],
        "dtbo_b": [MagicType.DTBO],
        "super": [MagicType.DYNAMIC_SUPER, MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "system": [MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "system_a": [MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "system_b": [MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "vendor": [MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "vendor_a": [MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "vendor_b": [MagicType.SPARSE_IMAGE, MagicType.EXT4_FS, MagicType.F2FS_FS],
        "abl": [MagicType.ELF_BOOTLOADER],
        "abl_a": [MagicType.ELF_BOOTLOADER],
        "abl_b": [MagicType.ELF_BOOTLOADER],
        "xbl": [MagicType.ELF_BOOTLOADER],
        "xbl_a": [MagicType.ELF_BOOTLOADER],
        "xbl_b": [MagicType.ELF_BOOTLOADER],
        "xbl_config": [MagicType.ELF_BOOTLOADER],
        "tz": [MagicType.ELF_BOOTLOADER],
        "tz_a": [MagicType.ELF_BOOTLOADER],
        "tz_b": [MagicType.ELF_BOOTLOADER],
        "hyp": [MagicType.ELF_BOOTLOADER],
        "hyp_a": [MagicType.ELF_BOOTLOADER],
        "hyp_b": [MagicType.ELF_BOOTLOADER],
    }

    # Protected User Data and Security Partitions (MUST NEVER BE WRITTEN IN SURGICAL UNBRICK)
    PROTECTED_PARTITIONS = {
        "userdata", "data", "metadata", "cache",
        "persist", "persist_a", "persist_b",
        "nvram", "nvdata", "nvcfg", "protect_f", "protect_s",
        "modemst1", "modemst2", "fsg", "fsc", "sec_efs", "efs",
        "proinfo", "frp", "devinfo", "keystore", "keymaster",
        "keymaster_a", "keymaster_b", "misc"
    }

    @classmethod
    def is_protected(cls, partition_name: str) -> bool:
        """Checks whether the partition holds private user data or sensitive RF/security tokens."""
        clean = partition_name.strip().lower()
        if clean in cls.PROTECTED_PARTITIONS:
            return True
        for p in cls.PROTECTED_PARTITIONS:
            if clean.startswith(p + "_") or clean == p:
                return True
        return False
