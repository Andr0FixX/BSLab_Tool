"""
Samsung .tar.md5 Firmware Unpacker & Built-In Pure-Python LZ4 Decompressor.
Extracts BL, AP, CP, CSC, PIT, and decompresses .img.lz4 -> .img without external tools.
"""

import os
import tarfile
import struct
from utils.file_utils import format_bytes

class SamsungTarUnpacker:
    """Unpacks Samsung .tar.md5 archives and decompresses LZ4 partition images."""

    LZ4_FRAME_MAGIC = 0x184D2204

    @staticmethod
    def decompress_lz4_block(src_bytes: bytes) -> bytes:
        """Decompresses a single standard LZ4 raw block."""
        src_len = len(src_bytes)
        src_pos = 0
        dest = bytearray()

        while src_pos < src_len:
            token = src_bytes[src_pos]
            src_pos += 1

            # 1. Literals
            literal_len = (token >> 4) & 0x0F
            if literal_len == 15:
                while src_pos < src_len:
                    b = src_bytes[src_pos]
                    src_pos += 1
                    literal_len += b
                    if b != 255:
                        break

            if src_pos + literal_len > src_len:
                break
            dest.extend(src_bytes[src_pos : src_pos + literal_len])
            src_pos += literal_len

            if src_pos >= src_len:
                break

            # 2. Match Offset (2 bytes, little-endian)
            if src_pos + 2 > src_len:
                break
            offset = struct.unpack("<H", src_bytes[src_pos : src_pos + 2])[0]
            src_pos += 2
            if offset == 0:
                break

            # 3. Match Length
            match_len = (token & 0x0F) + 4
            if match_len == 19:
                while src_pos < src_len:
                    b = src_bytes[src_pos]
                    src_pos += 1
                    match_len += b
                    if b != 255:
                        break

            # Copy match
            for _ in range(match_len):
                dest.append(dest[-offset])

        return bytes(dest)

    @classmethod
    def decompress_lz4_file(cls, lz4_path: str, out_img_path: str, progress_cb=None) -> bool:
        """Decompresses an LZ4 frame archive (.img.lz4 -> .img)."""
        if not os.path.exists(lz4_path):
            return False

        with open(lz4_path, "rb") as f_in, open(out_img_path, "wb") as f_out:
            magic = struct.unpack("<I", f_in.read(4))[0]
            if magic != cls.LZ4_FRAME_MAGIC:
                # If not standard frame magic, check if raw block
                f_in.seek(0)
                data = f_in.read()
                decomp = cls.decompress_lz4_block(data)
                f_out.write(decomp)
                return True

            # Skip frame descriptor
            flg = struct.unpack("<B", f_in.read(1))[0]
            bd = struct.unpack("<B", f_in.read(1))[0]
            has_content_size = (flg & 0x08) != 0
            if has_content_size:
                f_in.seek(8, os.SEEK_CUR)  # 8 bytes content size
            f_in.seek(1, os.SEEK_CUR)      # 1 byte header checksum

            file_size = os.path.getsize(lz4_path)

            while True:
                size_bytes = f_in.read(4)
                if not size_bytes or len(size_bytes) < 4:
                    break
                block_size = struct.unpack("<I", size_bytes)[0]
                if block_size == 0:  # End of frame
                    break

                is_uncompressed = (block_size & 0x80000000) != 0
                block_size &= 0x7FFFFFFF

                block_data = f_in.read(block_size)
                if is_uncompressed:
                    f_out.write(block_data)
                else:
                    decomp = cls.decompress_lz4_block(block_data)
                    f_out.write(decomp)

                if progress_cb:
                    progress_cb(f_in.tell() / file_size)

        return os.path.exists(out_img_path) and os.path.getsize(out_img_path) > 0

    @classmethod
    def unpack_samsung_tar(cls, tar_path: str, out_dir: str, decompress_lz4: bool = True, progress_cb=None, log_cb=None) -> list:
        """
        Extracts Samsung .tar.md5 and decompresses all embedded .img.lz4 partitions.
        Returns list of extracted file paths.
        """
        if not os.path.exists(tar_path):
            raise FileNotFoundError(f"Samsung archive not found: {tar_path}")

        os.makedirs(out_dir, exist_ok=True)
        extracted_files = []

        if log_cb: log_cb(f"Opening Samsung TAR Archive: {os.path.basename(tar_path)}...")

        # Open TAR (handles both .tar and .tar.md5 automatically)
        with tarfile.open(tar_path, "r:*") as tar:
            members = tar.getmembers()
            total = len(members)

            for idx, member in enumerate(members, start=1):
                tar.extract(member, path=out_dir)
                out_path = os.path.join(out_dir, member.name)

                # Check if it's an LZ4 compressed image
                if decompress_lz4 and member.name.endswith(".lz4"):
                    img_name = member.name[:-4]  # Remove .lz4
                    img_path = os.path.join(out_dir, img_name)
                    if log_cb: log_cb(f"[{idx}/{total}] Decompressing LZ4: {member.name} -> {img_name}...")

                    ok = cls.decompress_lz4_file(out_path, img_path)
                    if ok:
                        extracted_files.append({
                            "name": img_name,
                            "path": img_path,
                            "size": os.path.getsize(img_path),
                            "size_human": format_bytes(os.path.getsize(img_path))
                        })
                        try: os.remove(out_path)  # Clean .lz4
                        except Exception: pass
                    else:
                        extracted_files.append({
                            "name": member.name,
                            "path": out_path,
                            "size": member.size,
                            "size_human": format_bytes(member.size)
                        })
                else:
                    if log_cb: log_cb(f"[{idx}/{total}] Extracted: {member.name} ({format_bytes(member.size)})")
                    extracted_files.append({
                        "name": member.name,
                        "path": out_path,
                        "size": member.size,
                        "size_human": format_bytes(member.size)
                    })

                if progress_cb:
                    progress_cb(idx / total, f"Unpacked {member.name}")

        return extracted_files
