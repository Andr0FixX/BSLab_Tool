import os
import sys
import subprocess
import serial.tools.list_ports
from core.path_utils import get_platform_tool_path
from core.model_database import ModelDatabase

class DeviceDetector:
    """
    High-Performance Hardware Sniffer & Classifier (Zero-Click Engine).
    Sniffs Windows COM ports, ADB interfaces, and Fastboot endpoints using
    direct platform tool paths and silent subprocess flags.
    """

    _CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

    @classmethod
    def scan_all_devices(cls):
        """
        Scans COM ports, ADB, and Fastboot.
        Returns a dict:
        {
            "detected": bool,
            "text": str,
            "mode": "MTK"|"QUALCOMM"|"SPD"|"SAMSUNG"|"ADB"|"FASTBOOT"|"COM"|"NONE",
            "details": dict
        }
        """
        # 1. Check COM ports (MediaTek, Qualcomm 9008, Unisoc SPRD, Samsung Odin)
        try:
            coms = list(serial.tools.list_ports.comports())
            first_com = None
            for c in coms:
                desc_lower = (c.description or "").lower()
                vid = getattr(c, "vid", 0) or 0
                pid = getattr(c, "pid", 0) or 0

                # MediaTek BROM / Preloader
                if any(k in desc_lower for k in ["mediatek", "mtk", "preloader", "vcom", "da usb"]) or vid == 0x0E8D:
                    profile = ModelDatabase.resolve(c.description, mode="MTK", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    return {
                        "detected": True,
                        "text": f"🟢 MTK BROM: {profile['name']} ({c.device})",
                        "mode": "MTK",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    }
                # Qualcomm HS-USB QDLoader 9008
                elif (vid == 0x05C6 and pid == 0x9008) or any(k in desc_lower for k in ["qualcomm", "9008", "qdloader"]):
                    profile = ModelDatabase.resolve(c.description, mode="QUALCOMM", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    return {
                        "detected": True,
                        "text": f"🟢 Qualcomm EDL: {profile['name']} ({c.device})",
                        "mode": "QUALCOMM",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    }
                # Huawei / HiSilicon Kirin USB COM 1.0 (Test Point)
                elif (vid == 0x12D1 and pid == 0x3609) or any(k in desc_lower for k in ["usb com 1.0", "huawei usb com"]):
                    profile = ModelDatabase.resolve(c.description, mode="HUAWEI", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    return {
                        "detected": True,
                        "text": f"🟢 Huawei Kirin: {profile['name']} ({c.device})",
                        "mode": "HUAWEI",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    }
                # Huawei HiSilicon Manufacture Mode (PCUI / DBAdapter)
                elif (vid == 0x12D1 and any(k in desc_lower for k in ["pcui", "dbadapter", "manufacture"])) or any(k in desc_lower for k in ["adapter pcui", "dbadapter", "huawei pcui"]):
                    profile = ModelDatabase.resolve(c.description, mode="HUAWEI_PCUI", details={"port": c.device, "vid": hex(vid), "pid": hex(pid), "is_pcui": True})
                    return {
                        "detected": True,
                        "text": f"🟢 Huawei PCUI: {profile['name']} ({c.device})",
                        "mode": "HUAWEI_PCUI",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    }
                # Unisoc / Spreadtrum BSL / Diag
                elif any(k in desc_lower for k in ["spd", "sprd", "spreadtrum", "unisoc", "u2s"]):
                    profile = ModelDatabase.resolve(c.description, mode="SPD", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    return {
                        "detected": True,
                        "text": f"🟢 Unisoc Diag: {profile['name']} ({c.device})",
                        "mode": "SPD",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    }
                # Samsung Odin Download Mode / Modem
                elif any(k in desc_lower for k in ["samsung", "odin"]) or vid == 0x04E8:
                    profile = ModelDatabase.resolve(c.description, mode="SAMSUNG", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    return {
                        "detected": True,
                        "text": f"🟢 Samsung Odin: {profile['name']} ({c.device})",
                        "mode": "SAMSUNG",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    }
                elif c.device and not first_com:
                    first_com = c
        except Exception:
            first_com = None

        # 2. Check Fastboot devices first (prioritize low-level bootloader over adb)
        fb_bin = get_platform_tool_path("fastboot")
        try:
            res_fb = subprocess.run(
                [fb_bin, "devices"],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=cls._CREATE_NO_WINDOW
            )
            fb_lines = [l.strip() for l in res_fb.stdout.splitlines() if l.strip()]
            if fb_lines:
                fb_serial = fb_lines[0].split()[0]
                product_name = ""
                unlocked_state = ""
                try:
                    # Query product & unlocked state
                    res_var = subprocess.run(
                        [fb_bin, "-s", fb_serial, "getvar", "product"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        creationflags=cls._CREATE_NO_WINDOW
                    )
                    var_out = (res_var.stdout or "") + (res_var.stderr or "")
                    for line in var_out.splitlines():
                        if "product:" in line:
                            product_name = line.split("product:")[1].strip()
                            break

                    res_lock = subprocess.run(
                        [fb_bin, "-s", fb_serial, "getvar", "unlocked"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        creationflags=cls._CREATE_NO_WINDOW
                    )
                    lock_out = (res_lock.stdout or "") + (res_lock.stderr or "")
                    for line in lock_out.splitlines():
                        if "unlocked:" in line:
                            unlocked_state = line.split("unlocked:")[1].strip()
                            break
                except Exception:
                    pass

                profile = ModelDatabase.resolve(
                    product_name or fb_serial,
                    mode="FASTBOOT",
                    details={"product": product_name, "unlocked": unlocked_state, "serial": fb_serial}
                )
                lock_text = " [Unlocked]" if unlocked_state.lower() in ("yes", "true") else " [Locked]"
                display_title = f"🟢 Fastboot: {profile['name']} ({fb_serial[:10]}){lock_text}"

                return {
                    "detected": True,
                    "text": display_title,
                    "mode": "FASTBOOT",
                    "details": {
                        "serial": fb_serial,
                        "product": product_name or "Android Fastboot",
                        "unlocked": unlocked_state,
                        "profile": profile
                    }
                }
        except Exception:
            pass

        # 3. Check ADB devices
        adb_bin = get_platform_tool_path("adb")
        try:
            res_adb = subprocess.run(
                [adb_bin, "devices"],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=cls._CREATE_NO_WINDOW
            )
            adb_lines = [l.strip() for l in res_adb.stdout.splitlines() if l.strip() and not l.startswith("List of")]
            if adb_lines:
                dev_parts = adb_lines[0].split()
                dev_serial = dev_parts[0]
                is_unauth = "unauthorized" in adb_lines[0].lower()

                if is_unauth:
                    return {
                        "detected": True,
                        "text": f"🟡 ADB: {dev_serial[:12]} (UNAUTHORIZED - Tap Phone OK)",
                        "mode": "ADB",
                        "details": {"serial": dev_serial, "model": "Unauthorized ADB"}
                    }

                model_name = dev_serial
                brand_name = ""
                try:
                    res_model = subprocess.run(
                        [adb_bin, "-s", dev_serial, "shell", "getprop", "ro.product.model"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        creationflags=cls._CREATE_NO_WINDOW
                    )
                    m = res_model.stdout.strip()
                    if m:
                        model_name = m

                    res_b = subprocess.run(
                        [adb_bin, "-s", dev_serial, "shell", "getprop", "ro.product.brand"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        creationflags=cls._CREATE_NO_WINDOW
                    )
                    b = res_b.stdout.strip()
                    if b:
                        brand_name = b
                except Exception:
                    pass

                profile = ModelDatabase.resolve(
                    model_name,
                    mode="ADB",
                    details={"model": model_name, "brand": brand_name, "serial": dev_serial}
                )

                return {
                    "detected": True,
                    "text": f"🟢 ADB: {profile['name']} ({dev_serial[:10]})",
                    "mode": "ADB",
                    "details": {"serial": dev_serial, "model": model_name, "profile": profile}
                }
        except Exception:
            pass

        # 4. Fallback to generic COM port
        if first_com:
            return {
                "detected": True,
                "text": f"🟢 {first_com.description[:26]} ({first_com.device})",
                "mode": "COM",
                "details": {"port": first_com.device, "desc": first_com.description}
            }

        # 5. None detected
        return {
            "detected": False,
            "text": "⚪ No Device Connected (Listening...)",
            "mode": "NONE",
            "details": {}
        }

    @classmethod
    def scan_all_connected_devices(cls):
        """
        Scans all USB interfaces and returns a list of all currently connected devices
        (e.g. multiple phones plugged into a USB hub).
        """
        devices = []

        # 1. COM ports
        try:
            coms = list(serial.tools.list_ports.comports())
            for c in coms:
                desc_lower = (c.description or "").lower()
                vid = getattr(c, "vid", 0) or 0
                pid = getattr(c, "pid", 0) or 0

                if any(k in desc_lower for k in ["mediatek", "mtk", "preloader", "vcom", "da usb"]) or vid == 0x0E8D:
                    profile = ModelDatabase.resolve(c.description, mode="MTK", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 MTK BROM: {profile['name']} ({c.device})",
                        "mode": "MTK",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    })
                elif (vid == 0x05C6 and pid == 0x9008) or any(k in desc_lower for k in ["qualcomm", "9008", "qdloader"]):
                    profile = ModelDatabase.resolve(c.description, mode="QUALCOMM", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 Qualcomm EDL: {profile['name']} ({c.device})",
                        "mode": "QUALCOMM",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    })
                elif (vid == 0x12D1 and pid == 0x3609) or any(k in desc_lower for k in ["usb com 1.0", "huawei usb com"]):
                    profile = ModelDatabase.resolve(c.description, mode="HUAWEI", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 Huawei Kirin: {profile['name']} ({c.device})",
                        "mode": "HUAWEI",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    })
                elif (vid == 0x12D1 and any(k in desc_lower for k in ["pcui", "dbadapter", "manufacture"])) or any(k in desc_lower for k in ["adapter pcui", "dbadapter", "huawei pcui"]):
                    profile = ModelDatabase.resolve(c.description, mode="HUAWEI_PCUI", details={"port": c.device, "vid": hex(vid), "pid": hex(pid), "is_pcui": True})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 Huawei PCUI: {profile['name']} ({c.device})",
                        "mode": "HUAWEI_PCUI",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    })
                elif any(k in desc_lower for k in ["spd", "sprd", "spreadtrum", "unisoc", "u2s"]):
                    profile = ModelDatabase.resolve(c.description, mode="SPD", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 Unisoc Diag: {profile['name']} ({c.device})",
                        "mode": "SPD",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    })
                elif any(k in desc_lower for k in ["samsung", "odin"]) or vid == 0x04E8:
                    profile = ModelDatabase.resolve(c.description, mode="SAMSUNG", details={"port": c.device, "vid": hex(vid), "pid": hex(pid)})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 Samsung Odin: {profile['name']} ({c.device})",
                        "mode": "SAMSUNG",
                        "details": {"port": c.device, "desc": c.description, "vid": hex(vid), "pid": hex(pid), "profile": profile}
                    })
        except Exception:
            pass

        # 2. Fastboot
        fb_bin = get_platform_tool_path("fastboot")
        try:
            res_fb = subprocess.run([fb_bin, "devices"], capture_output=True, text=True, timeout=2, creationflags=cls._CREATE_NO_WINDOW)
            for line in res_fb.stdout.splitlines():
                if line.strip():
                    fb_serial = line.split()[0]
                    profile = ModelDatabase.resolve(fb_serial, mode="FASTBOOT", details={"serial": fb_serial})
                    devices.append({
                        "detected": True,
                        "text": f"🟢 Fastboot: {profile['name']} ({fb_serial[:10]})",
                        "mode": "FASTBOOT",
                        "details": {"serial": fb_serial, "profile": profile}
                    })
        except Exception:
            pass

        # 3. ADB
        adb_bin = get_platform_tool_path("adb")
        try:
            res_adb = subprocess.run([adb_bin, "devices"], capture_output=True, text=True, timeout=2, creationflags=cls._CREATE_NO_WINDOW)
            for line in res_adb.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    dev_serial = parts[0]
                    model_name = dev_serial
                    brand_name = ""
                    soc_name = ""
                    try:
                        res_m = subprocess.run([adb_bin, "-s", dev_serial, "shell", "getprop", "ro.product.model"],
                                               capture_output=True, text=True, timeout=2, creationflags=cls._CREATE_NO_WINDOW)
                        if res_m.stdout.strip():
                            model_name = res_m.stdout.strip()
                        res_b = subprocess.run([adb_bin, "-s", dev_serial, "shell", "getprop", "ro.product.brand"],
                                               capture_output=True, text=True, timeout=2, creationflags=cls._CREATE_NO_WINDOW)
                        if res_b.stdout.strip():
                            brand_name = res_b.stdout.strip()
                        res_s = subprocess.run([adb_bin, "-s", dev_serial, "shell", "getprop", "ro.board.platform"],
                                               capture_output=True, text=True, timeout=2, creationflags=cls._CREATE_NO_WINDOW)
                        if res_s.stdout.strip():
                            soc_name = res_s.stdout.strip()
                    except Exception:
                        pass

                    profile = ModelDatabase.resolve(model_name, mode="ADB", details={"model": model_name, "brand": brand_name, "soc": soc_name, "serial": dev_serial})
                    display_brand = (brand_name or profile.get("brand") or "Android").upper()
                    display_model = profile.get("name") or model_name
                    devices.append({
                        "detected": True,
                        "text": f"🟢 ADB: {display_brand} {display_model} ({dev_serial[:8]})",
                        "mode": "ADB",
                        "details": {
                            "serial": dev_serial,
                            "model": display_model,
                            "brand": display_brand,
                            "soc": soc_name,
                            "profile": profile
                        }
                    })
        except Exception:
            pass

        return devices
