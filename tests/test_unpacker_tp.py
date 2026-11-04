"""
Unit Tests for Firmware Unpackers & Test Point Database.
"""

import os
import sys
import tempfile
import tarfile
import struct
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.testpoints.tp_database import TEST_POINT_DATABASE
from engines.unpackers.samsung_tar_unpacker import SamsungTarUnpacker
from engines.unpackers.super_sparse_unpacker import SuperSparseUnpacker
from engines.unpackers.ofp_ops_unpacker import OfpOpsUnpacker


def test_tp_db():
    brands = list(set(v["brand"] for v in TEST_POINT_DATABASE.values()))
    assert len(brands) >= 6
    assert len(TEST_POINT_DATABASE) >= 8
    print(f"  [OK] TP Database: {len(brands)} brands, {len(TEST_POINT_DATABASE)} models verified.")


def test_samsung_unpacker():
    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = os.path.join(tmpdir, "test.tar")
        dummy_file = os.path.join(tmpdir, "boot.img")
        with open(dummy_file, "wb") as f:
            f.write(b"SAMPLE_BOOT_IMAGE_DATA")

        with tarfile.open(tar_path, "w") as tar:
            tar.add(dummy_file, arcname="boot.img")

        out_dir = os.path.join(tmpdir, "out")
        extracted = SamsungTarUnpacker.unpack_samsung_tar(tar_path, out_dir)
        assert len(extracted) >= 1
        assert extracted[0]["name"] == "boot.img"
        print("  [OK] Samsung TAR Unpacker verified.")


def test_sparse_unpacker():
    with tempfile.TemporaryDirectory() as tmpdir:
        sparse_file = os.path.join(tmpdir, "test.sparse.img")
        magic = SuperSparseUnpacker.SPARSE_HEADER_MAGIC
        maj_ver = 1
        min_ver = 0
        file_hdr_sz = 28
        chunk_hdr_sz = 12
        blk_sz = 4096
        total_blks = 10
        total_chunks = 1
        image_checksum = 0
        hdr = struct.pack("<IHHHHIIII", magic, maj_ver, min_ver, file_hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, image_checksum)
        with open(sparse_file, "wb") as f:
            f.write(hdr)
            f.write(b"\x00" * 100)

        assert SuperSparseUnpacker.is_sparse_image(sparse_file) is True
        print("  [OK] Super Sparse Unpacker header verified.")


if __name__ == "__main__":
    print("[TEST] Running Test Point & Unpacker Verification...")
    test_tp_db()
    test_samsung_unpacker()
    test_sparse_unpacker()
    print("\n[ALL UNPACKER & TP TESTS PASSED 100%]\n")
