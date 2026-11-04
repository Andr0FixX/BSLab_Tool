import os
import time
import struct
import serial
import serial.tools.list_ports

from core.logger import UILogger
from engines.qualcomm.sahara import SaharaEngine
from engines.qualcomm.firehose import FirehoseEngine
from engines.qualcomm.xml_parser import QualcommXMLParser

class QualcommEngine:
    """Master Qualcomm Snapdragon (EDL 9008) Servicing & Flashing Platform."""

    def __init__(self, logger: UILogger = None):
        self.logger = logger
        self.serial_port = None
        self.sahara = None
        self.firehose = None
        self.is_running = False

    def log(self, msg, level="info"):
        if self.logger:
            if level == "success":
                self.logger.success(msg)
            elif level == "error":
                self.logger.error(msg)
            elif level == "warn":
                self.logger.warn(msg)
            elif level == "brom":
                self.logger.brom(msg)
            else:
                self.logger.info(msg)
        else:
            print(f"[QC] {msg}")

    def _find_edl_port(self, specified_port: str = None) -> str:
        """Finds active Qualcomm HS-USB QDLoader 9008 COM port."""
        if specified_port and "auto" not in specified_port.lower():
            return specified_port

        coms = list(serial.tools.list_ports.comports())
        for c in coms:
            vid = c.vid or 0
            pid = c.pid or 0
            desc = (c.description or "").lower()
            if (vid == 0x05C6 and pid == 0x9008) or "9008" in desc or "qdloader" in desc:
                return c.device

        # If any COM found, return first
        return coms[0].device if coms else None

    def _open_port(self, port_name: str, baudrate: int = 115200, timeout: float = 0.5) -> bool:
        """Opens serial port with hardware handshaking lines toggled."""
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                write_timeout=timeout
            )
            # Passive open without toggling DTR/RTS to preserve Sahara BootROM buffer
            time.sleep(0.05)
            return True
        except Exception as e:
            self.log(f"Failed to open Qualcomm port {port_name}: {str(e)}", "error")
            return False

    def _close_port(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None
        self.sahara = None
        self.firehose = None

    def connect(self, port_name: str, programmer_path: str = None) -> bool:
        """
        Connects to Qualcomm EDL 9008 port, performs Sahara handshake,
        and initializes Firehose XML engine.
        """
        real_port = self._find_edl_port(port_name)
        if not real_port:
            self.log("Qualcomm 9008 Device Not Found! Connect phone in EDL mode (Test Point / EDL Cable).", "error")
            return False

        self.log(f"Connecting to Qualcomm Port: {real_port}...")
        if not self._open_port(real_port):
            return False

        # 1. Sahara Handshake (Load Firehose Programmer)
        if programmer_path and os.path.exists(programmer_path):
            self.sahara = SaharaEngine(self.serial_port, logger=self.logger)
            sahara_ok = self.sahara.execute_handshake(programmer_path)
            if not sahara_ok:
                self.log("Sahara Handshake failed. Ensure correct MBN/ELF programmer is selected.", "error")
                self._close_port()
                return False
        else:
            self.log("No custom programmer attached. Probing if target is already in Firehose mode...", "warn")

        # 2. Firehose Configuration
        self.firehose = FirehoseEngine(self.serial_port, logger=self.logger)
        cfg_ok = self.firehose.configure(memory_type="eMMC")
        if not cfg_ok:
            self.log("Firehose VIP handshake could not be established.", "error")
            self._close_port()
            return False

        return True

    def read_device_info(self, port_name: str, programmer_path: str = None) -> dict:
        """Reads hardware details, partition table info, and storage type."""
        self.is_running = True
        try:
            if not self.connect(port_name, programmer_path):
                return None
            info = self.firehose.get_device_info()
            return info
        finally:
            self.is_running = False
            self._close_port()

    def read_gpt_partitions(self, port_name: str, programmer_path: str = None) -> list:
        """Reads and parses the live GPT partition table directly from device eMMC/UFS without XML."""
        self.is_running = True
        try:
            if not self.connect(port_name, programmer_path):
                return []
            self.log("Reading live GPT partition sectors (LBA 0-33)...")
            raw_bytes = self.firehose.read_sectors_raw(start_sector=0, num_sectors=34, sector_size=512)
            if not raw_bytes or len(raw_bytes) < 1024:
                self.log("Failed to retrieve GPT sectors from device.", "error")
                return []

            partitions = []
            header_offset = -1
            if len(raw_bytes) >= 1024 and raw_bytes[512:520] == b'EFI PART':
                header_offset = 512
            elif raw_bytes[:8] == b'EFI PART':
                header_offset = 0

            if header_offset >= 0:
                num_entries = struct.unpack('<I', raw_bytes[header_offset+80:header_offset+84])[0]
                entry_size = struct.unpack('<I', raw_bytes[header_offset+84:header_offset+88])[0]
                if num_entries == 0 or num_entries > 256: num_entries = 128
                if entry_size == 0 or entry_size > 512: entry_size = 128

                entries_offset = header_offset + 512
                for i in range(num_entries):
                    pos = entries_offset + (i * entry_size)
                    if pos + entry_size > len(raw_bytes):
                        break
                    entry = raw_bytes[pos:pos+entry_size]
                    type_guid = entry[0:16]
                    if type_guid == b'\x00' * 16:
                        continue
                    start_lba = struct.unpack('<Q', entry[32:40])[0]
                    end_lba = struct.unpack('<Q', entry[40:48])[0]
                    if end_lba < start_lba:
                        continue
                    num_sectors = end_lba - start_lba + 1
                    name_raw = entry[56:128]
                    try:
                        name = name_raw.decode('utf-16le', errors='ignore').split('\x00')[0].strip()
                    except Exception:
                        name = f"part_{i}"
                    if name:
                        partitions.append({
                            "name": name,
                            "start_sector": start_lba,
                            "num_sectors": num_sectors,
                            "size_bytes": num_sectors * 512,
                            "sector_size": 512
                        })

                self.log(f"[✓] Live GPT Parsed Successfully: {len(partitions)} active partitions identified!", "success")
                return partitions
            else:
                self.log("No valid EFI PART GPT signature found in primary sectors.", "warn")
                return []
        finally:
            self.is_running = False
            self._close_port()

    def dump_partitions(self, port_name: str, programmer_path: str = None, target_names: list = None, out_dir: str = None, progress_cb = None) -> list:
        """Autonomous bit-by-bit raw partition dumper (boot, modem, carrier, etc.) to local folder."""
        self.is_running = True
        try:
            if not self.connect(port_name, programmer_path):
                return []

            self.log("Querying device partition table over Firehose...")
            raw_bytes = self.firehose.read_sectors_raw(start_sector=0, num_sectors=34, sector_size=512)
            partitions = []
            header_offset = 512 if len(raw_bytes) >= 1024 and raw_bytes[512:520] == b'EFI PART' else (0 if raw_bytes[:8] == b'EFI PART' else -1)
            if header_offset >= 0:
                num_entries = struct.unpack('<I', raw_bytes[header_offset+80:header_offset+84])[0]
                entry_size = struct.unpack('<I', raw_bytes[header_offset+84:header_offset+88])[0]
                if num_entries == 0 or num_entries > 256: num_entries = 128
                if entry_size == 0 or entry_size > 512: entry_size = 128
                entries_offset = header_offset + 512
                for i in range(num_entries):
                    pos = entries_offset + (i * entry_size)
                    if pos + entry_size > len(raw_bytes): break
                    entry = raw_bytes[pos:pos+entry_size]
                    if entry[0:16] == b'\x00' * 16: continue
                    start_lba = struct.unpack('<Q', entry[32:40])[0]
                    end_lba = struct.unpack('<Q', entry[40:48])[0]
                    if end_lba < start_lba: continue
                    num_sectors = end_lba - start_lba + 1
                    try:
                        name = entry[56:128].decode('utf-16le', errors='ignore').split('\x00')[0].strip()
                    except Exception:
                        name = f"part_{i}"
                    if name:
                        partitions.append({
                            "name": name,
                            "start_sector": start_lba,
                            "num_sectors": num_sectors,
                            "size_bytes": num_sectors * 512,
                            "sector_size": 512
                        })

            if not partitions:
                self.log("Partition table empty or unreadable. Cannot proceed with dump.", "error")
                return []

            # Filter targets
            if target_names:
                targets_lower = [t.lower() for t in target_names]
                dump_list = [p for p in partitions if p["name"].lower() in targets_lower]
            else:
                # Essential firmware list (boot, carrier, modem, EFS, persist, recovery, etc.)
                essential_names = {
                    "boot", "boot_a", "boot_b", "carrier", "modem", "modem_a", "modem_b",
                    "modemst1", "modemst2", "fsg", "fsc", "persist", "recovery", "dtbo", "dtbo_a", "dtbo_b",
                    "vbmeta", "vbmeta_a", "vbmeta_b", "splash", "logo", "devinfo", "config"
                }
                dump_list = [p for p in partitions if p["name"].lower() in essential_names]
                if not dump_list:
                    # Fallback to first 10 partitions if none of the above match
                    dump_list = partitions[:10]

            if not out_dir:
                timestamp = int(time.time())
                out_dir = os.path.join(os.getcwd(), "backups", f"qualcomm_dump_{timestamp}")
            os.makedirs(out_dir, exist_ok=True)

            self.log(f"Starting dump of {len(dump_list)} selected partitions to: {out_dir}", "brom")
            dumped_files = []
            total_parts = len(dump_list)

            for idx, p in enumerate(dump_list, 1):
                p_name = p["name"]
                target_file = os.path.join(out_dir, f"{p_name}.img")
                def single_cb(pct, status_text):
                    if progress_cb:
                        overall = ((idx - 1) + pct) / total_parts
                        progress_cb(min(1.0, overall), pct, p_name, status_text)

                ok = self.firehose.read_partition(
                    start_sector=p["start_sector"],
                    num_sectors=p["num_sectors"],
                    out_path=target_file,
                    partition_name=p_name,
                    sector_size=p["sector_size"],
                    progress_cb=single_cb
                )
                if ok:
                    dumped_files.append(target_file)

            if progress_cb:
                progress_cb(1.0, 1.0, "Complete", "Qualcomm Firmware Dump 100% Done!")

            self.log("==================================================", "success")
            self.log(f"QUALCOMM DUMP COMPLETED: {len(dumped_files)}/{total_parts} Partitions Saved!", "success")
            self.log(f"Folder: {out_dir}", "success")
            self.log("==================================================", "success")
            return dumped_files
        finally:
            self.is_running = False
            self._close_port()

    def reset_frp(self, port_name: str, programmer_path: str = None, rawprogram_path: str = None, progress_cb=None) -> bool:
        """Erases Google FRP Lock partition (frp / config)."""
        self.is_running = True
        try:
            self.log("Starting Qualcomm One-Click FRP Reset...")
            if not self.connect(port_name, programmer_path):
                return False

            if progress_cb: progress_cb(0.3, "Searching FRP Partition in XML...")

            # Locate FRP partition in RawProgram XML if available
            target_part = None
            if rawprogram_path and os.path.exists(rawprogram_path):
                parts = QualcommXMLParser.parse_rawprogram(rawprogram_path)
                for p in parts:
                    if p["name"].lower() in ("frp", "config"):
                        target_part = p
                        break

            if target_part:
                self.log(f"Found target FRP partition: {target_part['name']} at sector 0x{target_part['start_sector']:X}")
                if progress_cb: progress_cb(0.6, "Erasing FRP Partition...")
                ok = self.firehose.erase_partition(
                    start_sector=target_part["start_sector"],
                    num_sectors=target_part["num_sectors"],
                    partition_name=target_part["name"],
                    sector_size=target_part["sector_size"]
                )
            else:
                self.log("RawProgram XML not loaded. Erasing standard FRP partition (config)...", "warn")
                # Fallback to standard offset (512KB config block)
                ok = self.firehose.erase_partition(start_sector=0x2000, num_sectors=1024, partition_name="frp", sector_size=512)

            if ok:
                if progress_cb: progress_cb(1.0, "Reset FRP Done 100%")
                self.log("==================================================", "success")
                self.log("QUALCOMM RESET FRP COMPLETED SUCCESSFULLY (100%)!", "success")
                self.log("Google Account Lock Removed. Rebooting device...", "success")
                self.log("==================================================", "success")
                time.sleep(0.5)
                self.firehose.reboot()
                return True
            return False
        finally:
            self.is_running = False
            self._close_port()

    def factory_reset(self, port_name: str, programmer_path: str = None, rawprogram_path: str = None, wipe_frp: bool = False, progress_cb=None) -> bool:
        """Erases userdata and metadata partitions to remove Screen/Pattern Lock."""
        self.is_running = True
        try:
            self.log("Starting Qualcomm Factory Reset (Userdata Wipe)...")
            if not self.connect(port_name, programmer_path):
                return False

            targets = ["userdata", "metadata", "cache"]
            if wipe_frp:
                targets.append("frp")

            parts_to_erase = []
            if rawprogram_path and os.path.exists(rawprogram_path):
                all_parts = QualcommXMLParser.parse_rawprogram(rawprogram_path)
                for p in all_parts:
                    if p["name"].lower() in targets:
                        parts_to_erase.append(p)

            total = len(parts_to_erase)
            if parts_to_erase:
                for idx, p in enumerate(parts_to_erase, start=1):
                    if progress_cb: progress_cb(idx / total, f"Formatting {p['name']}...")
                    self.firehose.erase_partition(p["start_sector"], p["num_sectors"], p["name"], p["sector_size"])
            else:
                self.log("Formatting standard Userdata partition...", "warn")
                self.firehose.erase_partition(start_sector=0x100000, num_sectors=0x80000, partition_name="userdata")

            if progress_cb: progress_cb(1.0, "Factory Reset Done!")
            self.log("==================================================", "success")
            self.log("QUALCOMM FACTORY RESET COMPLETED SUCCESSFULLY!", "success")
            self.log("Screen Lock Wiped. Rebooting device...", "success")
            self.log("==================================================", "success")
            time.sleep(0.5)
            self.firehose.reboot()
            return True
        finally:
            self.is_running = False
            self._close_port()

    def backup_efs(self, port_name: str, programmer_path: str = None, rawprogram_path: str = None, out_dir: str = "backup_efs", progress_cb=None) -> bool:
        """Backs up Qualcomm EFS & Network Calibration partitions (modemst1, modemst2, fsg)."""
        self.is_running = True
        try:
            self.log(f"Starting EFS & Network Backup to {out_dir}...")
            if not self.connect(port_name, programmer_path):
                return False

            if not rawprogram_path or not os.path.exists(rawprogram_path):
                self.log("RawProgram XML required to resolve EFS sector boundaries.", "error")
                return False

            efs_targets = ["modemst1", "modemst2", "fsg", "fsc"]
            all_parts = QualcommXMLParser.parse_rawprogram(rawprogram_path)
            found_parts = [p for p in all_parts if p["name"].lower() in efs_targets]

            if not found_parts:
                self.log("No EFS partitions found in the provided RawProgram XML.", "error")
                return False

            os.makedirs(out_dir, exist_ok=True)
            total = len(found_parts)

            for idx, p in enumerate(found_parts, start=1):
                out_file = os.path.join(out_dir, f"{p['name']}.bin")
                if progress_cb: progress_cb(idx / total, f"Dumping {p['name']}...")
                self.firehose.read_partition(p["start_sector"], p["num_sectors"], out_file, p["name"], p["sector_size"])

            if progress_cb: progress_cb(1.0, "EFS Backup 100%")
            self.log(f"[✓] Qualcomm EFS Backup Saved ({total} partitions) -> {out_dir}", "success")
            return True
        finally:
            self.is_running = False
            self._close_port()

    def flash_firmware(self, port_name: str, programmer_path: str, rawprogram_path: str, patch_path: str = None,
                       partitions_to_flash: list = None, reboot_after: bool = True, dual_progress_cb=None) -> bool:
        """
        Flashes partition images from RawProgram XML with dual-progress reporting.
        """
        self.is_running = True
        try:
            self.log("==================================================", "brom")
            self.log("STARTING QUALCOMM SNAPDRAGON RAWPROGRAM FLASHING", "brom")
            self.log("==================================================", "brom")

            if not self.connect(port_name, programmer_path):
                return False

            if not rawprogram_path or not os.path.exists(rawprogram_path):
                self.log("RawProgram XML file missing or invalid.", "error")
                return False

            firmware_dir = os.path.dirname(rawprogram_path)
            items = partitions_to_flash if partitions_to_flash else QualcommXMLParser.parse_rawprogram(rawprogram_path, firmware_dir)
            valid_items = [p for p in items if p.get("exists", False) and p.get("file_path")]

            if not valid_items:
                self.log("No partition image files found on disk to flash.", "error")
                return False

            total_parts = len(valid_items)
            self.log(f"Total Partitions to Flash: {total_parts}")

            for idx, part in enumerate(valid_items):
                p_name = part["name"]
                f_path = part["file_path"]
                start_sec = part["start_sector"]
                num_sec = part["num_sectors"]
                sec_size = part["sector_size"]

                def single_cb(pct, status_text):
                    if dual_progress_cb:
                        part_weight = 1.0 / total_parts
                        overall_pct = min(1.0, (idx * part_weight) + (pct * part_weight))
                        dual_progress_cb(overall_pct, pct, p_name, status_text)

                ok = self.firehose.program_partition(start_sec, num_sec, f_path, p_name, sec_size, progress_cb=single_cb)
                if not ok:
                    self.log(f"Flashing halted due to error on {p_name}.", "error")
                    return False

            if dual_progress_cb:
                dual_progress_cb(1.0, 1.0, "Complete", "Qualcomm Flashing 100%!")

            self.log("==================================================", "success")
            self.log("ALL QUALCOMM PARTITIONS FLASHED SUCCESSFULLY (100%)!", "success")
            self.log("==================================================", "success")

            if reboot_after:
                time.sleep(1.0)
                self.firehose.reboot()

            return True
        finally:
            self.is_running = False
            self._close_port()

    def reboot_device(self, port_name: str, programmer_path: str = None, mode: str = "reset") -> bool:
        """Reboots Qualcomm device from EDL mode to Android or Fastboot."""
        self.is_running = True
        try:
            if not self.connect(port_name, programmer_path):
                return False
            return self.firehose.reboot(mode=mode)
        finally:
            self.is_running = False
            self._close_port()

    def abort(self):
        """Halts running Qualcomm operation."""
        self.is_running = False
        if self.sahara:
            self.sahara.aborted = True
        if self.firehose:
            self.firehose.aborted = True
        self._close_port()
        self.log("Qualcomm operation aborted by user.", "warn")
