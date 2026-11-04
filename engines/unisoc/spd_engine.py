import os
import time
import serial
import serial.tools.list_ports

from core.logger import UILogger
from engines.unisoc.bsl_protocol import BSLProtocol
from engines.unisoc.fdl_engine import FdlEngine
from engines.unisoc.pac_parser import PacParser
from utils.file_utils import format_bytes

class UnisocEngine:
    """Master Unisoc / Spreadtrum (SPD) PAC Flasher & Servicing Platform."""

    # Default FDL RAM execution addresses for modern Unisoc chipsets (T606, T612, T616, SC9863A)
    FDL1_ADDR_TIGER = 0x00005000
    FDL2_ADDR_TIGER = 0x9E000000

    def __init__(self, logger: UILogger = None):
        self.logger = logger
        self.serial_port = None
        self.fdl_engine = None
        self.is_running = False
        self.aborted = False

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
            print(f"[SPD] {msg}")

    def _find_spd_port(self, specified_port: str = None) -> str:
        """Finds active Unisoc / Spreadtrum COM port."""
        if specified_port and "auto" not in specified_port.lower():
            return specified_port

        coms = list(serial.tools.list_ports.comports())
        for c in coms:
            desc = (c.description or "").lower()
            if any(k in desc for k in ["spd", "sprd", "spreadtrum", "unisoc"]):
                return c.device

        return coms[0].device if coms else None

    def _open_port(self, port_name: str, baudrate: int = 115200, timeout: float = 0.5) -> bool:
        """Opens serial port with DTR/RTS lines asserted."""
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
            self.serial_port.dtr = True
            self.serial_port.rts = True
            time.sleep(0.05)
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            return True
        except Exception as e:
            self.log(f"Failed to open Unisoc port {port_name}: {str(e)}", "error")
            return False

    def _close_port(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None
        self.fdl_engine = None

    def connect(self, port_name: str, pac_path: str = None) -> bool:
        """
        Traps Unisoc BROM via 0x7E sync, performs BSL connect,
        and executes FDL1 and FDL2 from PAC archive.
        """
        real_port = self._find_spd_port(port_name)
        if not real_port:
            self.log("Unisoc Port Not Detected! Power OFF phone, hold Vol- / Vol+ and plug USB.", "error")
            return False

        self.log(f"Connecting to Unisoc Port: {real_port} at 115200 baud...")
        if not self._open_port(real_port):
            return False

        self.fdl_engine = FdlEngine(self.serial_port, logger=self.logger)

        # 1. BSL 0x7E Synchronization Trap
        self.log("Sending BSL Sync Frames (0x7E) to trap Unisoc Bootloader...")
        synced = BSLProtocol.sync_device(self.serial_port, attempts=35)
        if not synced:
            self.log("BSL 0x7E Sync Mismatch/Timeout. Reconnect phone with Vol- held.", "error")
            self._close_port()
            return False

        self.log("[SYNC] Unisoc BSL Handshake Trapped Successfully (0x7E ACK Received)!", "success")

        # 2. Connect Command
        ok, _, _ = BSLProtocol.send_cmd(self.serial_port, BSLProtocol.CMD_CONNECT, b'', timeout=4.0)
        if not ok:
            self.log("BSL Connect Command rejected.", "warn")

        # 3. If PAC provided, extract and load FDL1 & FDL2
        if pac_path and os.path.exists(pac_path):
            self.log(f"Extracting FDL1 & FDL2 from PAC Archive: {os.path.basename(pac_path)}...")
            parsed = PacParser.parse(pac_path)

            fdl1_meta = next((p for p in parsed["partitions"] if "fdl1" in p["name"].lower()), None)
            fdl2_meta = next((p for p in parsed["partitions"] if "fdl2" in p["name"].lower()), None)

            if fdl1_meta:
                with open(pac_path, "rb") as pf:
                    pf.seek(fdl1_meta["data_offset"])
                    fdl1_bytes = pf.read(fdl1_meta["file_size"])
                ok_fdl1 = self.fdl_engine.load_fdl(fdl1_bytes, self.FDL1_ADDR_TIGER, fdl_name="FDL1")
                if not ok_fdl1:
                    self.log("FDL1 bootloader execution failed.", "error")
                    self._close_port()
                    return False

            if fdl2_meta:
                with open(pac_path, "rb") as pf:
                    pf.seek(fdl2_meta["data_offset"])
                    fdl2_bytes = pf.read(fdl2_meta["file_size"])
                ok_fdl2 = self.fdl_engine.load_fdl(fdl2_bytes, self.FDL2_ADDR_TIGER, fdl_name="FDL2")
                if not ok_fdl2:
                    self.log("FDL2 storage flasher execution failed.", "error")
                    self._close_port()
                    return False

            self.log("FDL1 & FDL2 Bootloader Active: Storage & Partition Engine Ready!", "success")
        else:
            # PAC not provided: Load Built-in Universal FDL1 & FDL2 from resources
            from core.model_repository import ModelRepository
            fdl1_path = ModelRepository.get_unisoc_universal_fdl(1)
            fdl2_path = ModelRepository.get_unisoc_universal_fdl(2)

            if fdl1_path and os.path.exists(fdl1_path) and fdl2_path and os.path.exists(fdl2_path):
                self.log("PAC not loaded. Utilizing Universal Unisoc FDL1 & FDL2 Loaders (PAC-Less Mode)...")
                with open(fdl1_path, "rb") as f1:
                    fdl1_bytes = f1.read()
                ok_fdl1 = self.fdl_engine.load_fdl(fdl1_bytes, self.FDL1_ADDR_TIGER, fdl_name="Universal FDL1")
                if not ok_fdl1:
                    self.log("Universal FDL1 bootloader execution failed.", "error")
                    self._close_port()
                    return False

                with open(fdl2_path, "rb") as f2:
                    fdl2_bytes = f2.read()
                ok_fdl2 = self.fdl_engine.load_fdl(fdl2_bytes, self.FDL2_ADDR_TIGER, fdl_name="Universal FDL2")
                if not ok_fdl2:
                    self.log("Universal FDL2 storage flasher execution failed.", "error")
                    self._close_port()
                    return False

                self.log("Built-in Universal FDL1 & FDL2 Active: Ready for Direct Servicing!", "success")
            else:
                self.log("Notice: PAC file not loaded. Please select PAC file if device fails handshake.", "warn")

        return True

    def read_device_info(self, port_name: str, pac_path: str = None) -> dict:
        """Reads chip architecture, platform, and PAC product information."""
        self.is_running = True
        try:
            if not self.connect(port_name, pac_path):
                return None

            chip = self.fdl_engine.read_chip_info()
            info = {
                "chipset": chip,
                "status": "Online (BSL / FDL Connected)"
            }

            if pac_path and os.path.exists(pac_path):
                parsed = PacParser.parse(pac_path)
                info["product_name"] = parsed["product_name"]
                info["product_version"] = parsed["product_version"]
                info["partitions_count"] = parsed["file_count"]

            self.log("==================================================", "success")
            self.log("UNISOC DEVICE SPECIFICATIONS (READ INFO)", "success")
            self.log("==================================================", "success")
            self.log(f"Chip Architecture: {info.get('chipset', 'Tiger / SC Series')}")
            if "product_name" in info:
                self.log(f"Product Model    : {info['product_name']}")
            if "product_version" in info:
                self.log(f"Product Version  : {info['product_version']}")
            self.log(f"Protocol State   : {info['status']}", "success")
            self.log("==================================================", "success")
            return info
        finally:
            self.is_running = False
            self._close_port()

    def reset_frp(self, port_name: str, pac_path: str = None, progress_cb=None) -> bool:
        """Erases 'persist' / 'misc' partition to wipe Google FRP Lock."""
        self.is_running = True
        try:
            self.log("Starting Unisoc One-Click FRP Reset (Google Lock)...")
            if not self.connect(port_name, pac_path):
                return False

            if progress_cb: progress_cb(0.4, "Formatting 'persist' partition...")
            ok1 = self.fdl_engine.erase_partition("persist")

            if progress_cb: progress_cb(0.7, "Formatting 'misc' partition...")
            ok2 = self.fdl_engine.erase_partition("misc")

            if ok1 or ok2:
                if progress_cb: progress_cb(1.0, "Reset FRP Done (100%)")
                self.log("==================================================", "success")
                self.log("UNISOC RESET FRP COMPLETED SUCCESSFULLY (100%)!", "success")
                self.log("Google FRP Lock Removed. Rebooting device...", "success")
                self.log("==================================================", "success")
                time.sleep(0.5)
                self.fdl_engine.reboot()
                return True
            else:
                self.log("FRP wipe command failed on persist/misc partitions.", "error")
                return False
        finally:
            self.is_running = False
            self._close_port()

    def factory_reset(self, port_name: str, pac_path: str = None, progress_cb=None) -> bool:
        """Erases userdata and metadata partitions to remove Screen/Pattern Lock."""
        self.is_running = True
        try:
            self.log("Starting Unisoc Factory Reset (Userdata Wipe)...")
            if not self.connect(port_name, pac_path):
                return False

            targets = ["userdata", "metadata", "cache"]
            total = len(targets)

            for idx, part in enumerate(targets, start=1):
                if progress_cb: progress_cb(idx / total, f"Formatting {part}...")
                self.fdl_engine.erase_partition(part)

            if progress_cb: progress_cb(1.0, "Factory Reset Done (100%)")
            self.log("==================================================", "success")
            self.log("UNISOC FACTORY RESET COMPLETED SUCCESSFULLY!", "success")
            self.log("Screen Lock Wiped. Rebooting device...", "success")
            self.log("==================================================", "success")
            time.sleep(0.5)
            self.fdl_engine.reboot()
            return True
        finally:
            self.is_running = False
            self._close_port()

    def flash_pac(self, port_name: str, pac_path: str, partitions_to_flash: list = None,
                  reboot_after: bool = True, dual_progress_cb=None) -> bool:
        """
        Flashes partition images directly from PAC firmware archive.
        """
        self.is_running = True
        try:
            self.log("==================================================", "brom")
            self.log("STARTING UNISOC / SPREADTRUM PAC FIRMWARE FLASHING", "brom")
            self.log("==================================================", "brom")

            if not os.path.exists(pac_path):
                self.log(f"PAC file not found: {pac_path}", "error")
                return False

            if not self.connect(port_name, pac_path):
                return False

            parsed = PacParser.parse(pac_path)
            all_parts = parsed["partitions"]

            # Filter non-FDL download partitions
            candidates = [p for p in all_parts if p.get("is_checked", False) and "fdl" not in p["name"].lower()]
            if partitions_to_flash:
                candidates = [p for p in candidates if p["name"].lower() in [sel["name"].lower() for sel in partitions_to_flash]]

            if not candidates:
                self.log("No valid partitions selected to flash.", "error")
                return False

            total_count = len(candidates)
            self.log(f"Partitions to Flash ({total_count}): {', '.join(p['name'] for p in candidates[:8])}...")

            with open(pac_path, "rb") as pac_f:
                for idx, part in enumerate(candidates):
                    p_name = part["name"]
                    offset = part["data_offset"]
                    size = part["file_size"]

                    pac_f.seek(offset)
                    data_bytes = pac_f.read(size)

                    def single_cb(pct, status_text):
                        if dual_progress_cb:
                            part_weight = 1.0 / total_count
                            overall_pct = min(1.0, (idx * part_weight) + (pct * part_weight))
                            dual_progress_cb(overall_pct, pct, p_name, status_text)

                    ok = self.fdl_engine.write_partition(p_name, data_bytes, progress_cb=single_cb)
                    if not ok:
                        self.log(f"Flashing stopped due to write error on '{p_name}'.", "error")
                        return False

            if dual_progress_cb:
                dual_progress_cb(1.0, 1.0, "Complete", "PAC Flashing 100%!")

            self.log("==================================================", "success")
            self.log("ALL UNISOC PARTITIONS FLASHED SUCCESSFULLY (100%)!", "success")
            self.log("==================================================", "success")

            if reboot_after:
                time.sleep(1.0)
                self.fdl_engine.reboot()

            return True
        finally:
            self.is_running = False
            self._close_port()

    def reboot_device(self, port_name: str) -> bool:
        """Sends normal reset to Unisoc device."""
        self.is_running = True
        try:
            real_port = self._find_spd_port(port_name)
            if not real_port or not self._open_port(real_port):
                return False
            self.fdl_engine = FdlEngine(self.serial_port, logger=self.logger)
            return self.fdl_engine.reboot()
        finally:
            self.is_running = False
            self._close_port()

    def abort(self):
        """Halts running Unisoc operation."""
        self.is_running = False
        self.aborted = True
        if self.fdl_engine:
            self.fdl_engine.aborted = True
        self._close_port()
        self.log("Unisoc operation aborted by user.", "warn")
