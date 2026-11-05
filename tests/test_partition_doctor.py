"""
BSLab Tool PRO - Test Suite for Surgical Partition Doctor
Tests binary signature verification, magic byte detection, and data safeguard policies.
"""

import sys
import struct
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.partition_doctor.signatures import PartitionSignatures, MagicType
from engines.partition_doctor.header_parser import (
    PartitionHealthInspector,
    BootHeaderParser,
    AVBHeaderParser,
    DTBOHeaderParser,
    ELFHeaderParser
)

class TestPartitionDoctor(unittest.TestCase):

    def test_boot_header_valid(self):
        # Construct synthetic valid Android Boot header v2
        # magic (8s), kernel_size (I), kernel_addr (I), ramdisk_size (I), ramdisk_addr (I),
        # second_size (I), second_addr (I), tags_addr (I), page_size (I), header_version (I), os_version (I)
        os_ver = (13 << 25) | (0 << 18) | (0 << 11) | (24 << 4) | 10 # Android 13, 2024-10
        raw_boot = struct.pack(
            "<8sIIIIIIIIII",
            b"ANDROID!", 25000000, 0x10008000, 4500000, 0x11000000,
            0, 0, 0x10000100, 2048, 2, os_ver
        )
        raw_boot = raw_boot.ljust(2048, b"\x00")

        diag = PartitionHealthInspector.inspect("boot_a", raw_boot)
        self.assertEqual(diag["status"], "HEALTHY")
        self.assertTrue(diag["healthy"])
        self.assertEqual(diag["details"]["header_version"], 2)
        self.assertEqual(diag["details"]["os_version"], "13")
        self.assertEqual(diag["details"]["security_patch"], "2024-10")

    def test_corrupted_boot_partition(self):
        # Simulate user flashing a DTBO or random image onto boot partition!
        raw_dtbo = struct.pack(">4sIIIIIII", b"\xD7\xB7\xAB\x1E", 102400, 32, 256, 4, 32, 2048, 1)
        raw_dtbo = raw_dtbo.ljust(2048, b"\x00")

        diag = PartitionHealthInspector.inspect("boot", raw_dtbo)
        self.assertEqual(diag["status"], "MISMATCH_CORRUPTED")
        self.assertFalse(diag["healthy"])
        self.assertIn("CRITICAL", diag["recommendation"])
        self.assertIn("DTBO", diag["recommendation"])

    def test_avb_vbmeta_valid(self):
        raw_avb = struct.pack("<4sIIQQI", b"AVB0", 1, 2, 1024, 2048, 1)
        raw_avb = raw_avb.ljust(256, b"\x00")

        diag = PartitionHealthInspector.inspect("vbmeta_a", raw_avb)
        self.assertEqual(diag["status"], "HEALTHY")
        self.assertTrue(diag["healthy"])
        self.assertEqual(diag["details"]["libavb_version"], "1.2")

    def test_dtbo_valid(self):
        raw_dtbo = struct.pack(">4sIIIIIII", b"\xD7\xB7\xAB\x1E", 20480, 32, 256, 2, 32, 2048, 1)
        raw_dtbo = raw_dtbo.ljust(2048, b"\x00")

        diag = PartitionHealthInspector.inspect("dtbo", raw_dtbo)
        self.assertEqual(diag["status"], "HEALTHY")
        self.assertTrue(diag["healthy"])
        self.assertEqual(diag["details"]["dt_entry_count"], 2)

    def test_elf_bootloader_valid(self):
        # 64-bit ARM64 ELF header
        e_ident = b"\x7FELF\x02\x01\x01\x00" + b"\x00" * 8
        e_body = struct.pack("<HHIQ", 2, 183, 1, 0x80000000)
        raw_elf = (e_ident + e_body).ljust(512, b"\x00")

        diag = PartitionHealthInspector.inspect("abl_a", raw_elf)
        self.assertEqual(diag["status"], "HEALTHY")
        self.assertTrue(diag["healthy"])
        self.assertTrue(diag["details"]["is_64bit"])
        self.assertIn("AArch64", diag["details"]["architecture"])

    def test_empty_partition_detection(self):
        raw_empty = b"\x00" * 1024
        diag = PartitionHealthInspector.inspect("boot_b", raw_empty)
        self.assertEqual(diag["status"], "EMPTY_OR_WIPED")
        self.assertFalse(diag["healthy"])

    def test_userdata_safeguard_lockout(self):
        # Even if userdata has random bytes, it must be locked!
        raw_data = b"RANDOM_USER_DATA" * 50
        diag = PartitionHealthInspector.inspect("userdata", raw_data)
        self.assertEqual(diag["status"], "PROTECTED")
        self.assertFalse(diag["safe_to_flash"])
        self.assertIn("HARD LOCKED", diag["description"])

        # Also test nvram and persist
        self.assertTrue(PartitionSignatures.is_protected("nvram"))
        self.assertTrue(PartitionSignatures.is_protected("persist"))
        self.assertTrue(PartitionSignatures.is_protected("modemst1"))

if __name__ == "__main__":
    unittest.main()
