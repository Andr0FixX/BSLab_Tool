"""
Unit Test & Integration Verification for Samsung Odin Protocol & Modem Engine.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import struct
import tempfile
import tarfile
import hashlib
from engines.samsung.odin_protocol import OdinProtocolEngine, PitParser, PitEntry, PIT_MAGIC
from engines.samsung.samsung_modem import SamsungModemEngine


def test_pit_parser():
    print("[TEST] Testing Samsung PIT Parser...")
    # Construct a valid synthetic Samsung PIT binary
    magic = PIT_MAGIC
    entry_count = 2

    # Header: 28 bytes
    header = struct.pack("<II20s", magic, entry_count, b"\x00" * 20)

    # Entry 1: BOOT
    # Format: binary_type(4), device_type(4), partition_id(4), partition_type(4),
    # partition_name(32), filename(32), block_start(4), block_count(4), padding(44) = 132 bytes
    p1_name = b"BOOT\x00" + b"\x00" * 27
    p1_file = b"boot.img\x00" + b"\x00" * 23
    entry1 = struct.pack("<IIII32s32sII44s", 0, 2, 1, 0, p1_name, p1_file, 0x1000, 0x10000, b"\x00" * 44)

    # Entry 2: RECOVERY
    p2_name = b"RECOVERY\x00" + b"\x00" * 23
    p2_file = b"recovery.img\x00" + b"\x00" * 19
    entry2 = struct.pack("<IIII32s32sII44s", 0, 2, 2, 0, p2_name, p2_file, 0x20000, 0x20000, b"\x00" * 44)

    pit_data = header + entry1 + entry2
    parsed_entries = PitParser.parse_pit_bytes(pit_data)

    assert len(parsed_entries) == 2, f"Expected 2 entries, got {len(parsed_entries)}"
    assert parsed_entries[0].partition_name == "BOOT"
    assert parsed_entries[0].filename == "boot.img"
    assert parsed_entries[0].size_mb == 32.0 # 65536 blocks * 512 / 1024 / 1024 = 32 MB
    assert parsed_entries[1].partition_name == "RECOVERY"
    print("  [OK] PIT Parser Passed successfully.")


def test_tar_md5_verifier():
    print("[TEST] Testing Samsung TAR.MD5 Integrity Verifier...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy tar archive
        tar_path = os.path.join(tmpdir, "BL_A125F.tar.md5")
        dummy_boot = os.path.join(tmpdir, "boot.img")
        with open(dummy_boot, "wb") as f:
            f.write(b"\x00" * 4096)

        with tarfile.open(tar_path, "w") as tar:
            tar.add(dummy_boot, arcname="boot.img")

        # Append valid md5 checksum
        with open(tar_path, "rb") as f:
            tar_bytes = f.read()
        md5_hash = hashlib.md5(tar_bytes).hexdigest()
        with open(tar_path, "a") as f:
            f.write(f"\n{md5_hash}\n")

        valid, msg = OdinProtocolEngine.verify_tar_md5(tar_path)
        print(f"  Result: {valid} - {msg}")
        assert valid is True, f"Expected valid MD5, got {valid}"

        # Test tar contents inspection
        engine = OdinProtocolEngine()
        contents = engine.inspect_tar_contents(tar_path)
        assert len(contents) >= 1
        assert contents[0]["name"] == "boot.img"
        print("  [OK] TAR Inspection Passed.")


def test_modem_device_detection():
    print("[TEST] Testing Samsung Device Port Scanner...")
    devices = OdinProtocolEngine.scan_samsung_devices()
    print(f"  Found Samsung ports: {devices}")
    port = SamsungModemEngine.find_modem_port()
    print(f"  Modem port found: {port}")
    print("  [OK] Device Port Detection routines executed successfully.")


if __name__ == "__main__":
    test_pit_parser()
    test_tar_md5_verifier()
    test_modem_device_detection()
    print("\n[ALL SAMSUNG MODULE TESTS PASSED 100%]\n")
