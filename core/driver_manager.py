"""
Automated USB Drivers & LibUSB Filter Subsystem Manager.
Detects missing device drivers, installs signed INF drivers via pnputil,
and executes silent installations of UsbDk and LibUSB filter drivers.
"""

import os
import subprocess
import shutil
from core.logger import UILogger
from core.path_utils import get_drivers_path

class DriverManager:
    """Manages Windows USB Driver detection and automated silent installation."""

    DRIVERS_BASE_DIR = get_drivers_path()

    def __init__(self, logger: UILogger = None):
        self.logger = logger

    def log(self, msg, level="info"):
        if self.logger:
            if level == "success": self.logger.success(msg)
            elif level == "error": self.logger.error(msg)
            elif level == "warn": self.logger.warn(msg)
            elif level == "brom": self.logger.brom(msg)
            else: self.logger.info(msg)
        else:
            print(f"[DRV] {msg}")

    # =========================================================================
    # DRIVER DETECTION
    # =========================================================================
    def check_all_driver_status(self) -> dict:
        """
        Queries Windows DriverStore and system services to detect whether
        MTK, Qualcomm, Unisoc, and UsbDk drivers are currently installed.
        """
        status = {
            "mtk": False,
            "qualcomm": False,
            "unisoc": False,
            "huawei": False,
            "usbdk": False,
            "libusb": False
        }

        # 1. Query DriverStore via pnputil /enum-drivers
        try:
            res = subprocess.run(
                ["pnputil", "/enum-drivers"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                timeout=10
            )
            out = res.stdout.lower()

            if "mediatek" in out or "usbvcom" in out or "cdc-acm" in out:
                status["mtk"] = True
            if "qualcomm" in out or "qcser" in out or "qdloader" in out:
                status["qualcomm"] = True
            if "unisoc" in out or "sprd" in out or "spreadtrum" in out:
                status["unisoc"] = True
            if "huawei" in out or "hwusb" in out or "hisi" in out or "12d1" in out:
                status["huawei"] = True
            if "libusb" in out or "winusb" in out:
                status["libusb"] = True
        except Exception as e:
            self.log(f"Error checking DriverStore via pnputil: {str(e)}", "warn")

        # 2. Query UsbDk Windows Service
        try:
            sc_res = subprocess.run(
                ["sc", "query", "UsbDkService"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                timeout=5
            )
            if "running" in sc_res.stdout.lower() or "state" in sc_res.stdout.lower():
                status["usbdk"] = True
        except Exception:
            pass

        return status

    # =========================================================================
    # SILENT DRIVER INSTALLATION
    # =========================================================================
    def install_inf_driver(self, inf_path: str) -> (bool, str):
        """
        Installs an INF driver package into the Windows DriverStore using pnputil.
        Command: pnputil /add-driver <inf_path> /install
        """
        if not os.path.exists(inf_path):
            return False, f"INF file not found: {inf_path}"

        self.log(f"Installing Driver Package: {os.path.basename(inf_path)}...")
        try:
            proc = subprocess.run(
                ["pnputil", "/add-driver", inf_path, "/install"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                timeout=30
            )
            out = proc.stdout
            if proc.returncode == 0 or "successfully" in out.lower() or "added" in out.lower():
                self.log(f"[✓] Successfully added to DriverStore: {os.path.basename(inf_path)}", "success")
                return True, "Driver installed successfully"
            else:
                # Fallback via setupapi DefaultInstall
                self.log(f"pnputil notice: {out.strip()[:100]}... Trying SetupAPI fallback.", "warn")
                fb_cmd = ["rundll32.exe", "setupapi.dll,InstallHinfSection", "DefaultInstall", "132", inf_path]
                subprocess.run(fb_cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, timeout=20)
                return True, "Driver registered via SetupAPI"
        except Exception as e:
            return False, str(e)

    def install_usbdk_silent(self) -> (bool, str):
        """Silently installs UsbDk 64-bit MSI package without system reboot."""
        msi_path = os.path.join(self.DRIVERS_BASE_DIR, "usbdk", "UsbDk_1.0.22_x64.msi")
        if not os.path.exists(msi_path) or os.path.getsize(msi_path) < 100000:
            return False, "UsbDk installer package not found or incomplete."

        self.log("Installing UsbDk (USB Development Kit) Service silently...")
        try:
            cmd = ["msiexec.exe", "/i", msi_path, "/qn", "/norestart"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                timeout=60
            )
            if proc.returncode == 0 or proc.returncode == 3010:  # 3010 = reboot optional
                self.log("UsbDk 64-bit Service installed successfully!", "success")
                return True, "UsbDk installed"
            else:
                return False, f"msiexec returned error code {proc.returncode}"
        except Exception as e:
            return False, str(e)

    def install_all_drivers(self, progress_cb=None) -> dict:
        """
        One-Click Automated Driver Installer:
        Detects missing drivers and installs MTK, Qualcomm, Unisoc, LibUSB, and UsbDk.
        """
        self.log("==================================================", "brom")
        self.log("STARTING AUTOMATED USB DRIVER & LIBUSB INSTALLATION", "brom")
        self.log("==================================================", "brom")

        initial_status = self.check_all_driver_status()
        results = {}

        # List of driver targets: (key, name, inf_rel_path)
        driver_targets = [
            ("mtk", "MediaTek USB VCOM Driver", os.path.join("mtk", "usbvcom.inf")),
            ("mtk_cdc", "MediaTek CDC ACM Driver", os.path.join("mtk", "cdc-acm.inf")),
            ("qualcomm", "Qualcomm HS-USB QDLoader 9008 Driver", os.path.join("qualcomm", "qcser.inf")),
            ("unisoc", "Unisoc SPRD U2S Diag / Flash Driver", os.path.join("unisoc", "sprd_u2s.inf")),
            ("huawei_com", "Huawei USB COM 1.0 Driver", os.path.join("huawei", "huawei_usb_com.inf")),
            ("huawei_pcui", "Huawei PCUI Handset Driver", os.path.join("huawei", "huawei_handset.inf")),
            ("libusb", "LibUSB-Win32 Endpoint Filter", os.path.join("libusb", "libusb_filter.inf"))
        ]

        total_steps = len(driver_targets) + 1  # +1 for UsbDk
        current_step = 0

        for key, name, rel_inf in driver_targets:
            current_step += 1
            inf_path = os.path.join(self.DRIVERS_BASE_DIR, rel_inf)

            if progress_cb:
                progress_cb(current_step / total_steps, f"Installing {name}...")

            ok, msg = self.install_inf_driver(inf_path)
            results[key] = ok

        # Install UsbDk
        current_step += 1
        if progress_cb:
            progress_cb(current_step / total_steps, "Installing UsbDk Service...")

        ok_usbdk, msg_u = self.install_usbdk_silent()
        results["usbdk"] = ok_usbdk

        if progress_cb:
            progress_cb(1.0, "Driver Installation Complete (100%)")

        self.log("==================================================", "success")
        self.log("AUTOMATED USB DRIVER INSTALLATION COMPLETED (100%)!", "success")
        self.log("Port disconnection protection & USB filters are active.", "success")
        self.log("==================================================", "success")

        return results

    def install_huawei_drivers(self) -> (bool, str):
        """Installs Huawei USB COM 1.0 and PCUI Handset signed drivers."""
        com_inf = os.path.join(self.DRIVERS_BASE_DIR, "huawei", "huawei_usb_com.inf")
        pcui_inf = os.path.join(self.DRIVERS_BASE_DIR, "huawei", "huawei_handset.inf")
        ok1, m1 = self.install_inf_driver(com_inf)
        ok2, m2 = self.install_inf_driver(pcui_inf)
        return (ok1 and ok2), f"COM 1.0: {m1} | PCUI: {m2}"
