"""
BSLab Tool PRO - MediaTek Flash Engine & Servicing Test Suite
Tests ScatterParser, MtkFirmwareFlasher, MtkChipsetDatabase, and IMEI utilities.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mtk.flasher import ScatterParser, MtkFirmwareFlasher, format_bytes
from mtk.chipset_db import MtkChipsetDatabase
from utils.imei_utils import validate_imei, encode_imei_spd_bcd, decode_imei_spd_bcd

class DummyLogger:
    def info(self, msg): pass
    def brom(self, msg): pass
    def success(self, msg): pass
    def warn(self, msg): pass
    def error(self, msg): pass


class TestMtkFlashEngine(unittest.TestCase):

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertIn("KB", format_bytes(2048))
        self.assertIn("MB", format_bytes(1048576 * 5))
        self.assertIn("GB", format_bytes(1073741824 * 2))

    def test_scatter_parser_modern_yaml(self):
        scatter_content = """# MediaTek Android Scatter
- partition_index: SYS0
  partition_name: preloader
  file_name: preloader.bin
  is_download: true
  linear_start_addr: 0x0
  partition_size: 0x40000

- partition_index: SYS1
  partition_name: boot
  file_name: boot.img
  is_download: true
  linear_start_addr: 0x8000
  partition_size: 0x4000000
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            scat_path = os.path.join(tmp_dir, "MT6768_Android_scatter.txt")
            with open(scat_path, "w", encoding="utf-8") as f:
                f.write(scatter_content)

            # Create dummy preloader.bin
            with open(os.path.join(tmp_dir, "preloader.bin"), "wb") as f:
                f.write(b"\x00" * 4096)

            parts = ScatterParser.parse(scat_path)
            self.assertEqual(len(parts), 2)
            self.assertEqual(parts[0]["name"], "preloader")
            self.assertTrue(parts[0]["exists"])
            self.assertEqual(parts[0]["file_size"], 4096)
            self.assertEqual(parts[1]["name"], "boot")
            self.assertFalse(parts[1]["exists"])

    def test_scatter_parser_legacy_no_dash(self):
        scatter_content = """partition_index: SYS0
  partition_name: PRELOADER
  file_name: preloader.bin
  is_download: true
  linear_start_addr: 0x0
  partition_size: 0x40000

partition_index: SYS1
  partition_name: RECOVERY
  file_name: recovery.img
  is_download: true
  linear_start_addr: 0x10000
  partition_size: 0x2000000
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            scat_path = os.path.join(tmp_dir, "MT6580_Android_scatter.txt")
            with open(scat_path, "w", encoding="utf-8") as f:
                f.write(scatter_content)

            parts = ScatterParser.parse(scat_path)
            self.assertEqual(len(parts), 2)
            self.assertEqual(parts[0]["name"], "PRELOADER")
            self.assertEqual(parts[1]["name"], "RECOVERY")

    def test_find_preloader_case_insensitive(self):
        flasher = MtkFirmwareFlasher(DummyLogger())
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create PRELOADER_GALE.BIN
            pl_path = os.path.join(tmp_dir, "PRELOADER_GALE.BIN")
            with open(pl_path, "wb") as f:
                f.write(b"\x00" * 2048)

            found = flasher._find_preloader(tmp_dir)
            self.assertIsNotNone(found)
            self.assertTrue(os.path.exists(found))

    def test_is_valid_mtkclient_loader(self):
        flasher = MtkFirmwareFlasher(DummyLogger())
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Container DA (.da or allinone) must be rejected for mtkclient CLI
            da_file = os.path.join(tmp_dir, "MTK_AllInOne_DA.bin")
            with open(da_file, "wb") as f:
                f.write(b"\x00" * 50000)
            self.assertFalse(flasher._is_valid_mtkclient_loader(da_file))

            # Valid flat binary payload
            payload_bin = os.path.join(tmp_dir, "custom_payload.bin")
            with open(payload_bin, "wb") as f:
                f.write(b"\x00" * 5000)
            self.assertTrue(flasher._is_valid_mtkclient_loader(payload_bin))

            # Too small
            tiny_bin = os.path.join(tmp_dir, "tiny.bin")
            with open(tiny_bin, "wb") as f:
                f.write(b"\x00" * 50)
            self.assertFalse(flasher._is_valid_mtkclient_loader(tiny_bin))

    def test_gsm_operations_signature_compatibility(self):
        flasher = MtkFirmwareFlasher(DummyLogger())
        # Ensure all operations accept restart_after_job without TypeError
        import inspect
        ops = [
            flasher.reset_frp,
            flasher.factory_reset,
            flasher.safe_format,
            flasher.demo_remove,
            flasher.unlock_bootloader,
            flasher.relock_bootloader,
            flasher.patch_dm_verity,
            flasher.erase_rpmb,
            flasher.erase_partition
        ]
        for op in ops:
            params = inspect.signature(op).parameters
            self.assertTrue("restart_after_job" in params or "kwargs" in params, f"{op.__name__} must accept restart_after_job")

    def test_chipset_db_lookup(self):
        g85 = MtkChipsetDatabase.lookup(0x6768)
        self.assertIn("MT6769", g85["soc"])

        d700 = MtkChipsetDatabase.lookup(0x6833)
        self.assertIn("MT6833", d700["soc"])

        d9000 = MtkChipsetDatabase.lookup(0x6983)
        self.assertIn("MT6983", d9000["soc"])

    def test_imei_validation_and_bcd(self):
        valid, imei15, _ = validate_imei("86123456789012")  # 14 digits -> auto Luhn
        self.assertTrue(valid)
        self.assertEqual(len(imei15), 15)

        bcd = encode_imei_spd_bcd(imei15)
        self.assertEqual(len(bcd), 8)

        decoded = decode_imei_spd_bcd(bcd)
        self.assertEqual(decoded, imei15)


if __name__ == "__main__":
    unittest.main()
