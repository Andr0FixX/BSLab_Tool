import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.path_utils import get_platform_tool_path

class TestFastbootToolIntegration(unittest.TestCase):

    def test_bundled_tools_exist(self):
        adb_p = get_platform_tool_path("adb")
        fb_p = get_platform_tool_path("fastboot")
        self.assertTrue(os.path.exists(adb_p), f"adb not found at {adb_p}")
        self.assertTrue(os.path.exists(fb_p), f"fastboot not found at {fb_p}")

    def test_partition_name_detection(self):
        from ui.views.fastboot_view import FastbootADBView
        detect = FastbootADBView._detect_partition_name
        self.assertEqual(detect(None, "boot.img"), "boot")
        self.assertEqual(detect(None, "recovery_signed.img"), "recovery")
        self.assertEqual(detect(None, "vbmeta.img"), "vbmeta")
        self.assertEqual(detect(None, "super.img"), "super")
        self.assertEqual(detect(None, "userdata_ext4.img"), "userdata")
        self.assertEqual(detect(None, "NON-HLOS.bin"), "modem")

if __name__ == "__main__":
    unittest.main()
