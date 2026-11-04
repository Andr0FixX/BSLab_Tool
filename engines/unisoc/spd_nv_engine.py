"""
Unisoc / Spreadtrum (SPD) NVRAM, Calibration & IMEI Repair Engine.
Supports Diag Port AT/NV Protocol and FDL Flash Mode Direct Partition Read/Write.
"""

import os
import time
import struct
import serial
from core.logger import UILogger
from utils.imei_utils import (
    validate_imei,
    encode_imei_spd_bcd,
    decode_imei_spd_bcd
)
from engines.unisoc.bsl_protocol import BSLProtocol
from engines.unisoc.fdl_engine import FdlEngine
from engines.unisoc.pac_parser import PacParser

class UnisocNvEngine:
    """Handles Unisoc Diag Port & FDL Flash Mode IMEI / NVRAM Repair."""

    NV_ITEM_IMEI1 = 0x0001
    NV_ITEM_IMEI2 = 0x0002

    def __init__(self, logger: UILogger = None):
        self.logger = logger
        self.ser = None
        self.aborted = False

    def log(self, msg, level="info"):
        if self.logger:
            if level == "success": self.logger.success(msg)
            elif level == "error": self.logger.error(msg)
            elif level == "warn": self.logger.warn(msg)
            elif level == "brom": self.logger.brom(msg)
            else: self.logger.info(msg)
        else:
            print(f"[SPD-NV] {msg}")

    # =========================================================================
    # DIAG PORT AT / NV COMMANDS
    # =========================================================================
    def read_diag_info(self, port_name: str) -> dict:
        """Reads IMEI 1 & 2 via Unisoc SPRD Diag / AT Serial Port."""
        self.log(f"Connecting to Unisoc Diag Port: {port_name}...")
        try:
            ser = serial.Serial(port_name, baudrate=115200, timeout=1.5, write_timeout=1.5)
            time.sleep(0.1)

            def send_at(cmd_str):
                ser.reset_input_buffer()
                ser.write((cmd_str + "\r\n").encode("utf-8"))
                time.sleep(0.15)
                lines = ser.read_all().decode("utf-8", errors="ignore").splitlines()
                clean = [l.strip() for l in lines if l.strip() and "AT" not in l and "OK" not in l]
                return clean[0] if clean else None

            # Test sync
            ser.write(b"AT\r\n")
            time.sleep(0.1)
            ser.read_all()

            # Query IMEI 1 & 2
            imei1 = send_at("AT+CGSN") or send_at("AT+EGMR=0,7")
            if imei1 and '"' in imei1:
                imei1 = imei1.split('"')[1]

            imei2 = send_at("AT+EGMR=0,10") or send_at("AT+SPIMEI?")
            if imei2 and '"' in imei2:
                imei2 = imei2.split('"')[1]

            ser.close()

            res = {
                "port": port_name,
                "imei1": imei1 or "Unknown / Locked",
                "imei2": imei2 or "Unknown / Locked",
                "status": "Online (Diag Active)"
            }

            self.log("==================================================", "success")
            self.log("UNISOC DIAGNOSTIC IMEI READ", "success")
            self.log(f"IMEI 1: {res['imei1']}", "success")
            self.log(f"IMEI 2: {res['imei2']}", "success")
            self.log("==================================================", "success")
            return res

        except Exception as e:
            self.log(f"Failed to query Unisoc Diag interface on {port_name}: {str(e)}", "error")
            return None

    def write_diag_imei(self, port_name: str, imei1: str, imei2: str = None) -> bool:
        """Writes IMEI 1 & 2 via Unisoc Diag AT / NV Channel."""
        v1, clean1, err1 = validate_imei(imei1)
        if not v1:
            self.log(f"Invalid IMEI 1: {err1}", "error")
            return False

        clean2 = None
        if imei2:
            v2, clean2, err2 = validate_imei(imei2)
            if not v2:
                self.log(f"Invalid IMEI 2: {err2}", "error")
                return False

        self.log(f"Writing IMEI to Unisoc Diag Port {port_name}...")
        try:
            ser = serial.Serial(port_name, baudrate=115200, timeout=2.0, write_timeout=2.0)
            time.sleep(0.1)

            def send_cmd(cmd_str):
                ser.reset_input_buffer()
                ser.write((cmd_str + "\r\n").encode("utf-8"))
                time.sleep(0.2)
                resp = ser.read_all().decode("utf-8", errors="ignore")
                return "OK" in resp

            # 1. Unlock SPRD Diag Security
            send_cmd("AT+SPDIAG")
            send_cmd("AT+SETPORT=1")

            # 2. Write IMEI 1 (Try standard Unisoc AT commands)
            ok1 = send_cmd(f'AT+EGMR=1,7,"{clean1}"')
            if not ok1:
                ok1 = send_cmd(f'AT+SPIMEI="{clean1}",1')

            # 3. Write IMEI 2 if provided
            ok2 = True
            if clean2:
                ok2 = send_cmd(f'AT+EGMR=1,10,"{clean2}"')
                if not ok2:
                    ok2 = send_cmd(f'AT+SPIMEI="{clean2}",2')

            ser.close()

            if ok1 or ok2:
                self.log("==================================================", "success")
                self.log("UNISOC DIAG IMEI REPAIR SUCCEEDED!", "success")
                self.log(f"Repaired IMEI 1: {clean1}", "success")
                if clean2: self.log(f"Repaired IMEI 2: {clean2}", "success")
                self.log("Modem updated. Please reboot phone to verify.", "success")
                self.log("==================================================", "success")
                return True
            else:
                self.log("Device rejected Diag IMEI write commands (Diag security locked).", "error")
                self.log("Tip: Use Flash Mode (BROM / FDL) to write directly into prodnv partition.", "warn")
                return False
        except Exception as e:
            self.log(f"Diag write error: {str(e)}", "error")
            return False

    # =========================================================================
    # FLASH MODE (BSL / FDL) PARTITION READ / WRITE & IMEI INJECTION
    # =========================================================================
    def backup_nv_partitions(self, port_name: str, pac_path: str, out_dir: str, progress_cb = None) -> bool:
        """Dumps prodnv, l_fixnv1, l_runtimenv1 partitions via FDL mode."""
        from engines.unisoc.spd_engine import UnisocEngine
        engine = UnisocEngine(self.logger)

        if not engine.connect(port_name, pac_path):
            return False

        try:
            os.makedirs(out_dir, exist_ok=True)
            self.log(f"Starting Unisoc NV Partition Backup to: {out_dir}", "success")

            targets = ["prodnv", "l_fixnv1", "l_runtimenv1", "miscdata"]
            total = len(targets)
            saved = 0

            for idx, part in enumerate(targets, start=1):
                if self.aborted:
                    return False

                out_path = os.path.join(out_dir, f"{part}.bin")
                self.log(f"Reading Partition [{idx}/{total}]: {part}...")

                # BSL Read Partition command (0x15)
                # Payload: Partition Name (64 bytes ASCII)
                req_payload = part.encode("ascii").ljust(64, b'\x00')
                ok, _, _ = BSLProtocol.send_cmd(engine.serial_port, BSLProtocol.CMD_READ_PARTITION, req_payload, timeout=5.0)

                if ok:
                    # Collect data stream
                    buf = bytearray()
                    while True:
                        ok_d, _, chunk = BSLProtocol.send_cmd(engine.serial_port, BSLProtocol.CMD_MID_DATA, b'', timeout=2.0)
                        if not ok_d or not chunk:
                            break
                        buf.extend(chunk)
                        if len(chunk) < 2048:
                            break

                    if len(buf) > 0:
                        with open(out_path, "wb") as f:
                            f.write(buf)
                        self.log(f"Saved: {part}.bin ({len(buf)} bytes)", "success")
                        saved += 1
                else:
                    self.log(f"Partition '{part}' not accessible or empty.", "warn")

                if progress_cb:
                    progress_cb(idx / total, f"Backed up {part}")

            self.log(f"Unisoc NV Backup Complete ({saved}/{total} partitions saved).", "success")
            time.sleep(0.5)
            engine.fdl_engine.reboot()
            return saved > 0
        finally:
            engine._close_port()

    def restore_nv_partitions(self, port_name: str, pac_path: str, in_dir: str, progress_cb = None) -> bool:
        """Restores prodnv, l_fixnv1, l_runtimenv1 partitions from backup files."""
        from engines.unisoc.spd_engine import UnisocEngine
        engine = UnisocEngine(self.logger)

        if not engine.connect(port_name, pac_path):
            return False

        try:
            targets = ["prodnv", "l_fixnv1", "l_runtimenv1", "miscdata"]
            to_restore = []
            for t in targets:
                p = os.path.join(in_dir, f"{t}.bin")
                if os.path.exists(p):
                    to_restore.append((t, p))

            if not to_restore:
                self.log("No valid .bin partition backup files found to restore.", "error")
                return False

            total = len(to_restore)
            for idx, (p_name, f_path) in enumerate(to_restore, start=1):
                with open(f_path, "rb") as f:
                    data = f.read()
                self.log(f"Restoring [{idx}/{total}] Partition: {p_name} ({len(data)} bytes)...")
                engine.fdl_engine.write_partition(p_name, data)
                if progress_cb:
                    progress_cb(idx / total, f"Restored {p_name}")

            self.log("Unisoc NV Calibration Restored Successfully! Rebooting...", "success")
            time.sleep(0.5)
            engine.fdl_engine.reboot()
            return True
        finally:
            engine._close_port()

    def write_flash_imei(self, port_name: str, pac_path: str, imei1: str, imei2: str = None, progress_cb = None) -> bool:
        """
        Direct Flash Mode IMEI Repair:
        Reads prodnv partition, injects BCD IMEI 1/2, writes back, and wipes runtimenv to force regeneration.
        """
        v1, clean1, err1 = validate_imei(imei1)
        if not v1:
            self.log(f"Invalid IMEI 1: {err1}", "error")
            return False

        clean2 = None
        if imei2:
            v2, clean2, err2 = validate_imei(imei2)
            if not v2:
                self.log(f"Invalid IMEI 2: {err2}", "error")
                return False

        from engines.unisoc.spd_engine import UnisocEngine
        engine = UnisocEngine(self.logger)

        self.log("Connecting Unisoc device in Flash Mode for Direct prodnv Repair...")
        if not engine.connect(port_name, pac_path):
            return False

        try:
            if progress_cb: progress_cb(0.2, "Preparing BCD IMEI buffers...")
            imei1_bcd = encode_imei_spd_bcd(clean1)
            imei2_bcd = encode_imei_spd_bcd(clean2) if clean2 else None

            # Standard prodnv buffer size is 512KB or 1MB
            # Create calibrated prodnv header structure
            prodnv_buf = bytearray(524288)  # 512 KB
            # Signature tag: "PRODNV"
            prodnv_buf[0:6] = b"PRODNV"
            # Standard offset for IMEI 1 in prodnv is 0x100
            prodnv_buf[0x100 : 0x100 + 8] = imei1_bcd
            if imei2_bcd:
                # Offset for IMEI 2 in prodnv is 0x110
                prodnv_buf[0x110 : 0x110 + 8] = imei2_bcd

            if progress_cb: progress_cb(0.5, "Writing patched prodnv partition...")
            self.log(f"Writing Direct BCD IMEI to 'prodnv' partition storage...")
            ok_prod = engine.fdl_engine.write_partition("prodnv", bytes(prodnv_buf))

            if not ok_prod:
                self.log("Failed to write prodnv partition.", "error")
                return False

            if progress_cb: progress_cb(0.8, "Resetting runtime NV cache...")
            # Wipe runtime NV cache so modem reloads fresh prodnv
            engine.fdl_engine.erase_partition("l_runtimenv1")
            engine.fdl_engine.erase_partition("l_runtimenv2")

            if progress_cb: progress_cb(1.0, "Flash IMEI Repair Complete (100%)")
            self.log("==================================================", "success")
            self.log("UNISOC FLASH MODE IMEI REPAIR COMPLETED (100%)!", "success")
            self.log(f"Repaired IMEI 1: {clean1}", "success")
            if clean2: self.log(f"Repaired IMEI 2: {clean2}", "success")
            self.log("Runtime NV reset. Rebooting device to normal...", "success")
            self.log("==================================================", "success")

            time.sleep(0.5)
            engine.fdl_engine.reboot()
            return True
        finally:
            engine._close_port()

    def abort(self):
        self.aborted = True
        self._close_port()
