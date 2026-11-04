"""
Qualcomm QCN (Qualcomm Calibration Network) Parser, Diag Protocol & IMEI Repair Engine.
Supports NV Item 550 (NV_UE_IMEI_I), CRC16-CCITT HDLC Framing, and On-the-Fly QCN Patching.
"""

import os
import time
import struct
import serial
from core.logger import UILogger
from utils.imei_utils import (
    validate_imei,
    encode_imei_qc_bcd,
    decode_imei_qc_bcd
)

class QualcommQcnEngine:
    """Qualcomm Diagnostic Port Protocol & QCN NV Flasher."""

    # Qualcomm Diag Commands
    CMD_DIAG_VERNO = 0x00
    CMD_DIAG_ESN = 0x01
    CMD_DIAG_NV_READ = 0x26
    CMD_DIAG_NV_WRITE = 0x27
    CMD_DIAG_PHONE_MODE = 0x29

    # Common Qualcomm NV Item IDs
    NV_UE_IMEI_I = 550          # Primary IMEI (NV Item 550)
    NV_UE_IMEI2_I = 650         # Secondary IMEI (or dual SIM item)
    NV_FACTORY_DATA_1 = 2497    # Calibration data
    NV_FACTORY_DATA_2 = 2498

    # HDLC Framing constants
    FRAME_DELIMITER = 0x7E
    ESCAPE_BYTE = 0x7D

    def __init__(self, logger: UILogger = None):
        self.logger = logger
        self.ser = None
        self.aborted = False

    def log(self, msg, level="info"):
        if self.logger:
            if level == "success": self.logger.success(msg)
            elif level == "error": self.logger.error(msg)
            elif level == "warn": self.logger.warn(msg)
            else: self.logger.info(msg)
        else:
            print(f"[QC-QCN] {msg}")

    # =========================================================================
    # CRC16-CCITT & HDLC PACKET ENGINE
    # =========================================================================
    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """Calculates 16-bit CRC for Qualcomm Diag frames (Polynomial 0x8408)."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return crc ^ 0xFFFF

    @staticmethod
    def escape_diag_data(data: bytes) -> bytes:
        """Applies HDLC byte stuffing (0x7E -> 0x7D 0x5E, 0x7D -> 0x7D 0x5D)."""
        out = bytearray()
        for b in data:
            if b == QualcommQcnEngine.FRAME_DELIMITER:
                out.append(QualcommQcnEngine.ESCAPE_BYTE)
                out.append(0x5E)
            elif b == QualcommQcnEngine.ESCAPE_BYTE:
                out.append(QualcommQcnEngine.ESCAPE_BYTE)
                out.append(0x5D)
            else:
                out.append(b)
        return bytes(out)

    @staticmethod
    def unescape_diag_data(data: bytes) -> bytes:
        """Reverses HDLC byte stuffing."""
        out = bytearray()
        escaped = False
        for b in data:
            if escaped:
                if b == 0x5E:
                    out.append(QualcommQcnEngine.FRAME_DELIMITER)
                elif b == 0x5D:
                    out.append(QualcommQcnEngine.ESCAPE_BYTE)
                else:
                    out.append(b)
                escaped = False
            elif b == QualcommQcnEngine.ESCAPE_BYTE:
                escaped = True
            else:
                out.append(b)
        return bytes(out)

    @classmethod
    def build_frame(cls, payload: bytes) -> bytes:
        """Calculates CRC-16, appends it, escapes data, and adds 0x7E delimiters."""
        crc = cls.calculate_crc16(payload)
        crc_bytes = struct.pack("<H", crc)
        raw = payload + crc_bytes
        escaped = cls.escape_diag_data(raw)
        return bytes([cls.FRAME_DELIMITER]) + escaped + bytes([cls.FRAME_DELIMITER])

    # =========================================================================
    # DIAG SERIAL COMMUNICATION
    # =========================================================================
    def open_port(self, port_name: str, baud: int = 115200) -> bool:
        """Opens Qualcomm Diagnostic COM Port."""
        try:
            self._close_port()
            self.ser = serial.Serial(
                port=port_name,
                baudrate=baud,
                timeout=1.5,
                write_timeout=1.5
            )
            time.sleep(0.1)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            return True
        except Exception as e:
            self.log(f"Cannot open Diag Port {port_name}: {str(e)}", "error")
            return False

    def _close_port(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def send_diag_cmd(self, payload: bytes, timeout: float = 2.0) -> bytes:
        """Sends frame and reads unescaped response from phone."""
        if not self.ser or not self.ser.is_open:
            return b''

        frame = self.build_frame(payload)
        self.ser.write(frame)
        self.ser.flush()

        start = time.time()
        buf = bytearray()
        while time.time() - start < timeout:
            ch = self.ser.read(1)
            if not ch:
                continue
            if ch[0] == self.FRAME_DELIMITER:
                if len(buf) > 0:
                    # Delimiter reached end of frame
                    break
            else:
                buf.append(ch[0])

        if not buf:
            return b''

        unescaped = self.unescape_diag_data(bytes(buf))
        if len(unescaped) < 3:
            return b''

        # Verify CRC
        body = unescaped[:-2]
        recv_crc = struct.unpack("<H", unescaped[-2:])[0]
        calc_crc = self.calculate_crc16(body)
        if recv_crc != calc_crc:
            self.log("CRC Mismatch in Diag response.", "warn")

        return body

    # =========================================================================
    # QCN FILE PARSING & IMEI INJECTION
    # =========================================================================
    @staticmethod
    def parse_qcn(qcn_path: str) -> list:
        """
        Parses QCN file into a list of NV items:
        [{"item_id": int, "data": bytes}, ...]
        Supports standard 128-byte NV records and tagged QCN headers.
        """
        if not os.path.exists(qcn_path):
            raise FileNotFoundError(f"QCN file not found: {qcn_path}")

        items = []
        with open(qcn_path, "rb") as f:
            data = f.read()

        file_len = len(data)
        idx = 0

        # Check for signature header
        if data.startswith(b"QCN_FILE") or data.startswith(b"QCN\x00"):
            idx = 32

        # Standard QCN records: [item_id: uint16, length: uint16 (or static 128), payload: N bytes]
        while idx + 4 < file_len:
            item_id = struct.unpack("<H", data[idx:idx+2])[0]
            # Check length field
            item_len = struct.unpack("<H", data[idx+2:idx+4])[0]
            if 0 < item_len <= 512 and (idx + 4 + item_len <= file_len):
                payload = data[idx+4 : idx+4+item_len]
                items.append({"item_id": item_id, "data": payload})
                idx += 4 + item_len
            elif idx + 130 <= file_len:
                # 128-byte legacy record format
                payload = data[idx+2 : idx+130]
                items.append({"item_id": item_id, "data": payload})
                idx += 130
            else:
                break

        return items

    @classmethod
    def patch_qcn_file(cls, in_qcn: str, out_qcn: str, imei1: str, imei2: str = None) -> (bool, str):
        """
        Creates a copy of QCN with NV Item 550 (IMEI 1) and NV Item 650/dual-SIM (IMEI 2) replaced.
        """
        if not os.path.exists(in_qcn):
            return False, "Input QCN file not found."

        v1, clean_imei1, err1 = validate_imei(imei1)
        if not v1:
            return False, f"IMEI 1 validation failed: {err1}"

        imei1_bcd = encode_imei_qc_bcd(clean_imei1)
        imei2_bcd = encode_imei_qc_bcd(imei2) if imei2 else None

        items = cls.parse_qcn(in_qcn)
        if not items:
            return False, "No NV items parsed from QCN file."

        patched_count = 0
        with open(out_qcn, "wb") as f_out:
            for item in items:
                i_id = item["item_id"]
                p_data = bytearray(item["data"])

                if i_id == cls.NV_UE_IMEI_I:
                    # Patch first 9 bytes of 128-byte payload
                    p_data[0:9] = imei1_bcd
                    patched_count += 1
                elif i_id == cls.NV_UE_IMEI2_I and imei2_bcd:
                    p_data[0:9] = imei2_bcd
                    patched_count += 1

                # Write item: [item_id: uint16, length: uint16, data]
                f_out.write(struct.pack("<HH", i_id, len(p_data)))
                f_out.write(p_data)

        return True, f"Patched {patched_count} IMEI NV record(s) into {os.path.basename(out_qcn)}"

    # =========================================================================
    # HIGH-LEVEL IMEI / QCN SERVICING OPERATIONS
    # =========================================================================
    def read_imei_from_diag(self, port_name: str) -> dict:
        """Reads IMEI 1 & Phone Info from Qualcomm Diag Port."""
        if not self.open_port(port_name):
            return None

        self.log(f"Reading Qualcomm NV Item 550 from {port_name}...")
        try:
            # NV Read Command: 0x26 + item_id (550) + 128 dummy bytes
            req = struct.pack("<BH", self.CMD_DIAG_NV_READ, self.NV_UE_IMEI_I) + (b'\x00' * 128)
            resp = self.send_diag_cmd(req)

            if not resp or resp[0] != self.CMD_DIAG_NV_READ:
                self.log("Device rejected NV Read command or Diag port locked.", "error")
                return None

            # Skip cmd (1 byte) and item_id (2 bytes)
            nv_data = resp[3:]
            imei1_str = decode_imei_qc_bcd(nv_data[:9])

            self.log("==================================================", "success")
            self.log(f"QUALCOMM IMEI READ: {imei1_str}", "success")
            self.log("==================================================", "success")

            return {
                "port": port_name,
                "imei1": imei1_str,
                "status": "Online (Diag Active)"
            }
        except Exception as e:
            self.log(f"Error reading Diag IMEI: {str(e)}", "error")
            return None
        finally:
            self._close_port()

    def write_qcn_with_imei(self, port_name: str, qcn_path: str, imei1: str = None, imei2: str = None, progress_cb = None) -> bool:
        """
        Writes complete QCN calibration file to Qualcomm phone via Diag port.
        If imei1 / imei2 are supplied, patches them dynamically into the NV stream.
        """
        self.aborted = False
        if not os.path.exists(qcn_path):
            self.log(f"QCN file not found: {qcn_path}", "error")
            return False

        if not self.open_port(port_name):
            return False

        try:
            self.log("==================================================", "success")
            self.log(f"STARTING QUALCOMM QCN RESTORATION / IMEI REPAIR", "success")
            self.log(f"File: {os.path.basename(qcn_path)} | Port: {port_name}", "success")
            if imei1: self.log(f"Custom IMEI 1: {imei1}")
            if imei2: self.log(f"Custom IMEI 2: {imei2}")
            self.log("==================================================", "success")

            # Parse items
            items = self.parse_qcn(qcn_path)
            total = len(items)
            self.log(f"Loaded {total} RF/NV calibration records from QCN archive.")

            imei1_bcd = encode_imei_qc_bcd(imei1) if imei1 else None
            imei2_bcd = encode_imei_qc_bcd(imei2) if imei2 else None

            success_items = 0
            for idx, item in enumerate(items, start=1):
                if self.aborted:
                    self.log("QCN write aborted by user.", "warn")
                    return False

                item_id = item["item_id"]
                data = bytearray(item["data"])

                # Pad or truncate to 128 bytes (standard QC NV payload size)
                if len(data) < 128:
                    data = data + (b'\x00' * (128 - len(data)))
                elif len(data) > 128:
                    data = data[:128]

                # Inject custom IMEI
                if item_id == self.NV_UE_IMEI_I and imei1_bcd:
                    data[0:9] = imei1_bcd
                    self.log(f"[NV 550] Injected Custom IMEI 1: {imei1}", "success")
                elif item_id == self.NV_UE_IMEI2_I and imei2_bcd:
                    data[0:9] = imei2_bcd
                    self.log(f"[NV 650] Injected Custom IMEI 2: {imei2}", "success")

                # Build NV Write packet: 0x27 + item_id (uint16) + 128 bytes payload
                req = struct.pack("<BH", self.CMD_DIAG_NV_WRITE, item_id) + bytes(data)
                resp = self.send_diag_cmd(req, timeout=1.5)

                if resp and resp[0] == self.CMD_DIAG_NV_WRITE:
                    success_items += 1

                if progress_cb and idx % 5 == 0:
                    pct = idx / total
                    progress_cb(pct, f"Writing NV {item_id} ({idx}/{total})")

            # Final Progress
            if progress_cb:
                progress_cb(1.0, "QCN Flashing Complete (100%)")

            self.log(f"QCN Write Finished: {success_items}/{total} NV items written successfully.", "success")

            # Send Phone Reset Command to activate new NV
            self.log("Sending Phone Mode Reset to restart modem calibration...")
            # 0x29 + mode (1=Reset)
            reset_req = struct.pack("<BB", self.CMD_DIAG_PHONE_MODE, 0x01)
            self.send_diag_cmd(reset_req, timeout=1.0)
            self.log("Modem reset command sent. Phone is rebooting...", "success")

            return success_items > 0
        finally:
            self._close_port()

    def abort(self):
        self.aborted = True
        self._close_port()
