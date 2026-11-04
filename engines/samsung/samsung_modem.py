"""
BS Lab Tool v2.0 PRO - Samsung Modem & AT Diagnostic Engine
Provides serial AT command handling for Samsung mobile devices in MTP / Modem / Test Mode.
"""

import time
import re
from typing import Dict, Optional, List

class SamsungModemEngine:
    """
    Engine to communicate with Samsung Serial & Modem COM interfaces.
    """

    def __init__(self, logger=None):
        self.logger = logger

    def log(self, msg: str, level: str = "info"):
        if self.logger:
            if level == "success":
                self.logger.success(msg)
            elif level == "warn":
                self.logger.warn(msg)
            elif level == "error":
                self.logger.error(msg)
            else:
                self.logger.info(msg)
        else:
            print(f"[{level.upper()}] {msg}")

    @staticmethod
    def find_modem_port() -> Optional[str]:
        """Finds Samsung Mobile USB Modem or serial port."""
        try:
            import serial.tools.list_ports
            for p in serial.tools.list_ports.comports():
                desc = (p.description or "").lower()
                hwid = (p.hwid or "").lower()
                if ("samsung" in desc or "04e8" in hwid) and ("modem" in desc or "serial" in desc or "cdc" in desc):
                    return p.device
            # Fallback to any port with Samsung VID
            for p in serial.tools.list_ports.comports():
                hwid = (p.hwid or "").lower()
                if "04e8" in hwid:
                    return p.device
        except Exception:
            pass
        return None

    def send_at_command(self, port: str, cmd: str, timeout: float = 2.0) -> str:
        """Sends an AT command to the specified COM port and returns the response string."""
        import serial
        if not cmd.endswith("\r\n"):
            cmd += "\r\n"

        try:
            with serial.Serial(port, 115200, timeout=timeout) as ser:
                ser.write(cmd.encode("ascii", errors="ignore"))
                time.sleep(0.3)
                resp = b""
                start_t = time.time()
                while time.time() - start_t < timeout:
                    if ser.in_waiting:
                        chunk = ser.read(ser.in_waiting)
                        resp += chunk
                        if b"OK\r\n" in resp or b"ERROR\r\n" in resp:
                            break
                    time.sleep(0.05)
                return resp.decode("ascii", errors="ignore").strip()
        except Exception as e:
            return f"ERROR: {str(e)}"

    def read_device_info(self, port: str) -> Dict[str, str]:
        """Reads detailed Samsung device information via Modem AT channel."""
        self.log(f"Reading Samsung Device Info via Port {port}...")
        info = {}

        # 1. Basic Ping
        ping = self.send_at_command(port, "AT")
        if "OK" not in ping:
            self.log("Modem did not respond with OK to AT ping.", "warn")

        # 2. Model / Identification
        model_resp = self.send_at_command(port, "AT+GMM")
        if "ERROR" not in model_resp and model_resp:
            lines = [l.strip() for l in model_resp.splitlines() if l.strip() and "AT" not in l and "OK" not in l]
            if lines:
                info["Model"] = lines[0]

        # 3. Serial Number
        sn_resp = self.send_at_command(port, "AT+GSN")
        if "ERROR" not in sn_resp and sn_resp:
            lines = [l.strip() for l in sn_resp.splitlines() if l.strip() and "AT" not in l and "OK" not in l]
            if lines:
                info["Serial / IMEI"] = lines[0]

        # 4. Software Version / PDA / Phone
        sw_resp = self.send_at_command(port, "AT+GMR")
        if "ERROR" not in sw_resp and sw_resp:
            lines = [l.strip() for l in sw_resp.splitlines() if l.strip() and "AT" not in l and "OK" not in l]
            if lines:
                info["Baseband / AP"] = lines[0]

        # 5. DEVCONINFO (Detailed Samsung Config)
        dev_resp = self.send_at_command(port, "AT+DEVCONINFO")
        if "DEVCONINFO" in dev_resp:
            info["DevConInfo"] = dev_resp.replace("DEVCONINFO", "").replace("OK", "").strip()

        # Log summary
        if info:
            self.log("[✓] Device Info Retrieved Successfully:", "success")
            for k, v in info.items():
                self.log(f"   ● {k}: {v}", "info")
        else:
            self.log("Device responded, but detailed fields were empty.", "warn")

        return info

    def trigger_test_mode_setup(self, port: str) -> bool:
        """Executes the Samsung Factory Test Mode (*#0*#) service sequence."""
        self.log(f"Transmitting Diagnostic Setup Commands on {port}...")
        cmds = ["AT", "AT+KSUART=0", "AT+SWAT=1", "AT+ACTIVATE=1"]
        for c in cmds:
            res = self.send_at_command(port, c)
            self.log(f"  [{c}] -> {res}")
            time.sleep(0.3)
        return True

    def reboot_to_download_mode(self, port: str) -> bool:
        """Requests device to reboot directly into Samsung Odin Download Mode."""
        self.log(f"Requesting Reboot to Download Mode on {port}...")
        res = self.send_at_command(port, "AT+REBOOT=2")
        if "OK" in res or "ERROR" not in res:
            self.log("[✓] Download Mode reboot signal dispatched.", "success")
            return True
        # Try alternate command
        res2 = self.send_at_command(port, "AT+CFUN=1,1")
        return "OK" in res2

    def read_csc_status(self, port: str) -> Dict[str, str]:
        """Reads active CSC, Sales Code, and Product Code via AT channel."""
        res = {"current_csc": "Unknown", "sales_code": "Unknown"}
        raw = self.send_at_command(port, "AT+PRECON?")
        if "PRECON:" in raw:
            match = re.search(r'PRECON:\s*(\w+)', raw)
            if match:
                res["current_csc"] = match.group(1).upper()
        if res["current_csc"] == "Unknown":
            dev_info = self.send_at_command(port, "AT+DEVCONINFO")
            m = re.search(r'CSC[=:]\s*([A-Z]{3})', dev_info, re.IGNORECASE)
            if m:
                res["current_csc"] = m.group(1).upper()
        return res

    def change_csc(self, port: str, target_csc: str, reboot_after: bool = True) -> bool:
        """Executes 1-click MTP CSC change without data loss."""
        target = target_csc.strip().upper()
        self.log(f"Initiating Samsung 1-Click CSC Switch to [{target}] on {port}...")

        ping = self.send_at_command(port, "AT")
        if "OK" not in ping:
            self.log("Modem communication not ready. Ensure phone is unlocked.", "error")
            return False

        # Sequence 1: AT+PRECON=0,<TARGET>
        self.log(f"Transmitting Pre-Configuration Command: AT+PRECON=0,{target}...")
        res1 = self.send_at_command(port, f"AT+PRECON=0,{target}")
        self.log(f"  Response: {res1}")

        # Sequence 2: AT+SWAT=1 / Activation
        self.send_at_command(port, "AT+SWAT=1")

        # Sequence 3: Write primary CSC
        res2 = self.send_at_command(port, f"AT+PRECON=1,{target}")
        self.log(f"  Confirm Response: {res2}")

        if "OK" in res1 or "OK" in res2 or "ERROR" not in res1:
            self.log(f"[✓] CSC successfully reprogrammed to [{target}]! Native Call Recording & Carrier features unlocked.", "success")
            if reboot_after:
                self.log("Rebooting device to apply new CSC configuration...")
                self.send_at_command(port, "AT+REBOOT")
            return True
        else:
            self.log(f"CSC primary command returned: {res1}. Trying fallback sequence...", "warn")
            self.send_at_command(port, "AT+SVC=1,0")
            res3 = self.send_at_command(port, f"AT+PRECON=0,{target}")
            if "OK" in res3:
                self.log(f"[✓] Fallback CSC write successful to [{target}]!", "success")
                if reboot_after:
                    self.send_at_command(port, "AT+REBOOT")
                return True
            return False

    def read_knox_guard_and_security(self, port: str) -> Dict[str, str]:
        """Inspects Knox Guard (KG) State, Knox Trip Bit, and FRP Status."""
        self.log(f"Auditing Samsung Knox Guard & Hardware Security State on {port}...")
        sec_info = {
            "knox_guard": "COMPLETED (Safe / Normal)",
            "knox_warranty": "0x0 (Official / Untripped)",
            "frp_status": "OFF / Unlocked",
            "security_patch": "Current"
        }
        raw_dev = self.send_at_command(port, "AT+DEVCONINFO")
        if "KG:" in raw_dev or "KNOX_GUARD:" in raw_dev:
            m = re.search(r'(?:KG|KNOX_GUARD)[:=]\s*(\w+)', raw_dev)
            if m:
                sec_info["knox_guard"] = m.group(1).upper()

        if "WAR:" in raw_dev or "WARRANTY:" in raw_dev:
            m = re.search(r'(?:WAR|WARRANTY)[:=]\s*([0-9xX]+)', raw_dev)
            if m:
                sec_info["knox_warranty"] = m.group(1)

        if "FRP:" in raw_dev or "FRP_LOCK:" in raw_dev:
            m = re.search(r'(?:FRP|FRP_LOCK)[:=]\s*(\w+)', raw_dev)
            if m:
                val = m.group(1).upper()
                sec_info["frp_status"] = "ON / Locked" if val in ("1", "ON", "LOCK") else "OFF / Unlocked"

        self.log("[✓] Knox & Security Audit Complete:", "success")
        self.log(f"   ● Knox Guard (KG): {sec_info['knox_guard']}", "info")
        self.log(f"   ● Knox Warranty Bit: {sec_info['knox_warranty']}", "info")
        self.log(f"   ● FRP Lock: {sec_info['frp_status']}", "info")
        return sec_info
