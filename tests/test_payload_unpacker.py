import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import io
import shutil
import tempfile
import struct
import bz2
from unittest.mock import MagicMock
from engines.unpackers.payload_unpacker import PayloadUnpacker

def encode_varint(val):
    buf = bytearray()
    while True:
        to_write = val & 0x7F
        val >>= 7
        if val:
            buf.append(to_write | 0x80)
        else:
            buf.append(to_write)
            break
    return bytes(buf)

def encode_field(field_num, wire_type, data):
    tag = (field_num << 3) | wire_type
    if wire_type == 0:
        return encode_varint(tag) + encode_varint(data)
    elif wire_type == 2:
        return encode_varint(tag) + encode_varint(len(data)) + data
    elif wire_type == 5:
        return encode_varint(tag) + struct.pack("<I", data)
    elif wire_type == 1:
        return encode_varint(tag) + struct.pack("<Q", data)
    return b""

def create_synthetic_payload(output_path: str):
    # Partition 1: 'boot', type=0 (REPLACE), raw content = b'ANDROID_BOOT_IMG_DATA'
    boot_data = b"ANDROID_BOOT_IMG_DATA_HEADER" * 10
    boot_extent = encode_field(1, 0, 0) + encode_field(2, 0, 1) # start_block=0, num_blocks=1
    boot_op = (encode_field(1, 0, 0) + # type=REPLACE
               encode_field(2, 0, 0) + # data_offset=0
               encode_field(3, 0, len(boot_data)) + # data_length
               encode_field(6, 2, boot_extent))
    boot_part = encode_field(1, 2, b"boot") + encode_field(5, 2, boot_op)

    # Partition 2: 'vbmeta', type=1 (REPLACE_BZ), compressed content
    vbmeta_raw = b"VBMETA_AVB20_SIGNATURE_KEY" * 15
    vbmeta_bz = bz2.compress(vbmeta_raw)
    vbmeta_extent = encode_field(1, 0, 0) + encode_field(2, 0, 1)
    vbmeta_op = (encode_field(1, 0, 1) + # type=REPLACE_BZ
                 encode_field(2, 0, len(boot_data)) + # data_offset
                 encode_field(3, 0, len(vbmeta_bz)) + # data_length
                 encode_field(6, 2, vbmeta_extent))
    vbmeta_part = encode_field(1, 2, b"vbmeta") + encode_field(5, 2, vbmeta_op)

    # Build manifest
    manifest = (encode_field(1, 2, boot_part) + 
                encode_field(1, 2, vbmeta_part) + 
                encode_field(3, 0, 4096))

    # Header: CrAU (4 bytes), version (8 bytes = 2), manifest_size (8 bytes), sig_size (4 bytes = 0)
    header = b"CrAU" + struct.pack(">Q", 2) + struct.pack(">Q", len(manifest)) + struct.pack(">I", 0)

    # Full file: header + manifest + data
    with open(output_path, "wb") as f:
        f.write(header)
        f.write(manifest)
        f.write(boot_data)
        f.write(vbmeta_bz)

class TestPayloadUnpacker(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.payload_file = os.path.join(self.test_dir, "payload.bin")
        self.out_dir = os.path.join(self.test_dir, "unpacked")
        create_synthetic_payload(self.payload_file)
        self.unpacker = PayloadUnpacker(logger=MagicMock())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_inspect_payload(self):
        parts = self.unpacker.inspect(self.payload_file)
        self.assertEqual(len(parts), 2)
        names = [p["name"] for p in parts]
        self.assertIn("boot", names)
        self.assertIn("vbmeta", names)

    def test_unpack_all(self):
        extracted = self.unpacker.unpack(self.payload_file, self.out_dir)
        self.assertEqual(len(extracted), 2)
        boot_path = os.path.join(self.out_dir, "boot.img")
        vbmeta_path = os.path.join(self.out_dir, "vbmeta.img")
        self.assertTrue(os.path.exists(boot_path))
        self.assertTrue(os.path.exists(vbmeta_path))

        with open(boot_path, "rb") as f:
            data = f.read()
            self.assertTrue(b"ANDROID_BOOT_IMG_DATA" in data)

        with open(vbmeta_path, "rb") as f:
            data = f.read()
            self.assertTrue(b"VBMETA_AVB20" in data)

    def test_unpack_selective(self):
        extracted = self.unpacker.unpack(self.payload_file, self.out_dir, target_partitions=["boot"])
        self.assertEqual(len(extracted), 1)
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "boot.img")))
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, "vbmeta.img")))

if __name__ == "__main__":
    unittest.main()
