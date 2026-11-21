"""
BSLab Tool PRO - Universal Multi-Format Firmware Parser Unit & Integration Tests.
Verifies format detection, parsing, and flasher table integration for:
Scatter, OFP, OPS, OZIP, Huawei UPDATE.APP, Unisoc PAC, Qualcomm XML, Samsung TAR, Payload, and ZIP.
"""

import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.firmware_parser import UniversalFirmwareParser
from ui.main_window import BSLabApp


class TestUniversalFirmwareParser(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_formats_by_extension(self):
        cases = [
            ("MT6765_Android_scatter.txt", "scatter"),
            ("firmware.ofp", "ofp"),
            ("oneplus_flash.ops", "ops"),
            ("coloros_update.ozip", "ozip"),
            ("UPDATE.APP", "huawei_app"),
            ("honor_update.app", "huawei_app"),
            ("SC9863A_firmware.pac", "pac"),
            ("rawprogram0.xml", "qualcomm_xml"),
            ("AP_S928BXXU1AXB5.tar.md5", "samsung_tar"),
            ("BL_S928B.tar", "samsung_tar"),
            ("payload.bin", "payload"),
            ("fastboot_rom.zip", "zip"),
            ("boot.img", "raw_image"),
        ]

        for fname, expected_fmt in cases:
            fpath = os.path.join(self.dir_path, fname)
            with open(fpath, "wb") as f:
                f.write(b"SAMPLE DATA")
            detected = UniversalFirmwareParser.detect_format(fpath)
            self.assertEqual(detected, expected_fmt, f"Failed detecting {fname}")

    def test_parse_scatter_file(self):
        scatter_content = """
############################################################################################################
# General Setting
- general: MTK_PLATFORM_CFG
  info:
    - config_version: V1.1.2
      platform: MT6765
############################################################################################################
- partition_index: SYS0
  partition_name: preloader
  file_name: preloader_k65v1.bin
  is_download: true
  type: SV5_BL_BIN
  linear_start_addr: 0x0
  physical_start_addr: 0x0
  partition_size: 0x40000
  region: EMMC_BOOT1
- partition_index: SYS1
  partition_name: boot
  file_name: boot.img
  is_download: true
  type: NORMAL_ROM
  linear_start_addr: 0x80000
  physical_start_addr: 0x80000
  partition_size: 0x2000000
  region: EMMC_USER
"""
        sct_path = os.path.join(self.dir_path, "MT6765_Android_scatter.txt")
        with open(sct_path, "w", encoding="utf-8") as f:
            f.write(scatter_content)

        # Create dummy image files
        with open(os.path.join(self.dir_path, "boot.img"), "wb") as f:
            f.write(b"\x00" * 1024)

        parts = UniversalFirmwareParser.parse_firmware(sct_path)
        self.assertEqual(len(parts), 2)
        
        boot_part = [p for p in parts if p.get("name") == "boot"][0]
        self.assertEqual(boot_part["file_name"], "boot.img")
        self.assertTrue(boot_part["exists"])
        self.assertEqual(boot_part["format_type"], "scatter")

    def test_parse_raw_image(self):
        img_path = os.path.join(self.dir_path, "recovery.img")
        with open(img_path, "wb") as f:
            f.write(b"MOCK RECOVERY IMAGE DATA")

        parts = UniversalFirmwareParser.parse_firmware(img_path)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["name"], "recovery")
        self.assertEqual(parts[0]["file_name"], "recovery.img")
        self.assertEqual(parts[0]["format_type"], "raw_image")
        self.assertTrue(parts[0]["exists"])

    def test_parse_zip_firmware_archive(self):
        zip_path = os.path.join(self.dir_path, "fastboot_images.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("boot.img", b"BOOT IMAGE")
            zf.writestr("vbmeta.img", b"VBMETA IMAGE")
            zf.writestr("dtbo.img", b"DTBO IMAGE")

        parts = UniversalFirmwareParser.parse_firmware(zip_path)
        self.assertGreaterEqual(len(parts), 3)
        part_names = [p["name"] for p in parts]
        self.assertIn("boot", part_names)
        self.assertIn("vbmeta", part_names)
        self.assertIn("dtbo", part_names)

    def test_main_window_has_firmware_loaders(self):
        self.assertTrue(hasattr(BSLabApp, "load_scatter_details"))
        self.assertTrue(hasattr(BSLabApp, "load_firmware_details"))
        self.assertTrue(callable(getattr(BSLabApp, "load_scatter_details")))
        self.assertTrue(callable(getattr(BSLabApp, "load_firmware_details")))


if __name__ == "__main__":
    unittest.main()
