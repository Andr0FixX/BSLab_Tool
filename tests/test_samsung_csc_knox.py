import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import MagicMock
from engines.samsung.samsung_modem import SamsungModemEngine

class TestSamsungCSCKnox(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock()
        self.engine = SamsungModemEngine(logger=self.mock_logger)

    def test_read_csc_status(self):
        # Mock AT response for PRECON
        def mock_at(port, cmd):
            if "PRECON?" in cmd:
                return "AT+PRECON?\r\n+PRECON: INS\r\nOK"
            return "OK"

        self.engine.send_at_command = mock_at
        res = self.engine.read_csc_status("COM3")
        self.assertEqual(res.get("current_csc"), "INS")

    def test_change_csc(self):
        commands_sent = []
        def mock_at(port, cmd):
            commands_sent.append(cmd)
            return "OK"

        self.engine.send_at_command = mock_at
        success = self.engine.change_csc("COM3", "TUR", reboot_after=True)
        self.assertTrue(success)
        self.assertIn("AT+PRECON=0,TUR", commands_sent)
        self.assertIn("AT+PRECON=1,TUR", commands_sent)
        self.assertIn("AT+REBOOT", commands_sent)

    def test_read_knox_guard_and_security(self):
        def mock_at(port, cmd):
            if "DEVCONINFO" in cmd:
                return "DEVCONINFO\r\nKG:COMPLETED\r\nWAR:0x0\r\nFRP:OFF\r\nOK"
            return "OK"

        self.engine.send_at_command = mock_at
        sec = self.engine.read_knox_guard_and_security("COM3")
        self.assertEqual(sec.get("knox_guard"), "COMPLETED")
        self.assertEqual(sec.get("knox_warranty"), "0x0")
        self.assertEqual(sec.get("frp_status"), "OFF / Unlocked")

if __name__ == "__main__":
    unittest.main()
