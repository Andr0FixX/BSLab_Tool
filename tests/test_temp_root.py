"""
BSLab Tool PRO - 1-Click Temporary Root Unit & Integration Tests.
Verifies temp root target definitions, Smart Hub action integration,
and Fastboot/ADB controller operation hooks.
"""

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.path_utils import get_app_root


class TestTempRootIntegration(unittest.TestCase):

    def test_temp_root_targets_database(self):
        """Verifies engines/temp_root_targets.json exists, is valid JSON, and has targets."""
        targets_file = Path(get_app_root()) / "engines" / "temp_root_targets.json"
        self.assertTrue(targets_file.exists(), "temp_root_targets.json must exist")
        
        with open(targets_file, "r", encoding="utf-8") as f:
            targets = json.load(f)
        
        self.assertIsInstance(targets, list)
        self.assertGreater(len(targets), 5)
        
        # Check first target fields
        sample = targets[0]
        self.assertIn("brand", sample)
        self.assertIn("model", sample)
        self.assertIn("kernel", sample)
        self.assertIn("exploit", sample)

    def test_smart_hub_adb_temp_root_action(self):
        """Verifies SmartHubView provides 1-Click Temp Root in ADB mode."""
        from ui.views.smart_hub_view import SmartHubView
        
        # Create a mock view instance without GUI layout
        view = SmartHubView.__new__(SmartHubView)
        view.current_profile = {}
        view.current_details = {}
        view.controller = MagicMock()
        view._switch_and_run = MagicMock()

        actions = view._get_actions_for_mode("ADB")
        temp_root_actions = [a for a in actions if "temp root" in a.get("btn_text", "").lower() or "temp root" in a.get("title", "").lower()]
        self.assertGreater(len(temp_root_actions), 0, "ADB mode actions must contain 1-Click Temp Root")
        
        btn = temp_root_actions[0]
        self.assertEqual(btn["badge"], "SAFE TEMP ROOT")
        self.assertEqual(btn["category"], "unlock")

    def test_smart_hub_fastboot_temp_root_action(self):
        """Verifies SmartHubView provides 1-Click Temp Root in Fastboot mode."""
        from ui.views.smart_hub_view import SmartHubView
        
        view = SmartHubView.__new__(SmartHubView)
        view.current_profile = {}
        view.current_details = {}
        view.controller = MagicMock()
        view._switch_and_run = MagicMock()

        actions = view._get_actions_for_mode("FASTBOOT")
        temp_root_actions = [a for a in actions if "temp root" in a.get("btn_text", "").lower() or "temp root" in a.get("title", "").lower()]
        self.assertGreater(len(temp_root_actions), 0, "Fastboot mode actions must contain 1-Click Temp Root")
        
        btn = temp_root_actions[0]
        self.assertEqual(btn["badge"], "ZERO RISK RAM")
        self.assertEqual(btn["category"], "unlock")

    def test_main_window_has_op_temp_root(self):
        """Verifies BSLabApp controller exposes op_temp_root."""
        from ui.main_window import BSLabApp
        self.assertTrue(hasattr(BSLabApp, "op_temp_root"), "BSLabApp must define op_temp_root")
        self.assertTrue(callable(getattr(BSLabApp, "op_temp_root")), "op_temp_root must be callable")

    def test_fastboot_view_temp_root_delegation(self):
        """Verifies FastbootADBView delegates _adb_temp_root and _fb_temp_root to controller."""
        from ui.views.fastboot_view import FastbootADBView
        
        view = FastbootADBView.__new__(FastbootADBView)
        view.controller = MagicMock()
        view.logger = MagicMock()

        view._adb_temp_root()
        view.controller.op_temp_root.assert_called_with("ADB")

        view._fb_temp_root()
        view.controller.op_temp_root.assert_called_with("FASTBOOT")


if __name__ == "__main__":
    unittest.main()
