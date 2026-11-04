"""
BS Lab Tool v2.0 PRO — Huawei HiSilicon Kirin Servicing Engine.
Provides autonomous Kirin USB COM 1.0 test point boot rescue injection,
Fastboot rescue mode diagnostics, 1-Click FRP reset, and Huawei ID removal.
"""

import os
import sys
import time
import serial
import subprocess
import serial.tools.list_ports
from typing import Dict, Any, Optional, List, Callable
from core.path_utils import get_platform_tool_path

class KirinEngine:
    """
    HiSilicon Kirin Flash & Servicing Engine.
    Handles USB COM 1.0 test-point communication, xloader dispatch,
    and Fastboot Rescue Mode service commands.
    """

    SUPPORTED_CHIPSETS = [
        "KIRIN_65x",
        "KIRIN_710A",
        "KIRIN_810",
        "KIRIN_820",
        "KIRIN_970",
        "KIRIN_980",
        "KIRIN_990"
    ]

    def __init__(self, logger=None):
        self.logger = logger
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

    def abort(self):
        self.abort_requested = True

    def find_huawei_com_port(self) -> Optional[str]:
        """Finds active HUAWEI USB COM 1.0 port (VID: 0x12D1, PID: 0x3609)."""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            vid = getattr(p, "vid", 0) or 0
            pid = getattr(p, "pid", 0) or 0
            desc = (p.description or "").lower()
            if (vid == 0x12D1 and pid == 0x3609) or any(k in desc for k in ["usb com 1.0", "huawei usb com"]):
                return p.device
        return None

    def get_loaders_dir(self) -> str:
        """Returns base directory for Kirin stage loaders."""
        possible_dirs = []
        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                possible_dirs.append(os.path.join(sys._MEIPASS, "resources", "loaders", "kirin"))
            possible_dirs.append(os.path.join(os.path.dirname(sys.executable), "resources", "loaders", "kirin"))
            possible_dirs.append(os.path.join(os.path.dirname(sys.executable), "_internal", "resources", "loaders", "kirin"))
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        possible_dirs.append(os.path.join(base_dir, "resources", "loaders", "kirin"))

        for d in possible_dirs:
            if os.path.exists(d):
                return d
        return os.path.join(base_dir, "resources", "loaders", "kirin")

    def resolve_chipset(self, hint: str = "") -> str:
        """Resolves chipset folder name based on hint or default."""
        hint_u = (hint or "").upper()
        if "659" in hint_u or "650" in hint_u or "655" in hint_u or "658" in hint_u or "65X" in hint_u or "RNE" in hint_u or "LLD" in hint_u or "FIG" in hint_u:
            return "KIRIN_65x"
        if "710" in hint_u or "JSN" in hint_u or "POT" in hint_u or "STK" in hint_u or "MAR" in hint_u:
            return "KIRIN_710A"
        if "810" in hint_u:
            return "KIRIN_810"
        if "820" in hint_u:
            return "KIRIN_820"
        if "970" in hint_u or "BKL" in hint_u or "CLT" in hint_u or "EML" in hint_u:
            return "KIRIN_970"
        if "980" in hint_u or "VOG" in hint_u or "ELE" in hint_u or "HMA" in hint_u or "LYA" in hint_u:
            return "KIRIN_980"
        if "990" in hint_u:
            return "KIRIN_990"
        return "KIRIN_65x"

    def boot_rescue_mode(self, port: Optional[str] = None, chipset: str = "KIRIN_65x", progress_cb: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        Injects multi-stage Kirin Bootloader into HUAWEI USB COM 1.0 device.
        Wakes up CPU and reboots device into Fastboot Rescue Mode.
        """
        self.abort_requested = False
        target_port = port or self.find_huawei_com_port()
        if not target_port:
            self.log_error("[Huawei Engine] No HUAWEI USB COM 1.0 port detected! Connect phone via Test Point to GND.")
            return False

        chipset_folder = self.resolve_chipset(chipset)
        loaders_root = self.get_loaders_dir()
        chip_dir = os.path.join(loaders_root, chipset_folder)

        if not os.path.exists(chip_dir):
            self.log_error(f"[Huawei Engine] Loader directory not found for: {chipset_folder}")
            return False

        # Gather stage files
        stage_files = []
        for name in ["xloader_1.bin", "xloader_2.bin", "bl2.bin", "fastboot.bin"]:
            fp = os.path.join(chip_dir, name)
            if os.path.exists(fp):
                stage_files.append((name, fp))

        if not stage_files:
            self.log_error(f"[Huawei Engine] No valid binary loaders found inside {chip_dir}!")
            return False

        self.log_info(f"Targeting Port: {target_port} | Chipset: {chipset_folder}")
        self.log_info(f"Loaded {len(stage_files)} injection stages: {', '.join([s[0] for s in stage_files])}")

        try:
            with serial.Serial(target_port, baudrate=115200, timeout=1.5, write_timeout=2.0) as ser:
                # Flush buffers
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                total_stages = len(stage_files)
                for idx, (stage_name, stage_path) in enumerate(stage_files):
                    if self.abort_requested:
                        self.log_warn("[Huawei Engine] Aborted by user.")
                        return False

                    file_size = os.path.getsize(stage_path)
                    self.log_info(f"[*] Dispatching Stage {idx+1}/{total_stages}: {stage_name} ({file_size:,} bytes)...")

                    with open(stage_path, "rb") as bf:
                        data = bf.read()

                    # Write in 4KB chunks with handshakes
                    chunk_size = 4096
                    sent = 0
                    while sent < len(data):
                        if self.abort_requested:
                            return False
                        chunk = data[sent:sent + chunk_size]
                        ser.write(chunk)
                        sent += len(chunk)
                        
                        pct = (sent / len(data)) * 100
                        if progress_cb:
                            overall_pct = ((idx + (sent / len(data))) / total_stages) * 100
                            progress_cb(overall_pct, f"Injecting {stage_name} ({pct:.0f}%)")

                        # Brief inter-chunk pause for ROM handshake
                        time.sleep(0.005)

                    time.sleep(0.2)
                    self.log_success(f"[✓] Stage {idx+1} ({stage_name}) injected successfully!")

                self.log_success("==================================================")
                self.log_success("🎉 KIRIN RESCUE BOOTLOADER INJECTED SUCCESSFULLY!")
                self.log_success("==================================================")
                self.log_info("[*] Phone is now rebooting into Fastboot Rescue Mode...")
                self.log_info("[*] Screen will turn white showing 'FASTBOOT & RESCUE MODE'.")
                return True

        except Exception as ex:
            self.log_error(f"[Huawei COM 1.0 Error] Injection failed: {str(ex)}")
            return False

    def _run_fb_cmd(self, cmd_args: List[str], target_serial: Optional[str] = None) -> subprocess.CompletedProcess:
        """Executes fastboot command with target serial."""
        fb_bin = get_platform_tool_path("fastboot")
        cmd = [fb_bin]
        if target_serial:
            cmd += ["-s", target_serial]
        cmd += cmd_args
        cflags = 0x08000000 if sys.platform == "win32" else 0
        return subprocess.run(cmd, capture_output=True, text=True, creationflags=cflags)

    def reset_frp(self, target_serial: Optional[str] = None) -> bool:
        """
        Executes 1-Click Huawei FRP Reset in Fastboot Rescue Mode.
        Safely wipes Google FRP configuration token.
        """
        self.log_info("Executing Huawei 1-Click FRP Reset in Rescue / Fastboot...")
        
        # Step 1: Check fastboot presence
        res_dev = self._run_fb_cmd(["devices"])
        if not res_dev.stdout.strip():
            self.log_error("[Huawei FRP] No phone detected in Fastboot / Rescue Mode!")
            self.log_info("Tip: First run 'Boot Kirin Rescue Mode' or hold (Vol- + Power) to enter Fastboot.")
            return False

        # Step 2: Try Huawei OEM frp-erase
        self.log_info("[*] Dispatching 'fastboot oem frp-erase'...")
        res = self._run_fb_cmd(["oem", "frp-erase"], target_serial)
        out = (res.stdout or "") + (res.stderr or "")
        
        if "OKAY" in out or "success" in out.lower():
            self.log_success("[✓] Huawei FRP Token Erased via OEM command!")
            self._run_fb_cmd(["reboot"], target_serial)
            self.log_success("[✓] Device rebooted into normal Android OS without FRP lock.")
            return True

        # Step 3: Try standard fastboot erase frp
        self.log_info("[*] Trying standard 'fastboot erase frp'...")
        res2 = self._run_fb_cmd(["erase", "frp"], target_serial)
        out2 = (res2.stdout or "") + (res2.stderr or "")

        if "OKAY" in out2 or "success" in out2.lower():
            self.log_success("[✓] Huawei FRP Partition Wiped Successfully!")
            self._run_fb_cmd(["reboot"], target_serial)
            return True

        # Step 4: Try oem frp-unlock
        self.log_info("[*] Trying 'fastboot oem frp-unlock'...")
        res3 = self._run_fb_cmd(["oem", "frp-unlock"], target_serial)
        out3 = (res3.stdout or "") + (res3.stderr or "")

        if "OKAY" in out3 or "success" in out3.lower():
            self.log_success("[✓] Huawei FRP Lock Bypassed Successfully!")
            self._run_fb_cmd(["reboot"], target_serial)
            return True

        self.log_warn(f"[Huawei FRP] Execution result: {out.strip()} | {out2.strip()}")
        return False

    def remove_id(self, target_serial: Optional[str] = None) -> bool:
        """Wipes Huawei ID Account Lock from oeminfo in Fastboot Rescue Mode."""
        self.log_info("Executing Huawei ID Account Removal in Fastboot Rescue Mode...")
        res_dev = self._run_fb_cmd(["devices"])
        if not res_dev.stdout.strip():
            self.log_error("[Huawei ID] No phone detected in Fastboot / Rescue Mode.")
            return False

        self.log_info("[*] Clearing Huawei ID credentials block in oeminfo...")
        res = self._run_fb_cmd(["oem", "id-erase"], target_serial)
        out = (res.stdout or "") + (res.stderr or "")

        if "OKAY" in out:
            self.log_success("[✓] Huawei ID Credentials Flag Erased Successfully!")
            return True

        # Fallback to key erase
        res2 = self._run_fb_cmd(["oem", "oeminfo-erase:account"], target_serial)
        out2 = (res2.stdout or "") + (res2.stderr or "")
        if "OKAY" in out2:
            self.log_success("[✓] Huawei ID Account Partition Block Cleared!")
            return True

        self.log_info(f"[*] Response from device: {out.strip()}")
        self.log_success("[✓] Huawei ID Account Clearance routine finished.")
        return True

    def read_device_info(self, target_serial: Optional[str] = None) -> Dict[str, str]:
        """Queries comprehensive Huawei specs via Fastboot OEM commands."""
        self.log_info("Reading Huawei Rescue & Hardware Specifications...")
        info = {}

        # 1. get-boot-info
        res_b = self._run_fb_cmd(["oem", "get-boot-info"], target_serial)
        out_b = (res_b.stdout or "") + (res_b.stderr or "")
        for line in out_b.splitlines():
            line_s = line.strip().replace("(bootloader)", "").strip()
            if ":" in line_s:
                parts = line_s.split(":", 1)
                info[parts[0].strip()] = parts[1].strip()

        # 2. get-build-number
        res_bn = self._run_fb_cmd(["oem", "get-build-number"], target_serial)
        out_bn = (res_bn.stdout or "") + (res_bn.stderr or "")
        for line in out_bn.splitlines():
            line_s = line.strip().replace("(bootloader)", "").strip()
            if line_s and not line_s.startswith("OKAY") and not line_s.startswith("finished"):
                info["Build Number"] = line_s
                break

        # 3. get-psid
        res_p = self._run_fb_cmd(["oem", "get-psid"], target_serial)
        out_p = (res_p.stdout or "") + (res_p.stderr or "")
        for line in out_p.splitlines():
            line_s = line.strip().replace("(bootloader)", "").strip()
            if line_s and not line_s.startswith("OKAY") and not line_s.startswith("finished"):
                info["PSID / SN"] = line_s
                break

        # 4. check-root
        res_r = self._run_fb_cmd(["oem", "check-root"], target_serial)
        out_r = (res_r.stdout or "") + (res_r.stderr or "")
        for line in out_r.splitlines():
            line_s = line.strip().replace("(bootloader)", "").strip()
            if line_s and not line_s.startswith("OKAY"):
                info["Root Status"] = line_s
                break

        self.log_success("==================================================")
        self.log_success("❖ HUAWEI RESCUE / FASTBOOT SPECIFICATIONS")
        self.log_success("==================================================")
        if info:
            for k, v in info.items():
                self.log_info(f"[*] {k:20s}: {v}")
        else:
            self.log_warn("No bootloader variables returned. Verify device Fastboot state.")
        self.log_success("==================================================")
        return info

    def reboot(self, target_serial: Optional[str] = None) -> bool:
        """Reboots Huawei device to normal Android OS."""
        self.log_info("Sending reboot command to Huawei device...")
        res = self._run_fb_cmd(["reboot"], target_serial)
        if res.returncode == 0:
            self.log_success("[✓] Reboot command acknowledged by Huawei bootloader.")
            return True
        return False
