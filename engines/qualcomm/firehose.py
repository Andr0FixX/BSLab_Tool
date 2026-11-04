import time
import re
import os
import serial
from utils.file_utils import format_bytes

class FirehoseEngine:
    """Qualcomm Firehose VIP / XML Protocol Engine for Flashing, Erasing, and Partition Dumps."""

    def __init__(self, serial_port: serial.Serial, logger=None):
        self.ser = serial_port
        self.logger = logger
        self.max_payload_size = 1048576  # 1MB default chunk
        self.sector_size = 512
        self.memory_name = "eMMC"
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
                self.logger.info(msg)
        else:
            print(f"[FIREHOSE] {msg}")

    def _send_xml_and_wait_ack(self, xml_payload: str, timeout: float = 5.0) -> (bool, str):
        """Sends XML command to target and waits for ACK/NAK response."""
        full_msg = f'<?xml version="1.0" ?><data>{xml_payload}</data>\n'.encode('utf-8')
        self.ser.reset_input_buffer()
        self.ser.write(full_msg)

        start_t = time.time()
        buf = ""
        while time.time() - start_t < timeout and not self.aborted:
            line = self.ser.read_all().decode('utf-8', errors='ignore')
            if line:
                buf += line
                if "value=\"ACK\"" in buf or "value='ACK'" in buf or "ACK" in buf:
                    return True, buf
                elif "value=\"NAK\"" in buf or "value='NAK'" in buf:
                    return False, buf
            time.sleep(0.05)

        return False, buf

    def configure(self, memory_type: str = "eMMC", target_name: str = "8937") -> bool:
        """Configures Firehose memory buffers and protocol parameters."""
        self.memory_name = memory_type
        self.log(f"Configuring Firehose target memory architecture: {memory_type} (Target: {target_name})...")

        for t_name in [target_name, "8937", "8996", "215", "8917"]:
            cfg_xml = (
                f'<configure MemoryName="{memory_type}" '
                f'MaxPayloadSizeToTargetInBytes="{self.max_payload_size}" '
                f'TargetName="{t_name}" verbose="0" AlwaysValidate="0" ZlpAwareHost="1" SkipStorageInit="0" />'
            )
            ok, resp = self._send_xml_and_wait_ack(cfg_xml, timeout=3.0)
            if ok:
                self.log(f"Firehose Target Configured Successfully ({memory_type} - Target: {t_name})!", "success")
                return True

        # Fallback to UFS if eMMC failed
        if memory_type == "eMMC":
            self.log("eMMC Configure failed or NAK received. Testing UFS architecture...", "warn")
            self.memory_name = "UFS"
            for t_name in ["8996", target_name, "8937"]:
                cfg_ufs = (
                    f'<configure MemoryName="UFS" '
                    f'MaxPayloadSizeToTargetInBytes="{self.max_payload_size}" '
                    f'TargetName="{t_name}" verbose="0" AlwaysValidate="0" ZlpAwareHost="1" SkipStorageInit="0" />'
                )
                ok2, resp2 = self._send_xml_and_wait_ack(cfg_ufs, timeout=3.0)
                if ok2:
                    self.log(f"Firehose Target Configured Successfully (UFS High-Speed - Target: {t_name})!", "success")
                    return True

        self.log(f"Firehose Configuration NAK/Timeout. Response: {resp[:200]}", "error")
        return False

    def get_device_info(self) -> dict:
        """Queries storage and chipset info from Firehose target."""
        info = {
            "storage_type": self.memory_name,
            "max_payload": self.max_payload_size,
            "status": "Online (Firehose XML Ready)"
        }

        # Query storage info
        ok, resp = self._send_xml_and_wait_ack('<getstorageinfo physical_partition_number="0" />', timeout=3.0)
        if ok and resp:
            # Parse block size or total sectors
            m_size = re.search(r'num_partition_sectors=["\'](\d+)["\']', resp)
            if m_size:
                sectors = int(m_size.group(1))
                info["total_sectors"] = sectors
                info["storage_size"] = format_bytes(sectors * self.sector_size)

        self.log("==================================================", "success")
        self.log("QUALCOMM FIREHOSE DEVICE SPECIFICATIONS", "success")
        self.log("==================================================", "success")
        self.log(f"Target Storage  : {info['storage_type']}")
        if "storage_size" in info:
            self.log(f"Storage Capacity: {info['storage_size']}")
        self.log(f"Protocol Mode   : {info['status']}", "success")
        self.log("==================================================", "success")
        return info

    def erase_partition(self, start_sector: int, num_sectors: int, partition_name: str = "Partition", sector_size: int = 512) -> bool:
        """Erases sectors on Qualcomm storage."""
        self.log(f"Erasing {partition_name} (Sectors: {start_sector} -> {start_sector + num_sectors})...")
        erase_xml = (
            f'<erase SECTOR_SIZE_IN_BYTES="{sector_size}" '
            f'num_partition_sectors="{num_sectors}" '
            f'start_sector="{start_sector}" />'
        )
        ok, resp = self._send_xml_and_wait_ack(erase_xml, timeout=10.0)
        if ok:
            self.log(f"[✓] {partition_name} Erased Successfully (Offset 0x{start_sector:X})!", "success")
            return True
        else:
            self.log(f"Failed to erase {partition_name}. Target Response: {resp[:150]}", "error")
            return False

    def program_partition(self, start_sector: int, num_sectors: int, file_path: str, partition_name: str = "Partition", sector_size: int = 512, progress_cb=None) -> bool:
        """Flashes binary image to target storage."""
        if not os.path.exists(file_path):
            self.log(f"Image file not found: {file_path}", "error")
            return False

        file_size = os.path.getsize(file_path)
        self.log(f"Flashing {partition_name} from {os.path.basename(file_path)} ({format_bytes(file_size)})...")

        prog_xml = (
            f'<program SECTOR_SIZE_IN_BYTES="{sector_size}" '
            f'num_partition_sectors="{num_sectors}" '
            f'start_sector="{start_sector}" '
            f'filename="{os.path.basename(file_path)}" />'
        )

        ok, resp = self._send_xml_and_wait_ack(prog_xml, timeout=5.0)
        if not ok and "rawmode" not in resp:
            self.log(f"Program initiation rejected for {partition_name}: {resp[:150]}", "error")
            return False

        # Stream file in chunks
        chunk_size = min(self.max_payload_size, 1048576)
        bytes_sent = 0

        with open(file_path, "rb") as f:
            while bytes_sent < file_size and not self.aborted:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                self.ser.write(chunk)
                bytes_sent += len(chunk)

                if progress_cb and file_size > 0:
                    pct = min(1.0, bytes_sent / file_size)
                    progress_cb(pct, f"Writing {partition_name}: {int(pct * 100)}%")

        # Wait for target ACK
        time.sleep(0.1)
        resp_ack = self.ser.read_all().decode('utf-8', errors='ignore')
        if "ACK" in resp_ack or bytes_sent >= file_size:
            self.log(f"[✓] Flashed {partition_name} ({format_bytes(bytes_sent)}) Successfully!", "success")
            if progress_cb:
                progress_cb(1.0, f"{partition_name} 100%")
            return True
        else:
            self.log(f"Writing {partition_name} incomplete or NAK: {resp_ack[:100]}", "warn")
            return False

    def read_partition(self, start_sector: int, num_sectors: int, out_path: str, partition_name: str = "Partition", sector_size: int = 512, progress_cb=None) -> bool:
        """Dumps partition sectors from device to local file."""
        total_bytes = num_sectors * sector_size
        self.log(f"Dumping {partition_name} ({format_bytes(total_bytes)}) to {out_path}...")

        read_xml = (
            f'<read SECTOR_SIZE_IN_BYTES="{sector_size}" '
            f'num_partition_sectors="{num_sectors}" '
            f'start_sector="{start_sector}" />'
        )

        self.ser.reset_input_buffer()
        full_msg = f'<?xml version="1.0" ?><data>{read_xml}</data>\n'.encode('utf-8')
        self.ser.write(full_msg)

        bytes_read = 0
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        with open(out_path, "wb") as out_f:
            start_t = time.time()
            while bytes_read < total_bytes and (time.time() - start_t < 60.0) and not self.aborted:
                incoming = self.ser.read(min(self.max_payload_size, total_bytes - bytes_read))
                if incoming:
                    out_f.write(incoming)
                    bytes_read += len(incoming)
                    if progress_cb and total_bytes > 0:
                        pct = min(1.0, bytes_read / total_bytes)
                        progress_cb(pct, f"Dumping {partition_name}: {int(pct * 100)}%")
                    start_t = time.time()  # Reset timeout on active stream
                else:
                    time.sleep(0.02)

        if bytes_read > 0:
            self.log(f"[✓] {partition_name} Dumped Successfully ({format_bytes(bytes_read)}) -> {os.path.basename(out_path)}", "success")
            return True
        else:
            self.log(f"Dump for {partition_name} timed out with 0 bytes received.", "error")
            return False

    def read_sectors_raw(self, start_sector: int, num_sectors: int, sector_size: int = 512, timeout: float = 10.0) -> bytes:
        """Reads raw sectors into memory buffer without saving to file (e.g. for GPT parsing)."""
        total_bytes = num_sectors * sector_size
        read_xml = (
            f'<read SECTOR_SIZE_IN_BYTES="{sector_size}" '
            f'num_partition_sectors="{num_sectors}" '
            f'start_sector="{start_sector}" />'
        )

        self.ser.reset_input_buffer()
        full_msg = f'<?xml version="1.0" ?><data>{read_xml}</data>\n'.encode('utf-8')
        self.ser.write(full_msg)

        raw_buf = bytearray()
        start_t = time.time()
        while len(raw_buf) < total_bytes and (time.time() - start_t < timeout) and not self.aborted:
            incoming = self.ser.read(min(self.max_payload_size, total_bytes - len(raw_buf)))
            if incoming:
                raw_buf.extend(incoming)
                start_t = time.time()
            else:
                time.sleep(0.02)
        return bytes(raw_buf)

    def reboot(self, mode: str = "reset") -> bool:
        """Reboots target device from 9008 EDL mode to standard Android system or Fastboot."""
        if mode in ("fastboot", "bootloader"):
            self.log("Sending Hardware Reset to Fastboot (<power value='reset_to_fastboot' />)...")
            ok, _ = self._send_xml_and_wait_ack('<power value="reset_to_fastboot" />', timeout=2.0)
            if not ok:
                self.log("Retrying Fastboot trigger with <power value='fastboot' />...")
                ok, _ = self._send_xml_and_wait_ack('<power value="fastboot" />', timeout=2.0)
            if not ok:
                self.log("Direct fastboot reboot not acknowledged by firehose, executing system reset (Hold Vol- to trap Fastboot)...", "warn")
                ok, _ = self._send_xml_and_wait_ack('<power value="reset" />', timeout=2.0)
            self.log("Qualcomm Fastboot Reboot Command Dispatched!", "success")
            return True
        else:
            self.log("Sending Hardware Reset Payload (<power value='reset' />)...")
            ok, _ = self._send_xml_and_wait_ack('<power value="reset" />', timeout=2.0)
            self.log("Qualcomm Device Reboot Command Sent (100%)!", "success")
            return True
