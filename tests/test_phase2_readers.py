"""
BSLab Tool PRO - Test Suite for Phase 2 Low-Level Partition Readers
Tests GPT binary parsing, Fastboot A/B slot diagnostic, and EDL header stream evaluation.
"""

import sys
import uuid
import struct
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.partition_doctor.signatures import PartitionSignatures
from engines.partition_doctor.gpt_parser import GPTParser, GPTPartitionEntry
from engines.partition_doctor.fastboot_reader import FastbootPartitionReader
from engines.partition_doctor.edl_reader import EDLPartitionReader

class TestPhase2Readers(unittest.TestCase):

    def _create_synthetic_gpt(self):
        sector_size = 512
        # Create 34 sectors
        data = bytearray(sector_size * 34)

        # LBA 1: GPT Header (offset 512)
        # signature (8s), revision (I), header_size (I), crc32 (I), reserved (I),
        # current_lba (Q), backup_lba (Q), first_usable_lba (Q), last_usable_lba (Q),
        # disk_guid (16s), partition_entry_lba (Q), num_entries (I), entry_size (I), entries_crc32 (I)
        guid_bytes = uuid.uuid4().bytes_le
        hdr = struct.pack(
            "<8sIIIIQQQQ16sQII",
            b"EFI PART", 0x00010000, 92, 0, 0,
            1, 62500000, 34, 62499966,
            guid_bytes, 2, 128, 128
        )
        data[512:512 + len(hdr)] = hdr

        # LBA 2: Partition entries (offset 1024, each 128 bytes)
        partitions_to_add = [
            ("boot_a", 2048, 133119),     # 64 MB
            ("dtbo_a", 133120, 153599),   # 10 MB
            ("super", 153600, 8546303),   # ~4.1 GB
            ("userdata", 8546304, 62499966) # Rest
        ]

        for i, (name, s_lba, e_lba) in enumerate(partitions_to_add):
            off = 1024 + (i * 128)
            type_guid = uuid.uuid4().bytes_le
            uniq_guid = uuid.uuid4().bytes_le
            attrs = 0
            name_bytes = name.encode("utf-16le").ljust(72, b"\x00")
            
            entry_bytes = type_guid + uniq_guid + struct.pack("<QQQ", s_lba, e_lba, attrs) + name_bytes
            data[off:off + 128] = entry_bytes

        return bytes(data)

    def test_gpt_parser_valid(self):
        raw_gpt = self._create_synthetic_gpt()
        res = GPTParser.parse(raw_gpt, sector_size=512)

        self.assertTrue(res["valid"])
        self.assertEqual(res["total_partitions"], 4)
        
        part_map = res["partition_map"]
        self.assertIn("boot_a", part_map)
        self.assertIn("userdata", part_map)

        boot_entry: GPTPartitionEntry = part_map["boot_a"]
        self.assertEqual(boot_entry.start_lba, 2048)
        self.assertEqual(boot_entry.size_mb, 64.0)
        self.assertFalse(boot_entry.is_protected)

        userdata_entry: GPTPartitionEntry = part_map["userdata"]
        self.assertTrue(userdata_entry.is_protected) # Critical data safeguard!

    def test_fastboot_ab_slot_failure_diagnosis(self):
        reader = FastbootPartitionReader(serial="TEST_SERIAL")

        # Mock 'fastboot getvar all' response with failed slot 'a' and healthy slot 'b'
        mock_vars = {
            "product": "redmi_note_11",
            "unlocked": "yes",
            "current-slot": "a",
            "slot-successful:a": "no",
            "slot-unbootable:a": "yes",
            "slot-retry-count:a": "0",
            "slot-successful:b": "yes",
            "slot-unbootable:b": "no",
            "partition-size:boot_a": "0x4000000",
            "partition-size:boot_b": "0x4000000"
        }
        reader.get_all_variables = MagicMock(return_value=mock_vars)

        report = reader.inspect_device_health()
        self.assertTrue(report["connected"])
        self.assertFalse(report["is_overall_healthy"])
        self.assertEqual(len(report["anomalies"]), 1)
        self.assertIn("slot 'a' marked unbootable", report["anomalies"][0])
        
        # Verify instant unbrick recommendation was generated!
        self.assertEqual(len(report["recommendations"]), 1)
        self.assertIn("fastboot set_active b", report["recommendations"][0])

    def test_edl_partition_reader_diagnosis(self):
        raw_gpt = self._create_synthetic_gpt()
        edl = EDLPartitionReader()
        gpt_res = edl.parse_gpt_from_bytes(raw_gpt)
        self.assertTrue(gpt_res["valid"])

        # Mock stream callback: boot_a returns valid ANDROID! magic, dtbo_a returns random garbage (corrupted)
        def mock_stream(part_name, start_lba, num_sectors):
            if part_name == "boot_a":
                # Valid boot
                return b"ANDROID!" + (b"\x00" * 4088)
            elif part_name == "dtbo_a":
                # Corrupted dtbo
                return b"CORRUPTED_GARBAGE_BYTES" + (b"\x00" * 4070)
            return b"\x00" * 4096

        diags = edl.diagnose_partitions_from_headers(gpt_res, mock_stream)
        self.assertTrue(len(diags) >= 2)

        diag_map = {d["partition"]: d for d in diags}
        self.assertEqual(diag_map["boot_a"]["status"], "HEALTHY")
        self.assertEqual(diag_map["dtbo_a"]["status"], "MISMATCH_CORRUPTED")

if __name__ == "__main__":
    unittest.main()
