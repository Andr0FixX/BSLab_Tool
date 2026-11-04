"""
BS Lab Tool v2.0 PRO - Dedicated Samsung Odin Flasher & MTP/Modem Servicing View.
Features 4-File Flashing (BL/AP/CP/CSC/PIT), Auto-Folder Firmware Matcher, Dual-Progress HUD,
Samsung Test Mode Services, and PIT Partition Inspector.
"""

import os
import re
import glob
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from engines.samsung.odin_protocol import OdinProtocolEngine, PitParser, PitEntry
from engines.samsung.samsung_modem import SamsungModemEngine
from core.sound_manager import SoundManager
from ui.theme import Theme
from core.path_utils import get_resource_path


class SamsungView:
    """Dedicated Samsung Platform View (Odin Flasher, Modem Diagnostics & Services)."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # Engines
        self.odin_engine = OdinProtocolEngine(logger=self.logger)
        self.modem_engine = SamsungModemEngine(logger=self.logger)

        # State Variables
        self.port_var = tk.StringVar(value="Auto-Detect (Samsung Port)")
        self.slot_bl_var = tk.StringVar()
        self.slot_ap_var = tk.StringVar()
        self.slot_cp_var = tk.StringVar()
        self.slot_csc_var = tk.StringVar()
        self.slot_pit_var = tk.StringVar()

        self.opt_auto_reboot = tk.BooleanVar(value=True)
        self.opt_f_reset_time = tk.BooleanVar(value=True)
        self.opt_repartition = tk.BooleanVar(value=False)
        self.opt_nand_erase = tk.BooleanVar(value=False)

        # CSC & Knox Guard State Variables
        self.csc_choice_var = tk.StringVar(value="INS (India - Call Recording)")
        self.csc_custom_var = tk.StringVar(value="")
        self.csc_reboot_var = tk.BooleanVar(value=True)
        self.lbl_kg_status_var = tk.StringVar(value="Knox Guard: Ready to Inspect")
        self.lbl_warranty_var = tk.StringVar(value="Warranty: 0x0")
        self.lbl_frp_var = tk.StringVar(value="FRP: Not Audited")

        self.progress_file_var = tk.DoubleVar(value=0.0)
        self.progress_total_var = tk.DoubleVar(value=0.0)
        self.lbl_file_status_var = tk.StringVar(value="Idle - Ready for Firmware")
        self.lbl_total_status_var = tk.StringVar(value="Total Progress: 0%")

        self.is_flashing = False

        self._build_left_panel()
        self._build_center_panel()

    # =========================================================================
    # LEFT PANEL: Device Detection, Port Scanner, Power Modes, Odin Options
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

        # 1. Device Detection & Odin Port Card
        ctk.CTkLabel(self.left_panel, text="SAMSUNG PORTS & DETECT", font=Theme.font_bold(size=11), text_color=Theme.ACCENT_CYAN).pack(anchor="w", padx=10, pady=(8, 2))
        stat_card = ctk.CTkFrame(
            self.left_panel, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        stat_card.pack(fill="x", padx=10, pady=(0, 10))

        btn_row = ctk.CTkFrame(stat_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(btn_row, text="🔍 Odin Port", font=Theme.font_bold(size=11), fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, height=30, command=self._scan_odin_ports).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(btn_row, text="🔍 Modem Port", font=Theme.font_bold(size=11), fg_color="#334155", hover_color="#475569", height=30, command=self._scan_modem_ports).pack(side="right", fill="x", expand=True, padx=(3, 0))

        self.lbl_samsung_port = ctk.CTkLabel(
            stat_card,
            text="● Port: Ready to Scan",
            font=Theme.font_bold(size=10),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_samsung_port.pack(anchor="w", padx=10, pady=(0, 8))

        # 2. Power & Mode Switcher
        ctk.CTkLabel(self.left_panel, text="POWER & MODE SWITCHER", font=Theme.font_bold(size=11), text_color=Theme.ACCENT_GOLD).pack(anchor="w", padx=10, pady=(2, 2))
        pwr_card = ctk.CTkFrame(
            self.left_panel, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        pwr_card.pack(fill="x", padx=10, pady=(0, 10))

        p1 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        p1.pack(fill="x", padx=8, pady=(8, 3))
        ctk.CTkButton(p1, text="🔄 Reboot System", font=Theme.font_bold(size=10), height=30, fg_color=Theme.ACCENT_GREEN, hover_color=Theme.ACCENT_GREEN_HOVER, command=self._reboot_system).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(p1, text="⚡ Download Mode", font=Theme.font_bold(size=10), height=30, fg_color="#2563EB", hover_color="#1D4ED8", command=self._reboot_download).pack(side="right", fill="x", expand=True, padx=(3, 0))

        p2 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        p2.pack(fill="x", padx=8, pady=(3, 8))
        ctk.CTkButton(p2, text="💥 Soft Reset", font=Theme.font_bold(size=10), height=30, fg_color="#334155", hover_color="#475569", command=self._soft_reset).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(p2, text="🔌 Recovery Mode", font=Theme.font_bold(size=10), height=30, fg_color="#7C3AED", hover_color="#6D28D9", command=self._reboot_recovery).pack(side="right", fill="x", expand=True, padx=(3, 0))

        # 3. Odin Flashing Options
        ctk.CTkLabel(self.left_panel, text="ODIN FLASH PARAMETERS", font=Theme.font_bold(size=11), text_color="#A5B4FC").pack(anchor="w", padx=10, pady=(2, 2))
        opt_card = ctk.CTkFrame(
            self.left_panel, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        opt_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkCheckBox(opt_card, text="Auto Reboot (Standard)", variable=self.opt_auto_reboot, font=ctk.CTkFont(size=10), checkbox_height=18, checkbox_width=18).pack(anchor="w", padx=10, pady=(8, 4))
        ctk.CTkCheckBox(opt_card, text="F. Reset Time", variable=self.opt_f_reset_time, font=ctk.CTkFont(size=10), checkbox_height=18, checkbox_width=18).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(opt_card, text="Re-Partition (Requires PIT)", variable=self.opt_repartition, font=ctk.CTkFont(size=10), checkbox_height=18, checkbox_width=18).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(opt_card, text="NAND Erase All (Dangerous)", variable=self.opt_nand_erase, font=ctk.CTkFont(size=10), text_color="#F87171", checkbox_height=18, checkbox_width=18).pack(anchor="w", padx=10, pady=(4, 8))

        # 4. Official PIT Partition Table Selector
        ctk.CTkLabel(self.left_panel, text="OFFICIAL PIT SELECTOR (485+ PITS)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(2, 2))
        pit_card = ctk.CTkFrame(self.left_panel, fg_color="#1A1A22", corner_radius=6)
        pit_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(pit_card, text="Quick Galaxy Model Match:", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=10, pady=(6, 2))

        self.pit_model_var = tk.StringVar(value="Select Galaxy PIT...")
        self.pit_model_menu = ctk.CTkOptionMenu(
            pit_card,
            values=self._get_pit_options(),
            variable=self.pit_model_var,
            fg_color="#059669",
            button_hover_color="#047857",
            height=30,
            command=self._on_pit_selected
        )
        self.pit_model_menu.pack(fill="x", padx=10, pady=(0, 8))

    def _get_pit_options(self) -> list:
        pit_dir = get_resource_path("loaders", "samsung", "pit")
        if not os.path.exists(pit_dir):
            return ["No PIT files found"]
        files = [f for f in os.listdir(pit_dir) if f.lower().endswith(".pit")]
        popular = [
            "A025F (Galaxy A02s)",
            "A032F (Galaxy A03 Core)",
            "A035F (Galaxy A03)",
            "A037F (Galaxy A03s)",
            "A125F (Galaxy A12)",
            "A127F (Galaxy A12 Nacho)",
            "A135F (Galaxy A13)",
            "A225F (Galaxy A22)",
            "A325F (Galaxy A32)",
            "A515F (Galaxy A51)",
            "A525F (Galaxy A52)",
            "A715F (Galaxy A71)"
        ]
        return ["Select Galaxy PIT..."] + popular + files[:15]

    def _on_pit_selected(self, choice: str):
        if choice.startswith("Select"):
            return
        pit_dir = get_resource_path("loaders", "samsung", "pit")
        if not os.path.exists(pit_dir):
            return
        model_code = choice.split()[0].strip()
        matched = None
        for f in os.listdir(pit_dir):
            if f.lower() == choice.lower():
                matched = os.path.join(pit_dir, f)
                break
            if f.lower().startswith(model_code.lower()):
                matched = os.path.join(pit_dir, f)
                break
        if matched and os.path.exists(matched):
            self.slot_pit_var.set(matched)
            self.opt_repartition.set(True)
            self.logger.success(f"Attached Official Samsung PIT: {os.path.basename(matched)}")
            self.logger.info("Re-Partition option auto-enabled for repair flashing.")

    # =========================================================================
    # CENTER PANEL: Segmented Tabs (4-File Odin, Diagnostics, PIT Viewer)
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
            values=["⚡ 4-File Odin Flasher", "🛠️ Diagnostics & Services", "📋 PIT Partition Viewer"],
            command=self._on_tab_changed,
            font=Theme.font_bold(size=11),
            selected_color=Theme.ACCENT_BLUE,
            selected_hover_color=Theme.ACCENT_BLUE_HOVER,
            unselected_color=Theme.SURFACE_INPUT,
            unselected_hover_color=Theme.SURFACE_CARD,
            height=34
        )
        self.tab_selector.pack(fill="x", padx=12, pady=(10, 8))
        self.tab_selector.set("⚡ 4-File Odin Flasher")

        self.tab_container = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # TAB 1: 4-File Odin Flasher
        self._build_flasher_tab()

        # TAB 2: Diagnostics & Services
        self._build_services_tab()

        # TAB 3: PIT Viewer
        self._build_pit_tab()

        self._show_tab("⚡ 4-File Odin Flasher")

    def _build_flasher_tab(self):
        self.frame_flasher = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")

        # Header banner with Auto-Load button
        top_bar = ctk.CTkFrame(
            self.frame_flasher, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        top_bar.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            top_bar,
            text="⚡ High-Speed Samsung 4-File Odin Protocol Flasher (BL / AP / CP / CSC / PIT)",
            font=Theme.font_bold(size=11),
            text_color=Theme.ACCENT_CYAN
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            top_bar,
            text="📁 Auto-Load Firmware Folder",
            height=28,
            font=Theme.font_bold(size=10),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self._auto_load_firmware_folder
        ).pack(side="right", padx=10, pady=6)

        # Slots Table Frame
        slots_card = ctk.CTkFrame(
            self.frame_flasher, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        slots_card.pack(fill="x", pady=(0, 10))

        # BL Slot
        self._create_slot_row(slots_card, "BL", "Bootloader Package", self.slot_bl_var, "#0284C7", 0)
        # AP Slot
        self._create_slot_row(slots_card, "AP", "System & Core Data", self.slot_ap_var, "#7C3AED", 1)
        # CP Slot
        self._create_slot_row(slots_card, "CP", "Modem / Radio Baseband", self.slot_cp_var, "#D97706", 2)
        # CSC Slot
        self._create_slot_row(slots_card, "CSC", "Country Software / Region", self.slot_csc_var, "#059669", 3)
        # PIT Slot
        self._create_slot_row(slots_card, "PIT", "Partition Information Table (Optional)", self.slot_pit_var, "#475569", 4)

        # Dual Progress Bars HUD
        hud_card = ctk.CTkFrame(
            self.frame_flasher, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        hud_card.pack(fill="x", pady=(0, 10))

        # File Progress
        fp_lbl_row = ctk.CTkFrame(hud_card, fg_color="transparent")
        fp_lbl_row.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(fp_lbl_row, text="CURRENT FILE / PARTITION:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94A3B8").pack(side="left")
        self.lbl_file_status = ctk.CTkLabel(fp_lbl_row, textvariable=self.lbl_file_status_var, font=ctk.CTkFont(size=10), text_color="#38BDF8")
        self.lbl_file_status.pack(side="right")

        self.bar_file = ctk.CTkProgressBar(hud_card, height=10, corner_radius=4, fg_color="#272736", progress_color="#0284C7")
        self.bar_file.pack(fill="x", padx=12, pady=(0, 8))
        self.bar_file.set(0.0)

        # Total Progress
        tp_lbl_row = ctk.CTkFrame(hud_card, fg_color="transparent")
        tp_lbl_row.pack(fill="x", padx=12, pady=(2, 2))
        ctk.CTkLabel(tp_lbl_row, text="OVERALL FIRMWARE FLASH:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94A3B8").pack(side="left")
        self.lbl_total_status = ctk.CTkLabel(tp_lbl_row, textvariable=self.lbl_total_status_var, font=ctk.CTkFont(size=10, weight="bold"), text_color="#34D399")
        self.lbl_total_status.pack(side="right")

        self.bar_total = ctk.CTkProgressBar(hud_card, height=14, corner_radius=5, fg_color="#272736", progress_color="#10B981")
        self.bar_total.pack(fill="x", padx=12, pady=(0, 10))
        self.bar_total.set(0.0)

        # Control Action Buttons Row
        action_row = ctk.CTkFrame(self.frame_flasher, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 10))

        self.btn_flash = ctk.CTkButton(
            action_row,
            text="⚡ START ODIN FLASH",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=self._start_odin_flash
        )
        self.btn_flash.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_launch_odin = ctk.CTkButton(
            action_row,
            text="🚀 LAUNCH ODIN3 ENGINE",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self._launch_official_odin
        )
        self.btn_launch_odin.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_abort = ctk.CTkButton(
            action_row,
            text="🛑 ABORT",
            width=100,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self._abort_flash
        )
        self.btn_abort.pack(side="right", padx=(6, 0))

    def _create_slot_row(self, parent, slot_tag, placeholder, var, btn_color, row_idx):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=5)

        # Tag button
        btn_tag = ctk.CTkButton(
            f,
            text=slot_tag,
            width=50,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=btn_color,
            command=lambda: self._browse_slot_file(slot_tag, var)
        )
        btn_tag.pack(side="left", padx=(0, 8))

        # Path entry
        entry = ctk.CTkEntry(
            f,
            textvariable=var,
            placeholder_text=f"Select {placeholder} (*.tar, *.tar.md5, *.pit)...",
            height=30,
            font=ctk.CTkFont(size=10),
            fg_color="#0F0F12"
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # File browse icon
        ctk.CTkButton(
            f,
            text="📁",
            width=32,
            height=30,
            fg_color="#272736",
            hover_color="#334155",
            command=lambda: self._browse_slot_file(slot_tag, var)
        ).pack(side="left", padx=(0, 4))

        # Clear icon
        ctk.CTkButton(
            f,
            text="✕",
            width=28,
            height=30,
            fg_color="#1E1E28",
            hover_color="#DC2626",
            command=lambda: var.set("")
        ).pack(side="right")

    def _build_services_tab(self):
        self.frame_services = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")

        hdr = ctk.CTkFrame(
            self.frame_services, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            hdr,
            text="🛠️ Samsung MTP, Modem AT & Factory Diagnostic Test Mode Services",
            font=Theme.font_bold(size=11),
            text_color=Theme.ACCENT_CYAN
        ).pack(anchor="w", padx=10, pady=8)

        # Card 1: Read Info via Modem AT
        c1 = ctk.CTkFrame(
            self.frame_services, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c1.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(c1, text="READ SAMSUNG DEVICE INFORMATION (MODEM / MTP)", font=Theme.font_bold(size=11), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(c1, text="Connect Samsung phone powered ON via USB to read Model, CSC, PDA and Serial.", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(0, 8))
        
        ctk.CTkButton(
            c1,
            text="📱 Read Full Samsung Info (AT+DEVCONINFO)",
            height=36,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=self._read_samsung_info
        ).pack(fill="x", padx=12, pady=(0, 10))

        # Card 2: Samsung Test Mode Service (*#0*#)
        c2 = ctk.CTkFrame(
            self.frame_services, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c2.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(c2, text="FACTORY TEST MODE (*#0*#) SERVICE ROUTINE", font=Theme.font_bold(size=11), text_color=Theme.ACCENT_GOLD).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(c2, text="Dial *#0*# on Emergency Call screen, then click execute to enable debugging and complete setup.", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            c2,
            text="🔓 Execute Samsung Factory Test Service (*#0*#)",
            height=38,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            command=self._execute_test_mode
        ).pack(fill="x", padx=12, pady=(0, 10))

        # Card 3: Download Mode Switcher
        c3 = ctk.CTkFrame(
            self.frame_services, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c3.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(c3, text="FORCE REBOOT TO DOWNLOAD MODE (ODIN MODE)", font=Theme.font_bold(size=11), text_color="#38BDF8").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(c3, text="Send modem switch packet to reboot phone into Samsung Download Mode without key combos.", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            c3,
            text="🚀 Reboot Device to Download Mode (AT+REBOOT=2)",
            height=36,
            font=Theme.font_bold(size=11),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self._reboot_download
        ).pack(fill="x", padx=12, pady=(0, 10))

        # Card 4: Samsung Free MTP CSC Changer (Instant Call Recording & Region Switch)
        c4 = ctk.CTkFrame(
            self.frame_services, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c4.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(c4, text="SAMSUNG FREE MTP CSC CHANGER (NO DATA LOSS / NO ROOT)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#10B981").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(c4, text="Enable Native Call Recording or change carrier CSC in 1-Click via standard MTP/Modem mode.", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(0, 8))

        csc_row = ctk.CTkFrame(c4, fg_color="transparent")
        csc_row.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(csc_row, text="Target CSC:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#CBD5E1").pack(side="left", padx=(0, 6))
        self.menu_csc = ctk.CTkOptionMenu(
            csc_row,
            values=[
                "INS (India - Call Recording)",
                "TUR (Turkey - Call Recording)",
                "EGY (Egypt - Call Recording)",
                "THL (Thailand - Call Recording)",
                "SEK (Ukraine - Call Recording)",
                "PAK (Pakistan)",
                "MID (Middle East)",
                "KSA (Saudi Arabia)",
                "XAA (USA Unlocked)",
                "EUX (Europe Universal)"
            ],
            variable=self.csc_choice_var,
            width=210,
            height=28,
            font=ctk.CTkFont(size=10),
            fg_color="#047857",
            button_hover_color="#065F46"
        )
        self.menu_csc.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(csc_row, text="Or Custom:", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(side="left", padx=(0, 4))
        self.entry_custom_csc = ctk.CTkEntry(
            csc_row,
            textvariable=self.csc_custom_var,
            placeholder_text="e.g. BTC",
            width=65,
            height=28,
            font=ctk.CTkFont(size=10),
            fg_color="#0F0F12"
        )
        self.entry_custom_csc.pack(side="left", padx=(0, 8))

        ctk.CTkCheckBox(
            csc_row,
            text="Auto-Reboot",
            variable=self.csc_reboot_var,
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        ).pack(side="left")

        csc_btn_row = ctk.CTkFrame(c4, fg_color="transparent")
        csc_btn_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            csc_btn_row,
            text="🔍 Read Current CSC",
            height=34,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._read_csc
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            csc_btn_row,
            text="⚡ 1-Click Change CSC (Apply Region)",
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=self._change_csc
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 5: Knox Guard (KG) & Security State Inspector
        c5 = ctk.CTkFrame(
            self.frame_services, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        c5.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(c5, text="SAMSUNG KNOX GUARD (KG) & PRE-FLASH SECURITY AUDIT", font=Theme.font_bold(size=11), text_color="#F43F5E").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(c5, text="Inspect KG Lock State (Active/Prenormal/Completed), Knox Trip Bit (0x0/0x1), and FRP Status.", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(0, 8))

        sec_badges = ctk.CTkFrame(c5, fg_color=Theme.SURFACE_INPUT, corner_radius=6, border_width=1, border_color=Theme.BORDER_CARD)
        sec_badges.pack(fill="x", padx=12, pady=(0, 8))

        self.lbl_kg_display = ctk.CTkLabel(sec_badges, textvariable=self.lbl_kg_status_var, font=ctk.CTkFont(size=10, weight="bold"), text_color="#FB7185")
        self.lbl_kg_display.pack(side="left", padx=10, pady=6)

        self.lbl_warranty_display = ctk.CTkLabel(sec_badges, textvariable=self.lbl_warranty_var, font=ctk.CTkFont(size=10), text_color="#38BDF8")
        self.lbl_warranty_display.pack(side="left", padx=10, pady=6)

        self.lbl_frp_display = ctk.CTkLabel(sec_badges, textvariable=self.lbl_frp_var, font=ctk.CTkFont(size=10), text_color="#FBBF24")
        self.lbl_frp_display.pack(side="right", padx=10, pady=6)

        ctk.CTkButton(
            c5,
            text="🛡️ Deep Security & Knox Guard (KG) Audit",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#BE123C",
            hover_color="#9F1239",
            command=self._audit_knox_guard
        ).pack(fill="x", padx=12, pady=(0, 10))

    def _build_pit_tab(self):
        self.frame_pit = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        top = ctk.CTkFrame(self.frame_pit, fg_color="#1C1C24", corner_radius=6)
        top.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(top, text="📋 Samsung PIT (Partition Information Table) Inspector", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00D2FF").pack(side="left", padx=10, pady=8)
        ctk.CTkButton(top, text="📂 Load PIT File", height=28, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#0284C7", command=self._load_pit_file).pack(side="right", padx=10, pady=6)

        # PIT Table Treeview
        tree_frame = ctk.CTkFrame(self.frame_pit, fg_color="#141418", corner_radius=6)
        tree_frame.pack(fill="both", expand=True)

        cols = ("name", "filename", "size_mb", "blk_start", "blk_count", "dev_type")
        self.pit_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")

        self.pit_tree.heading("name", text="Partition Name")
        self.pit_tree.heading("filename", text="Image Filename")
        self.pit_tree.heading("size_mb", text="Size (MB)")
        self.pit_tree.heading("blk_start", text="Block Start")
        self.pit_tree.heading("blk_count", text="Block Count")
        self.pit_tree.heading("dev_type", text="Device Type")

        self.pit_tree.column("name", width=130, anchor="w")
        self.pit_tree.column("filename", width=140, anchor="w")
        self.pit_tree.column("size_mb", width=90, anchor="e")
        self.pit_tree.column("blk_start", width=100, anchor="e")
        self.pit_tree.column("blk_count", width=100, anchor="e")
        self.pit_tree.column("dev_type", width=90, anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.pit_tree.yview)
        self.pit_tree.configure(yscrollcommand=sb.set)

        self.pit_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.pit_tree.tag_configure("even", background=Theme.TABLE_ROW_EVEN)
        self.pit_tree.tag_configure("odd", background=Theme.TABLE_ROW_ODD)

    # =========================================================================
    # TAB SWITCHING
    # =========================================================================
    def _show_tab(self, tab_name):
        self.frame_flasher.pack_forget()
        self.frame_services.pack_forget()
        self.frame_pit.pack_forget()

        if "Odin Flasher" in tab_name:
            self.frame_flasher.pack(fill="both", expand=True)
        elif "Diagnostics" in tab_name:
            self.frame_services.pack(fill="both", expand=True)
        elif "PIT" in tab_name:
            self.frame_pit.pack(fill="both", expand=True)

    def _on_tab_changed(self, value):
        self._show_tab(value)

    # =========================================================================
    # ACTIONS & HANDLERS
    # =========================================================================
    def _browse_slot_file(self, slot_tag: str, var: tk.StringVar):
        exts = [("Samsung Tar / Tar.MD5", "*.tar.md5;*.tar"), ("All Files", "*.*")]
        if slot_tag == "PIT":
            exts = [("PIT Binary", "*.pit"), ("All Files", "*.*")]

        f = filedialog.askopenfilename(title=f"Select Samsung {slot_tag} File", filetypes=exts)
        if f:
            var.set(f)
            self.logger.info(f"Loaded {slot_tag}: {os.path.basename(f)}")

    def _auto_load_firmware_folder(self):
        folder = filedialog.askdirectory(title="Select Extracted Samsung Firmware Folder")
        if not folder:
            return

        self.logger.info(f"Scanning folder for Samsung 4-File firmware: {folder}")
        files = glob.glob(os.path.join(folder, "*.*"))

        matched = 0
        for f in files:
            bn = os.path.basename(f).upper()
            if bn.endswith(".TAR.MD5") or bn.endswith(".TAR"):
                if bn.startswith("BL_") or "BOOTLOADER" in bn:
                    self.slot_bl_var.set(f)
                    self.logger.success(f"  [✓] Auto-Assigned BL  -> {os.path.basename(f)}")
                    matched += 1
                elif bn.startswith("AP_") or bn.startswith("PDA_"):
                    self.slot_ap_var.set(f)
                    self.logger.success(f"  [✓] Auto-Assigned AP  -> {os.path.basename(f)}")
                    matched += 1
                elif bn.startswith("CP_") or bn.startswith("MODEM_") or bn.startswith("PHONE_"):
                    self.slot_cp_var.set(f)
                    self.logger.success(f"  [✓] Auto-Assigned CP  -> {os.path.basename(f)}")
                    matched += 1
                elif bn.startswith("CSC_") or bn.startswith("HOME_CSC_"):
                    self.slot_csc_var.set(f)
                    self.logger.success(f"  [✓] Auto-Assigned CSC -> {os.path.basename(f)}")
                    matched += 1
            elif bn.endswith(".PIT"):
                self.slot_pit_var.set(f)
                self.logger.success(f"  [✓] Auto-Assigned PIT -> {os.path.basename(f)}")
                matched += 1

        if matched > 0:
            self.logger.success(f"[✓] {matched} Firmware files successfully auto-loaded into Odin slots.")
        else:
            self.logger.warn("[!] No matching BL_, AP_, CP_, CSC_ or PIT files identified in folder.")

    def _scan_odin_ports(self):
        self.logger.info("Scanning for connected Samsung devices in Odin / Download Mode...")
        devices = OdinProtocolEngine.scan_samsung_devices()
        if devices:
            d = devices[0]
            self.port_var.set(d["port"])
            self.lbl_samsung_port.configure(text=f"🟢 {d['port']} ({d['mode']})", text_color="#34D399")
            self.logger.success(f"[Odin Port Detected] {d['port']} - {d['description']}")
        else:
            self.lbl_samsung_port.configure(text="🔴 No Samsung Odin Port Detected", text_color="#F87171")
            self.logger.warn("[Odin Scan] No device in Download Mode detected. Put phone in Download Mode (Vol Down + Power + USB).")

    def _scan_modem_ports(self):
        self.logger.info("Scanning for Samsung Mobile Modem COM Port...")
        port = SamsungModemEngine.find_modem_port()
        if port:
            self.port_var.set(port)
            self.lbl_samsung_port.configure(text=f"🟢 Modem: {port}", text_color="#34D399")
            self.logger.success(f"[Modem Port Detected] {port}")
        else:
            self.lbl_samsung_port.configure(text="🔴 No Samsung Modem Port", text_color="#F87171")
            self.logger.warn("[Modem Scan] No Samsung Modem port found. Make sure Samsung USB Drivers are installed.")

    def _start_odin_flash(self):
        if self.is_flashing:
            messagebox.showwarning("Busy", "Flashing session is already in progress.")
            return

        slots = {
            "BL": self.slot_bl_var.get().strip(),
            "AP": self.slot_ap_var.get().strip(),
            "CP": self.slot_cp_var.get().strip(),
            "CSC": self.slot_csc_var.get().strip(),
            "PIT": self.slot_pit_var.get().strip()
        }

        active_slots = {k: v for k, v in slots.items() if v and os.path.exists(v)}
        if not active_slots:
            messagebox.showerror("No Firmware", "Please load at least one valid firmware file (BL, AP, CP, or CSC).")
            return

        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            # Auto scan
            devices = OdinProtocolEngine.scan_samsung_devices()
            if devices:
                port = devices[0]["port"]
            else:
                port = "COM3" # default fallback
                self.logger.warn(f"[Odin] Defaulting target to {port}. Ensure phone is in Download Mode.")

        self.is_flashing = True
        self.btn_flash.configure(state="disabled")

        def progress_file_cb(pct, fname):
            self.bar_file.set(pct / 100.0)
            self.lbl_file_status_var.set(f"{fname}: {pct:.1f}%")

        def progress_total_cb(pct):
            self.bar_total.set(pct / 100.0)
            self.lbl_total_status_var.set(f"Total Progress: {pct:.1f}%")

        def run():
            try:
                SoundManager.play_start()
                success = self.odin_engine.flash_firmware(
                    port_name=port,
                    slots=active_slots,
                    repartition=self.opt_repartition.get(),
                    auto_reboot=self.opt_auto_reboot.get(),
                    progress_file_cb=progress_file_cb,
                    progress_total_cb=progress_total_cb
                )
                if success:
                    SoundManager.play_success()
                    self.lbl_file_status_var.set("Flashing Completed Successfully!")
                else:
                    SoundManager.play_error()
                    self.lbl_file_status_var.set("Flashing Interrupted / Aborted")
            except Exception as e:
                SoundManager.play_error()
                self.logger.error(f"[Odin Flashing Error] {str(e)}")
            finally:
                self.is_flashing = False
                self.btn_flash.configure(state="normal")

        threading.Thread(target=run, daemon=True).start()

    def _abort_flash(self):
        if self.is_flashing:
            self.logger.warn("Aborting Odin Flash operation...")
            self.odin_engine.abort()

    def _launch_official_odin(self):
        slots = {
            "BL": self.slot_bl_var.get().strip(),
            "AP": self.slot_ap_var.get().strip(),
            "CP": self.slot_cp_var.get().strip(),
            "CSC": self.slot_csc_var.get().strip(),
            "PIT": self.slot_pit_var.get().strip()
        }
        repart = self.opt_repartition.get() if hasattr(self, "opt_repartition") else False
        reboot = self.opt_auto_reboot.get() if hasattr(self, "opt_auto_reboot") else True
        self.odin_engine.launch_official_odin(slots, repartition=repart, auto_reboot=reboot)

    def _read_samsung_info(self):
        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            port = SamsungModemEngine.find_modem_port()
            if not port:
                messagebox.showerror("Port Error", "No Samsung Modem port found. Connect phone powered ON.")
                return

        def run():
            self.modem_engine.read_device_info(port)
        threading.Thread(target=run, daemon=True).start()

    def _execute_test_mode(self):
        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            port = SamsungModemEngine.find_modem_port()
            if not port:
                messagebox.showerror("Port Error", "No Samsung Modem port found.")
                return

        def run():
            self.modem_engine.trigger_test_mode_setup(port)
        threading.Thread(target=run, daemon=True).start()

    def _reboot_download(self):
        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            port = SamsungModemEngine.find_modem_port()
            if not port:
                port = "COM1"

        def run():
            self.modem_engine.reboot_to_download_mode(port)
        threading.Thread(target=run, daemon=True).start()

    def _read_csc(self):
        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            port = SamsungModemEngine.find_modem_port()
            if not port:
                messagebox.showerror("Port Error", "No Samsung Modem port found. Connect phone powered ON.")
                return

        def run():
            csc_data = self.modem_engine.read_csc_status(port)
            self.logger.info(f"[CSC Status] Current Device CSC: {csc_data.get('current_csc', 'Unknown')}")
        threading.Thread(target=run, daemon=True).start()

    def _change_csc(self):
        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            port = SamsungModemEngine.find_modem_port()
            if not port:
                messagebox.showerror("Port Error", "No Samsung Modem port found. Connect phone powered ON in MTP mode.")
                return

        custom = self.csc_custom_var.get().strip().upper()
        if custom:
            target_csc = custom
        else:
            raw_sel = self.csc_choice_var.get()
            target_csc = raw_sel.split()[0].upper()

        if not target_csc or len(target_csc) != 3:
            messagebox.showwarning("Invalid CSC", f"'{target_csc}' is not a valid 3-letter CSC code (e.g. INS, TUR, PAK).")
            return

        reboot = self.csc_reboot_var.get()

        def run():
            self.logger.info(f"Targeting Samsung CSC Switch to [{target_csc}]...")
            ok = self.modem_engine.change_csc(port, target_csc, reboot_after=reboot)
            if ok:
                self.logger.success(f"[✓] CSC Changed to [{target_csc}] Successfully!")
            else:
                self.logger.error(f"[✗] Failed to apply CSC [{target_csc}]. Verify device connection.")
        threading.Thread(target=run, daemon=True).start()

    def _audit_knox_guard(self):
        port = self.port_var.get().split()[0]
        if "Auto" in port or not port.upper().startswith("COM"):
            port = SamsungModemEngine.find_modem_port()
            if not port:
                messagebox.showerror("Port Error", "No Samsung Modem port found. Connect phone powered ON.")
                return

        def run():
            res = self.modem_engine.read_knox_guard_and_security(port)
            self.lbl_kg_status_var.set(f"Knox Guard: {res.get('knox_guard', 'Unknown')}")
            self.lbl_warranty_var.set(f"Warranty: {res.get('knox_warranty', '0x0')}")
            self.lbl_frp_var.set(f"FRP: {res.get('frp_status', 'Unknown')}")
        threading.Thread(target=run, daemon=True).start()

    def _reboot_system(self):
        self.logger.info("Sending Reboot System command...")
        import subprocess
        subprocess.run(["adb", "reboot"], capture_output=True)

    def _reboot_recovery(self):
        self.logger.info("Sending Reboot Recovery command...")
        import subprocess
        subprocess.run(["adb", "reboot", "recovery"], capture_output=True)

    def _soft_reset(self):
        self.logger.warn("Requesting Samsung Soft Reset...")
        port = self.port_var.get().split()[0]
        if port.upper().startswith("COM"):
            def run():
                self.modem_engine.send_at_command(port, "AT+CFUN=1,1")
            threading.Thread(target=run, daemon=True).start()

    def _load_pit_file(self):
        f = filedialog.askopenfilename(title="Select PIT File", filetypes=[("Samsung PIT File", "*.pit"), ("All Files", "*.*")])
        if not f:
            return

        try:
            entries = PitParser.parse_pit_file(f)
            # Clear tree
            for item in self.pit_tree.get_children():
                self.pit_tree.delete(item)

            for idx, e in enumerate(entries):
                dev_str = "eMMC / UFS" if e.device_type in (2, 7) else f"Type {e.device_type}"
                tag = "even" if idx % 2 == 0 else "odd"
                self.pit_tree.insert("", "end", values=(
                    e.partition_name,
                    e.filename,
                    f"{e.size_mb:.2f}",
                    f"0x{e.block_start:08X}",
                    f"{e.block_count:,}",
                    dev_str
                ), tags=(tag,))

            self.slot_pit_var.set(f)
            self.logger.success(f"[PIT Loaded] {os.path.basename(f)}: {len(entries)} Partitions Displayed.")
        except Exception as e:
            self.logger.error(f"[PIT Error] Failed to parse: {str(e)}")

    def show(self):
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel.grid_forget()
        self.center_panel.grid_forget()
