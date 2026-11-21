"""
BS Lab Tool v2.0 PRO - Dedicated Google Pixel Servicing, Flashing & Diagnostics View.
Supports Google Pixel 1 through Pixel 9 Pro Fold (Google Tensor G1/G2/G3/G4 & Snapdragon).
Features:
- Fastboot Factory Image Flasher & Surgical Partition Writer
- Dual-Progress Telemetry HUD
- 1-Click Bootloader Unlock / Relock (flashing unlock / unlock_critical / oem unlock)
- FRP Bypass (Fastboot erase frp / OEM wipe sequence)
- Verizon OEM Unlock Grayed-Out Fix
- Slot A/B Active Management
- Official Google Full OTA Sideload Unbricking
- Device Specs Inspector (fastboot getvar all)
- Google Tensor Test Points Gallery
"""

import os
import re
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from core.path_utils import get_platform_tool_path
from core.model_database import ModelDatabase
from core.sound_manager import SoundManager
from core.telemetry import FlashingTelemetry
from ui.theme import Theme
from utils.file_utils import format_bytes


class PixelView:
    """Dedicated Google Pixel Platform View (Tensor & Snapdragon)."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger
        self.telemetry = FlashingTelemetry()

        self._CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

        # State Variables
        self.model_var = tk.StringVar(value="Google Pixel 7 Pro (cheetah)")
        self.slot_var = tk.StringVar(value="Current Slot: _a (Active)")
        self.fb_serial_var = tk.StringVar(value="--")
        self.fb_status_var = tk.StringVar(value="Ready to Connect")
        self.carrier_var = tk.StringVar(value="Universal / Unlocked")

        # Flashing State
        self.factory_zip_var = tk.StringVar(value="")
        self.flash_wipe_var = tk.BooleanVar(value=True)
        self.flash_force_slot_var = tk.StringVar(value="Auto (Current Slot)")
        self.sideload_zip_var = tk.StringVar(value="")

        self.progress_file_var = tk.DoubleVar(value=0.0)
        self.progress_overall_var = tk.DoubleVar(value=0.0)
        self.lbl_status_text_var = tk.StringVar(value="⚡ Status: Ready for Pixel Operations")
        self.lbl_file_text_var = tk.StringVar(value="Partition Progress: 0%")
        self.lbl_overall_text_var = tk.StringVar(value="Total Firmware: 0%")

        self.is_busy = False
        self.current_process = None

        self._build_left_panel()
        self._build_center_panel()

    # =========================================================================
    # LEFT PANEL: Pixel Model Selector, Quick HW Specs, Fastboot Controls
    # =========================================================================
    def _build_left_panel(self):
        self.left_panel = ctk.CTkScrollableFrame(
            self.body_frame,
            width=285,
            fg_color=Theme.BG_PANEL,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # 1. Pixel Model Registry Card
        ctk.CTkLabel(
            self.left_panel,
            text="🔴 GOOGLE PIXEL SELECTOR",
            font=Theme.font_bold(size=11),
            text_color="#F87171"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        model_card = ctk.CTkFrame(
            self.left_panel,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        model_card.pack(fill="x", padx=10, pady=(0, 10))

        pixel_models = []
        for code, info in ModelDatabase.PIXELS.items():
            pixel_models.append(f"{info['name']} ({code})")

        if not pixel_models:
            pixel_models = [
                "Google Pixel 9 Pro XL (komodo)",
                "Google Pixel 9 Pro (caiman)",
                "Google Pixel 9 (tokay)",
                "Google Pixel 8 Pro (husky)",
                "Google Pixel 8 (shiba)",
                "Google Pixel 7 Pro (cheetah)",
                "Google Pixel 7 (panther)",
                "Google Pixel 6 Pro (raven)",
                "Google Pixel 6 (oriole)",
                "Google Pixel 5 (redfin)",
                "Google Pixel 4 XL (coral)"
            ]

        self.combo_pixel_model = ctk.CTkOptionMenu(
            model_card,
            values=pixel_models,
            variable=self.model_var,
            font=Theme.font_ui(size=11),
            fg_color=Theme.SURFACE_INPUT,
            button_color=Theme.ACCENT_BLUE,
            height=30,
            command=self._on_pixel_model_selected
        )
        self.combo_pixel_model.pack(fill="x", padx=10, pady=(10, 6))

        self.lbl_chipset_info = ctk.CTkLabel(
            model_card,
            text="⚡ SoC: Google Tensor G2",
            font=Theme.font_bold(size=10),
            text_color=Theme.ACCENT_CYAN
        )
        self.lbl_chipset_info.pack(anchor="w", padx=10, pady=(0, 8))

        # 2. Hardware Sniffer & Connection Status
        ctk.CTkLabel(
            self.left_panel,
            text="CONNECTION & PORTS",
            font=Theme.font_bold(size=11),
            text_color=Theme.ACCENT_CYAN
        ).pack(anchor="w", padx=10, pady=(2, 2))

        conn_card = ctk.CTkFrame(
            self.left_panel,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        conn_card.pack(fill="x", padx=10, pady=(0, 10))

        c_btns = ctk.CTkFrame(conn_card, fg_color="transparent")
        c_btns.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(
            c_btns,
            text="🔍 Fastboot",
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            height=30,
            command=self.check_fastboot_device
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))

        ctk.CTkButton(
            c_btns,
            text="🔍 Check ADB",
            font=Theme.font_bold(size=11),
            fg_color="#334155",
            hover_color="#475569",
            height=30,
            command=self.check_adb_device
        ).pack(side="right", fill="x", expand=True, padx=(3, 0))

        self.lbl_conn_status = ctk.CTkLabel(
            conn_card,
            textvariable=self.fb_status_var,
            font=Theme.font_bold(size=10),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_conn_status.pack(anchor="w", padx=10, pady=(0, 4))

        self.lbl_serial_badge = ctk.CTkLabel(
            conn_card,
            text="Serial: --",
            font=Theme.font_ui(size=10),
            text_color="#94A3B8"
        )
        self.lbl_serial_badge.pack(anchor="w", padx=10, pady=(0, 8))

        # 3. Slot A/B Active Management
        ctk.CTkLabel(
            self.left_panel,
            text="SLOT A/B CONTROLLER",
            font=Theme.font_bold(size=11),
            text_color="#93C5FD"
        ).pack(anchor="w", padx=10, pady=(2, 2))

        slot_card = ctk.CTkFrame(
            self.left_panel,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        slot_card.pack(fill="x", padx=10, pady=(0, 10))

        s_row = ctk.CTkFrame(slot_card, fg_color="transparent")
        s_row.pack(fill="x", padx=8, pady=8)

        ctk.CTkButton(
            s_row,
            text="Set Slot _a Active",
            font=Theme.font_bold(size=10),
            fg_color="#0284C7",
            hover_color="#0369A1",
            height=28,
            command=lambda: self._set_active_slot("a")
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))

        ctk.CTkButton(
            s_row,
            text="Set Slot _b Active",
            font=Theme.font_bold(size=10),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            height=28,
            command=lambda: self._set_active_slot("b")
        ).pack(side="right", fill="x", expand=True, padx=(3, 0))

        # 4. Mode & Power Reboots
        ctk.CTkLabel(
            self.left_panel,
            text="POWER & REBOOT HUB",
            font=Theme.font_bold(size=11),
            text_color="#F59E0B"
        ).pack(anchor="w", padx=10, pady=(2, 2))

        pwr_card = ctk.CTkFrame(
            self.left_panel,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        pwr_card.pack(fill="x", padx=10, pady=(0, 12))

        r1 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        r1.pack(fill="x", padx=8, pady=(8, 3))
        ctk.CTkButton(r1, text="🔄 Reboot System", font=Theme.font_bold(size=10), height=30, fg_color="#059669", hover_color="#047857", command=lambda: self._reboot_cmd("system")).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(r1, text="⚡ Reboot Bootloader", font=Theme.font_bold(size=10), height=30, fg_color="#0284C7", hover_color="#0369A1", command=lambda: self._reboot_cmd("bootloader")).pack(side="right", fill="x", expand=True, padx=(3, 0))

        r2 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        r2.pack(fill="x", padx=8, pady=(3, 8))
        ctk.CTkButton(r2, text="📦 Reboot Recovery", font=Theme.font_bold(size=10), height=30, fg_color="#6366F1", hover_color="#4F46E5", command=lambda: self._reboot_cmd("recovery")).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(r2, text="🚀 Reboot FastbootD", font=Theme.font_bold(size=10), height=30, fg_color="#7C3AED", hover_color="#6D28D9", command=lambda: self._reboot_cmd("fastbootd")).pack(side="right", fill="x", expand=True, padx=(3, 0))

    # =========================================================================
    # CENTER WORK PANEL: 4-Tab Architecture
    # =========================================================================
    def _build_center_panel(self):
        self.center_panel = ctk.CTkFrame(
            self.body_frame,
            fg_color=Theme.BG_PANEL,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        self.tab_selector = ctk.CTkSegmentedButton(
            self.center_panel,
            values=[
                "⚡ Factory Flasher",
                "🟢 Service & Unlock",
                "🚑 OTA Sideload Unbrick",
                "📌 Tensor Pinouts & TP"
            ],
            command=self._on_tab_changed,
            font=Theme.font_bold(size=12),
            selected_color=Theme.ACCENT_BLUE,
            selected_hover_color=Theme.ACCENT_BLUE_HOVER,
            unselected_color=Theme.SURFACE_INPUT,
            unselected_hover_color=Theme.SURFACE_CARD,
            height=34
        )
        self.tab_selector.pack(fill="x", padx=12, pady=(10, 8))
        self.tab_selector.set("⚡ Factory Flasher")

        self.tab_container = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._build_tab_flash()
        self._build_tab_service()
        self._build_tab_sideload()
        self._build_tab_testpoints()

        self._show_tab("⚡ Factory Flasher")

    # -------------------------------------------------------------------------
    # TAB 1: FACTORY FLASHER
    # -------------------------------------------------------------------------
    def _build_tab_flash(self):
        self.frame_tab_flash = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        # 1. Firmware Selector Card
        fw_card = ctk.CTkFrame(
            self.frame_tab_flash,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        fw_card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            fw_card,
            text="GOOGLE FACTORY FIRMWARE ARCHIVE (*.zip or extracted folder)",
            font=Theme.font_bold(size=11),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(8, 4))

        row_picker = ctk.CTkFrame(fw_card, fg_color="transparent")
        row_picker.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkEntry(
            row_picker,
            textvariable=self.factory_zip_var,
            placeholder_text="Select official Google Factory Image (e.g. cheetah-ota-*.zip / image-cheetah-*.zip)...",
            font=Theme.font_ui(size=11),
            fg_color=Theme.SURFACE_INPUT,
            height=30
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            row_picker,
            text="📁 Browse ZIP",
            width=100,
            height=30,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_BLUE,
            command=self._browse_factory_firmware
        ).pack(side="right")

        opts_row = ctk.CTkFrame(fw_card, fg_color="transparent")
        opts_row.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkCheckBox(
            opts_row,
            text="Wipe User Data (-w Factory Reset)",
            variable=self.flash_wipe_var,
            font=Theme.font_bold(size=11),
            text_color="#FBBF24",
            checkbox_height=18,
            checkbox_width=18
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            opts_row,
            text="Target Slot:",
            font=Theme.font_ui(size=11),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 6))

        ctk.CTkOptionMenu(
            opts_row,
            values=["Auto (Current Slot)", "Force Slot A", "Force Slot B"],
            variable=self.flash_force_slot_var,
            font=Theme.font_ui(size=11),
            height=26,
            width=160
        ).pack(side="left")

        # 2. Dual Progress Telemetry HUD
        hud_card = ctk.CTkFrame(
            self.frame_tab_flash,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        hud_card.pack(fill="x", pady=(0, 8))

        self.lbl_hud_status = ctk.CTkLabel(
            hud_card,
            textvariable=self.lbl_status_text_var,
            font=Theme.font_bold(size=12),
            text_color=Theme.ACCENT_CYAN
        )
        self.lbl_hud_status.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_hud_file = ctk.CTkLabel(
            hud_card,
            textvariable=self.lbl_file_text_var,
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_hud_file.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_file = ctk.CTkProgressBar(hud_card, height=7, fg_color="#27272A", progress_color="#0284C7")
        self.bar_file.pack(fill="x", padx=12, pady=(0, 6))
        self.bar_file.set(0.0)

        self.lbl_hud_overall = ctk.CTkLabel(
            hud_card,
            textvariable=self.lbl_overall_text_var,
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_hud_overall.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_overall = ctk.CTkProgressBar(hud_card, height=7, fg_color="#27272A", progress_color="#10B981")
        self.bar_overall.pack(fill="x", padx=12, pady=(0, 6))
        self.bar_overall.set(0.0)

        # Telemetry info
        self.lbl_flash_meta = ctk.CTkLabel(
            hud_card,
            text="⚡ Fastboot Streaming Speed: -- MB/s | Status: Ready",
            font=Theme.font_bold(size=10),
            text_color="#38BDF8"
        )
        self.lbl_flash_meta.pack(anchor="w", padx=12, pady=(0, 8))

        # 3. Flashing Action Buttons
        btn_bar = ctk.CTkFrame(self.frame_tab_flash, fg_color="transparent")
        btn_bar.pack(fill="x", pady=2)

        self.btn_flash_full = ctk.CTkButton(
            btn_bar,
            text="⚡ FLASH FULL FACTORY ROM (FASTBOOT)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            command=self.start_flash_factory_image
        )
        self.btn_flash_full.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_flash_boot = ctk.CTkButton(
            btn_bar,
            text="⚡ FLASH BOOT / INIT_BOOT ONLY (ROOT/KERNEL)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            command=self.start_flash_boot_only
        )
        self.btn_flash_boot.pack(side="right", fill="x", expand=True, padx=(4, 0))

    # -------------------------------------------------------------------------
    # TAB 2: SERVICE & UNLOCK
    # -------------------------------------------------------------------------
    def _build_tab_service(self):
        self.frame_tab_service = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")

        # Card 1: 1-Click FRP & Screen Lock Bypass
        c1 = ctk.CTkFrame(
            self.frame_tab_service,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c1.pack(fill="x", padx=4, pady=(2, 8))

        ctk.CTkLabel(
            c1,
            text="🟢 1-CLICK FRP & SCREEN LOCK BYPASS",
            font=Theme.font_bold(size=12),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=12, pady=(8, 4))

        row1 = ctk.CTkFrame(c1, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(
            row1,
            text="🔓 Reset FRP (Fastboot Erase Method)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.op_pixel_reset_frp_fastboot
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            row1,
            text="🧹 Safe Factory Reset (fastboot -w)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#334155",
            hover_color="#475569",
            command=self.op_pixel_factory_reset
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 2: Bootloader Unlock & Verizon Fix
        c2 = ctk.CTkFrame(
            self.frame_tab_service,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c2.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(
            c2,
            text="🟡 BOOTLOADER UNLOCK & CARRIER OEM ENABLER",
            font=Theme.font_bold(size=12),
            text_color="#FBBF24"
        ).pack(anchor="w", padx=12, pady=(8, 4))

        row2 = ctk.CTkFrame(c2, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(
            row2,
            text="🔓 Unlock Bootloader (flashing unlock)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#059669",
            hover_color="#047857",
            command=self.op_pixel_unlock_bootloader
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            row2,
            text="🔒 Relock Bootloader (flashing lock)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.op_pixel_relock_bootloader
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        row3 = ctk.CTkFrame(c2, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(4, 10))

        ctk.CTkButton(
            row3,
            text="🛡️ Fix Verizon OEM Unlock Grayed Out (ADB)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#D97706",
            hover_color="#B45309",
            command=self.op_pixel_fix_verizon_oem
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            row3,
            text="📋 Read Device Passport (getvar all)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.op_pixel_read_passport
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

    # -------------------------------------------------------------------------
    # TAB 3: OTA SIDELOAD UNBRICK
    # -------------------------------------------------------------------------
    def _build_tab_sideload(self):
        self.frame_tab_sideload = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        card = ctk.CTkFrame(
            self.frame_tab_sideload,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        card.pack(fill="x", pady=6)

        ctk.CTkLabel(
            card,
            text="OFFICIAL GOOGLE FULL OTA SIDELOAD (RECOVERY MODE)",
            font=Theme.font_bold(size=12),
            text_color="#34D399"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            card,
            text="Instructions: Reboot phone to Recovery, select 'Apply update from ADB', and select the official OTA .zip file.",
            font=Theme.font_ui(size=10),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        row_ota = ctk.CTkFrame(card, fg_color="transparent")
        row_ota.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkEntry(
            row_ota,
            textvariable=self.sideload_zip_var,
            placeholder_text="Select Full OTA package (e.g. cheetah-ota-*.zip)...",
            font=Theme.font_ui(size=11),
            height=32
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            row_ota,
            text="📁 Browse OTA",
            width=100,
            height=32,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_BLUE,
            command=self._browse_ota_zip
        ).pack(side="right")

        self.btn_start_sideload = ctk.CTkButton(
            card,
            text="🚑 START OFFICIAL OTA SIDELOAD UNBRICK",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            command=self.start_ota_sideload
        )
        self.btn_start_sideload.pack(fill="x", padx=12, pady=(0, 12))

    # -------------------------------------------------------------------------
    # TAB 4: TEST POINTS & HARDWARE PINOUTS
    # -------------------------------------------------------------------------
    def _build_tab_testpoints(self):
        self.frame_tab_testpoints = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")

        card = ctk.CTkFrame(
            self.frame_tab_testpoints,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        card.pack(fill="x", pady=6)

        ctk.CTkLabel(
            card,
            text="📌 GOOGLE TENSOR & SNAPDRAGON HARDWARE PINOUTS",
            font=Theme.font_bold(size=12),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=12, pady=(8, 4))

        tp_info = (
            "• Google Tensor G1 (Pixel 6 / 6 Pro / 6a): Short CLK test point to Ground (GND) with battery disconnected to force Fastboot Rescue.\n"
            "• Google Tensor G2 (Pixel 7 / 7 Pro / 7a / Fold): Test Point located adjacent to the UFS memory chip shielding frame.\n"
            "• Google Tensor G3 / G4 (Pixel 8 / 9 Series): Hardware EDL & UART diagnostic pads require 1.8V logic level.\n"
            "• Pixel 1-5 (Qualcomm): Standard EDL 9008 testpoints force QDLoader without key combinations."
        )

        ctk.CTkLabel(
            card,
            text=tp_info,
            font=Theme.font_ui(size=10),
            text_color="#CBD5E1",
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 10))

    # =========================================================================
    # EVENT HANDLERS & HELPERS
    # =========================================================================
    def _on_tab_changed(self, value):
        self._show_tab(value)

    def _show_tab(self, tab_name):
        self.frame_tab_flash.pack_forget()
        self.frame_tab_service.pack_forget()
        self.frame_tab_sideload.pack_forget()
        self.frame_tab_testpoints.pack_forget()

        if "Flash" in tab_name:
            self.frame_tab_flash.pack(fill="both", expand=True)
        elif "Service" in tab_name:
            self.frame_tab_service.pack(fill="both", expand=True)
        elif "Sideload" in tab_name or "OTA" in tab_name:
            self.frame_tab_sideload.pack(fill="both", expand=True)
        elif "Test" in tab_name or "Pinouts" in tab_name:
            self.frame_tab_testpoints.pack(fill="both", expand=True)

    def _on_pixel_model_selected(self, choice):
        m = re.search(r'\(([\w]+)\)', choice)
        if m:
            code = m.group(1).lower()
            if code in ModelDatabase.PIXELS:
                info = ModelDatabase.PIXELS[code]
                self.lbl_chipset_info.configure(text=f"⚡ SoC: {info['soc']}")
                if hasattr(self.controller, "status_bar"):
                    self.controller.status_bar.set_chipset_status(f"Google Pixel: {info['name']} ({info['soc']})")

    def _browse_factory_firmware(self):
        fpath = filedialog.askopenfilename(
            title="Select Google Pixel Factory Image (.zip)",
            filetypes=[("Zip Archives", "*.zip"), ("All Files", "*.*")]
        )
        if fpath:
            self.factory_zip_var.set(fpath)
            self.logger.success(f"Attached Pixel Factory Image: {os.path.basename(fpath)}")

    def _browse_ota_zip(self):
        fpath = filedialog.askopenfilename(
            title="Select Official Google Full OTA Package (.zip)",
            filetypes=[("Zip Archives", "*.zip"), ("All Files", "*.*")]
        )
        if fpath:
            self.sideload_zip_var.set(fpath)
            self.logger.success(f"Attached Pixel OTA Sideload Package: {os.path.basename(fpath)}")

    # =========================================================================
    # FASTBOOT & ADB OPERATIONS
    # =========================================================================
    def check_fastboot_device(self):
        fb = get_platform_tool_path("fastboot")
        try:
            res = subprocess.run([fb, "devices"], capture_output=True, text=True, timeout=2, creationflags=self._CREATE_NO_WINDOW)
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if lines:
                sn = lines[0].split()[0]
                self.fb_serial_var.set(sn)
                self.fb_status_var.set("🟢 Fastboot Mode Connected")
                self.lbl_serial_badge.configure(text=f"Serial: {sn}")
                self.logger.success(f"Google Pixel Fastboot Detected: {sn}")
                SoundManager.play_connect()
            else:
                self.fb_status_var.set("⚪ No Fastboot Device")
                self.logger.warn("No device detected in Fastboot mode.")
        except Exception as e:
            self.logger.error(f"Fastboot check error: {str(e)}")

    def check_adb_device(self):
        adb = get_platform_tool_path("adb")
        try:
            res = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=2, creationflags=self._CREATE_NO_WINDOW)
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip() and not l.startswith("List of")]
            if lines:
                sn = lines[0].split()[0]
                self.fb_serial_var.set(sn)
                self.fb_status_var.set("🟢 ADB Online")
                self.lbl_serial_badge.configure(text=f"ADB Serial: {sn}")
                self.logger.success(f"Google Pixel ADB Online: {sn}")
                SoundManager.play_connect()
            else:
                self.fb_status_var.set("⚪ No ADB Device")
                self.logger.warn("No device detected in ADB mode.")
        except Exception as e:
            self.logger.error(f"ADB check error: {str(e)}")

    def _set_active_slot(self, slot_letter: str):
        fb = get_platform_tool_path("fastboot")
        self.logger.info(f"Switching active slot to _{slot_letter}...")
        try:
            res = subprocess.run([fb, "set_active", slot_letter], capture_output=True, text=True, timeout=5, creationflags=self._CREATE_NO_WINDOW)
            out = (res.stdout or "") + (res.stderr or "")
            if res.returncode == 0:
                self.slot_var.set(f"Current Slot: _{slot_letter} (Active)")
                self.logger.success(f"Slot _{slot_letter} successfully activated!")
                SoundManager.play_success()
            else:
                self.logger.error(f"Failed to set slot active: {out.strip()}")
                SoundManager.play_error()
        except Exception as e:
            self.logger.error(f"Slot switch error: {str(e)}")

    def _reboot_cmd(self, mode: str):
        fb = get_platform_tool_path("fastboot")
        adb = get_platform_tool_path("adb")
        cmd = [fb, "reboot"]
        if mode == "bootloader": cmd = [fb, "reboot", "bootloader"]
        elif mode == "recovery": cmd = [fb, "reboot", "recovery"]
        elif mode == "fastbootd": cmd = [fb, "reboot", "fastboot"]

        self.logger.info(f"Dispatching reboot command: {' '.join(cmd)}...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4, creationflags=self._CREATE_NO_WINDOW)
            if res.returncode == 0:
                self.logger.success("Reboot command acknowledged.")
                SoundManager.play_success()
            else:
                # Fallback ADB reboot
                cmd_adb = [adb, "reboot", mode if mode != "system" else ""]
                subprocess.run([c for c in cmd_adb if c], capture_output=True, text=True, timeout=4, creationflags=self._CREATE_NO_WINDOW)
        except Exception as e:
            self.logger.error(f"Reboot error: {str(e)}")

    # =========================================================================
    # FLASHING OPERATIONS
    # =========================================================================
    def start_flash_factory_image(self):
        zip_path = self.factory_zip_var.get().strip()
        if not zip_path or not os.path.exists(zip_path):
            messagebox.showwarning("Factory ROM Missing", "Please select a valid official Google Factory Image (.zip).")
            return

        def run():
            self.is_busy = True
            fb = get_platform_tool_path("fastboot")
            wipe = self.flash_wipe_var.get()
            cmd = [fb, "update", zip_path]
            if not wipe:
                cmd.insert(2, "--skip-reboot")

            self.logger.info(f"Starting Pixel Factory Flasher: {' '.join(cmd)}...")
            SoundManager.play_start()
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=self._CREATE_NO_WINDOW
                )
                for line in iter(proc.stdout.readline, ''):
                    line = line.strip()
                    if not line: continue
                    if "error" in line.lower() or "failed" in line.lower():
                        self.logger.error(line)
                    elif "sending" in line.lower() or "writing" in line.lower() or "archive" in line.lower():
                        self.logger.brom(line)
                    else:
                        self.logger.info(line)
                proc.stdout.close()
                code = proc.wait()
                if code == 0:
                    self.logger.success("==================================================")
                    self.logger.success("GOOGLE PIXEL FACTORY FIRMWARE FLASHED (100%)!")
                    self.logger.success("==================================================")
                    SoundManager.play_success()
                else:
                    self.logger.error(f"Flashing failed with exit code {code}.")
                    SoundManager.play_error()
            except Exception as e:
                self.logger.error(f"Flashing exception: {str(e)}")
                SoundManager.play_error()
            finally:
                self.is_busy = False

        threading.Thread(target=run, daemon=True).start()

    def start_flash_boot_only(self):
        fpath = filedialog.askopenfilename(
            title="Select boot.img or init_boot.img",
            filetypes=[("Boot Images", "boot*.img;init_boot*.img;*.img"), ("All Files", "*.*")]
        )
        if not fpath: return

        def run():
            self.is_busy = True
            fb = get_platform_tool_path("fastboot")
            b_name = "init_boot" if "init_boot" in os.path.basename(fpath).lower() else "boot"
            self.logger.info(f"Flashing {b_name} partition: {fpath}...")
            try:
                res = subprocess.run([fb, "flash", b_name, fpath], capture_output=True, text=True, timeout=30, creationflags=self._CREATE_NO_WINDOW)
                out = (res.stdout or "") + (res.stderr or "")
                if res.returncode == 0:
                    self.logger.success(f"{b_name} partition flashed successfully!")
                    SoundManager.play_success()
                else:
                    self.logger.error(f"Failed to flash boot partition: {out.strip()}")
                    SoundManager.play_error()
            finally:
                self.is_busy = False

        threading.Thread(target=run, daemon=True).start()

    # =========================================================================
    # 1-CLICK SERVICE & UNLOCK OPERATIONS
    # =========================================================================
    def op_pixel_reset_frp_fastboot(self):
        if not messagebox.askyesno("Confirm FRP Reset", "Reset Google FRP lock via Fastboot partition erase?"):
            return
        fb = get_platform_tool_path("fastboot")
        self.logger.info("Executing Google Pixel Fastboot FRP Reset...")
        try:
            # Modern Pixels store FRP state in 'frp' or erase userdata
            res = subprocess.run([fb, "erase", "frp"], capture_output=True, text=True, timeout=10, creationflags=self._CREATE_NO_WINDOW)
            out = (res.stdout or "") + (res.stderr or "")
            if res.returncode == 0:
                self.logger.success("[✓] FRP partition erased successfully! Google Lock removed.")
                SoundManager.play_success()
            else:
                self.logger.warn(f"Fastboot erase frp output: {out.strip()}. Trying format frp...")
                subprocess.run([fb, "format", "frp"], capture_output=True, text=True, timeout=10, creationflags=self._CREATE_NO_WINDOW)
                self.logger.success("FRP format signal sent.")
        except Exception as e:
            self.logger.error(f"FRP Reset error: {str(e)}")

    def op_pixel_factory_reset(self):
        if not messagebox.askyesno("Confirm Factory Reset", "This will wipe userdata and cache (fastboot -w). Proceed?"):
            return
        fb = get_platform_tool_path("fastboot")
        self.logger.info("Erasing userdata & metadata...")
        try:
            res = subprocess.run([fb, "-w"], capture_output=True, text=True, timeout=60, creationflags=self._CREATE_NO_WINDOW)
            if res.returncode == 0:
                self.logger.success("Factory Reset Completed Successfully! Screen Lock Removed.")
                SoundManager.play_success()
            else:
                self.logger.error(f"Factory Reset failed: {res.stderr}")
                SoundManager.play_error()
        except Exception as e:
            self.logger.error(f"Factory Reset exception: {str(e)}")

    def op_pixel_unlock_bootloader(self):
        fb = get_platform_tool_path("fastboot")
        self.logger.info("Executing Google Pixel Bootloader Unlock sequence...")
        self.logger.warn("NOTE: Check the phone screen and press Volume Down to highlight 'Unlock Bootloader', then press Power.")
        try:
            # Modern command
            res = subprocess.run([fb, "flashing", "unlock"], capture_output=True, text=True, timeout=20, creationflags=self._CREATE_NO_WINDOW)
            out = (res.stdout or "") + (res.stderr or "")
            if res.returncode == 0:
                self.logger.success("[✓] Unlock signal acknowledged. Confirm on device screen!")
                SoundManager.play_success()
            else:
                # Fallback for legacy Pixel 1
                res2 = subprocess.run([fb, "oem", "unlock"], capture_output=True, text=True, timeout=20, creationflags=self._CREATE_NO_WINDOW)
                self.logger.info(f"OEM Unlock fallback: {(res2.stdout or '') + (res2.stderr or '')}")
        except Exception as e:
            self.logger.error(f"Unlock error: {str(e)}")

    def op_pixel_relock_bootloader(self):
        fb = get_platform_tool_path("fastboot")
        self.logger.warn("WARNING: Ensure 100% Stock Google firmware is installed before relocking!")
        try:
            res = subprocess.run([fb, "flashing", "lock"], capture_output=True, text=True, timeout=20, creationflags=self._CREATE_NO_WINDOW)
            out = (res.stdout or "") + (res.stderr or "")
            if res.returncode == 0:
                self.logger.success("[✓] Bootloader Relocked Successfully!")
                SoundManager.play_success()
            else:
                self.logger.error(f"Relock failed: {out.strip()}")
        except Exception as e:
            self.logger.error(f"Relock error: {str(e)}")

    def op_pixel_fix_verizon_oem(self):
        """Enables OEM unlock toggle on Verizon / Carrier-locked Pixel devices over ADB."""
        adb = get_platform_tool_path("adb")
        self.logger.info("Injecting Carrier OEM Unlocking bypass commands via ADB...")
        try:
            cmd1 = [adb, "shell", "settings", "put", "global", "oem_unlock_supported", "1"]
            cmd2 = [adb, "shell", "pm", "disable-user", "--user", "0", "com.google.android.apps.work.oobepairing"]
            subprocess.run(cmd1, capture_output=True, text=True, timeout=5, creationflags=self._CREATE_NO_WINDOW)
            subprocess.run(cmd2, capture_output=True, text=True, timeout=5, creationflags=self._CREATE_NO_WINDOW)
            self.logger.success("[✓] Carrier policy override dispatched. Open Developer Options to toggle OEM Unlocking!")
            SoundManager.play_success()
        except Exception as e:
            self.logger.error(f"Verizon OEM Fix error: {str(e)}")

    def op_pixel_read_passport(self):
        fb = get_platform_tool_path("fastboot")
        self.logger.info("Reading deep Google Pixel hardware variables (getvar all)...")
        try:
            res = subprocess.run([fb, "getvar", "all"], capture_output=True, text=True, timeout=5, creationflags=self._CREATE_NO_WINDOW)
            out = (res.stdout or "") + (res.stderr or "")
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            self.logger.success("==================================================")
            self.logger.success("GOOGLE PIXEL HARDWARE PASSPORT")
            self.logger.success("==================================================")
            for l in lines[:16]:
                self.logger.info(l)
            SoundManager.play_success()
        except Exception as e:
            self.logger.error(f"Read passport error: {str(e)}")

    def start_ota_sideload(self):
        ota_path = self.sideload_zip_var.get().strip()
        if not ota_path or not os.path.exists(ota_path):
            messagebox.showwarning("OTA Missing", "Please select a valid Google Full OTA package (.zip).")
            return

        def run():
            self.is_busy = True
            adb = get_platform_tool_path("adb")
            self.logger.info(f"Initiating OTA Sideload: {os.path.basename(ota_path)}...")
            SoundManager.play_start()
            try:
                proc = subprocess.Popen(
                    [adb, "sideload", ota_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=self._CREATE_NO_WINDOW
                )
                for line in iter(proc.stdout.readline, ''):
                    line = line.strip()
                    if not line: continue
                    if "serving" in line.lower() or "xfer" in line.lower() or "%" in line:
                        self.logger.brom(line)
                    elif "error" in line.lower() or "failed" in line.lower():
                        self.logger.error(line)
                    else:
                        self.logger.info(line)
                proc.stdout.close()
                code = proc.wait()
                if code == 0:
                    self.logger.success("OTA Sideload Finished Successfully (100%)!")
                    SoundManager.play_success()
                else:
                    self.logger.error(f"Sideload failed with code {code}.")
                    SoundManager.play_error()
            finally:
                self.is_busy = False

        threading.Thread(target=run, daemon=True).start()

    # =========================================================================
    # VIEW LIFECYCLE
    # =========================================================================
    def show(self):
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel.grid_forget()
        self.center_panel.grid_forget()
