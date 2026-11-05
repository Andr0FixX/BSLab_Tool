"""
BSLab Tool PRO - Partition Header Parsers & Forensic Health Inspector
Parses binary headers for Boot images, AVB vbmeta, DTBO tables, and ELF bootloaders.
"""

import struct
from typing import Dict, Any, Optional
from .signatures import PartitionSignatures, MagicType

class BootHeaderParser:
    """Parses Android Boot Image Headers (v0, v1, v2, v3, v4)"""

    @staticmethod
    def parse(header_bytes: bytes) -> Dict[str, Any]:
        if len(header_bytes) < 64:
            return {"valid": False, "error": "Header chunk too short (<64 bytes)"}
        
        if not header_bytes.startswith(PartitionSignatures.BOOT_MAGIC):
            return {"valid": False, "error": "Missing 'ANDROID!' boot magic"}

        try:
            # Android boot header format v0-v2 starts with:
            # magic (8s), kernel_size (I), kernel_addr (I), ramdisk_size (I), ramdisk_addr (I),
            # second_size (I), second_addr (I), tags_addr (I), page_size (I), header_version (I), os_version (I)
            magic, k_size, k_addr, r_size, r_addr, s_size, s_addr, tags_addr, page_size, header_ver, os_ver = struct.unpack_from(
                "<8sIIIIIIIIII", header_bytes, 0
            )

            # Parse OS version & patch level (encoded into 32-bit uint)
            os_version_str = "Unknown"
            patch_level_str = "Unknown"
            if os_ver > 0:
                os_a = (os_ver >> 25) & 0x7F
                os_b = (os_ver >> 18) & 0x7F
                os_c = (os_ver >> 11) & 0x7F
                os_version_str = f"{os_a}.{os_b}.{os_c}".rstrip(".0") or f"{os_a}"
                y = ((os_ver >> 4) & 0x7F) + 2000
                m = os_ver & 0xF
                patch_level_str = f"{y:04d}-{m:02d}"

            info = {
                "valid": True,
                "magic": "ANDROID!",
                "header_version": header_ver,
                "page_size": page_size,
                "kernel_size_bytes": k_size,
                "ramdisk_size_bytes": r_size,
                "second_size_bytes": s_size,
                "os_version": os_version_str,
                "security_patch": patch_level_str
            }

            # If v1 or v2, read recovery_dtbo and dtb sizes
            if header_ver in [1, 2] and len(header_bytes) >= 1640:
                # v1: recovery_dtbo_size at offset 1632
                rec_dtbo_size = struct.unpack_from("<I", header_bytes, 1632)[0]
                info["recovery_dtbo_size"] = rec_dtbo_size
                if header_ver == 2 and len(header_bytes) >= 1648:
                    dtb_size = struct.unpack_from("<I", header_bytes, 1644)[0]
                    info["dtb_size"] = dtb_size

            return info
        except Exception as e:
            return {"valid": False, "error": f"Header unpack error: {str(e)}"}


class AVBHeaderParser:
    """Parses Android Verified Boot 2.0 (AVB) VBMeta Headers"""

    @staticmethod
    def parse(header_bytes: bytes) -> Dict[str, Any]:
        if len(header_bytes) < 64:
            return {"valid": False, "error": "Chunk too small for AVB"}
        
        if not header_bytes.startswith(PartitionSignatures.AVB_MAGIC):
            return {"valid": False, "error": "Missing 'AVB0' magic"}

        try:
            # AVB header struct:
            # magic (4s), required_libavb_version_major (I), required_libavb_version_minor (I),
            # authentication_data_block_size (Q), auxiliary_data_block_size (Q),
            # algorithm_type (I), hash_offset (Q), hash_size (Q), signature_offset (Q), signature_size (Q),
            # public_key_offset (Q), public_key_size (Q), public_key_metadata_offset (Q), public_key_metadata_size (Q),
            # descriptors_offset (Q), descriptors_size (Q), rollback_index (Q), flags (I)
            magic, req_maj, req_min, auth_sz, aux_sz, alg_type = struct.unpack_from("<4sIIQQI", header_bytes, 0)
            rollback_idx = struct.unpack_from("<Q", header_bytes, 104)[0]
            flags = struct.unpack_from("<I", header_bytes, 112)[0]

            return {
                "valid": True,
                "magic": "AVB0",
                "libavb_version": f"{req_maj}.{req_min}",
                "auth_block_size": auth_sz,
                "aux_block_size": aux_sz,
                "algorithm_type": alg_type,
                "rollback_index": rollback_idx,
                "flags": flags,
                "is_verification_disabled": bool(flags & 1),
                "is_dm_verity_disabled": bool(flags & 2)
            }
        except Exception as e:
            return {"valid": False, "error": f"AVB unpack error: {str(e)}"}


class DTBOHeaderParser:
    """Parses Device Tree Blob Overlay (DTBO) Tables"""

    @staticmethod
    def parse(header_bytes: bytes) -> Dict[str, Any]:
        if len(header_bytes) < 32:
            return {"valid": False, "error": "Chunk too small for DTBO"}

        if not header_bytes.startswith(PartitionSignatures.DTBO_MAGIC):
            return {"valid": False, "error": "Missing DTBO table magic (0xD7B7AB1E)"}

        try:
            # DTBO table header:
            # magic (4s), total_size (I), header_size (I), dt_entry_size (I),
            # dt_entry_count (I), dt_entries_offset (I), page_size (I), version (I)
            magic, total_size, hdr_size, entry_size, entry_count, entries_offset, page_size, version = struct.unpack_from(
                ">4sIIIIIII", header_bytes, 0
            )

            return {
                "valid": True,
                "magic": "DTBO",
                "total_size": total_size,
                "header_size": hdr_size,
                "dt_entry_count": entry_count,
                "dt_entry_size": entry_size,
                "page_size": page_size,
                "version": version
            }
        except Exception as e:
            return {"valid": False, "error": f"DTBO unpack error: {str(e)}"}


class ELFHeaderParser:
    """Parses ELF Executable Headers for Bootloaders (xbl, abl, tz, sbl)"""

    @staticmethod
    def parse(header_bytes: bytes) -> Dict[str, Any]:
        if len(header_bytes) < 52:
            return {"valid": False, "error": "Chunk too small for ELF"}

        if not header_bytes.startswith(PartitionSignatures.ELF_MAGIC):
            return {"valid": False, "error": "Missing '\\x7FELF' magic"}

        try:
            elf_class = header_bytes[4] # 1 = 32-bit, 2 = 64-bit
            data_enc = header_bytes[5]   # 1 = little-endian, 2 = big-endian
            version = header_bytes[6]
            os_abi = header_bytes[7]

            endian = "<" if data_enc == 1 else ">"
            if elf_class == 2:
                # 64-bit ELF
                e_type, e_machine, e_version, e_entry = struct.unpack_from(f"{endian}HHIQ", header_bytes, 16)
                arch = "AArch64 (64-bit)" if e_machine == 183 else f"Machine {e_machine}"
            else:
                # 32-bit ELF
                e_type, e_machine, e_version, e_entry = struct.unpack_from(f"{endian}HHII", header_bytes, 16)
                arch = "ARM (32-bit)" if e_machine == 40 else f"Machine {e_machine}"

            return {
                "valid": True,
                "magic": "ELF",
                "is_64bit": (elf_class == 2),
                "architecture": arch,
                "entry_point": hex(e_entry)
            }
        except Exception as e:
            return {"valid": False, "error": f"ELF unpack error: {str(e)}"}


class PartitionHealthInspector:
    """
    High-level forensic inspector that checks any raw partition chunk
    against expected partition signatures and diagnoses faults.
    """

    @classmethod
    def identify_magic(cls, raw_chunk: bytes) -> MagicType:
        """Determines the magic type contained in a binary chunk."""
        if not raw_chunk:
            return MagicType.UNKNOWN

        # Check if entirely zeroed or 0xFF
        is_all_zero = all(b == 0 for b in raw_chunk[:512])
        is_all_ff = all(b == 255 for b in raw_chunk[:512])
        if is_all_zero or is_all_ff:
            return MagicType.EMPTY_ZERO

        if raw_chunk.startswith(PartitionSignatures.BOOT_MAGIC):
            return MagicType.BOOT_IMG
        if raw_chunk.startswith(PartitionSignatures.AVB_MAGIC):
            return MagicType.AVB_VBMETA
        if raw_chunk.startswith(PartitionSignatures.DTBO_MAGIC):
            return MagicType.DTBO
        if raw_chunk.startswith(PartitionSignatures.ELF_MAGIC):
            return MagicType.ELF_BOOTLOADER
        if raw_chunk.startswith(PartitionSignatures.SPARSE_MAGIC):
            return MagicType.SPARSE_IMAGE
        if raw_chunk.startswith(PartitionSignatures.HUAWEI_APP_MAGIC):
            return MagicType.HUAWEI_APP
        if len(raw_chunk) >= 520 and raw_chunk[512:520] == PartitionSignatures.GPT_MAGIC:
            return MagicType.GPT_HEADER
        if len(raw_chunk) >= 1082 and raw_chunk[1080:1082] == PartitionSignatures.EXT4_MAGIC:
            return MagicType.EXT4_FS
        if len(raw_chunk) >= 1028 and raw_chunk[1024:1028] == PartitionSignatures.F2FS_MAGIC:
            return MagicType.F2FS_FS

        return MagicType.UNKNOWN

    @classmethod
    def inspect(cls, partition_name: str, raw_chunk: bytes) -> Dict[str, Any]:
        """
        Forensically inspects a partition chunk against the partition name.
        Returns full diagnostic health verdict.
        """
        part_clean = partition_name.strip().lower()
        is_protected = PartitionSignatures.is_protected(part_clean)

        if is_protected:
            return {
                "partition": partition_name,
                "status": "PROTECTED",
                "healthy": True,
                "risk_level": "CRITICAL_LOCKED",
                "detected_type": "USER_DATA_OR_SECURITY",
                "description": "User Data / IMEI / Security partition. HARD LOCKED: NEVER WRITE IN SURGICAL UNBRICK.",
                "safe_to_flash": False,
                "recommendation": "Preserve untouched to guarantee Zero Data Loss."
            }

        detected_type = cls.identify_magic(raw_chunk)
        expected_types = PartitionSignatures.PARTITION_EXPECTATION_MAP.get(part_clean, [])

        # Default inspection template
        result = {
            "partition": partition_name,
            "status": "UNKNOWN",
            "healthy": False,
            "detected_type": detected_type.value,
            "expected_types": [e.value for e in expected_types],
            "details": {},
            "safe_to_flash": True,
            "recommendation": ""
        }

        # Case 1: Empty or zeroed partition
        if detected_type == MagicType.EMPTY_ZERO:
            result["status"] = "EMPTY_OR_WIPED"
            result["healthy"] = False
            result["recommendation"] = f"Partition '{partition_name}' is blank/unwritten! Reflash required."
            return result

        # Case 2: Specific parser based on detected type
        if detected_type == MagicType.BOOT_IMG:
            result["details"] = BootHeaderParser.parse(raw_chunk)
        elif detected_type == MagicType.AVB_VBMETA:
            result["details"] = AVBHeaderParser.parse(raw_chunk)
        elif detected_type == MagicType.DTBO:
            result["details"] = DTBOHeaderParser.parse(raw_chunk)
        elif detected_type == MagicType.ELF_BOOTLOADER:
            result["details"] = ELFHeaderParser.parse(raw_chunk)

        # Case 3: Compare detected with expected
        if expected_types:
            if detected_type in expected_types:
                result["status"] = "HEALTHY"
                result["healthy"] = True
                result["recommendation"] = f"Partition '{partition_name}' header signature is 100% valid."
            else:
                result["status"] = "MISMATCH_CORRUPTED"
                result["healthy"] = False
                result["recommendation"] = (
                    f"CRITICAL: '{partition_name}' expected {[e.value for e in expected_types]} "
                    f"but detected '{detected_type.value}'. File was wrongly written! Reflash exact image."
                )
        else:
            # Generic partition (not in strict map)
            if detected_type != MagicType.UNKNOWN:
                result["status"] = "DETECTED_NON_EMPTY"
                result["healthy"] = True
                result["recommendation"] = f"Valid signature detected ({detected_type.value})."
            else:
                result["status"] = "UNKNOWN_OR_RAW"
                result["healthy"] = True # Might be proprietary raw data
                result["recommendation"] = "Raw or proprietary data. Review if device boots normally."

        return result
