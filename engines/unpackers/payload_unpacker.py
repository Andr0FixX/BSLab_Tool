"""
Universal Android OTA Payload.bin Unpacker Engine
Supports Google Pixel, Xiaomi / Redmi (HyperOS/MIUI), OnePlus (OxygenOS),
Realme, Oppo, Motorola, Nothing Phone, and ROG Phone OTA updates.
Extracts individual images (boot.img, vbmeta.img, init_boot.img) or full firmware.
"""

import os
import struct
import io
import bz2
import lzma
from typing import List, Dict, Any, Callable, Optional

# Optional zstandard support for Android 12+ ZSTD payloads
try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False


class PayloadUnpacker:
    """Universal Android OTA payload.bin extractor engine."""

    MAGIC = b"CrAU"

    # Operation Types
    OP_REPLACE = 0
    OP_REPLACE_BZ = 1
    OP_MOVE = 2
    OP_BSDIFF = 3
    OP_SOURCE_COPY = 4
    OP_SOURCE_BSDIFF = 5
    OP_ZERO = 6
    OP_DISCARD = 7
    OP_REPLACE_XZ = 8
    OP_REPLACE_ZSTD = 9

    def __init__(self, logger=None):
        self.logger = logger
        self.abort_requested = False

    def log(self, msg: str, level: str = "info"):
        if self.logger:
            if level == "error":
                self.logger.error(msg)
            elif level == "warn":
                self.logger.warn(msg)
            elif level == "success":
                self.logger.success(msg)
            else:
                self.logger.info(msg)

    def abort(self):
        self.abort_requested = True

    @staticmethod
    def _read_varint(stream: io.BytesIO) -> Optional[int]:
        result = 0
        shift = 0
        while True:
            b = stream.read(1)
            if not b:
                return None
            val = b[0]
            result |= (val & 0x7F) << shift
            if not (val & 0x80):
                break
            shift += 7
        return result

    @classmethod
    def _parse_protobuf(cls, data: bytes) -> Dict[int, List[Any]]:
        """Parses raw protobuf length-delimited and varint fields into a field map."""
        stream = io.BytesIO(data)
        fields = {}
        while True:
            tag = cls._read_varint(stream)
            if tag is None:
                break
            field_num = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                val = cls._read_varint(stream)
            elif wire_type == 1:  # 64-bit
                raw = stream.read(8)
                val = struct.unpack("<Q", raw)[0] if len(raw) == 8 else 0
            elif wire_type == 2:  # Length-delimited
                length = cls._read_varint(stream)
                val = stream.read(length) if length else b""
            elif wire_type == 5:  # 32-bit
                raw = stream.read(4)
                val = struct.unpack("<I", raw)[0] if len(raw) == 4 else 0
            else:
                break

            fields.setdefault(field_num, []).append(val)
        return fields

    @classmethod
    def _parse_extent(cls, raw: bytes) -> Dict[str, int]:
        f = cls._parse_protobuf(raw)
        start = f.get(1, [0])[0] if 1 in f else 0
        num = f.get(2, [0])[0] if 2 in f else 0
        return {"start_block": start, "num_blocks": num}

    @classmethod
    def _parse_operation(cls, raw: bytes) -> Dict[str, Any]:
        f = cls._parse_protobuf(raw)
        op_type = f.get(1, [0])[0]
        data_offset = f.get(2, [0])[0] if 2 in f else 0
        data_length = f.get(3, [0])[0] if 3 in f else 0
        dst_extents = [cls._parse_extent(ext_raw) for ext_raw in f.get(6, [])]
        dst_length = f.get(7, [0])[0] if 7 in f else 0
        return {
            "type": op_type,
            "data_offset": data_offset,
            "data_length": data_length,
            "dst_extents": dst_extents,
            "dst_length": dst_length,
        }

    @classmethod
    def _parse_partition(cls, raw: bytes) -> Dict[str, Any]:
        f = cls._parse_protobuf(raw)
        part_name = f.get(1, [b"unknown"])[0].decode("utf-8", errors="ignore")

        # Size from PartitionInfo
        size = 0
        if 4 in f and f[4]:
            info_f = cls._parse_protobuf(f[4][0])
            size = info_f.get(1, [0])[0]

        operations = [cls._parse_operation(op_raw) for op_raw in f.get(5, [])]
        return {
            "name": part_name,
            "size": size,
            "operations": operations
        }

    def inspect(self, payload_path: str) -> List[Dict[str, Any]]:
        """Reads payload header and returns list of contained partitions with sizes."""
        if not os.path.exists(payload_path):
            raise FileNotFoundError(f"File not found: {payload_path}")

        with open(payload_path, "rb") as f:
            magic = f.read(4)
            if magic != self.MAGIC:
                raise ValueError(f"Invalid OTA Payload header magic: {magic} (Expected {self.MAGIC})")

            file_format_version = struct.unpack(">Q", f.read(8))[0]
            manifest_size = struct.unpack(">Q", f.read(8))[0]

            metadata_sig_size = 0
            if file_format_version >= 2:
                metadata_sig_size = struct.unpack(">I", f.read(4))[0]

            manifest_bytes = f.read(manifest_size)
            if len(manifest_bytes) != manifest_size:
                raise ValueError("Truncated payload manifest header.")

        top_f = self._parse_protobuf(manifest_bytes)
        block_size = top_f.get(3, [4096])[0] if 3 in top_f else 4096

        partitions = []
        for p_raw in top_f.get(1, []):
            p = self._parse_partition(p_raw)
            p["block_size"] = block_size
            partitions.append(p)

        return partitions

    def unpack(
        self,
        payload_path: str,
        output_dir: str,
        target_partitions: Optional[List[str]] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None
    ) -> List[str]:
        """
        Unpacks partitions from payload.bin into output_dir.
        If target_partitions is given, only extracts those specified (e.g. ['boot', 'vbmeta']).
        """
        self.abort_requested = False
        os.makedirs(output_dir, exist_ok=True)

        self.log(f"Inspecting Android OTA Payload: {payload_path}")
        with open(payload_path, "rb") as f:
            magic = f.read(4)
            if magic != self.MAGIC:
                raise ValueError(f"Invalid payload magic: {magic}")

            version = struct.unpack(">Q", f.read(8))[0]
            manifest_size = struct.unpack(">Q", f.read(8))[0]
            metadata_sig_size = 0
            if version >= 2:
                metadata_sig_size = struct.unpack(">I", f.read(4))[0]

            manifest_bytes = f.read(manifest_size)
            f.seek(metadata_sig_size, os.SEEK_CUR)
            data_start_offset = f.tell()

            top_f = self._parse_protobuf(manifest_bytes)
            block_size = top_f.get(3, [4096])[0] if 3 in top_f else 4096

            all_partitions = [self._parse_partition(p_raw) for p_raw in top_f.get(1, [])]

            # Filter targets if requested
            if target_partitions:
                target_set = {p.lower() for p in target_partitions}
                selected = [p for p in all_partitions if p["name"].lower() in target_set]
            else:
                selected = all_partitions

            total_partitions = len(selected)
            self.log(f"[Payload Manifest] Found {len(all_partitions)} partitions. Extracting {total_partitions} target(s)...")

            extracted_files = []
            for idx, part in enumerate(selected):
                if self.abort_requested:
                    self.log("Extraction aborted by user.", "warn")
                    break

                part_name = part["name"]
                out_filename = f"{part_name}.img"
                out_path = os.path.join(output_dir, out_filename)

                self.log(f"[{idx + 1}/{total_partitions}] Extracting partition '{part_name}' -> {out_filename}...")
                if progress_cb:
                    progress_cb((idx / total_partitions) * 100.0, f"Extracting {part_name}.img...")

                with open(out_path, "wb") as out_f:
                    for op in part["operations"]:
                        if self.abort_requested:
                            break

                        op_type = op["type"]
                        op_data_offset = op["data_offset"]
                        op_data_len = op["data_length"]

                        # Read payload chunk
                        if op_data_len > 0:
                            f.seek(data_start_offset + op_data_offset)
                            chunk = f.read(op_data_len)
                        else:
                            chunk = b""

                        # Decompress according to operation type
                        if op_type == self.OP_REPLACE:
                            decompressed = chunk
                        elif op_type == self.OP_REPLACE_BZ:
                            decompressed = bz2.decompress(chunk)
                        elif op_type == self.OP_REPLACE_XZ:
                            decompressed = lzma.decompress(chunk)
                        elif op_type == self.OP_REPLACE_ZSTD:
                            if HAS_ZSTD:
                                dctx = zstd.ZstdDecompressor()
                                decompressed = dctx.decompress(chunk)
                            else:
                                self.log(f"Warning: ZSTD not installed for op in {part_name}, skipping op chunk.", "warn")
                                decompressed = b""
                        elif op_type == self.OP_ZERO:
                            decompressed = None
                        else:
                            decompressed = chunk

                        # Write extents
                        for ext in op["dst_extents"]:
                            start_b = ext["start_block"]
                            num_b = ext["num_blocks"]
                            out_f.seek(start_b * block_size)

                            if decompressed is None or op_type == self.OP_ZERO:
                                out_f.write(b"\x00" * (num_b * block_size))
                            else:
                                out_f.write(decompressed[:num_b * block_size])

                if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    extracted_files.append(out_path)
                    self.log(f"[✓] Extracted: {out_filename} ({os.path.getsize(out_path):,} bytes)", "success")

            if progress_cb:
                progress_cb(100.0, "Extraction Completed!")

            self.log(f"[Payload Extraction Complete] {len(extracted_files)} partition images saved in '{output_dir}'.", "success")
            return extracted_files
