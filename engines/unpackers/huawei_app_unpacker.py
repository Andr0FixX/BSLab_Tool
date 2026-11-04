"""
Huawei Official UPDATE.APP Firmware Unpacker & Partition Extractor.
Parses binary headers (Magic 0x55 0xAA 0x5A 0xA5) to extract bootloader components,
xloaders, kernels, system, vendor, and recovery images from official Huawei packages.
"""

import os
import struct
from typing import Callable, Optional, List, Dict
from utils.file_utils import format_bytes


class HuaweiAppUnpacker:
    """Production-grade binary stream unpacker for Huawei / Honor UPDATE.APP packages."""

    MAGIC_HEADER = b"\x55\xAA\x5A\xA5"
    HEADER_MIN_LEN = 98
    BUFFER_SIZE = 1024 * 1024  # 1MB chunk size for high-speed streaming

    @classmethod
    def unpack_update_app(
        cls,
        app_path: str,
        out_dir: str,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict]:
        """
        Extracts all embedded partition images (.img) from official Huawei UPDATE.APP.
        Returns a list of extracted partition file metadata dicts.
        """
        if not os.path.exists(app_path):
            raise FileNotFoundError(f"Huawei UPDATE.APP not found: {app_path}")

        total_file_size = os.path.getsize(app_path)
        if total_file_size < cls.HEADER_MIN_LEN:
            raise ValueError(f"File too small to be a valid Huawei UPDATE.APP ({total_file_size} bytes)")

        os.makedirs(out_dir, exist_ok=True)
        extracted_files = []
        name_counts: Dict[str, int] = {}

        if log_cb:
            log_cb(f"Opening Huawei UPDATE.APP container: {os.path.basename(app_path)} ({format_bytes(total_file_size)})...")

        with open(app_path, "rb") as f:
            # 1. First pass: quick scan of partition directory to get total partitions & names
            entries = []
            f.seek(0)
            while True:
                magic = f.read(4)
                if not magic or len(magic) < 4:
                    break
                if magic != cls.MAGIC_HEADER:
                    # Scan ahead byte by byte if misaligned
                    byte = f.read(1)
                    if not byte:
                        break
                    continue

                # Read header size
                h_size_bytes = f.read(4)
                if len(h_size_bytes) < 4:
                    break
                header_size = struct.unpack("<I", h_size_bytes)[0]
                if header_size < 76 or header_size > 1024:
                    continue

                # Seek 16 bytes
                f.seek(16, 1)

                # Read file payload size
                f_size_bytes = f.read(4)
                if len(f_size_bytes) < 4:
                    break
                payload_size = struct.unpack("<I", f_size_bytes)[0]

                # Seek 32 bytes (date/time strings)
                f.seek(32, 1)

                # Read partition name (16 bytes)
                raw_name = f.read(16)
                clean_name = raw_name.split(b"\x00")[0].decode("ascii", errors="ignore").strip()
                if not clean_name:
                    clean_name = f"PARTITION_{len(entries)+1}"

                # Skip rest of header
                already_read = 4 + 4 + 16 + 4 + 32 + 16  # 76 bytes
                if header_size > already_read:
                    f.seek(header_size - already_read, 1)

                payload_offset = f.tell()
                entries.append({
                    "name": clean_name,
                    "offset": payload_offset,
                    "size": payload_size
                })

                # Skip payload and padding to reach next header
                f.seek(payload_size, 1)
                rem = payload_size % 4
                if rem > 0:
                    f.seek(4 - rem, 1)

            total_entries = len(entries)
            if total_entries == 0:
                raise ValueError("No valid Huawei partition headers (0x55AA5AA5) found in UPDATE.APP.")

            if log_cb:
                log_cb(f"Detected {total_entries} partitions in package. Starting extraction...")

            # 2. Second pass: Extract each partition directly
            for idx, entry in enumerate(entries, start=1):
                p_name = entry["name"]
                p_size = entry["size"]
                p_offset = entry["offset"]

                # Ensure filename ends with .img
                if not p_name.lower().endswith(".img"):
                    out_filename = f"{p_name}.img"
                else:
                    out_filename = p_name

                # Avoid file collisions
                if out_filename in name_counts:
                    name_counts[out_filename] += 1
                    base, ext = os.path.splitext(out_filename)
                    out_filename = f"{base}_{name_counts[out_filename]}{ext}"
                else:
                    name_counts[out_filename] = 1

                out_file_path = os.path.join(out_dir, out_filename)
                f.seek(p_offset)

                if log_cb:
                    log_cb(f"[{idx}/{total_entries}] Extracting {out_filename} ({format_bytes(p_size)})...")

                bytes_remaining = p_size
                with open(out_file_path, "wb") as out_f:
                    while bytes_remaining > 0:
                        chunk_size = min(bytes_remaining, cls.BUFFER_SIZE)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        bytes_remaining -= len(chunk)

                extracted_files.append({
                    "name": out_filename,
                    "path": out_file_path,
                    "size": p_size,
                    "size_human": format_bytes(p_size)
                })

                if progress_cb:
                    progress_cb(idx / total_entries, f"Extracted {out_filename}")

        if log_cb:
            log_cb(f"[✓] Successfully unpacked {len(extracted_files)} Huawei partition images to: {out_dir}")

        return extracted_files
