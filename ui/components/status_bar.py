import os
import platform
import subprocess
import webbrowser
from datetime import datetime
import customtkinter as ctk
from ui.theme import Theme

class StatusBar(ctk.CTkFrame):
    """Bottom Status Bar with Global Progress, Device/SoC Status, DevMgr/Drivers shortcuts and Live Clock."""

    def __init__(self, master, logger=None):
        super().__init__(master, height=28, corner_radius=0, fg_color=Theme.BG_HEADER)
        self.pack(fill="x", side="bottom")

        self.logger = logger
        self._build_ui()
        self._update_live_clock()

    def _build_ui(self):
        # 1. Full-width slim progress bar
        self.bar_global = ctk.CTkProgressBar(self, height=3, fg_color=Theme.SURFACE_INPUT, progress_color=Theme.ACCENT_CYAN)
        self.bar_global.pack(fill="x", side="top")
        self.bar_global.set(0.0)

        # 2. Capsules row
        caps_row = ctk.CTkFrame(self, fg_color="transparent")
        caps_row.pack(fill="x", padx=12, pady=4)

        self.lbl_dev_status = ctk.CTkLabel(
            caps_row,
            text="🔴 Waiting / No Device Connected",
            font=Theme.font_bold(size=11),
            text_color="#E57373"
        )
        self.lbl_dev_status.pack(side="left")

        self.lbl_chipset_status = ctk.CTkLabel(
            caps_row,
            text="SoC: MediaTek Helio G37 (MT6765)",
            font=Theme.font_ui(size=11),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_chipset_status.pack(side="left", padx=(15, 10))

        # 3. Community & Developer Support Capsule (WhatsApp, Telegram, Facebook)
        support_frame = ctk.CTkFrame(caps_row, fg_color=Theme.SURFACE_INPUT, corner_radius=5)
        support_frame.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(
            support_frame,
            text="💬 Support:",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#94A3B8"
        ).pack(side="left", padx=(6, 4))

        # WhatsApp Direct Contact Button
        self.btn_whatsapp = ctk.CTkButton(
            support_frame,
            text="🟢 WhatsApp",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#064E3B",
            hover_color="#059669",
            text_color="#34D399",
            border_width=1,
            border_color="#047857",
            corner_radius=4,
            height=20,
            width=76,
            cursor="hand2",
            command=self._open_whatsapp
        )
        self.btn_whatsapp.pack(side="left", padx=2, pady=2)

        # Telegram Community Button
        self.btn_telegram = ctk.CTkButton(
            support_frame,
            text="✈️ Telegram",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0F2B48",
            hover_color="#0284C7",
            text_color="#38BDF8",
            border_width=1,
            border_color="#0369A1",
            corner_radius=4,
            height=20,
            width=76,
            cursor="hand2",
            command=self._open_telegram
        )
        self.btn_telegram.pack(side="left", padx=2, pady=2)

        # Facebook Page Button
        self.btn_facebook = ctk.CTkButton(
            support_frame,
            text="🌐 Facebook",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1E1B4B",
            hover_color="#3B82F6",
            text_color="#93C5FD",
            border_width=1,
            border_color="#2563EB",
            corner_radius=4,
            height=20,
            width=76,
            cursor="hand2",
            command=self._open_facebook
        )
        self.btn_facebook.pack(side="left", padx=(2, 6), pady=2)

        # System Tray Style Digital Clock (12-Hour AM/PM Daylight format with Seconds & Date)
        self.lbl_clock = ctk.CTkLabel(
            caps_row,
            text="",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            fg_color="#181824",
            text_color="#00D2FF",
            corner_radius=4,
            padx=8,
            pady=2
        )
        self.lbl_clock.pack(side="right", padx=(8, 0))

        # Drivers & Fix System Tray Button
        self.btn_drivers = ctk.CTkButton(
            caps_row,
            text="🔧 Drivers",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2A1E14",
            hover_color="#D97706",
            text_color="#FDBA74",
            border_width=1,
            border_color="#5D3A1A",
            corner_radius=4,
            height=20,
            width=68,
            cursor="hand2",
            command=self._open_drivers_fix
        )
        self.btn_drivers.pack(side="right", padx=(4, 0))

        # Device Manager System Tray Button
        self.btn_devmgr = ctk.CTkButton(
            caps_row,
            text="🛠️ DevMgr",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1A233A",
            hover_color="#0284C7",
            text_color="#38BDF8",
            border_width=1,
            border_color="#23385D",
            corner_radius=4,
            height=20,
            width=68,
            cursor="hand2",
            command=self._open_device_manager
        )
        self.btn_devmgr.pack(side="right", padx=(4, 0))

        # Hostname Capsule
        try:
            pc_name = platform.node() or "DESKTOP"
        except Exception:
            pc_name = "DESKTOP"

        self.lbl_hostname = ctk.CTkLabel(
            caps_row,
            text=f"💻 {pc_name}",
            font=ctk.CTkFont(size=10),
            fg_color="#1A1A22",
            text_color="#94A3B8",
            corner_radius=4,
            padx=6,
            pady=2
        )
        self.lbl_hostname.pack(side="right", padx=(8, 0))

        self.lbl_parts_count = ctk.CTkLabel(
            caps_row,
            text="Partitions: 0 Loaded",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.lbl_parts_count.pack(side="right")

    def _update_live_clock(self):
        try:
            now_str = datetime.now().strftime("🕒 %I:%M:%S %p | %d-%b-%Y")
            self.lbl_clock.configure(text=now_str)
        except Exception:
            pass
        self.after(1000, self._update_live_clock)

    def _open_device_manager(self):
        """Quick shortcut to launch Windows Device Manager (devmgmt.msc)."""
        try:
            subprocess.Popen("devmgmt.msc", shell=True)
            if self.logger:
                self.logger.success("[SYSTEM] Windows Device Manager (devmgmt.msc) launched successfully.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SYSTEM] Could not launch Device Manager: {e}")

    def _open_drivers_fix(self):
        """Quick shortcut for USB Drivers & LibUSB Filter diagnostic / folder."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        drivers_dir = os.path.join(base_dir, "drivers")
        os.makedirs(drivers_dir, exist_ok=True)

        if self.logger:
            self.logger.info("==================================================")
            self.logger.info("[DRIVERS & FIX] USB Driver & LibUSB Filter Subsystem")
            self.logger.info(f"[DRIVERS] Directory: {drivers_dir}")

            libusb_path = os.path.join(base_dir, "libusb-1.0.dll")
            if os.path.exists(libusb_path):
                self.logger.success("[DRIVERS] LibUSB Core: libusb-1.0.dll is Present & Ready.")
            else:
                self.logger.warn("[DRIVERS] Warning: libusb-1.0.dll missing in tool root!")

            self.logger.info("[DRIVERS] Opening Drivers folder in Explorer...")
            self.logger.info("==================================================")

        try:
            os.startfile(drivers_dir)
        except Exception:
            try:
                subprocess.Popen(f'explorer "{drivers_dir}"')
            except Exception:
                pass

    def _open_whatsapp(self):
        """Direct WhatsApp support link to wa.me/923048640338."""
        url = "https://wa.me/923048640338"
        try:
            webbrowser.open(url)
            if self.logger:
                self.logger.success(f"[SUPPORT] Opening WhatsApp Direct Support ({url})...")
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SUPPORT] Could not open WhatsApp link: {e}")

    def _open_telegram(self):
        """Official Telegram Channel / Support Group link."""
        url = "https://t.me/BSLabTool"
        try:
            webbrowser.open(url)
            if self.logger:
                self.logger.success(f"[SUPPORT] Opening Telegram Community ({url})...")
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SUPPORT] Could not open Telegram link: {e}")

    def _open_facebook(self):
        """Official Facebook Page / Group link (Placeholder for user page)."""
        url = "https://facebook.com/BSLabTool"
        try:
            webbrowser.open(url)
            if self.logger:
                self.logger.success(f"[SUPPORT] Opening Facebook Page ({url})...")
        except Exception as e:
            if self.logger:
                self.logger.error(f"[SUPPORT] Could not open Facebook link: {e}")

    def set_device_status(self, text: str, text_color: str):
        self.lbl_dev_status.configure(text=text, text_color=text_color)

    def set_chipset_status(self, text: str):
        self.lbl_chipset_status.configure(text=text)

    def set_partitions_count(self, count: int):
        self.lbl_parts_count.configure(text=f"Partitions: {count} Loaded")

    def set_progress(self, progress: float):
        self.bar_global.set(progress)
