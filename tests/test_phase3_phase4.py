"""
BSLab Tool PRO - Test Suite for Phase 3 & 4
Tests Anomaly Detection Brain, Zero-Data-Loss Safeguard Firewall, and Surgical Flasher.
"""

import os
import sys
import zipfile
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.partition_doctor.analyzer import PartitionDoctorBrain, FaultSeverity
from engines.partition_doctor.surgical_flasher import (
    DataLossFirewall,
    SurgicalSinglePartitionFlasher,
    ProtectedPartitionViolationError,
    HeaderMismatchError
)

class TestPhase3AndPhase4(unittest.TestCase):

    def test_fastboot_anomaly_instant_fix(self):
        # Failed slot A with healthy slot B
        mock_data = {
            "connected": True,
            "product": "redmi_note_11",
            "current_slot": "a",
            "slot_report": {
                "a": {"healthy": False, "successful": "no", "unbootable": "yes"},
                "b": {"healthy": True, "successful": "yes", "unbootable": "no"}
            },
            "partitions": {
                "boot_a": {"size_bytes": 67108864, "healthy": True}
            }
        }
        report = PartitionDoctorBrain.analyze_fastboot_health(mock_data)
        self.assertEqual(report.overall_health, FaultSeverity.INSTANT_FIX)
        self.assertEqual(len(report.instant_commands), 1)
        self.assertEqual(report.instant_commands[0], "fastboot set_active b")
        self.assertEqual(report.userdata_status, "100% PROTECTED & UNTOUCHED")

    def test_edl_partition_magic_mismatch_analysis(self):
        diags = [
            {
                "partition": "boot_a",
                "status": "MISMATCH_CORRUPTED",
                "healthy": False,
                "expected_types": ["BOOT_IMG"],
                "detected_type": "DTBO"
            },
            {
                "partition": "userdata",
                "status": "PROTECTED",
                "healthy": True
            }
        ]
        report = PartitionDoctorBrain.analyze_partition_inspections(diags, device_mode="EDL_9008")
        self.assertEqual(report.overall_health, FaultSeverity.SURGICAL_FIXABLE)
        self.assertEqual(len(report.corrupted_partitions), 1)
        self.assertEqual(report.corrupted_partitions[0], "boot_a")
        self.assertEqual(len(report.surgical_repair_steps), 1)
        self.assertEqual(report.surgical_repair_steps[0]["action"], "SURGICAL_RESTORE")

    def test_dataloss_firewall_lockout(self):
        # 1. Allowed partitions must pass
        DataLossFirewall.validate_target("boot")
        DataLossFirewall.validate_target("boot_a")
        DataLossFirewall.validate_target("recovery")
        DataLossFirewall.validate_target("dtbo")

        # 2. Protected partitions must raise ProtectedPartitionViolationError
        with self.assertRaises(ProtectedPartitionViolationError):
            DataLossFirewall.validate_target("userdata")

        with self.assertRaises(ProtectedPartitionViolationError):
            DataLossFirewall.validate_target("nvram")

        with self.assertRaises(ProtectedPartitionViolationError):
            DataLossFirewall.validate_target("persist_a")

        with self.assertRaises(ProtectedPartitionViolationError):
            DataLossFirewall.validate_target("modemst1")

        # 3. Filter check
        mixed = ["boot", "userdata", "dtbo", "nvram", "cache"]
        safe = DataLossFirewall.filter_safe_partitions(mixed)
        self.assertEqual(safe, ["boot", "dtbo"])

    def test_pre_flash_header_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a fake DTBO image
            dtbo_path = os.path.join(tmp_dir, "dtbo.img")
            with open(dtbo_path, "wb") as f:
                f.write(b"\xD7\xB7\xAB\x1E" + (b"\x00" * 4092))

            # Attempting to flash DTBO into boot partition MUST be rejected by safety check!
            with self.assertRaises(HeaderMismatchError):
                SurgicalSinglePartitionFlasher.verify_image_before_flash("boot_a", dtbo_path)

            # Flashing DTBO into dtbo partition MUST succeed verification
            SurgicalSinglePartitionFlasher.verify_image_before_flash("dtbo_a", dtbo_path)

    def test_single_image_extraction_from_zip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "firmware.zip")
            out_dir = os.path.join(tmp_dir, "extracted")

            # Create synthetic firmware zip containing boot.img and system.img
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.writestr("boot.img", b"ANDROID!" + (b"\x00" * 100))
                z.writestr("system.img", b"LARGE_SYSTEM_IMAGE" * 50)

            # Extract ONLY boot.img
            extracted = SurgicalSinglePartitionFlasher.extract_single_image(zip_path, "boot", out_dir)
            self.assertTrue(os.path.exists(extracted))
            self.assertEqual(os.path.basename(extracted).lower(), "boot.img")
            # System image was NOT extracted, saving time and disk space!
            self.assertFalse(os.path.exists(os.path.join(out_dir, "system.img")))

if __name__ == "__main__":
    unittest.main()
