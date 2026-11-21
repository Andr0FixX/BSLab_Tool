import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from utils.imei_utils import validate_imei, calculate_luhn_check_digit

class TestADBFastbootIMEIRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except Exception:
            cls.root = None

    @classmethod
    def tearDownClass(cls):
        if cls.root:
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_luhn_validation(self):
        # Standard test IMEI with known valid Luhn checksum
        # 35894109123456 -> check digit
        prefix14 = "35894109123456"
        check_digit = calculate_luhn_check_digit(prefix14)
        full_imei = prefix14 + str(check_digit)
        
        is_valid, computed_full, _ = validate_imei(full_imei)
        self.assertTrue(is_valid)
        self.assertEqual(computed_full, full_imei)

        # Tampered check digit should fail
        wrong_digit = str((int(check_digit) + 1) % 10)
        is_valid_wrong, _, _ = validate_imei(prefix14 + wrong_digit)
        self.assertFalse(is_valid_wrong)

    def test_fastboot_view_imei_attributes(self):
        if not self.root:
            self.skipTest("Tkinter display not available")
        
        from ui.views.fastboot_view import FastbootADBView
        view = FastbootADBView(self.root, controller=MagicMock())
        
        self.assertTrue(hasattr(view, "adb_imei1_var"))
        self.assertTrue(hasattr(view, "adb_imei2_var"))
        self.assertTrue(hasattr(view, "_adb_read_imei"))
        self.assertTrue(hasattr(view, "_adb_write_imei"))
        self.assertTrue(hasattr(view, "_fb_read_imei"))

    def test_smart_hub_imei_actions(self):
        from ui.views.smart_hub_view import SmartHubView
        mock_controller = MagicMock()
        mock_controller.fastboot_view = MagicMock()
        hub = SmartHubView(None, controller=mock_controller)

        # Check FASTBOOT actions
        fb_actions = hub._get_actions_for_mode("FASTBOOT")
        fb_titles = [a.get("title", "") for a in fb_actions]
        self.assertTrue(any("Hardware IMEI" in t for t in fb_titles))

        # Check ADB actions
        adb_actions = hub._get_actions_for_mode("ADB")
        adb_titles = [a.get("title", "") for a in adb_actions]
        self.assertTrue(any("Hardware IMEI (ADB)" in t for t in adb_titles))

    def test_adb_imei_read_simulation(self):
        if not self.root:
            self.skipTest("Tkinter display not available")
            
        from ui.views.fastboot_view import FastbootADBView
        mock_controller = MagicMock()
        view = FastbootADBView(self.root, controller=mock_controller)
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "[persist.radio.imei]: [358941091234567]\n[persist.radio.imei2]: [358941091234568]\n"
        
        # Patch threading.Thread to execute synchronously
        with patch("threading.Thread", side_effect=lambda target, daemon=True: MagicMock(start=lambda: target())):
            with patch.object(view, "_run_tool", return_value=mock_proc):
                view._adb_read_imei()
                
        self.assertEqual(view.adb_imei1_var.get(), "358941091234567")
        self.assertEqual(view.adb_imei2_var.get(), "358941091234568")

if __name__ == "__main__":
    unittest.main()
