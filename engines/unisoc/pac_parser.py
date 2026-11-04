import os
import struct
from utils.file_utils import format_bytes

class PacParser:
    """
    Parses Spreadtrum / Unisoc .PAC firmware archives.
    Extracts embedded partition images, FDL1, FDL2, and partition table mappings.
    """

    PAC_HEADER_MAGIC = ["PAC_FORMAT_V1.0", "BP_R1.0.0", "PAC_FORMAT_V2.0"]

    @staticmethod
    def parse(pac_path: str) -> dict:
        """
        Parses PAC header and file entries.
        Returns:
        {
            "version": str,
            "product_name": str,
            "product_version": str,
            "file_count": int,
            "partitions": [{
                "name": str,
                "filename": str,
                "file_size": int,
                "file_size_human": str,
                "data_offset": int,
                "is_download": bool,
                "is_checked": bool
            }, ...]
        }
        """
        if not os.path.exists(pac_path):
            raise FileNotFoundError(f"PAC file not found: {pac_path}")

        file_size = os.path.getsize(pac_path)
        if file_size < 2048:
            raise ValueError("File is too small to be a valid PAC archive.")

        with open(pac_path, "rb") as f:
            # Read header prefix (version tag)
            ver_raw = f.read(48)
            try:
                version = ver_raw.decode("utf-16le", errors="ignore").strip("\x00")
                if not version or len(version) < 3:
                    version = ver_raw.decode("ascii", errors="ignore").strip("\x00")
            except Exception:
                version = "PAC_FORMAT_V1.0"

            # Check header size
            f.seek(48)
            hdr_size = struct.unpack("<I", f.read(4))[0]

            # Product Name (512 bytes UTF-16LE)
            prd_name_raw = f.read(512)
            try:
                prd_name = prd_name_raw.decode("utf-16le", errors="ignore").strip("\x00")
            except Exception:
                prd_name = "Unisoc Device"

            # Product Version (512 bytes UTF-16LE)
            prd_ver_raw = f.read(512)
            try:
                prd_version = prd_ver_raw.decode("utf-16le", errors="ignore").strip("\x00")
            except Exception:
                prd_version = "Unknown"

            # Read File Count & Offset
            # The header layout:
            # 48 (version) + 4 (size) + 512 (name) + 512 (ver) + 512 (alias) = 1588
            # Then file count at offset 2096 or 2100 depending on PAC format variant
            f.seek(2096)
            file_count = struct.unpack("<I", f.read(4))[0]
            if file_count > 256 or file_count == 0:
                f.seek(2100)
                file_count = struct.unpack("<I", f.read(4))[0]
            if file_count > 256 or file_count == 0:
                # Fallback search for reasonable file count
                f.seek(2124)
                file_count = struct.unpack("<I", f.read(4))[0]
                if file_count > 256 or file_count == 0:
                    file_count = 32

            # Seek to file table start (typically offset 2124 or 2128)
            f.seek(2124)
            partitions = []

            # Each file entry in standard PAC is 2560 bytes (0xA00):
            # dwSize (4) + szFileID (512 UTF-16) + szFileName (512 UTF-16) + szFileVersion (100) + ...
            # nFileSize (4 or 8) + nFileFlag (4) + nCheckFlag (4) + dwDataOffset (4 or 8)
            entry_size = 2560

            for i in range(file_count):
                entry_start = 2124 + (i * entry_size)
                if entry_start + entry_size > file_size:
                    break

                f.seek(entry_start)
                f_entry_size = struct.unpack("<I", f.read(4))[0]
                if f_entry_size == 0 or f_entry_size > 5000:
                    f_entry_size = entry_size

                # FileID (Partition name, 512 bytes UTF-16LE)
                file_id_raw = f.read(512)
                try:
                    file_id = file_id_raw.decode("utf-16le", errors="ignore").strip("\x00")
                except Exception:
                    file_id = f"part_{i}"

                # FileName (Image name, 512 bytes UTF-16LE)
                file_name_raw = f.read(512)
                try:
                    file_name = file_name_raw.decode("utf-16le", errors="ignore").strip("\x00")
                except Exception:
                    file_name = file_id

                if not file_id:
                    continue

                # Seek to sizes and offsets within this entry
                # Offset 4 + 512 + 512 + 100 = 1128
                f.seek(entry_start + 1128)
                n_file_size = struct.unpack("<I", f.read(4))[0]
                n_file_flag = struct.unpack("<I", f.read(4))[0]
                n_check_flag = struct.unpack("<I", f.read(4))[0]
                dw_data_offset = struct.unpack("<I", f.read(4))[0]

                # Check if data offset and size are valid within PAC
                if dw_data_offset < file_size and n_file_size > 0:
                    is_download = (n_file_flag != 0)
                    partitions.append({
                        "name": file_id,
                        "filename": file_name if file_name else f"{file_id}.bin",
                        "file_size": n_file_size,
                        "file_size_human": format_bytes(n_file_size),
                        "data_offset": dw_data_offset,
                        "is_download": is_download,
                        "is_checked": is_download and n_file_size > 0
                    })

            return {
                "version": version,
                "product_name": prd_name if prd_name else "Unisoc Chipset",
                "product_version": prd_version,
                "file_count": len(partitions),
                "partitions": partitions
            }

    @staticmethod
    def extract_file(pac_path: str, partition_name: str, out_path: str) -> bool:
        """Extracts a single partition from the PAC file to out_path."""
        parsed = PacParser.parse(pac_path)
        part = next((p for p in parsed["partitions"] if p["name"].lower() == partition_name.lower()), None)
        if not part:
            return False

        offset = part["data_offset"]
        length = part["file_size"]

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(pac_path, "rb") as pac_f, open(out_path, "wb") as out_f:
            pac_f.seek(offset)
            copied = 0
            chunk_size = 1048576  # 1MB
            while copied < length:
                chunk = pac_f.read(min(chunk_size, length - copied))
                if not chunk:
                    break
                out_f.write(chunk)
                copied += len(chunk)

        return os.path.exists(out_path) and os.path.getsize(out_path) == length
