import time
import struct
import serial
from engines.unisoc.bsl_protocol import BSLProtocol
from utils.file_utils import format_bytes

class FdlEngine:
    """
    Handles Unisoc / Spreadtrum FDL1 and FDL2 loading, execution,
    partition block writes, and partition erases.
    """

    CHUNK_SIZE = 2048  # 2KB chunks for BSL MID_DATA

    def __init__(self, serial_port: serial.Serial, logger=None):
        self.ser = serial_port
        self.logger = logger
        self.aborted = False

    def log(self, msg, level="info"):
        if self.logger:
            if level == "success":
                self.logger.success(msg)
            elif level == "error":
                self.logger.error(msg)
            elif level == "warn":
                self.logger.warn(msg)
            else:
                self.logger.brom(msg)
        else:
            print(f"[FDL] {msg}")

    def load_fdl(self, fdl_data: bytes, load_addr: int, fdl_name: str = "FDL1", progress_cb=None) -> bool:
        """
        Streams FDL binary image into Unisoc RAM and executes it.
        """
        data_len = len(fdl_data)
        self.log(f"Initiating {fdl_name} Transfer ({format_bytes(data_len)} at RAM address: 0x{load_addr:08X})...")

        # 1. START DATA: [addr: uint32 BE, length: uint32 BE]
        start_payload = struct.pack(">II", load_addr, data_len)
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_START_DATA, start_payload, timeout=5.0)
        if not ok:
            self.log(f"{fdl_name} Start Data rejected by device.", "error")
            return False

        # 2. MID DATA: send chunks
        offset = 0
        while offset < data_len and not self.aborted:
            chunk = fdl_data[offset : offset + self.CHUNK_SIZE]
            ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_MID_DATA, chunk, timeout=4.0)
            if not ok:
                self.log(f"Error streaming {fdl_name} chunk at offset 0x{offset:X}", "error")
                return False

            offset += len(chunk)
            if progress_cb:
                pct = min(1.0, offset / data_len)
                progress_cb(pct, f"Sending {fdl_name}: {int(pct * 100)}%")

        # 3. END DATA
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_END_DATA, b'', timeout=4.0)
        if not ok:
            self.log(f"{fdl_name} End Data rejected.", "error")
            return False

        # 4. EXEC DATA: Execute FDL in RAM
        self.log(f"Executing {fdl_name} in target RAM...")
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_EXEC_DATA, b'', timeout=5.0)
        if ok:
            self.log(f"[✓] {fdl_name} Executed Successfully!", "success")
            time.sleep(0.3)
            return True
        else:
            self.log(f"{fdl_name} Exec Data reported error.", "warn")
            return False

    def read_chip_info(self) -> str:
        """Queries hardware chip name / SoC ID from device."""
        ok, resp_type, data = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_READ_CHIP_TYPE, b'', timeout=3.0)
        if ok and data:
            try:
                chip_name = data.decode("utf-16le", errors="ignore").strip("\x00")
                if not chip_name:
                    chip_name = data.decode("ascii", errors="ignore").strip("\x00")
                return chip_name if chip_name else "Unisoc Universal (Tiger/SC)"
            except Exception:
                return "Unisoc Universal (Tiger/SC)"
        return "Unisoc Tiger T606 / T612 / SC9863A"

    def erase_partition(self, partition_name: str) -> bool:
        """Erases specific partition on device (e.g. persist, misc, userdata)."""
        self.log(f"Erasing Unisoc partition '{partition_name}'...")
        # Encode partition name as UTF-16LE with null termination
        p_bytes = partition_name.encode("utf-16le") + b'\x00\x00'
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_ERASE_PARTITION, p_bytes, timeout=8.0)
        if ok:
            self.log(f"[✓] Partition '{partition_name}' Erased Successfully!", "success")
            return True
        else:
            # Fallback with ASCII encoding
            p_ascii = partition_name.encode("ascii") + b'\x00'
            ok2, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_ERASE_PARTITION, p_ascii, timeout=8.0)
            if ok2:
                self.log(f"[✓] Partition '{partition_name}' Erased Successfully!", "success")
                return True
            self.log(f"Failed to erase partition '{partition_name}'.", "error")
            return False

    def write_partition(self, partition_name: str, image_bytes: bytes, progress_cb=None) -> bool:
        """Flashes a partition image to target storage."""
        data_len = len(image_bytes)
        self.log(f"Flashing partition '{partition_name}' ({format_bytes(data_len)})...")

        # 1. START DATA with partition name and size
        p_name_bytes = partition_name.encode("utf-16le") + b'\x00\x00'
        start_payload = p_name_bytes + struct.pack(">I", data_len)
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_WRITE_PARTITION, start_payload, timeout=6.0)
        if not ok:
            self.log(f"Target rejected write initialization for '{partition_name}'.", "error")
            return False

        # 2. MID DATA stream
        offset = 0
        chunk_sz = 4096  # 4KB chunk size
        while offset < data_len and not self.aborted:
            chunk = image_bytes[offset : offset + chunk_sz]
            ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_MID_DATA, chunk, timeout=5.0)
            if not ok:
                self.log(f"Write error on '{partition_name}' at offset 0x{offset:X}", "error")
                return False

            offset += len(chunk)
            if progress_cb:
                pct = min(1.0, offset / data_len)
                progress_cb(pct, f"Writing {partition_name}: {int(pct * 100)}%")

        # 3. END DATA
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_END_DATA, b'', timeout=5.0)
        if ok:
            self.log(f"[✓] Flashed '{partition_name}' ({format_bytes(data_len)}) Successfully!", "success")
            return True
        return False

    def reboot(self) -> bool:
        """Sends Normal Reset command to boot device into Android."""
        self.log("Sending Normal Reset command (BSL_CMD_NORMAL_RESET)...")
        ok, _, _ = BSLProtocol.send_cmd(self.ser, BSLProtocol.CMD_NORMAL_RESET, b'', timeout=3.0)
        self.log("Unisoc Device Reboot Command Dispatched!", "success")
        return True
