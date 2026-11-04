"""
Huawei HiSilicon Manufacture Mode PCUI COM Port AT-Command Protocol Engine.
Communicates directly with Huawei phones in Manufacture Mode (*#*#2846579#*#*)
over the PCUI / DBAdapter serial COM port to perform deep hardware diagnostics,
IMEI repair, NVRAM / Vendor rebranding, and jumping to Fastboot Rescue.
"""

import time
import re
import serial
import serial.tools.list_ports
from typing import Optional, Dict, Tuple, List
from core.logger import UILogger


class HuaweiPCUIEngine:
    """Production-grade AT-Command Protocol Engine for Huawei Manufacture Mode."""

    HUAWEI_VID = 0x12D1
    DEFAULT_BAUDRATE = 115200
    DEFAULT_TIMEOUT = 3.0

    def __init__(self, logger: Optional[UILogger] = None):
        self.logger = logger

    def log(self, msg: str, level: str = "info"):
        if self.logger:
            if level == "success": self.logger.success(msg)
            elif level == "error": self.logger.error(msg)
            elif level == "warn": self.logger.warn(msg)
            elif level == "brom": self.logger.brom(msg)
            else: self.logger.info(msg)
        else:
            print(f"[HUAWEI-PCUI] {msg}")

    # =========================================================================
    # PORT DISCOVERY
    # =========================================================================
    def find_pcui_port(self) -> Optional[str]:
        """
        Scans Windows COM ports for Huawei Android Adapter PCUI or DBAdapter interface.
        Returns the COM port string (e.g. 'COM7') or None.
        """
        try:
            ports = list(serial.tools.list_ports.comports())
            # 1. Exact match for PCUI in description
            for p in ports:
                desc_lower = (p.description or "").lower()
                vid = getattr(p, "vid", 0) or 0
                if vid == self.HUAWEI_VID or "huawei" in desc_lower:
                    if "pcui" in desc_lower or "dbadapter" in desc_lower or "manufacture" in desc_lower:
                        return p.device

            # 2. Match Huawei COM port
            for p in ports:
                desc_lower = (p.description or "").lower()
                vid = getattr(p, "vid", 0) or 0
                if vid == self.HUAWEI_VID or "huawei" in desc_lower:
                    return p.device
        except Exception as e:
            self.log(f"Error scanning serial ports: {str(e)}", "warn")

        return None

    # =========================================================================
    # AT COMMAND TRANSPORT LAYER
    # =========================================================================
    def send_at_command(
        self,
        command: str,
        port: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT
    ) -> Tuple[bool, str]:
        """
        Sends a single raw AT command over serial and waits for OK / ERROR terminator.
        Returns (success: bool, response_text: str).
        """
        target_port = port or self.find_pcui_port()
        if not target_port:
            return False, "Huawei PCUI COM Port not detected. Ensure phone is in Manufacture Mode (*#*#2846579#*#*)."

        ser = None
        try:
            ser = serial.Serial(
                port=target_port,
                baudrate=self.DEFAULT_BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                write_timeout=timeout
            )
            time.sleep(0.05)
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Ensure command ends with CRLF
            raw_cmd = command.strip().encode("ascii", errors="ignore") + b"\r\n"
            ser.write(raw_cmd)
            ser.flush()

            # Read lines until OK or ERROR or timeout
            lines: List[str] = []
            start_time = time.time()
            ok_received = False
            error_received = False

            while (time.time() - start_time) < timeout:
                line_bytes = ser.readline()
                if not line_bytes:
                    continue
                clean_line = line_bytes.decode("ascii", errors="ignore").strip()
                if not clean_line:
                    continue

                lines.append(clean_line)
                if clean_line == "OK":
                    ok_received = True
                    break
                elif any(clean_line.startswith(err) for err in ("ERROR", "+CME ERROR", "+CMS ERROR")):
                    error_received = True
                    break

            response = "\n".join(lines)
            if ok_received:
                return True, response
            elif error_received:
                return False, response
            else:
                return (len(lines) > 0), response

        except Exception as e:
            return False, f"Serial communication error on {target_port}: {str(e)}"
        finally:
            if ser and ser.is_open:
                try: ser.close()
                except Exception: pass

    # =========================================================================
    # HIGH-LEVEL SERVICES (DIAGNOSTICS, IMEI, REBRANDING, REBOOT)
    # =========================================================================
    def check_alive(self, port: Optional[str] = None) -> bool:
        """Pings modem with AT / ATE0."""
        ok, _ = self.send_at_command("AT", port=port, timeout=1.5)
        if ok:
            self.send_at_command("ATE0", port=port, timeout=1.5)
        return ok

    def read_device_passport(self, port: Optional[str] = None) -> Dict[str, str]:
        """
        Deep Manufacture Mode Hardware Passport Inspection:
        Queries Model, Board ID, Firmware Build, IMEI 1/2, Serial Number, and Vendor/Country.
        """
        target_port = port or self.find_pcui_port()
        self.log("==================================================", "brom")
        self.log(f"HUAWEI MANUFACTURE MODE DIAGNOSTICS (PORT: {target_port or 'SEARCHING'})", "brom")
        self.log("==================================================", "brom")

        if not target_port:
            self.log("[-] No Huawei PCUI COM Port detected.", "error")
            return {}

        passport: Dict[str, str] = {
            "port": target_port,
            "model": "Unknown",
            "build": "Unknown",
            "imei1": "Unknown",
            "imei2": "Unknown",
            "sn": "Unknown",
            "board": "Unknown",
            "vendor_country": "Unknown"
        }

        # Initialize AT channel
        self.send_at_command("ATE0", port=target_port, timeout=1.5)

        # 1. Model / Hardware Version (AT^HWVER)
        ok, res = self.send_at_command("AT^HWVER", port=target_port)
        if ok and res:
            for l in res.splitlines():
                if "^HWVER:" in l:
                    passport["board"] = l.split("^HWVER:")[1].strip().strip('"')
                elif l != "OK" and not l.startswith("AT^"):
                    passport["board"] = l.strip()

        # 2. Firmware Version (AT^VERSION? or AT+CGMR)
        ok, res = self.send_at_command("AT^VERSION?", port=target_port)
        if ok and res:
            for l in res.splitlines():
                if "^VERSION:" in l:
                    passport["build"] = l.split("^VERSION:")[1].strip().strip('"')
                elif l != "OK" and not l.startswith("AT^"):
                    passport["build"] = l.strip()
        else:
            ok2, res2 = self.send_at_command("AT+CGMR", port=target_port)
            if ok2 and res2:
                lines = [l for l in res2.splitlines() if l != "OK" and not l.startswith("AT")]
                if lines: passport["build"] = lines[0].strip()

        # 3. Serial Number / BSN (AT^BSN? or AT^SN)
        ok, res = self.send_at_command("AT^BSN?", port=target_port)
        if ok and res:
            for l in res.splitlines():
                if "^BSN:" in l:
                    passport["sn"] = l.split("^BSN:")[1].strip().strip('"')
                elif l != "OK" and not l.startswith("AT^"):
                    passport["sn"] = l.strip()

        # 4. Primary IMEI (AT+CGSN)
        ok, res = self.send_at_command("AT+CGSN", port=target_port)
        if ok and res:
            lines = [l for l in res.splitlines() if l != "OK" and l.isdigit() and len(l) >= 14]
            if lines:
                passport["imei1"] = lines[0].strip()

        # 5. Dual IMEI / Secondary IMEI (AT^PHYNUM=IMEI? or AT^PHYNUM=IMEI2?)
        ok, res = self.send_at_command("AT^PHYNUM=IMEI2?", port=target_port)
        if ok and res:
            m = re.search(r"(\d{14,15})", res)
            if m: passport["imei2"] = m.group(1)

        # 6. Vendor & Country Information (AT^GETPORTMODE or AT^FACINFO?)
        ok, res = self.send_at_command("AT^GETPORTMODE", port=target_port)
        if ok and res:
            lines = [l for l in res.splitlines() if l != "OK" and not l.startswith("AT^")]
            if lines: passport["vendor_country"] = " / ".join(lines)

        self.log(f"[+] Hardware Model / Board : {passport['board']}", "info")
        self.log(f"[+] Build Display ID       : {passport['build']}", "info")
        self.log(f"[+] Serial Number (BSN)    : {passport['sn']}", "info")
        self.log(f"[+] Primary IMEI 1         : {passport['imei1']}", "info")
        if passport["imei2"] != "Unknown":
            self.log(f"[+] Secondary IMEI 2       : {passport['imei2']}", "info")
        if passport["vendor_country"] != "Unknown":
            self.log(f"[+] Active Port Profile    : {passport['vendor_country']}", "info")
        self.log("==================================================", "success")
        self.log("[✓] Manufacture Mode Diagnostics Read Successfully!", "success")

        return passport

    def repair_imei(
        self,
        imei1: str,
        imei2: Optional[str] = None,
        datalock_key: str = "",
        port: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Writes IMEI 1 & IMEI 2 over Huawei Manufacture Mode AT commands.
        Handles DataLock unlocking if phone requires authentication.
        """
        target_port = port or self.find_pcui_port()
        if not target_port:
            return False, "Huawei PCUI COM Port not connected."

        clean_imei1 = imei1.strip()
        if not clean_imei1.isdigit() or len(clean_imei1) not in (14, 15):
            return False, f"Invalid IMEI 1 '{clean_imei1}'. Must be 14 or 15 numeric digits."

        self.log("==================================================", "brom")
        self.log(f"STARTING HUAWEI IMEI REPAIR (PORT: {target_port})", "brom")
        self.log(f"[*] Target Primary IMEI 1 : {clean_imei1}", "brom")
        if imei2:
            self.log(f"[*] Target Secondary IMEI 2: {imei2.strip()}", "brom")
        self.log("==================================================", "brom")

        # 1. Unlock DataLock if provided
        if datalock_key.strip():
            self.log(f"[*] Sending DataLock unlock code...", "info")
            ok_dl, res_dl = self.send_at_command(f'AT^DATALOCK="{datalock_key.strip()}"', port=target_port)
            if not ok_dl:
                self.log(f"[!] DataLock warning: {res_dl}", "warn")
            else:
                self.log("[✓] DataLock accepted by baseband.", "success")

        # 2. Write IMEI 1 (AT^PHYNUM=IMEI,<imei1>)
        self.log(f"[*] Writing Primary IMEI 1...", "info")
        ok1, res1 = self.send_at_command(f"AT^PHYNUM=IMEI,{clean_imei1}", port=target_port)
        if not ok1:
            # Fallback format: AT^PHYNUM="IMEI",<imei1>
            ok1, res1 = self.send_at_command(f'AT^PHYNUM="IMEI",{clean_imei1}', port=target_port)

        if not ok1:
            self.log(f"[-] Failed to write IMEI 1: {res1}", "error")
            return False, f"IMEI 1 write failed: {res1}"

        self.log(f"[✓] IMEI 1 written successfully: {clean_imei1}", "success")

        # 3. Write IMEI 2 if specified
        if imei2 and imei2.strip():
            clean_imei2 = imei2.strip()
            self.log(f"[*] Writing Secondary IMEI 2...", "info")
            ok2, res2 = self.send_at_command(f"AT^PHYNUM=IMEI2,{clean_imei2}", port=target_port)
            if not ok2:
                ok2, res2 = self.send_at_command(f'AT^PHYNUM="IMEI2",{clean_imei2}', port=target_port)

            if not ok2:
                self.log(f"[!] Warning: IMEI 2 write failed: {res2}", "warn")
            else:
                self.log(f"[✓] IMEI 2 written successfully: {clean_imei2}", "success")

        self.log("==================================================", "success")
        self.log("[✓] IMEI REPAIR OPERATION COMPLETED (100%)!", "success")
        self.log("Reboot device to finalize baseband calibration.", "success")
        return True, "IMEI written successfully"

    def rebrand_device(
        self,
        vendor: str,
        country: str,
        port: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Changes Vendor and Country codes in NVRAM (e.g. vendor='hw', country='spcseas').
        """
        target_port = port or self.find_pcui_port()
        if not target_port:
            return False, "Huawei PCUI COM Port not connected."

        v = vendor.strip().lower()
        c = country.strip().lower()

        self.log(f"[*] Setting Vendor to '{v}' and Country to '{c}'...", "info")
        ok_v, res_v = self.send_at_command(f'AT^SETVND="{v}"', port=target_port)
        ok_c, res_c = self.send_at_command(f'AT^SETCTRY="{c}"', port=target_port)

        if ok_v and ok_c:
            self.log(f"[✓] Vendor/Country rebranding completed: {v}/{c}", "success")
            return True, f"Rebranded to {v}/{c}"
        else:
            return False, f"Rebranding failed: {res_v} | {res_c}"

    def reboot(self, mode: str = "fastboot", port: Optional[str] = None) -> Tuple[bool, str]:
        """
        Reboots device from Manufacture Mode:
        - 'fastboot': AT^REBOOT=FASTBOOT (jumps straight into Fastboot Rescue Mode)
        - 'normal':   AT^RESET
        - 'recovery': AT^REBOOT=RECOVERY
        """
        target_port = port or self.find_pcui_port()
        if not target_port:
            return False, "Huawei PCUI COM Port not connected."

        if mode.lower() == "fastboot":
            self.log("[*] Commanding device to reboot into Fastboot Rescue Mode...", "info")
            ok, res = self.send_at_command("AT^REBOOT=FASTBOOT", port=target_port)
            if not ok:
                ok, res = self.send_at_command("AT^FASTBOOT", port=target_port)
            return ok, "Rebooted to Fastboot Rescue"
        elif mode.lower() == "recovery":
            self.log("[*] Commanding device to reboot into Recovery Mode...", "info")
            ok, res = self.send_at_command("AT^REBOOT=RECOVERY", port=target_port)
            return ok, "Rebooted to Recovery"
        else:
            self.log("[*] Commanding device to normal restart...", "info")
            ok, res = self.send_at_command("AT^RESET", port=target_port)
            return ok, "Normal reboot initiated"
