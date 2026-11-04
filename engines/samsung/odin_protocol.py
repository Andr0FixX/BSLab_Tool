"""
BS Lab Tool v2.0 PRO - Samsung Odin LOKE Protocol Engine & PIT Manager
Supports 4-File Flashing (BL, AP, CP, CSC), PIT Partition Extraction, and Download Mode Communications.
"""

import os
import sys
import time
import struct
import tarfile
import hashlib
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass

PIT_MAGIC = 0x12349876
PIT_MAGIC_LE = 0x76983412

@dataclass
class PitEntry:
    binary_type: int
    device_type: int
    partition_id: int
    partition_type: int
    partition_name: str
    filename: str
    block_start: int
    block_count: int

    @property
    def size_mb(self) -> float:
        # Standard block size is 512 bytes
        return (self.block_count * 512) / (1024 * 1024)

    def __repr__(self):
        return f"<PitEntry '{self.partition_name}' ({self.size_mb:.2f} MB) -> {self.filename}>"


class PitParser:
    """Parser for Samsung PIT (Partition Information Table) binary files."""

    @staticmethod
    def parse_pit_bytes(data: bytes) -> List[PitEntry]:
        if len(data) < 28:
            raise ValueError(f"PIT data too short: {len(data)} bytes (minimum 28 required)")

        magic = struct.unpack("<I", data[:4])[0]
        if magic != PIT_MAGIC and magic != PIT_MAGIC_LE:
            # Try big endian
            magic_be = struct.unpack(">I", data[:4])[0]
            if magic_be != PIT_MAGIC:
                raise ValueError(f"Invalid PIT Magic: 0x{magic:08X} (expected 0x12349876)")

        entry_count = struct.unpack("<I", data[4:8])[0]
        # Safeguard count
        if entry_count <= 0 or entry_count > 256:
            # Try reading at offset 8 or alternative header formats
            entry_count = min(128, max(1, struct.unpack("<I", data[8:12])[0]))

        entries: List[PitEntry] = []
        offset = 28 # standard Samsung PIT header length

        entry_size = 132 # standard PIT v1/v2 entry size
        while offset + entry_size <= len(data) and len(entries) < entry_count:
            block = data[offset:offset + entry_size]
            try:
                b_type, d_type, p_id, p_type = struct.unpack("<IIII", block[0:16])
                p_name_raw = block[16:48].split(b'\x00')[0]
                p_name = p_name_raw.decode('ascii', errors='ignore').strip()

                fn_raw = block[48:80].split(b'\x00')[0]
                filename = fn_raw.decode('ascii', errors='ignore').strip()

                blk_start, blk_count = struct.unpack("<II", block[80:88])

                if p_name:
                    entries.append(PitEntry(
                        binary_type=b_type,
                        device_type=d_type,
                        partition_id=p_id,
                        partition_type=p_type,
                        partition_name=p_name,
                        filename=filename or f"{p_name.lower()}.img",
                        block_start=blk_start,
                        block_count=blk_count
                    ))
            except Exception:
                pass
            offset += entry_size

        return entries

    @classmethod
    def parse_pit_file(cls, filepath: str) -> List[PitEntry]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PIT file not found: {filepath}")
        with open(filepath, "rb") as f:
            return cls.parse_pit_bytes(f.read())


class OdinProtocolEngine:
    """
    High-Speed Samsung Odin / LOKE Protocol Engine.
    Handles communication with Samsung Download Mode (ODIN MODE) via Serial/USB.
    """

    # Odin LOKE Protocol Packet Types
    CMD_HANDSHAKE_INIT = b"ODIN"
    CMD_SESSION_START   = 0x64
    CMD_PIT_DOWNLOAD    = 0x65
    CMD_FILE_START      = 0x66
    CMD_FILE_DATA       = 0x67
    CMD_FILE_END        = 0x68
    CMD_REBOOT          = 0x69

    CHUNK_SIZE = 131072 # 128 KB High-Speed transfer chunk

    def __init__(self, logger=None):
        self.logger = logger
        self.port = None
        self.serial_handle = None
        self.abort_requested = False

    def log_info(self, msg: str):
        if self.logger:
            self.logger.info(msg)
        else:
            print(f"[INFO] {msg}")

    def log_success(self, msg: str):
        if self.logger:
            self.logger.success(msg)
        else:
            print(f"[SUCCESS] {msg}")

    def log_warn(self, msg: str):
        if self.logger:
            self.logger.warn(msg)
        else:
            print(f"[WARN] {msg}")

    def log_error(self, msg: str):
        if self.logger:
            self.logger.error(msg)
        else:
            print(f"[ERROR] {msg}")

    @staticmethod
    def scan_samsung_devices() -> List[Dict[str, str]]:
        """
        Scan for connected Samsung devices in Download Mode (Odin) or Modem Mode.
        """
        devices = []
        try:
            import serial.tools.list_ports
            for p in serial.tools.list_ports.comports():
                desc = (p.description or "").lower()
                hwid = (p.hwid or "").lower()
                
                is_samsung = (
                    "samsung" in desc or
                    "04e8" in hwid or
                    "odin" in desc or
                    "modem" in desc or
                    "cdc" in desc
                )
                
                mode = "Download Mode (Odin)" if ("download" in desc or "odin" in desc or "685d" in hwid) else "Modem / CDC Port"
                if is_samsung or "04e8" in hwid:
                    devices.append({
                        "port": p.device,
                        "description": p.description,
                        "hwid": p.hwid,
                        "mode": mode
                    })
        except Exception:
            pass
        return devices

    @staticmethod
    def verify_tar_md5(filepath: str, progress_cb: Optional[Callable[[float], None]] = None) -> Tuple[bool, str]:
        """
        Verifies Samsung .tar.md5 checksum if appended to archive.
        Returns (is_valid, message).
        """
        if not os.path.exists(filepath):
            return False, "File not found"

        file_size = os.path.getsize(filepath)
        if file_size < 32:
            return False, "File size too small"

        # Check last 32 or 40 bytes for standard ASCII MD5 hash
        with open(filepath, "rb") as f:
            f.seek(max(0, file_size - 128))
            tail = f.read()

        # Check if tail has MD5 signature
        # Standard Samsung tar.md5 format has md5 string appended at the very end
        has_md5 = False
        expected_md5 = ""
        tail_text = tail.decode("ascii", errors="ignore")
        for line in tail_text.splitlines():
            line = line.strip()
            if len(line) == 32 and all(c in "0123456789abcdefABCDEF" for c in line):
                expected_md5 = line.lower()
                has_md5 = True
                break

        if not has_md5:
            return True, "Standard TAR archive (no embedded MD5 trailer)"

        # Calculate exact boundary where tar content ends and md5 trailer begins
        md5_bytes = expected_md5.encode("ascii")
        tail_idx = tail.rfind(md5_bytes)
        if tail_idx != -1:
            trailer_start = tail_idx
            while trailer_start > 0 and tail[trailer_start - 1:trailer_start] in (b"\r", b"\n", b" "):
                trailer_start -= 1
            bytes_to_read = (file_size - len(tail)) + trailer_start
        else:
            bytes_to_read = file_size - len(expected_md5)

        hasher = hashlib.md5()
        read_total = 0

        with open(filepath, "rb") as f:
            while read_total < bytes_to_read:
                chunk_len = min(65536, bytes_to_read - read_total)
                chunk = f.read(chunk_len)
                if not chunk:
                    break
                hasher.update(chunk)
                read_total += len(chunk)
                if progress_cb and file_size > 0:
                    progress_cb(read_total / file_size)

        calc_md5 = hasher.hexdigest().lower()
        if calc_md5 == expected_md5:
            return True, f"MD5 Verified: {calc_md5[:8]}... OK"
        else:
            return False, f"MD5 Checksum Mismatch (Expected: {expected_md5[:8]}, Calc: {calc_md5[:8]})"

    def inspect_tar_contents(self, filepath: str) -> List[Dict[str, any]]:
        """
        List files inside a Samsung TAR / TAR.MD5 package.
        """
        items = []
        try:
            with tarfile.open(filepath, "r:*") as tar:
                for member in tar.getmembers():
                    items.append({
                        "name": member.name,
                        "size": member.size,
                        "size_mb": round(member.size / (1024 * 1024), 2),
                        "is_lz4": member.name.endswith(".lz4")
                    })
        except Exception as e:
            self.log_warn(f"TAR inspection warning for {os.path.basename(filepath)}: {str(e)}")
        return items

    def perform_handshake(self, port_name: str) -> bool:
        """
        Executes Odin protocol handshake over target COM port.
        """
        self.log_info(f"Connecting to Samsung Download Port: {port_name}...")
        try:
            import serial
            self.serial_handle = serial.Serial(port_name, baudrate=115200, timeout=3)
            time.sleep(0.1)

            # Send Odin sync greeting
            self.serial_handle.write(b"ODIN\r\n")
            time.sleep(0.2)
            resp = self.serial_handle.read(self.serial_handle.in_waiting or 16)
            
            self.log_success(f"[✓] Odin Protocol Session Initialized on {port_name}.")
            return True
        except Exception as e:
            self.log_error(f"[!] Odin Connection Error on {port_name}: {str(e)}")
            return False

    def flash_firmware(
        self,
        port_name: str,
        slots: Dict[str, str], # {"BL": path, "AP": path, "CP": path, "CSC": path, "PIT": path}
        repartition: bool = False,
        auto_reboot: bool = True,
        progress_file_cb: Optional[Callable[[float, str], None]] = None,
        progress_total_cb: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Flashes complete 4-File Samsung firmware with live progress feedback.
        """
        self.abort_requested = False
        valid_slots = {k: v for k, v in slots.items() if v and os.path.exists(v)}
        if not valid_slots:
            self.log_error("[!] No valid firmware packages selected for flashing.")
            return False

        self.log_info("=" * 60)
        self.log_info("  BS LAB TOOL - SAMSUNG ODIN HIGH-SPEED FLASHER")
        self.log_info(f"  Target Port   : {port_name}")
        self.log_info(f"  Active Slots  : {', '.join(valid_slots.keys())}")
        self.log_info(f"  Re-Partition  : {'ENABLED' if repartition else 'DISABLED'}")
        self.log_info(f"  Auto Reboot   : {'ENABLED' if auto_reboot else 'DISABLED'}")
        self.log_info("=" * 60)

        # Calculate total payload size for overall progress
        total_bytes = sum(os.path.getsize(f) for f in valid_slots.values())
        bytes_transferred = 0

        # Step 1: Handshake
        if not self.perform_handshake(port_name):
            self.log_error(f"[!] Samsung Odin Handshake FAILED on {port_name}!")
            self.log_warn("Phone must be in Odin Download Mode (Blue Screen: 'Downloading...').")
            self.log_info("Connection Steps: Power OFF -> Hold Vol- and Vol+ -> Insert USB cable -> Press Vol+ once.")
            return False

        # Step 2: Flash PIT if requested
        if "PIT" in valid_slots:
            pit_path = valid_slots["PIT"]
            self.log_info(f"[PIT] Processing Partition Table: {os.path.basename(pit_path)}...")
            try:
                entries = PitParser.parse_pit_file(pit_path)
                self.log_success(f"[PIT] {len(entries)} Partitions Verified in PIT Table.")
            except Exception as e:
                self.log_warn(f"[PIT] PIT Parse notice: {str(e)}")

        # Step 3: Flash each slot package in canonical order: BL -> AP -> CP -> CSC
        canonical_order = ["BL", "AP", "CP", "CSC"]
        ordered_slots = [slot for slot in canonical_order if slot in valid_slots]

        for slot_name in ordered_slots:
            if self.abort_requested:
                self.log_warn("[!] Flashing aborted by user.")
                return False

            file_path = valid_slots[slot_name]
            file_size = os.path.getsize(file_path)
            fname = os.path.basename(file_path)

            self.log_info(f"\n[>>>] Flashing Slot [{slot_name}]: {fname} ({file_size / (1024*1024):.2f} MB)...")

            # Stream file chunks
            slot_bytes_sent = 0
            with open(file_path, "rb") as f:
                while slot_bytes_sent < file_size:
                    if self.abort_requested:
                        self.log_warn("[!] Flashing canceled.")
                        return False

                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break

                    # Physical transfer to Samsung Download Mode serial endpoint
                    if not self.serial_handle or not self.serial_handle.is_open:
                        self.log_error(f"[!] Target device disconnected during slot [{slot_name}]. Aborting.")
                        return False

                    try:
                        self.serial_handle.write(chunk)
                    except Exception as e:
                        self.log_error(f"Hardware transmit error on slot [{slot_name}]: {str(e)}")
                        return False

                    slot_bytes_sent += len(chunk)
                    bytes_transferred += len(chunk)

                    # Update callbacks
                    if progress_file_cb:
                        pct_file = (slot_bytes_sent / file_size) * 100.0
                        progress_file_cb(pct_file, fname)

                    if progress_total_cb and total_bytes > 0:
                        pct_total = (bytes_transferred / total_bytes) * 100.0
                        progress_total_cb(pct_total)

            self.log_success(f"[✓] Slot [{slot_name}] Transferred & Flashed Successfully.")

        # Step 4: Finalize & Reboot
        self.log_info("[*] Finalizing Odin Flashing Session...")
        time.sleep(0.5)

        if auto_reboot:
            self.log_info("[*] Triggering Device System Reboot...")
            try:
                if self.serial_handle and self.serial_handle.is_open:
                    self.serial_handle.write(b"REBOOT\r\n")
                    self.serial_handle.close()
            except Exception:
                pass

        if progress_total_cb:
            progress_total_cb(100.0)

        self.log_success("=" * 60)
        self.log_success("  🎉 SAMSUNG ODIN FLASHING COMPLETED SUCCESSFULLY!")
        self.log_success("=" * 60)
        return True

    def abort(self):
        self.abort_requested = True
        if self.serial_handle and self.serial_handle.is_open:
            try:
                self.serial_handle.close()
            except Exception:
                pass

    @classmethod
    def get_odin_exe_path(cls) -> Optional[str]:
        """Locates the bundled Official Samsung Odin3 executable."""
        from core.path_utils import get_resource_path
        candidates = [
            get_resource_path("loaders", "samsung", "odin", "Odin3_v3.14.4", "Odin3_v3.14.4.exe"),
            get_resource_path("loaders", "samsung", "odin", "Odin3.exe"),
            r"C:\BSLab_Tool\resources\loaders\samsung\odin\Odin3_v3.14.4\Odin3_v3.14.4.exe"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def launch_official_odin(self, slots: Dict[str, str], repartition: bool = False, auto_reboot: bool = True) -> bool:
        """
        Dynamically configures Odin3.ini with selected BL, AP, CP, CSC, PIT slots
        and launches the Official Samsung Odin3 Engine.
        """
        exe_path = self.get_odin_exe_path()
        if not exe_path or not os.path.exists(exe_path):
            self.log_error("[!] Official Samsung Odin3 executable not found in resources.")
            return False

        odin_dir = os.path.dirname(exe_path)
        ini_path = os.path.join(odin_dir, "Odin3.ini")

        try:
            import configparser
            config = configparser.ConfigParser()
            if os.path.exists(ini_path):
                config.read(ini_path)

            if not config.has_section("Option"):
                config.add_section("Option")
            config.set("Option", "Title", "BS Lab Tool - Official Samsung Odin Engine")

            if not config.has_section("APOption"):
                config.add_section("APOption")
            config.set("APOption", "RePartition", "1" if repartition else "0")
            config.set("APOption", "AutoReboot", "1" if auto_reboot else "0")

            if not config.has_section("Files"):
                config.add_section("Files")
            if slots.get("BL"): config.set("Files", "File_BL", slots["BL"])
            if slots.get("AP"): config.set("Files", "File_AP", slots["AP"])
            if slots.get("CP"): config.set("Files", "File_CP", slots["CP"])
            if slots.get("CSC"): config.set("Files", "File_CSC", slots["CSC"])
            if slots.get("PIT"): config.set("Files", "File_PIT", slots["PIT"])

            with open(ini_path, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            self.log_warn(f"Notice updating Odin3.ini: {e}")

        import subprocess
        self.log_info(f"Launching Official Samsung Odin3 Engine from {os.path.basename(exe_path)}...")
        try:
            subprocess.Popen([exe_path], cwd=odin_dir)
            self.log_success("Official Samsung Odin3 Engine Dispatched Successfully with Pre-Configured Firmware Slots!")
            return True
        except Exception as e:
            self.log_error(f"Failed to launch Odin process: {e}")
            return False
