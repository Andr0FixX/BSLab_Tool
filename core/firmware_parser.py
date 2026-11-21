"""
BS Lab Tool v2.0 PRO — Universal Multi-Format Firmware Parser & Dispatcher.
Fully supports:
1. MediaTek Scatter (.txt)
2. Oppo / Realme OFP (.ofp)
3. OnePlus OPS (.ops)
4. Oppo / Realme OZIP (.ozip)
5. Huawei Official UPDATE.APP (UPDATE.APP, *.app)
6. Unisoc / Spreadtrum PAC (*.pac)
7. Qualcomm Rawprogram XML (rawprogram*.xml, *.xml)
8. Samsung Odin TAR / MD5 (*.tar, *.tar.md5, *.md5)
9. Android OTA Payload (payload.bin)
10. Fastboot ROM Archive (*.zip) & Direct Partition Images (*.img, *.bin)
"""

import os
import sys
import glob
import zipfile
from typing import List, Dict, Any, Optional, Callable

from utils.file_utils import format_bytes
from mtk.flasher import ScatterParser
from engines.unpackers.ofp_ops_unpacker import OfpOpsUnpacker
from engines.unpackers.huawei_app_unpacker import HuaweiAppUnpacker
from engines.unpackers.pac_unpacker import PacUnpacker
from engines.unisoc.pac_parser import PacParser
from engines.qualcomm.xml_parser import QualcommXMLParser
from engines.unpackers.samsung_tar_unpacker import SamsungTarUnpacker
from engines.unpackers.payload_unpacker import PayloadUnpacker


class UniversalFirmwareParser:
    """Universal Android & Embedded Firmware Parser and Unpacker."""

    @classmethod
    def detect_format(cls, file_path: str) -> str:
        """Determines firmware package format based on file extension and magic headers."""
        if not os.path.exists(file_path):
            return "unknown"

        ext = os.path.splitext(file_path)[1].lower()
        base = os.path.basename(file_path).lower()

        # Check by name/extension first
        if "scatter" in base and ext == ".txt":
            return "scatter"
        if ext == ".ofp":
            return "ofp"
        if ext == ".ops":
            return "ops"
        if ext == ".ozip":
            return "ozip"
        if base == "update.app" or ext == ".app":
            return "huawei_app"
        if ext == ".pac":
            return "pac"
        if "rawprogram" in base and ext == ".xml":
            return "qualcomm_xml"
        if ext in (".tar", ".md5") or base.endswith(".tar.md5"):
            return "samsung_tar"
        if base == "payload.bin" or (ext == ".bin" and cls._is_payload_bin(file_path)):
            return "payload"
        if ext == ".zip":
            return "zip"
        if ext in (".img", ".bin"):
            return "raw_image"

        # Content inspection
        try:
            with open(file_path, "rb") as f:
                head = f.read(512)
                if head.startswith(b"PK\x03\x04"):
                    return "zip"
                if head.startswith(b"CrAU"):
                    return "payload"
                if head.startswith(b"\x55\xAA\x5A\xA5"):
                    return "huawei_app"
                if head.startswith(b"OPPOENCRYPT!"):
                    return "ozip"
                if b"partition_index:" in head or b"linear_start_addr:" in head:
                    return "scatter"
                if b"<?xml" in head and b"<program" in head:
                    return "qualcomm_xml"
        except Exception:
            pass

        if ext == ".txt":
            return "scatter"
        if ext == ".xml":
            return "qualcomm_xml"

        return "unknown"

    @classmethod
    def _is_payload_bin(cls, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(4) == b"CrAU"
        except Exception:
            return False

    @classmethod
    def parse_firmware(
        cls,
        firmware_path: str,
        log_cb: Optional[Callable[[str], None]] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Parses or extracts ANY supported firmware container and returns a standardized
        list of partition dictionaries ready for flashing.
        """
        if not os.path.exists(firmware_path):
            raise FileNotFoundError(f"Firmware path does not exist: {firmware_path}")

        fmt = cls.detect_format(firmware_path)
        fw_dir = os.path.dirname(os.path.abspath(firmware_path))
        base_name = os.path.splitext(os.path.basename(firmware_path))[0]

        if log_cb:
            log_cb(f"[*] Detected Firmware Container Format: {fmt.upper()}")

        # -------------------------------------------------------------
        # 1. SCATTER (.txt)
        # -------------------------------------------------------------
        if fmt == "scatter":
            parts = ScatterParser.parse(firmware_path)
            for p in parts:
                p["format_type"] = "scatter"
                if "file_size" in p:
                    p["size"] = p["file_size"]
            return parts

        # -------------------------------------------------------------
        # 2. OPPO / REALME OFP (.ofp)
        # -------------------------------------------------------------
        if fmt == "ofp":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Extracting Oppo/Realme OFP into: {out_dir}...")
            OfpOpsUnpacker.unpack_ofp(firmware_path, out_dir, log_cb=log_cb)

            # Check if scatter exists inside extracted files
            scatters = glob.glob(os.path.join(out_dir, "*scatter*.txt")) + glob.glob(os.path.join(out_dir, "*.txt"))
            for s in scatters:
                try:
                    p_list = ScatterParser.parse(s)
                    if p_list:
                        for p in p_list: p["format_type"] = "ofp"
                        return p_list
                except Exception:
                    pass

            return cls._dir_to_partitions(out_dir, "ofp")

        # -------------------------------------------------------------
        # 3. ONEPLUS OPS (.ops)
        # -------------------------------------------------------------
        if fmt == "ops":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Extracting OnePlus OPS container into: {out_dir}...")
            OfpOpsUnpacker.unpack_ops(firmware_path, out_dir, log_cb=log_cb)
            return cls._dir_to_partitions(out_dir, "ops")

        # -------------------------------------------------------------
        # 4. OPPO / REALME OZIP (.ozip)
        # -------------------------------------------------------------
        if fmt == "ozip":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Decrypting and unpacking Oppo/Realme OZIP into: {out_dir}...")
            OfpOpsUnpacker.unpack_ozip(firmware_path, out_dir, log_cb=log_cb)

            scatters = glob.glob(os.path.join(out_dir, "*scatter*.txt")) + glob.glob(os.path.join(out_dir, "*.txt"))
            for s in scatters:
                try:
                    p_list = ScatterParser.parse(s)
                    if p_list:
                        for p in p_list: p["format_type"] = "ozip"
                        return p_list
                except Exception:
                    pass

            return cls._dir_to_partitions(out_dir, "ozip")

        # -------------------------------------------------------------
        # 5. HUAWEI UPDATE.APP (*.app)
        # -------------------------------------------------------------
        if fmt == "huawei_app":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Unpacking Huawei UPDATE.APP binary into: {out_dir}...")
            extracted = HuaweiAppUnpacker.unpack_update_app(firmware_path, out_dir, log_cb=log_cb)
            parts = []
            for idx, item in enumerate(extracted):
                fpath = item.get("path")
                fname = item.get("name")
                pname = os.path.splitext(fname)[0].lower()
                fsize = item.get("size", 0)
                parts.append({
                    "name": pname,
                    "file_name": fname,
                    "file_path": fpath,
                    "file_size": fsize,
                    "size": fsize,
                    "file_size_human": format_bytes(fsize),
                    "start_addr": f"0x{idx * 0x10000000:08X}",
                    "exists": os.path.exists(fpath),
                    "is_checked": True,
                    "is_download": True,
                    "format_type": "huawei_app"
                })
            return parts

        # -------------------------------------------------------------
        # 6. UNISOC / SPREADTRUM PAC (.pac)
        # -------------------------------------------------------------
        if fmt == "pac":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Parsing and extracting Unisoc PAC into: {out_dir}...")
            extracted = PacUnpacker.unpack_pac(firmware_path, out_dir)
            parts = []
            for idx, item in enumerate(extracted):
                fpath = item.get("path")
                fname = item.get("name")
                pname = os.path.splitext(fname)[0].lower()
                fsize = item.get("size", 0)
                parts.append({
                    "name": pname,
                    "file_name": fname,
                    "file_path": fpath,
                    "file_size": fsize,
                    "size": fsize,
                    "file_size_human": format_bytes(fsize),
                    "start_addr": f"0x{idx * 0x08000000:08X}",
                    "exists": os.path.exists(fpath),
                    "is_checked": True,
                    "is_download": True,
                    "format_type": "pac"
                })
            return parts

        # -------------------------------------------------------------
        # 7. QUALCOMM RAWPROGRAM XML (rawprogram*.xml)
        # -------------------------------------------------------------
        if fmt == "qualcomm_xml":
            if log_cb: log_cb(f"[*] Parsing Qualcomm Rawprogram XML: {os.path.basename(firmware_path)}...")
            raw_parts = QualcommXMLParser.parse_rawprogram(firmware_path, fw_dir)
            parts = []
            for p in raw_parts:
                fpath = p.get("file_path")
                fname = p.get("filename")
                fsize = p.get("file_size", 0)
                parts.append({
                    "name": p.get("name"),
                    "file_name": fname,
                    "file_path": fpath,
                    "file_size": fsize,
                    "size": fsize,
                    "file_size_human": p.get("file_size_human", "--"),
                    "start_addr": f"Sector {p.get('start_sector', 0)}",
                    "exists": p.get("exists", False),
                    "is_checked": p.get("exists", False) and fname != "",
                    "is_download": True,
                    "format_type": "qualcomm_xml"
                })
            return parts

        # -------------------------------------------------------------
        # 8. SAMSUNG ODIN TAR / MD5 (*.tar, *.tar.md5)
        # -------------------------------------------------------------
        if fmt == "samsung_tar":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Unpacking Samsung TAR/LZ4 firmware into: {out_dir}...")
            extracted = SamsungTarUnpacker.unpack_samsung_tar(firmware_path, out_dir, decompress_lz4=True, log_cb=log_cb)
            parts = []
            for idx, item in enumerate(extracted):
                fpath = item.get("path")
                fname = item.get("name")
                pname = os.path.splitext(fname)[0].replace(".img", "").lower()
                fsize = item.get("size", 0)
                parts.append({
                    "name": pname,
                    "file_name": fname,
                    "file_path": fpath,
                    "file_size": fsize,
                    "size": fsize,
                    "file_size_human": format_bytes(fsize),
                    "start_addr": f"0x{idx * 0x04000000:08X}",
                    "exists": os.path.exists(fpath),
                    "is_checked": True,
                    "is_download": True,
                    "format_type": "samsung_tar"
                })
            return parts

        # -------------------------------------------------------------
        # 9. ANDROID OTA PAYLOAD (payload.bin)
        # -------------------------------------------------------------
        if fmt == "payload":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Extracting Android OTA payload.bin partitions into: {out_dir}...")
            unp = PayloadUnpacker()
            unp.unpack(firmware_path, out_dir)
            return cls._dir_to_partitions(out_dir, "payload")

        # -------------------------------------------------------------
        # 10. FASTBOOT ROM / ZIP ARCHIVE (*.zip)
        # -------------------------------------------------------------
        if fmt == "zip":
            out_dir = os.path.join(fw_dir, f"unpacked_{base_name}")
            if log_cb: log_cb(f"[*] Extracting Fastboot ROM ZIP archive into: {out_dir}...")
            os.makedirs(out_dir, exist_ok=True)
            with zipfile.ZipFile(firmware_path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith("/") or name.startswith("__MACOSX"):
                        continue
                    bname = os.path.basename(name)
                    if bname.endswith((".img", ".bin", ".txt", ".xml", ".mbn", ".elf")):
                        target_p = os.path.join(out_dir, bname)
                        with open(target_p, "wb") as out_f:
                            out_f.write(zf.read(name))

            # Look for scatter in zip
            scatters = glob.glob(os.path.join(out_dir, "*scatter*.txt")) + glob.glob(os.path.join(out_dir, "*.txt"))
            for s in scatters:
                try:
                    p_list = ScatterParser.parse(s)
                    if p_list:
                        for p in p_list: p["format_type"] = "zip_scatter"
                        return p_list
                except Exception:
                    pass

            return cls._dir_to_partitions(out_dir, "zip")

        # -------------------------------------------------------------
        # 11. RAW IMAGE (*.img, *.bin)
        # -------------------------------------------------------------
        if fmt == "raw_image":
            fsize = os.path.getsize(firmware_path)
            pname = os.path.splitext(os.path.basename(firmware_path))[0].lower()
            return [{
                "name": pname,
                "file_name": os.path.basename(firmware_path),
                "file_path": firmware_path,
                "file_size": fsize,
                "size": fsize,
                "file_size_human": format_bytes(fsize),
                "start_addr": "0x00000000",
                "exists": True,
                "is_checked": True,
                "is_download": True,
                "format_type": "raw_image"
            }]

        raise ValueError(f"Unrecognized firmware format for file: {firmware_path}")

    @classmethod
    def _dir_to_partitions(cls, directory: str, format_type: str) -> List[Dict[str, Any]]:
        """Scans a directory of extracted images and returns partition dicts."""
        parts = []
        if not os.path.exists(directory):
            return parts

        for idx, fname in enumerate(sorted(os.listdir(directory))):
            fpath = os.path.join(directory, fname)
            if not os.path.isfile(fpath):
                continue
            if not fname.lower().endswith((".img", ".bin", ".elf", ".mbn", ".sin")):
                continue

            pname = os.path.splitext(fname)[0].lower()
            fsize = os.path.getsize(fpath)
            parts.append({
                "name": pname,
                "file_name": fname,
                "file_path": fpath,
                "file_size": fsize,
                "size": fsize,
                "file_size_human": format_bytes(fsize),
                "start_addr": f"0x{idx * 0x02000000:08X}",
                "exists": True,
                "is_checked": True,
                "is_download": True,
                "format_type": format_type
            })
        return parts
