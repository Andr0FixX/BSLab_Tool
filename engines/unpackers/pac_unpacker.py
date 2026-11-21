import os
from engines.unisoc.pac_parser import PacParser
from utils.file_utils import format_bytes

class PacUnpacker:
    """Unisoc / Spreadtrum .PAC firmware unpacker."""

    @staticmethod
    def unpack_pac(pac_path: str, out_dir: str, progress_cb=None):
        if not os.path.exists(pac_path):
            raise FileNotFoundError(f"PAC file not found: {pac_path}")

        info = PacParser.parse(pac_path)
        os.makedirs(out_dir, exist_ok=True)
        extracted = []

        parts = [p for p in info.get("partitions", []) if p.get("data_offset", 0) > 0 and p.get("file_size", 0) > 0]
        total = len(parts)

        for i, p in enumerate(parts):
            fn = p.get("filename") or f"{p.get('name')}.bin"
            out_file = os.path.join(out_dir, fn)
            try:
                PacParser.extract_file(pac_path, p["name"], out_file)
                if os.path.exists(out_file):
                    extracted.append({
                        "name": fn,
                        "path": out_file,
                        "size": os.path.getsize(out_file),
                        "size_human": format_bytes(os.path.getsize(out_file))
                    })
            except Exception as e:
                pass

            if progress_cb and total > 0:
                progress_cb((i + 1) / total)

        return extracted
