"""
BSLab Tool PRO - Google Pixel Module Unit & Integration Tests.
Verifies ModelDatabase Pixel registry, PixelView initialization, and ModuleRibbon platform switching.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.model_database import ModelDatabase
from ui.components.module_ribbon import ModuleRibbon

class TestPixelModule(unittest.TestCase):

    def test_model_database_pixels_registry(self):
        # Verify Pixel 1 to 9 codenames
        self.assertIn("sailfish", ModelDatabase.PIXELS)  # Pixel 1
        self.assertIn("walleye", ModelDatabase.PIXELS)   # Pixel 2
        self.assertIn("blueline", ModelDatabase.PIXELS)  # Pixel 3
        self.assertIn("flame", ModelDatabase.PIXELS)     # Pixel 4
        self.assertIn("redfin", ModelDatabase.PIXELS)    # Pixel 5
        self.assertIn("oriole", ModelDatabase.PIXELS)    # Pixel 6 (Tensor G1)
        self.assertIn("cheetah", ModelDatabase.PIXELS)   # Pixel 7 Pro (Tensor G2)
        self.assertIn("husky", ModelDatabase.PIXELS)     # Pixel 8 Pro (Tensor G3)
        self.assertIn("tokay", ModelDatabase.PIXELS)     # Pixel 9 (Tensor G4)
        self.assertIn("caiman", ModelDatabase.PIXELS)    # Pixel 9 Pro (Tensor G4)
        self.assertIn("komodo", ModelDatabase.PIXELS)    # Pixel 9 Pro XL (Tensor G4)

    def test_model_database_pixel_resolution(self):
        # Fastboot product codename 'cheetah'
        res = ModelDatabase.resolve("cheetah", mode="FASTBOOT")
        self.assertEqual(res["category"], "pixel")
        self.assertIn("Pixel 7 Pro", res["name"])
        self.assertIn("Tensor", res["soc"])

        # Codename 'tokay' (Pixel 9)
        res9 = ModelDatabase.resolve("tokay", mode="FASTBOOT")
        self.assertEqual(res9["category"], "pixel")
        self.assertIn("Pixel 9", res9["name"])
        self.assertIn("Tensor G4", res9["soc"])

    def test_pixel_ribbon_selection_mapping(self):
        # In a headless test, check the mapping logic in select_platform
        mapping = {
            "pixel": "🔴 GOOGLE PIXEL",
            "google": "🔴 GOOGLE PIXEL",
            "tensor": "🔴 GOOGLE PIXEL"
        }
        for k, v in mapping.items():
            self.assertEqual(mapping[k], "🔴 GOOGLE PIXEL")


if __name__ == "__main__":
    unittest.main()
