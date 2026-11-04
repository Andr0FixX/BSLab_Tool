"""
Driver Manager Modal Dialog.
Provides a live hardware driver detection checklist, one-click silent installer,
and UsbDk / LibUSB filter configuration.
"""

import os
import threading
import customtkinter as ctk
from core.driver_manager import DriverManager

class DriverDialog(ctk.CTkToplevel):
    """Modern modal dialog for automated USB driver management."""

    def __init__(self, master, logger=None):
        super().__init__(master)

        self.title("BS Lab Tool — Automated USB Drivers & LibUSB Subsystem")
        self.geometry("640x520")
        self.resizable(False, False)
        self.configure(fg_color="#0F0F14")
        self.transient(master)
        self.grab_set()

        self.logger = logger
        self.driver_mgr = DriverManager(logger)

        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        # Header
        top_frame = ctk.CTkFrame(self, fg_color="#181822", corner_radius=0, height=54)
        top_frame.pack(fill="x", side="top")

        ctk.CTkLabel(
            top_frame,
            text="🔧 AUTOMATED USB DRIVER & LIBUSB FILTER SUBSYSTEM",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=16, pady=12)

        # Content Card
        self.content_card = ctk.CTkFrame(self, fg_color="#14141B", corner_radius=8)
        self.content_card.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            self.content_card,
            text="SYSTEM DRIVER INTEGRITY STATUS:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        # Checklist rows
        self.lbl_mtk = self._make_status_row(self.content_card, "MediaTek USB VCOM Driver (CDC / Preloader)")
        self.lbl_qc = self._make_status_row(self.content_card, "Qualcomm HS-USB QDLoader 9008 Driver")
        self.lbl_spd = self._make_status_row(self.content_card, "Unisoc SPRD U2S Diag & Flash Driver")
        self.lbl_huawei = self._make_status_row(self.content_card, "Huawei USB COM 1.0 & PCUI Handset Driver")
        self.lbl_usbdk = self._make_status_row(self.content_card, "UsbDk 64-bit Service (Port Disconnection Fix)")
        self.lbl_libusb = self._make_status_row(self.content_card, "LibUSB-Win32 Endpoint Filter Driver")

        # Progress HUD
        hud_box = ctk.CTkFrame(self.content_card, fg_color="#1A1A24", corner_radius=6)
        hud_box.pack(fill="x", padx=16, pady=(14, 8))

        self.lbl_status = ctk.CTkLabel(
            hud_box,
            text="Status: Ready",
            font=ctk.CTkFont(size=11),
            text_color="#CBD5E1"
        )
        self.lbl_status.pack(anchor="w", padx=12, pady=(6, 2))

        self.bar_install = ctk.CTkProgressBar(hud_box, height=8, fg_color="#27272A", progress_color="#059669")
        self.bar_install.pack(fill="x", padx=12, pady=(0, 8))
        self.bar_install.set(0.0)

        # Action Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(0, 16))

        self.btn_install_all = ctk.CTkButton(
            btn_bar,
            text="⚡ Install All Missing Drivers (Silent)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            command=self._start_install_all
        )
        self.btn_install_all.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_rescan = ctk.CTkButton(
            btn_bar,
            text="🔄 Re-Scan",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=90,
            height=38,
            fg_color="#334155",
            hover_color="#1E293B",
            command=self._refresh_status
        )
        self.btn_rescan.pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar,
            text="📁 Open Folder",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=100,
            height=38,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._open_drivers_folder
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar,
            text="✖️ Close",
            font=ctk.CTkFont(size=11),
            width=70,
            height=38,
            fg_color="#1E1E2A",
            command=self.destroy
        ).pack(side="right", padx=(4, 0))

    def _make_status_row(self, parent, label_text):
        row = ctk.CTkFrame(parent, fg_color="#1A1A24", corner_radius=6, height=36)
        row.pack(fill="x", padx=16, pady=3)

        ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11)).pack(side="left", padx=12, pady=6)
        badge = ctk.CTkLabel(
            row,
            text="Checking...",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#94A3B8",
            fg_color="#27272A",
            corner_radius=4,
            padx=8,
            pady=2
        )
        badge.pack(side="right", padx=12, pady=6)
        return badge

    def _refresh_status(self):
        def run():
            st = self.driver_mgr.check_all_driver_status()
            self.after(0, lambda: self._apply_status(st))
        threading.Thread(target=run, daemon=True).start()

    def _apply_status(self, st: dict):
        def set_b(badge, is_ok):
            if is_ok:
                badge.configure(text="✓ INSTALLED", text_color="#34D399", fg_color="#064E3B")
            else:
                badge.configure(text="✗ NOT INSTALLED", text_color="#FCA5A5", fg_color="#7F1D1D")

        set_b(self.lbl_mtk, st.get("mtk", False))
        set_b(self.lbl_qc, st.get("qualcomm", False))
        set_b(self.lbl_spd, st.get("unisoc", False))
        set_b(self.lbl_huawei, st.get("huawei", False))
        set_b(self.lbl_usbdk, st.get("usbdk", False))
        set_b(self.lbl_libusb, st.get("libusb", False))

    def _start_install_all(self):
        self.btn_install_all.configure(state="disabled", text="⏳ INSTALLING DRIVERS...")

        def run():
            def cb(pct, msg):
                self.after(0, lambda: self.bar_install.set(pct))
                self.after(0, lambda: self.lbl_status.configure(text=f"Status: {msg} ({int(pct*100)}%)"))

            res = self.driver_mgr.install_all_drivers(progress_cb=cb)
            self.after(0, self._on_install_done)

        threading.Thread(target=run, daemon=True).start()

    def _on_install_done(self):
        self.btn_install_all.configure(state="normal", text="⚡ Install All Missing Drivers (Silent)")
        self.bar_install.set(1.0)
        self.lbl_status.configure(text="Status: Driver Installation Completed!")
        self._refresh_status()

    def _open_drivers_folder(self):
        d = self.driver_mgr.DRIVERS_BASE_DIR
        if os.path.exists(d):
            os.startfile(d)
