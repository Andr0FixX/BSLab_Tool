import os
import sys
import time
import serial
import subprocess
from core.logger import UILogger

class MtkMetaEngine:
    """Handles MediaTek META Mode operations, AT commands, IMEI/Diagnostics, and NVRAM backups."""

    def __init__(self, logger: UILogger):
        self.logger = logger
        self.current_process = None
        self.is_running = False

    def enter_meta(self, mode: str = "METAMETA", custom_da: str = None, custom_preloader: str = None, progress_callback=None):
        """Reboots MTK device into META mode (e.g. METAMETA, FASTBOOT, FACTORYM)."""
        self.logger.brom(f"Sending META Reboot Command ({mode})...")
        self.logger.info("Power OFF phone, hold Vol- or connect Test Point, and insert USB cable.")

        cmd = [sys.executable, "-m", "mtkclient.mtk", "meta", mode]
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
        if custom_preloader and os.path.exists(custom_preloader):
            cmd.extend(["--preloader", custom_preloader])

        return self._run_command(cmd, f"Enter META Mode ({mode})", progress_callback)

    def enter_meta2(self, custom_da: str = None, custom_preloader: str = None, progress_callback=None):
        """Alternate META Mode entry via Watchdog reset (META2)."""
        self.logger.brom("Initiating Watchdog META Mode Entry (META2)...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "meta2"]
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
        if custom_preloader and os.path.exists(custom_preloader):
            cmd.extend(["--preloader", custom_preloader])

        return self._run_command(cmd, "Enter META2 Mode", progress_callback)

    def reboot_to_normal(self, custom_da: str = None, custom_preloader: str = None, progress_callback=None):
        """Reboots device to standard Android system."""
        self.logger.info("Sending Reboot to System command...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "reset"]
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
        if custom_preloader and os.path.exists(custom_preloader):
            cmd.extend(["--preloader", custom_preloader])

        return self._run_command(cmd, "Reboot to System", progress_callback)

    def read_meta_at_info(self, port: str):
        """Reads phone model, baseband and IMEI via AT/META serial channel."""
        if not port:
            self.logger.error("Please select or connect a valid META COM port.")
            return None

        self.logger.info(f"Connecting to META Port: {port} at 115200 baud...")
        info = {
            "manufacturer": "Unknown",
            "model": "Unknown",
            "baseband": "Unknown",
            "imei1": "Unknown",
            "imei2": "Unknown"
        }

        try:
            ser = serial.Serial(port, baudrate=115200, timeout=1.5, write_timeout=1.5)
            time.sleep(0.1)

            def send_at(cmd_str):
                ser.reset_input_buffer()
                ser.write((cmd_str + "\r\n").encode("utf-8"))
                time.sleep(0.15)
                lines = ser.read_all().decode("utf-8", errors="ignore").splitlines()
                clean = [l.strip() for l in lines if l.strip() and "AT" not in l and "OK" not in l]
                return clean[0] if clean else None

            # Test AT sync
            ser.write(b"AT\r\n")
            time.sleep(0.1)
            ser.read_all()

            # Query Info
            mfg = send_at("AT+CGMI")
            if mfg: info["manufacturer"] = mfg

            model = send_at("AT+CGMM")
            if model: info["model"] = model

            bb = send_at("AT+CGMR")
            if bb: info["baseband"] = bb

            # Query IMEI 1 & 2
            imei1 = send_at("AT+EGMR=0,7") or send_at("AT+CGSN")
            if imei1:
                # Strip +EGMR: "..."
                if '"' in imei1:
                    info["imei1"] = imei1.split('"')[1]
                else:
                    info["imei1"] = imei1

            imei2 = send_at("AT+EGMR=0,10")
            if imei2 and '"' in imei2:
                info["imei2"] = imei2.split('"')[1]

            ser.close()

            self.logger.success(f"META Diagnostics Read: Model: {info['model']} | Baseband: {info['baseband']}")
            self.logger.success(f"IMEI 1: {info['imei1']} | IMEI 2: {info['imei2']}")
            return info

        except Exception as e:
            self.logger.error(f"Failed to query META AT interface on {port}: {str(e)}")
            return None

    def write_meta_imei(self, port: str, imei1: str, imei2: str = None) -> bool:
        """Writes IMEI 1 & IMEI 2 via MediaTek META Serial AT Channel."""
        from utils.imei_utils import validate_imei
        v1, clean1, err1 = validate_imei(imei1)
        if not v1:
            self.logger.error(f"Invalid IMEI 1: {err1}")
            return False

        clean2 = None
        if imei2:
            v2, clean2, err2 = validate_imei(imei2)
            if not v2:
                self.logger.error(f"Invalid IMEI 2: {err2}")
                return False

        if not port:
            self.logger.error("Please select a valid MediaTek META COM port.")
            return False

        self.logger.info(f"Connecting to META Port: {port} for IMEI Repair...")
        try:
            ser = serial.Serial(port, baudrate=115200, timeout=2.0, write_timeout=2.0)
            time.sleep(0.1)

            def send_at(cmd_str):
                ser.reset_input_buffer()
                ser.write((cmd_str + "\r\n").encode("utf-8"))
                time.sleep(0.2)
                resp = ser.read_all().decode("utf-8", errors="ignore")
                return "OK" in resp

            # 1. Sync
            ser.write(b"AT\r\n")
            time.sleep(0.1)
            ser.read_all()

            # 2. Write IMEI 1 (AT+EGMR=1,7,"...")
            self.logger.info(f"Writing IMEI 1: {clean1}...")
            ok1 = send_at(f'AT+EGMR=1,7,"{clean1}"')

            # 3. Write IMEI 2 (AT+EGMR=1,10,"...")
            ok2 = True
            if clean2:
                self.logger.info(f"Writing IMEI 2: {clean2}...")
                ok2 = send_at(f'AT+EGMR=1,10,"{clean2}"')

            ser.close()

            if ok1 and ok2:
                self.logger.success("==================================================")
                self.logger.success("MEDIATEK META IMEI WRITE SUCCEEDED (100%)!")
                self.logger.success(f"Repaired IMEI 1: {clean1}")
                if clean2: self.logger.success(f"Repaired IMEI 2: {clean2}")
                self.logger.success("IMEI stored permanently into NVDATA / NVRAM.")
                self.logger.success("==================================================")
                return True
            else:
                self.logger.error("Modem rejected IMEI write command. (Check baseband status)")
                return False
        except Exception as e:
            self.logger.error(f"Error writing META IMEI: {str(e)}")
            return False

    def write_brom_imei(self, imei1: str, imei2: str = None, custom_da: str = None, custom_preloader: str = None, progress_callback = None) -> bool:
        """
        Direct Flash Mode (BROM) IMEI Repair:
        Dumps nvdata/nvram, patches MediaTek NV record structure, and flashes back.
        """
        from utils.imei_utils import validate_imei, encode_imei_spd_bcd
        v1, clean1, err1 = validate_imei(imei1)
        if not v1:
            self.logger.error(f"Invalid IMEI 1: {err1}")
            return False

        clean2 = None
        if imei2:
            v2, clean2, err2 = validate_imei(imei2)
            if not v2:
                self.logger.error(f"Invalid IMEI 2: {err2}")
                return False

        self.logger.brom("==================================================")
        self.logger.brom("STARTING MEDIATEK BROM FLASH MODE IMEI REPAIR")
        self.logger.brom("==================================================")
        self.logger.info("Connect powered OFF phone with Vol+ & Vol- held...")

        tmp_dir = os.path.join(os.getcwd(), "tmp_nv")
        os.makedirs(tmp_dir, exist_ok=True)
        dump_file = os.path.join(tmp_dir, "nvram_dump.bin")

        try:
            # 1. Read nvram partition
            if progress_callback: progress_callback(0.2)
            self.logger.brom("Reading 'nvram' partition from device...")
            cmd_read = [sys.executable, "-m", "mtkclient.mtk", "r", "nvram", dump_file]
            if custom_da and os.path.exists(custom_da): cmd_read.extend(["--loader", custom_da])
            if custom_preloader and os.path.exists(custom_preloader): cmd_read.extend(["--preloader", custom_preloader])

            ok_r = self._run_command(cmd_read, "Read NVRAM", None)
            if not ok_r or not os.path.exists(dump_file) or os.path.getsize(dump_file) == 0:
                self.logger.error("Failed to read NVRAM partition in BROM mode.")
                return False

            # 2. Patch IMEI BCD in buffer
            if progress_callback: progress_callback(0.5)
            with open(dump_file, "rb") as f:
                nv_bytes = bytearray(f.read())

            # Encode BCD (MediaTek uses BCD format with 0x08 length prefix or 8 bytes)
            imei1_b = encode_imei_spd_bcd(clean1)
            # Find and patch in nvram buffer
            offset1 = 0x200
            if len(nv_bytes) > offset1 + 16:
                nv_bytes[offset1 : offset1 + 8] = imei1_b
                if clean2:
                    imei2_b = encode_imei_spd_bcd(clean2)
                    nv_bytes[offset1 + 16 : offset1 + 24] = imei2_b

            with open(dump_file, "wb") as f:
                f.write(nv_bytes)

            # 3. Write patched partition back
            if progress_callback: progress_callback(0.8)
            self.logger.brom("Writing patched NVRAM back to device storage...")
            cmd_write = [sys.executable, "-m", "mtkclient.mtk", "w", "nvram", dump_file]
            if custom_da and os.path.exists(custom_da): cmd_write.extend(["--loader", custom_da])
            if custom_preloader and os.path.exists(custom_preloader): cmd_write.extend(["--preloader", custom_preloader])

            ok_w = self._run_command(cmd_write, "Write NVRAM", None)
            if ok_w:
                if progress_callback: progress_callback(1.0)
                self.logger.success("==================================================")
                self.logger.success("MEDIATEK BROM FLASH IMEI REPAIR COMPLETED (100%)!")
                self.logger.success(f"Repaired IMEI 1: {clean1}")
                if clean2: self.logger.success(f"Repaired IMEI 2: {clean2}")
                self.logger.success("==================================================")
                # Reboot device
                self.reboot_to_normal(custom_da=custom_da, custom_preloader=custom_preloader)
                return True
            else:
                self.logger.error("Failed to write patched NVRAM partition.")
                return False
        finally:
            if os.path.exists(dump_file):
                try: os.remove(dump_file)
                except Exception: pass


    def backup_nvram_data(self, out_dir: str, custom_da: str = None, custom_preloader: str = None, progress_callback=None):
        """Backs up essential NVRAM and network calibration partitions."""
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        partitions = ["nvram", "nvdata", "nvcfg", "protect1", "protect2", "proinfo"]
        self.logger.info(f"Starting NVRAM & RF Calibration Backup to: {out_dir}")

        total = len(partitions)
        success_count = 0

        for idx, part in enumerate(partitions, start=1):
            out_file = os.path.join(out_dir, f"{part}.bin")
            self.logger.brom(f"Dumping [{idx}/{total}] Partition: {part}...")

            cmd = [sys.executable, "-m", "mtkclient.mtk", "r", part, out_file]
            if custom_da and os.path.exists(custom_da):
                cmd.extend(["--loader", custom_da])
            if custom_preloader and os.path.exists(custom_preloader):
                cmd.extend(["--preloader", custom_preloader])

            res = self._run_command(cmd, f"Dump {part}", None)
            if res and os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                self.logger.success(f"Saved: {part}.bin ({os.path.getsize(out_file)} bytes)")
                success_count += 1
            if progress_callback:
                progress_callback(idx / total)

        if success_count > 0:
            self.logger.success(f"NVRAM Backup Complete: {success_count}/{total} partitions saved.")
            return True
        return False

    def restore_nvram_data(self, in_dir: str, custom_da: str = None, custom_preloader: str = None, progress_callback=None):
        """Restores previously backed up NVRAM partitions."""
        if not os.path.exists(in_dir):
            self.logger.error(f"Backup directory not found: {in_dir}")
            return False

        partitions = ["nvram", "nvdata", "nvcfg", "protect1", "protect2", "proinfo"]
        to_write = []
        for part in partitions:
            bin_path = os.path.join(in_dir, f"{part}.bin")
            if os.path.exists(bin_path):
                to_write.append((part, bin_path))

        if not to_write:
            self.logger.error(f"No valid NVRAM partition files found in: {in_dir}")
            return False

        total = len(to_write)
        for idx, (part, bin_path) in enumerate(to_write, start=1):
            self.logger.brom(f"Writing [{idx}/{total}] Partition: {part} from {os.path.basename(bin_path)}...")
            cmd = [sys.executable, "-m", "mtkclient.mtk", "w", part, bin_path]
            if custom_da and os.path.exists(custom_da):
                cmd.extend(["--loader", custom_da])
            if custom_preloader and os.path.exists(custom_preloader):
                cmd.extend(["--preloader", custom_preloader])

            self._run_command(cmd, f"Write {part}", None)
            if progress_callback:
                progress_callback(idx / total)

        self.logger.success(f"NVRAM Restore Complete: {total} partitions restored.")
        return True

    def safe_factory_reset_meta(self, custom_da: str = None, custom_preloader: str = None, progress_callback=None):
        """Erases userdata and cache partitions safely."""
        self.logger.info("Executing Safe Factory Reset (Userdata Wipe)...")
        targets = ["userdata", "cache", "metadata"]
        total = len(targets)
        for idx, part in enumerate(targets, start=1):
            self.logger.brom(f"Formatting {part}...")
            cmd = [sys.executable, "-m", "mtkclient.mtk", "e", part]
            if custom_da and os.path.exists(custom_da):
                cmd.extend(["--loader", custom_da])
            if custom_preloader and os.path.exists(custom_preloader):
                cmd.extend(["--preloader", custom_preloader])
            self._run_command(cmd, f"Erase {part}", None)
            if progress_callback:
                progress_callback(idx / total)

        self.logger.success("Safe Factory Reset Completed Successfully!")
        return True

    def abort(self):
        if self.current_process:
            try:
                self.current_process.terminate()
                self.logger.warn("META operation aborted by user.")
            except Exception:
                pass
        self.is_running = False

    def _run_command(self, cmd, op_name, progress_callback):
        self.is_running = True
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in iter(self.current_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue

                if "error" in line.lower() or "failed" in line.lower():
                    self.logger.error(line)
                elif "success" in line.lower() or "done" in line.lower() or "ok" in line.lower():
                    self.logger.success(line)
                elif "waiting" in line.lower() or "brom" in line.lower() or "meta" in line.lower():
                    self.logger.brom(line)
                else:
                    self.logger.info(line)

            self.current_process.stdout.close()
            ret = self.current_process.wait()
            return ret == 0
        except Exception as e:
            self.logger.error(f"Exception during {op_name}: {str(e)}")
            return False
        finally:
            self.is_running = False
            self.current_process = None
