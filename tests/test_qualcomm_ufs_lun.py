import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import shutil
import tempfile
from engines.qualcomm.xml_parser import QualcommXMLParser

class TestQualcommUFSLUN(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.xml0 = os.path.join(self.test_dir, "rawprogram0.xml")
        self.xml1 = os.path.join(self.test_dir, "rawprogram1.xml")

        # Create dummy partition files
        with open(os.path.join(self.test_dir, "boot.img"), "wb") as f:
            f.write(b"BOOT_IMG_DATA")
        with open(os.path.join(self.test_dir, "xbl_a.img"), "wb") as f:
            f.write(b"XBL_A_DATA")

        # rawprogram0 (LUN 0)
        xml0_content = """<?xml version="1.0" ?>
<data>
  <program SECTOR_SIZE_IN_BYTES="4096" file_sector_offset="0" filename="boot.img" label="boot" num_partition_sectors="32" physical_partition_number="0" size_in_KB="128.0" sparse="false" start_byte_hex="0x0" start_sector="100"/>
</data>"""
        with open(self.xml0, "w") as f:
            f.write(xml0_content)

        # rawprogram1 (LUN 1)
        xml1_content = """<?xml version="1.0" ?>
<data>
  <program SECTOR_SIZE_IN_BYTES="4096" file_sector_offset="0" filename="xbl_a.img" label="xbl_a" num_partition_sectors="16" physical_partition_number="1" size_in_KB="64.0" sparse="false" start_byte_hex="0x0" start_sector="0"/>
</data>"""
        with open(self.xml1, "w") as f:
            f.write(xml1_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_rawprogram_with_lun(self):
        parts0 = QualcommXMLParser.parse_rawprogram(self.xml0)
        self.assertEqual(len(parts0), 1)
        self.assertEqual(parts0[0]["name"], "boot")
        self.assertEqual(parts0[0]["lun"], 0)

        parts1 = QualcommXMLParser.parse_rawprogram(self.xml1)
        self.assertEqual(len(parts1), 1)
        self.assertEqual(parts1[0]["name"], "xbl_a")
        self.assertEqual(parts1[0]["lun"], 1)

    def test_parse_all_rawprograms(self):
        all_parts = QualcommXMLParser.parse_all_rawprograms(self.test_dir)
        self.assertEqual(len(all_parts), 2)
        names = {p["name"]: p["lun"] for p in all_parts}
        self.assertIn("boot", names)
        self.assertIn("xbl_a", names)
        self.assertEqual(names["boot"], 0)
        self.assertEqual(names["xbl_a"], 1)

if __name__ == "__main__":
    unittest.main()
