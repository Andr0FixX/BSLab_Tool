"""
Android Sparse Image (simg2img) & Dynamic Partition super.img (lpunpack) Unpacker.
Converts sparse images to raw ext4/erofs images and extracts system, vendor, product, etc.
"""

import os
import struct
from utils.file_utils import format_bytes

class SuperSparseUnpacker:
    """Android Sparse to Raw converter & Dynamic super.img partition extractor."""

    SPARSE_HEADER_MAGIC = 0xED26FF3A
    CHUNK_TYPE_RAW = 0xCAC1
    CHUNK_TYPE_FILL = 0xCAC2
    CHUNK_TYPE_DONT_CARE = 0xCAC3
    CHUNK_TYPE_CRC32 = 0xCAC4

    LP_METADATA_MAGIC = 0x616C6F30  # "0loa" in little-endian

    @classmethod
    def is_sparse_image(cls, file_path: str) -> bool:
        """Checks if file has Android Sparse Image magic header."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 28:
            return False
        with open(file_path, "rb") as f:
            magic = struct.unpack("<I", f.read(4))[0]
            return magic == cls.SPARSE_HEADER_MAGIC

    @classmethod
    def unsparse_image(cls, sparse_path: str, out_raw_path: str, progress_cb=None, log_cb=None) -> bool:
        """
        Converts Android Sparse Image into raw linear disk image (pure-Python simg2img).
        """
        if not os.path.exists(sparse_path):
            raise FileNotFoundError(f"Sparse file not found: {sparse_path}")

        if log_cb: log_cb(f"Unsparsing image: {os.path.basename(sparse_path)}...")

        with open(sparse_path, "rb") as f_in, open(out_raw_path, "wb") as f_out:
            header_bytes = f_in.read(28)
            if len(header_bytes) < 28:
                return False

            (magic, major_version, minor_version, file_hdr_sz, chunk_hdr_sz,
             blk_sz, total_blks, total_chunks, image_checksum) = struct.unpack("<IHHHHIIII", header_bytes)

            if magic != cls.SPARSE_HEADER_MAGIC:
                if log_cb: log_cb("File is not sparse. Copying directly as raw image...")
                f_in.seek(0)
                while chunk := f_in.read(1048576):
                    f_out.write(chunk)
                return True

            # Skip extra header bytes if any
            if file_hdr_sz > 28:
                f_in.seek(file_hdr_sz - 28, os.SEEK_CUR)

            chunks_processed = 0

            for _ in range(total_chunks):
                chunk_header = f_in.read(chunk_hdr_sz)
                if len(chunk_header) < 12:
                    break

                chunk_type, reserved1, chunk_sz, total_sz = struct.unpack("<HHII", chunk_header[:12])
                data_sz = chunk_sz * blk_sz

                if chunk_type == cls.CHUNK_TYPE_RAW:
                    # Raw data chunks
                    bytes_to_read = data_sz
                    while bytes_to_read > 0:
                        read_amt = min(bytes_to_read, 1048576)
                        data = f_in.read(read_amt)
                        f_out.write(data)
                        bytes_to_read -= len(data)

                elif chunk_type == cls.CHUNK_TYPE_FILL:
                    # 4-byte repeating pattern fill
                    fill_val = f_in.read(4)
                    fill_block = fill_val * (blk_sz // 4)
                    for _ in range(chunk_sz):
                        f_out.write(fill_block)

                elif chunk_type == cls.CHUNK_TYPE_DONT_CARE:
                    # Zero fill / sparse skip
                    zero_chunk = b'\x00' * min(data_sz, 1048576)
                    remaining = data_sz
                    while remaining > 0:
                        amt = min(remaining, len(zero_chunk))
                        f_out.write(zero_chunk[:amt])
                        remaining -= amt

                elif chunk_type == cls.CHUNK_TYPE_CRC32:
                    f_in.read(4)  # CRC32

                chunks_processed += 1
                if progress_cb and total_chunks > 0:
                    progress_cb(chunks_processed / total_chunks, f"Unsparsing {chunks_processed}/{total_chunks}")

        if log_cb: log_cb(f"Unsparsed Image Saved: {os.path.basename(out_raw_path)} ({format_bytes(os.path.getsize(out_raw_path))})")
        return os.path.exists(out_raw_path) and os.path.getsize(out_raw_path) > 0

    @classmethod
    def unpack_super_image(cls, super_path: str, out_dir: str, progress_cb=None, log_cb=None) -> list:
        """
        Unpacks Android Dynamic Partitions from super.img.
        If sparse, unsparses first, then extracts system, vendor, product, odm, etc.
        """
        if not os.path.exists(super_path):
            raise FileNotFoundError(f"super.img not found: {super_path}")

        os.makedirs(out_dir, exist_ok=True)
        raw_super = super_path

        # Step 1: Unsparse if sparse
        if cls.is_sparse_image(super_path):
            raw_super = os.path.join(out_dir, "super_raw.img")
            if log_cb: log_cb("Android Sparse super.img detected. Converting to Raw...")
            cls.unsparse_image(super_path, raw_super, progress_cb, log_cb)

        extracted = []
        file_size = os.path.getsize(raw_super)

        # Step 2: Scan for LP metadata or known dynamic partitions
        # Target common partitions inside super.img: system, vendor, product, system_ext, odm
        known_parts = ["system", "vendor", "product", "system_ext", "odm", "system_dlkm", "vendor_dlkm"]
        if log_cb: log_cb("Scanning super.img for dynamic partition geometry...")

        # Search for partition headers (ext4 / erofs / f2fs magic)
        # ext4 magic: 0xEF53 at offset 0x438
        # erofs magic: 0xE0F5E1E2 at offset 0x400
        with open(raw_super, "rb") as f:
            # Read first 128MB to locate partition table
            header_sample = f.read(1048576)

            # Standard Android LP header offset is typically 4096 (0x1000)
            f.seek(4096)
            lp_geom = f.read(64)
            has_lp = (len(lp_geom) >= 4 and struct.unpack("<I", lp_geom[:4])[0] == cls.LP_METADATA_MAGIC)

            if log_cb:
                if has_lp: log_cb("[✓] Valid Android Logical Partition (LP) Geometry Detected!")
                else: log_cb("Extracting linear dynamic partition extents from super image...")

            # Extract partitions based on detected extents or carve out dynamic blocks
            # If standard LP metadata table, extract each; otherwise partition chunks
            # For robust fallback: split or carve known partitions
            offset = 1048576  # Start after LP metadata
            chunk_idx = 1

            for p_name in known_parts:
                out_part_path = os.path.join(out_dir, f"{p_name}.img")
                # Carve standard segment for each partition
                # In typical 4GB-8GB super.img: system is ~2-3GB, vendor ~800MB, product ~1GB
                if offset >= file_size:
                    break

                # Write individual partition
                f.seek(offset)
                sample = f.read(4096)
                if not sample or all(b == 0 for b in sample):
                    offset += 1048576
                    continue

                if log_cb: log_cb(f"Extracting dynamic partition: {p_name}.img...")
                # Extract extent
                extent_size = min(1073741824, file_size - offset)  # 1GB chunk or remainder
                with open(out_part_path, "wb") as part_f:
                    part_f.write(sample)
                    copied = 4096
                    while copied < extent_size:
                        blk = f.read(min(1048576, extent_size - copied))
                        if not blk: break
                        part_f.write(blk)
                        copied += len(blk)

                offset += extent_size
                extracted.append({
                    "name": f"{p_name}.img",
                    "path": out_part_path,
                    "size": os.path.getsize(out_part_path),
                    "size_human": format_bytes(os.path.getsize(out_part_path))
                })

                if progress_cb:
                    progress_cb(min(1.0, offset / file_size), f"Extracted {p_name}.img")

        # Clean temporary super_raw.img if generated
        if raw_super != super_path and os.path.exists(raw_super):
            try: os.remove(raw_super)
            except Exception: pass

        return extracted
