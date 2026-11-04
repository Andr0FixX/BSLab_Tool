import os
import sys
import re
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from core.path_utils import get_platform_tool_path
from ui.theme import Theme

class FastbootADBView:
    """Universal Android Fastboot Flasher & Live ADB Services View."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.fb_slot_var = tk.StringVar(value="Slot: _a (Active)")
        self.adb_cmd_var = tk.StringVar()
        self.adb_apk_path_var = tk.StringVar()
        self.sideload_zip_path_var = tk.StringVar()
        self.mtp_url_var = tk.StringVar(value="https://www.youtube.com")
        self.fb_logical_part_var = tk.StringVar(value="system")
        self.fb_logical_size_var = tk.StringVar(value="2048M")
        self.fb_custom_cmd_var = tk.StringVar(value="")
        self.fb_rom_folder_var = tk.StringVar(value="")
        self.fb_disable_verity_var = tk.BooleanVar(value=True)
        self.fb_partitions = []

        self._build_left_panel()
        self._build_center_panel()

    def _build_left_panel(self):
        self.left_panel_fb = ctk.CTkScrollableFrame(self.body_frame, width=285, fg_color="#141418", corner_radius=8)

        # 1. Device Detection & Status Card
        ctk.CTkLabel(self.left_panel_fb, text="DEVICE DETECTION & PORTS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00D2FF").pack(anchor="w", padx=10, pady=(8, 2))
        stat_card = ctk.CTkFrame(self.left_panel_fb, fg_color="#1A1A22", corner_radius=6)
        stat_card.pack(fill="x", padx=10, pady=(0, 10))
        
        btn_row = ctk.CTkFrame(stat_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(btn_row, text="🔍 Check ADB", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8", height=30, command=self._adb_check_device).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(btn_row, text="🔍 Fastboot", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#334155", hover_color="#475569", height=30, command=self._fb_check_device).pack(side="right", fill="x", expand=True, padx=(3, 0))

        self.lbl_fb_device_stat = ctk.CTkLabel(
            stat_card,
            text="● Status: Ready to Scan",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#94A3B8"
        )
        self.lbl_fb_device_stat.pack(anchor="w", padx=10, pady=(0, 8))

        # 2. Power & Mode Switcher Hub (One-Click Reboots)
        ctk.CTkLabel(self.left_panel_fb, text="⚡ POWER & MODE SWITCHER", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=10, pady=(2, 2))
        pwr_card = ctk.CTkFrame(self.left_panel_fb, fg_color="#1A1A22", corner_radius=6)
        pwr_card.pack(fill="x", padx=10, pady=(0, 10))

        p1 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        p1.pack(fill="x", padx=8, pady=(8, 3))
        ctk.CTkButton(p1, text="🔄 Reboot System", font=ctk.CTkFont(size=10, weight="bold"), height=30, fg_color="#059669", hover_color="#047857", command=lambda: self._reboot_device_mode("system")).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(p1, text="⚡ Reboot Fastboot", font=ctk.CTkFont(size=10, weight="bold"), height=30, fg_color="#0284C7", hover_color="#0369A1", command=lambda: self._reboot_device_mode("bootloader")).pack(side="right", fill="x", expand=True, padx=(3, 0))

        p2 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        p2.pack(fill="x", padx=8, pady=3)
        ctk.CTkButton(p2, text="📦 Reboot Recovery", font=ctk.CTkFont(size=10, weight="bold"), height=30, fg_color="#4F46E5", hover_color="#4338CA", command=lambda: self._reboot_device_mode("recovery")).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(p2, text="💥 Reboot EDL 9008", font=ctk.CTkFont(size=10, weight="bold"), height=30, fg_color="#D97706", hover_color="#B45309", command=lambda: self._reboot_device_mode("edl")).pack(side="right", fill="x", expand=True, padx=(3, 0))

        p3 = ctk.CTkFrame(pwr_card, fg_color="transparent")
        p3.pack(fill="x", padx=8, pady=(3, 8))
        ctk.CTkButton(p3, text="🚀 Reboot FastbootD", font=ctk.CTkFont(size=10, weight="bold"), height=30, fg_color="#7C3AED", hover_color="#6D28D9", command=lambda: self._reboot_device_mode("fastbootd")).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(p3, text="🔌 Power Off Device", font=ctk.CTkFont(size=10, weight="bold"), height=30, fg_color="#334155", hover_color="#475569", command=lambda: self._reboot_device_mode("poweroff")).pack(side="right", fill="x", expand=True, padx=(3, 0))

        # 3. Slot A/B Controller Card
        ctk.CTkLabel(self.left_panel_fb, text="SLOT A/B CONTROLLER", font=ctk.CTkFont(size=11, weight="bold"), text_color="#93C5FD").pack(anchor="w", padx=10, pady=(2, 2))
        slot_card = ctk.CTkFrame(self.left_panel_fb, fg_color="#1A1A22", corner_radius=6)
        slot_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkOptionMenu(slot_card, values=["Slot: _a (Active)", "Slot: _b (Secondary)", "Set Active Slot: a", "Set Active Slot: b"], variable=self.fb_slot_var, fg_color="#1E293B", height=30, command=self._on_slot_changed).pack(fill="x", padx=8, pady=8)

    def _build_center_panel(self):
        self.center_panel_fb = ctk.CTkFrame(self.body_frame, fg_color="#141418", corner_radius=8)
        
        self.tab_fb_selector = ctk.CTkSegmentedButton(
            self.center_panel_fb,
            values=["🤖 ADB Services & FRP", "⚡ Fastboot Flasher", "⚙️ Fastboot Ops", "📦 APK & Debloater", "🌐 MTP & Sideload"],
            command=self._on_tab_changed,
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color="#0284C7",
            selected_hover_color="#0369A1",
            height=34
        )
        self.tab_fb_selector.pack(fill="x", padx=12, pady=(10, 8))
        self.tab_fb_selector.set("🤖 ADB Services & FRP")

        self.tab_container_fb = ctk.CTkFrame(self.center_panel_fb, fg_color="transparent")
        self.tab_container_fb.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # TAB 1: ADB SERVICES & FRP
        self.frame_fb_adb = ctk.CTkScrollableFrame(self.tab_container_fb, fg_color="transparent")
        adb_hdr = ctk.CTkFrame(self.frame_fb_adb, fg_color="#1C1C24", corner_radius=6)
        adb_hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            adb_hdr,
            text="🤖 Android Live ADB Service Suite (Phone Powered ON with USB Debugging)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00D2FF"
        ).pack(anchor="w", padx=10, pady=6)

        # Row 1
        r1 = ctk.CTkFrame(self.frame_fb_adb, fg_color="transparent")
        r1.pack(fill="x", pady=4)
        ctk.CTkButton(r1, text="📱 Read Full Info (getprop)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#4F46E5", hover_color="#4338CA", command=self._adb_read_info).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(r1, text="🔓 Reset FRP (ADB One-Click)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#0284C7", hover_color="#0369A1", command=self._adb_reset_frp).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 2
        r2 = ctk.CTkFrame(self.frame_fb_adb, fg_color="transparent")
        r2.pack(fill="x", pady=4)
        ctk.CTkButton(r2, text="🛡️ Bypass Setup Wizard", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#7C3AED", hover_color="#6D28D9", command=self._adb_bypass_setup_wizard).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(r2, text="🚫 Disable Mi Account / Cloud", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#7C3AED", hover_color="#6D28D9", command=self._adb_disable_mi_account).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 3
        r3 = ctk.CTkFrame(self.frame_fb_adb, fg_color="transparent")
        r3.pack(fill="x", pady=4)
        ctk.CTkButton(r3, text="✨ Disable Demo Mode (Vivo/Oppo)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#DC2626", hover_color="#B91C1C", command=self._adb_disable_demo_mode).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(r3, text="📶 Enable Qualcomm Diag Port", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#D97706", hover_color="#B45309", command=self._adb_enable_diag).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 4
        r4 = ctk.CTkFrame(self.frame_fb_adb, fg_color="transparent")
        r4.pack(fill="x", pady=4)
        ctk.CTkButton(r4, text="🔒 Remove Screen Lock (Rooted)", font=ctk.CTkFont(size=11, weight="bold"), height=36, fg_color="#334155", hover_color="#475569", command=self._adb_remove_screenlock).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(r4, text="🧹 Wipe Dalvik / User Cache", font=ctk.CTkFont(size=11, weight="bold"), height=36, fg_color="#334155", hover_color="#475569", command=self._adb_wipe_cache).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 5: ADB Shell Runner
        shell_card = ctk.CTkFrame(self.frame_fb_adb, fg_color="#181822", corner_radius=6)
        shell_card.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(shell_card, text="⌨️ Direct ADB Shell Command Runner:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#34D399").pack(anchor="w", padx=10, pady=(6, 2))
        
        sh_row = ctk.CTkFrame(shell_card, fg_color="transparent")
        sh_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkEntry(sh_row, textvariable=self.adb_cmd_var, placeholder_text="e.g. getprop ro.build.version.release", font=ctk.CTkFont(size=10), height=28, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(sh_row, text="🚀 Run Shell", width=85, height=28, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#059669", hover_color="#047857", command=self._adb_run_shell_cmd).pack(side="right")

        # TAB 2: FASTBOOT FLASHER
        self.frame_fb_flash = ctk.CTkFrame(self.tab_container_fb, fg_color="transparent")

        # Section 1: Fastboot Command Terminal
        cmd_card = ctk.CTkFrame(
            self.frame_fb_flash,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        cmd_card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            cmd_card,
            text="⌨️ Interactive Fastboot Command Terminal (Direct CLI Execution)",
            font=Theme.font_bold(size=11),
            text_color=Theme.ACCENT_CYAN
        ).pack(anchor="w", padx=12, pady=(8, 4))

        # Command entry & run row
        cmd_row = ctk.CTkFrame(cmd_card, fg_color="transparent")
        cmd_row.pack(fill="x", padx=12, pady=(0, 6))

        self.entry_fb_cmd = ctk.CTkEntry(
            cmd_row,
            textvariable=self.fb_custom_cmd_var,
            placeholder_text="Enter Fastboot Command (e.g. fastboot getvar all / fastboot erase frp / fastboot -w)",
            font=Theme.font_mono(size=11),
            height=32,
            fg_color=Theme.SURFACE_INPUT
        )
        self.entry_fb_cmd.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_fb_cmd.bind("<Return>", lambda e: self._fb_run_custom_cmd())

        ctk.CTkButton(
            cmd_row,
            text="🚀 Run Command",
            width=120,
            height=32,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_CYAN_HOVER,
            hover_color=Theme.ACCENT_CYAN,
            command=self._fb_run_custom_cmd
        ).pack(side="right")

        # Quick chips row
        chips_frame = ctk.CTkFrame(cmd_card, fg_color="transparent")
        chips_frame.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(chips_frame, text="Quick Shortcuts:", font=Theme.font_bold(size=10), text_color="#94A3B8").pack(side="left", padx=(0, 6))

        quick_cmds = [
            ("getvar all", "getvar all"),
            ("devices", "devices"),
            ("erase frp", "erase frp"),
            ("flashing unlock", "flashing unlock"),
            ("-w (Wipe)", "-w"),
            ("oem edl", "oem edl"),
            ("reboot recovery", "reboot-recovery"),
            ("reboot fastbootd", "reboot fastboot"),
        ]

        for lbl, cmd_str in quick_cmds:
            ctk.CTkButton(
                chips_frame,
                text=lbl,
                height=22,
                width=65,
                font=Theme.font_ui(size=10),
                fg_color="#1E293B",
                hover_color="#334155",
                command=lambda c=cmd_str: self._set_and_run_fb_cmd(c)
            ).pack(side="left", padx=2)

        # Section 2: Universal Firmware ROM Dump & Partition Flasher
        flasher_card = ctk.CTkFrame(
            self.frame_fb_flash,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        flasher_card.pack(fill="both", expand=True)

        # Folder selector header
        f_hdr = ctk.CTkFrame(flasher_card, fg_color="transparent")
        f_hdr.pack(fill="x", padx=12, pady=(8, 6))

        ctk.CTkLabel(
            f_hdr,
            text="⚡ Fastboot Multi-Partition Flasher (Firmware Dump / ROM Images)",
            font=Theme.font_bold(size=11),
            text_color="#FDE68A"
        ).pack(side="left")

        ctk.CTkButton(
            f_hdr,
            text="📁 Browse ROM Folder",
            height=28,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_CYAN_HOVER,
            hover_color=Theme.ACCENT_CYAN,
            command=self._browse_rom_folder
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            f_hdr,
            text="+ Add Image File",
            height=28,
            font=Theme.font_bold(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._add_single_img
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            f_hdr,
            text="Clear",
            height=28,
            width=55,
            font=Theme.font_ui(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._clear_fb_partitions
        ).pack(side="right", padx=4)

        # Path display bar
        path_bar = ctk.CTkFrame(flasher_card, fg_color="transparent")
        path_bar.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkEntry(
            path_bar,
            textvariable=self.fb_rom_folder_var,
            placeholder_text="ROM dump folder path will appear here...",
            font=Theme.font_mono(size=10),
            height=26,
            fg_color=Theme.SURFACE_INPUT
        ).pack(fill="x")

        # Partition Treeview Table
        tree_frame = ctk.CTkFrame(flasher_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        cols_fb = ("check", "partition", "file", "size", "status")
        self.tree_fb_parts = ttk.Treeview(tree_frame, columns=cols_fb, show="headings", selectmode="browse")
        self.tree_fb_parts.heading("check", text="[✓]")
        self.tree_fb_parts.heading("partition", text="Target Partition")
        self.tree_fb_parts.heading("file", text="Image File Name / Path")
        self.tree_fb_parts.heading("size", text="Size")
        self.tree_fb_parts.heading("status", text="Status")

        self.tree_fb_parts.column("check", width=40, anchor="center")
        self.tree_fb_parts.column("partition", width=140, anchor="w")
        self.tree_fb_parts.column("file", width=260, anchor="w")
        self.tree_fb_parts.column("size", width=85, anchor="e")
        self.tree_fb_parts.column("status", width=90, anchor="center")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_fb_parts.yview)
        self.tree_fb_parts.configure(yscrollcommand=tree_scroll.set)
        self.tree_fb_parts.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree_fb_parts.tag_configure("even", background=Theme.TABLE_ROW_EVEN)
        self.tree_fb_parts.tag_configure("odd", background=Theme.TABLE_ROW_ODD)
        self.tree_fb_parts.bind("<ButtonRelease-1>", self._on_tree_fb_click)

        # Batch Controls & Flash Action Bar
        act_bar = ctk.CTkFrame(flasher_card, fg_color="transparent")
        act_bar.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(
            act_bar,
            text="✓ Select All",
            width=85,
            height=28,
            font=Theme.font_ui(size=10),
            fg_color="#334155",
            hover_color="#475569",
            command=self._select_all_fb_partitions
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            act_bar,
            text="✗ Deselect All",
            width=90,
            height=28,
            font=Theme.font_ui(size=10),
            fg_color="#334155",
            hover_color="#475569",
            command=self._deselect_all_fb_partitions
        ).pack(side="left", padx=4)

        ctk.CTkCheckBox(
            act_bar,
            text="Disable Verity on Vbmeta (--disable-verity --disable-verification)",
            variable=self.fb_disable_verity_var,
            font=Theme.font_ui(size=10),
            fg_color=Theme.ACCENT_CYAN,
            hover_color=Theme.ACCENT_CYAN_HOVER
        ).pack(side="left", padx=10)

        self.btn_fb_flash_all = ctk.CTkButton(
            act_bar,
            text="⚡ FLASH SELECTED PARTITIONS (FASTBOOT)",
            height=34,
            font=Theme.font_bold(size=12),
            fg_color="#059669",
            hover_color="#047857",
            command=self._fb_flash_selected_partitions
        )
        self.btn_fb_flash_all.pack(side="right")

        # TAB 3: FASTBOOT OPS
        self.frame_fb_ops = ctk.CTkScrollableFrame(self.tab_container_fb, fg_color="transparent")
        ops_hdr = ctk.CTkFrame(self.frame_fb_ops, fg_color="#1C1C24", corner_radius=6)
        ops_hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            ops_hdr,
            text="⚙️ Fastboot Bootloader Servicing & Wipe Operations",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F59E0B"
        ).pack(anchor="w", padx=10, pady=6)

        op_r1 = ctk.CTkFrame(self.frame_fb_ops, fg_color="transparent")
        op_r1.pack(fill="x", pady=4)
        ctk.CTkButton(op_r1, text="🔓 OEM Unlock Bootloader (fastboot flashing unlock)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#D97706", hover_color="#B45309", command=self._fb_unlock_bootloader).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(op_r1, text="🔒 OEM Relock Bootloader (fastboot flashing lock)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#D97706", hover_color="#B45309", command=self._fb_lock_bootloader).pack(side="left", fill="x", expand=True, padx=(4, 0))

        op_r2 = ctk.CTkFrame(self.frame_fb_ops, fg_color="transparent")
        op_r2.pack(fill="x", pady=4)
        ctk.CTkButton(op_r2, text="🧹 Wipe Userdata & Cache (fastboot -w)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#DC2626", hover_color="#B91C1C", command=self._fb_wipe_userdata).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(op_r2, text="🗑️ Erase FRP Partition (fastboot erase frp)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#DC2626", hover_color="#B91C1C", command=self._fb_erase_frp).pack(side="left", fill="x", expand=True, padx=(4, 0))

        op_r3 = ctk.CTkFrame(self.frame_fb_ops, fg_color="transparent")
        op_r3.pack(fill="x", pady=4)
        ctk.CTkButton(op_r3, text="🔄 Fastboot Reboot (Reboot Normal)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#059669", hover_color="#047857", command=self._fb_reboot).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(op_r3, text="💥 Fastboot Reboot to EDL (Reboot EDL)", font=ctk.CTkFont(size=11, weight="bold"), height=38, fg_color="#D97706", hover_color="#B45309", command=self._fb_reboot_edl).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # TAB 4: APK & DEBLOATER
        self.frame_fb_apk = ctk.CTkScrollableFrame(self.tab_container_fb, fg_color="transparent")
        apk_hdr = ctk.CTkFrame(self.frame_fb_apk, fg_color="#1C1C24", corner_radius=6)
        apk_hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            apk_hdr,
            text="📦 Android Package Manager & System Bloatware Remover",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A5B4FC"
        ).pack(anchor="w", padx=10, pady=6)

        apk_card = ctk.CTkFrame(self.frame_fb_apk, fg_color="#1A1A22", corner_radius=6)
        apk_card.pack(fill="x", pady=4)
        ctk.CTkLabel(apk_card, text="Install Single / Multiple APK:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#E2E8F0").pack(anchor="w", padx=10, pady=(8, 2))
        
        apk_row = ctk.CTkFrame(apk_card, fg_color="transparent")
        apk_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(apk_row, textvariable=self.adb_apk_path_var, font=ctk.CTkFont(size=10), height=28, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(apk_row, text="📁", width=32, height=28, fg_color="#4F46E5", command=self._browse_apk).pack(side="right")

        ctk.CTkButton(apk_card, text="📥 Install Selected APK to Phone", height=34, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#059669", hover_color="#047857", command=self._adb_install_apk).pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkButton(self.frame_fb_apk, text="🧹 Batch Debloat Carrier / Telemetry Bloatware", height=38, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#7C3AED", hover_color="#6D28D9", command=self._adb_debloat_carrier).pack(fill="x", pady=4)
        ctk.CTkButton(self.frame_fb_apk, text="📋 List Installed Packages (Third-Party)", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#334155", hover_color="#475569", command=self._adb_list_packages).pack(fill="x", pady=4)

        # TAB 5: MTP FRP & SIDELOAD
        self.frame_fb_mtp = ctk.CTkScrollableFrame(self.tab_container_fb, fg_color="transparent")
        mtp_hdr = ctk.CTkFrame(self.frame_fb_mtp, fg_color="#1C1C24", corner_radius=6)
        mtp_hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            mtp_hdr,
            text="🌐 Universal MTP Browser FRP Launcher & Recovery Sideload Flasher",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00D2FF"
        ).pack(anchor="w", padx=10, pady=6)

        # Card 1: MTP Browser Push
        mtp_card = ctk.CTkFrame(self.frame_fb_mtp, fg_color="#181822", corner_radius=8)
        mtp_card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(mtp_card, text="MTP BROWSER FRP LAUNCHER (NO USB DEBUGGING REQUIRED)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(mtp_card, text="Pushes browser intent popup to phone screen at Google lock setup screen.", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(0, 6))

        url_row = ctk.CTkFrame(mtp_card, fg_color="transparent")
        url_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(url_row, text="Target URL:", width=75, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkEntry(url_row, textvariable=self.mtp_url_var, font=ctk.CTkFont(size=10), height=28, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkOptionMenu(
            url_row,
            values=["https://www.youtube.com", "https://maps.google.com", "https://www.google.com"],
            command=lambda val: self.mtp_url_var.set(val),
            width=140,
            height=28,
            fg_color="#334155"
        ).pack(side="right")

        m_btn_row1 = ctk.CTkFrame(mtp_card, fg_color="transparent")
        m_btn_row1.pack(fill="x", padx=12, pady=(4, 4))
        ctk.CTkButton(m_btn_row1, text="🚀 Push Browser Intent (MTP YouTube)", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#0284C7", hover_color="#0369A1", command=self._mtp_push_browser).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(m_btn_row1, text="📱 Read MTP Device Info", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#4F46E5", hover_color="#4338CA", command=self._mtp_read_info).pack(side="right", fill="x", expand=True, padx=(4, 0))

        m_btn_row2 = ctk.CTkFrame(mtp_card, fg_color="transparent")
        m_btn_row2.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(m_btn_row2, text="🔓 Samsung One-Click FRP (*#0*# Test Mode)", height=38, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#059669", hover_color="#047857", command=self._samsung_mtp_test_mode_frp).pack(fill="x")

        # Card 2: Recovery Sideload Flasher
        side_card = ctk.CTkFrame(self.frame_fb_mtp, fg_color="#181822", corner_radius=8)
        side_card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(side_card, text="RECOVERY SIDELOAD OTA & ROM FLASHER", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(side_card, text="Flash official OTA ZIP or custom ROMs in Recovery Sideload mode.", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(0, 6))

        side_row = ctk.CTkFrame(side_card, fg_color="transparent")
        side_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkEntry(side_row, textvariable=self.sideload_zip_path_var, placeholder_text="Select OTA / ROM update.zip file...", font=ctk.CTkFont(size=10), height=28, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(side_row, text="📁", width=32, height=28, fg_color="#4F46E5", command=self._browse_sideload_zip).pack(side="right")

        ctk.CTkButton(side_card, text="⚡ Flash Sideload ZIP Package (adb sideload)", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8", command=self._adb_sideload_flash).pack(fill="x", padx=12, pady=(2, 10))

        # Card 3: FastbootD Dynamic Partitions Controller
        fbd_card = ctk.CTkFrame(self.frame_fb_mtp, fg_color="#181822", corner_radius=8)
        fbd_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(fbd_card, text="FASTBOOTD DYNAMIC PARTITIONS CONTROLLER (ANDROID 10-15)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkButton(fbd_card, text="🔄 Switch Bootloader to FastbootD Mode (reboot fastboot)", height=34, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#7C3AED", hover_color="#6D28D9", command=self._fb_reboot_fastbootd).pack(fill="x", padx=12, pady=(4, 8))

        fbd_row = ctk.CTkFrame(fbd_card, fg_color="transparent")
        fbd_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(fbd_row, text="Partition:", width=60, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkEntry(fbd_row, textvariable=self.fb_logical_part_var, width=120, font=ctk.CTkFont(size=10), height=28, fg_color="#0F0F12").pack(side="left", padx=(0, 6))
        ctk.CTkLabel(fbd_row, text="Size:", width=40, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkEntry(fbd_row, textvariable=self.fb_logical_size_var, width=90, font=ctk.CTkFont(size=10), height=28, fg_color="#0F0F12").pack(side="left")

        fbd_btn_row = ctk.CTkFrame(fbd_card, fg_color="transparent")
        fbd_btn_row.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(fbd_btn_row, text="➕ Create", height=32, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#059669", hover_color="#047857", command=self._fb_create_logical_part).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(fbd_btn_row, text="📐 Resize", height=32, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8", command=self._fb_resize_logical_part).pack(side="left", fill="x", expand=True, padx=3)
        ctk.CTkButton(fbd_btn_row, text="🗑️ Delete", height=32, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#DC2626", hover_color="#B91C1C", command=self._fb_delete_logical_part).pack(side="right", fill="x", expand=True, padx=(3, 0))

        self._show_tab("🤖 ADB Services & FRP")

    def _show_tab(self, tab_name):
        self.frame_fb_adb.pack_forget()
        self.frame_fb_flash.pack_forget()
        self.frame_fb_ops.pack_forget()
        self.frame_fb_apk.pack_forget()
        self.frame_fb_mtp.pack_forget()

        if tab_name == "🤖 ADB Services & FRP":
            self.frame_fb_adb.pack(fill="both", expand=True)
        elif tab_name == "⚡ Fastboot Flasher":
            self.frame_fb_flash.pack(fill="both", expand=True)
        elif tab_name == "⚙️ Fastboot Ops":
            self.frame_fb_ops.pack(fill="both", expand=True)
        elif tab_name == "📦 APK & Debloater":
            self.frame_fb_apk.pack(fill="both", expand=True)
        elif tab_name == "🌐 MTP & Sideload":
            self.frame_fb_mtp.pack(fill="both", expand=True)

    def _on_tab_changed(self, value):
        self._show_tab(value)

    # -------------------------------------------------------------------------
    # ADB & FASTBOOT IMPLEMENTATIONS
    # -------------------------------------------------------------------------
    def _fb_check_device(self):
        self.logger.info("Scanning for connected Fastboot devices...")
        def run():
            try:
                res = self._run_tool(["fastboot", "devices"], capture_output=True, text=True)
                out = res.stdout.strip()
                if out:
                    self.logger.success(f"[Fastboot] Device Connected: {out}")
                    self.lbl_fb_device_stat.after(0, lambda: self.lbl_fb_device_stat.configure(text=f"🟢 Fastboot: {out.split()[0]}", text_color="#34D399"))
                else:
                    self.logger.warn("[Fastboot] No device detected in Fastboot mode.")
                    self.lbl_fb_device_stat.after(0, lambda: self.lbl_fb_device_stat.configure(text="🔴 No Fastboot Device", text_color="#F87171"))
            except Exception as e:
                self.logger.error(f"[Fastboot] Error checking devices: {str(e)}")
        threading.Thread(target=run, daemon=True).start()

    def _adb_check_device(self):
        self.logger.info("Scanning for connected ADB devices (USB Debugging)...")
        def run():
            try:
                res = self._run_tool(["adb", "devices"], capture_output=True, text=True)
                lines = [l.strip() for l in res.stdout.splitlines() if l.strip() and not l.startswith("List of")]
                if lines:
                    dev_info = lines[0]
                    self.logger.success(f"[ADB] Device Connected: {dev_info}")
                    dev_id = dev_info.split()[0]
                    self.lbl_fb_device_stat.after(0, lambda: self.lbl_fb_device_stat.configure(text=f"🟢 ADB: {dev_id} [Online]", text_color="#34D399"))
                else:
                    self.logger.warn("[ADB] No authorized ADB device found. Ensure USB Debugging is ON.")
                    self.lbl_fb_device_stat.after(0, lambda: self.lbl_fb_device_stat.configure(text="🔴 No ADB Device (Check USB Debug)", text_color="#F87171"))
            except Exception as e:
                self.logger.error(f"[ADB] Error checking devices: {str(e)}")
        threading.Thread(target=run, daemon=True).start()

    def _reboot_device_mode(self, mode):
        self.logger.info(f"Triggering Reboot to: {mode.upper()}...")
        def run():
            if mode == "system":
                self._run_tool(["adb", "reboot"], capture_output=True)
                self._run_tool(["fastboot", "reboot"], capture_output=True)
                self.logger.success("[Reboot] Command sent to reboot system normally.")
            elif mode == "bootloader":
                self._run_tool(["adb", "reboot", "bootloader"], capture_output=True)
                self.logger.success("[Reboot] Sent 'adb reboot bootloader' payload.")
            elif mode == "recovery":
                self._run_tool(["adb", "reboot", "recovery"], capture_output=True)
                self._run_tool(["fastboot", "reboot-recovery"], capture_output=True)
                self.logger.success("[Reboot] Command sent to reboot into Recovery Mode.")
            elif mode == "edl":
                self._run_tool(["adb", "reboot", "edl"], capture_output=True)
                self._run_tool(["fastboot", "oem", "edl"], capture_output=True)
                self.logger.brom("[Reboot] Command sent to force Qualcomm EDL 9008 Mode.")
            elif mode == "fastbootd":
                self._run_tool(["fastboot", "reboot", "fastboot"], capture_output=True)
                self.logger.success("[Reboot] Sent 'fastboot reboot fastboot' for Dynamic Partitions.")
            elif mode == "poweroff":
                self._run_tool(["adb", "shell", "reboot", "-p"], capture_output=True)
                self.logger.info("[Power] Sent power off command.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_read_info(self):
        self.logger.info("Querying Android Device Properties via ADB (getprop)...")
        def run():
            try:
                dev_res = self._run_tool(["adb", "devices"], capture_output=True, text=True)
                lines = [l.strip() for l in dev_res.stdout.splitlines() if l.strip() and not l.startswith("List of")]
                if not lines:
                    self.logger.error("[ADB] No connected ADB device found. Please verify cable and USB Debugging.")
                    return
                if any("unauthorized" in l for l in lines):
                    self.logger.warn("[ADB] Device UNAUTHORIZED! Check phone screen and tap Always allow from this computer -> OK.")
                    return
                serial = lines[0].split()[0]
                res = self._run_tool(["adb", "-s", serial, "shell", "getprop"], capture_output=True, text=True)
                if not res.stdout or not res.stdout.strip():
                    self.logger.error("[ADB] Device shell returned empty response or permission denied.")
                    return
                props = {}
                for line in res.stdout.splitlines():
                    if "]: [" in line:
                        parts = line.split("]: [", 1)
                        k = parts[0].replace("[", "").strip()
                        v = parts[1].rstrip("]").strip()
                        props[k] = v
                mfg = props.get("ro.product.manufacturer", "UNKNOWN").upper()
                model = props.get("ro.product.model", props.get("ro.product.device", "UNKNOWN"))
                brand = props.get("ro.product.brand", mfg).upper()
                ver = props.get("ro.build.version.release", "UNKNOWN")
                sdk = props.get("ro.build.version.sdk", "UNKNOWN")
                sec = props.get("ro.build.version.security_patch", "UNKNOWN")
                build = props.get("ro.build.display.id", "UNKNOWN")
                cpu = props.get("ro.product.cpu.abi", "UNKNOWN")
                soc = props.get("ro.board.platform", props.get("ro.hardware", "UNKNOWN"))
                bat_res = self._run_tool(["adb", "-s", serial, "shell", "dumpsys", "battery"], capture_output=True, text=True)
                bat_lvl = "Unknown"
                if bat_res and bat_res.stdout:
                    for bline in bat_res.stdout.splitlines():
                        if "level:" in bline:
                            bat_lvl = bline.split(":")[1].strip() + "%"
                            break
                self.logger.success("==================================================")
                self.logger.success("ANDROID DEVICE SPECIFICATIONS (ADB READ INFO)")
                self.logger.success("==================================================")
                self.logger.info(f"Brand / Maker   : {brand} ({mfg})")
                self.logger.info(f"Model Name      : {model} [Serial: {serial}]")
                self.logger.info(f"Android Version : Android {ver} (SDK API {sdk})")
                self.logger.info(f"Security Patch  : {sec}")
                self.logger.info(f"Build Display ID: {build}")
                self.logger.info(f"Chipset / Board : {soc} ({cpu})")
                self.logger.info(f"Battery Status  : {bat_lvl}")
                self.logger.success("[✓] ADB Handshake and Diagnostics Completed Successfully!")
            except Exception as e:
                self.logger.error(f"[ADB] Failed to read info: {str(e)}")
        threading.Thread(target=run, daemon=True).start()
    def _adb_reset_frp(self):
        self.logger.warn("Executing One-Click Google FRP Bypass via ADB...")
        def run():
            cmds = [
                ["adb", "shell", "content", "insert", "--uri", "content://settings/secure", "--bind", "name:s:user_setup_complete", "--bind", "value:s:1"],
                ["adb", "shell", "settings", "put", "secure", "user_setup_complete", "1"],
                ["adb", "shell", "settings", "put", "global", "device_provisioned", "1"],
                ["adb", "shell", "settings", "put", "secure", "device_provisioned", "1"],
                ["adb", "shell", "am", "start", "-n", "com.google.android.gsf.login/"]
            ]
            for cmd in cmds:
                self._run_tool(cmd, capture_output=True)
            self.logger.success("==================================================")
            self.logger.success("FRP BYPASS COMPLETED VIA ADB!")
            self.logger.success("Restart phone or swipe to Home Screen to verify.")
            self.logger.success("==================================================")
        threading.Thread(target=run, daemon=True).start()

    def _adb_bypass_setup_wizard(self):
        self.logger.info("Bypassing Initial Setup Wizard...")
        def run():
            self._run_tool(["adb", "shell", "settings", "put", "global", "setup_wizard_has_run", "1"], capture_output=True)
            self._run_tool(["adb", "shell", "settings", "put", "secure", "user_setup_complete", "1"], capture_output=True)
            self._run_tool(["adb", "shell", "settings", "put", "global", "device_provisioned", "1"], capture_output=True)
            self.logger.success("[✓] Setup Wizard Bypassed Successfully!")
        threading.Thread(target=run, daemon=True).start()

    def _adb_disable_mi_account(self):
        self.logger.info("Freezing Xiaomi Mi Cloud & Find Device Services...")
        def run():
            pkgs = ["com.xiaomi.finddevice", "com.miui.cloudservice", "com.xiaomi.micloud.sdk"]
            for pkg in pkgs:
                res = self._run_tool(["adb", "shell", "pm", "disable-user", "--user", "0", pkg], capture_output=True, text=True)
                self.logger.info(f"[{pkg}] {res.stdout.strip() or 'Disabled'}")
            self.logger.success("[✓] Xiaomi Cloud & Account Services Disabled.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_disable_demo_mode(self):
        self.logger.info("Removing Vivo / Oppo / Realme Live Demo Mode...")
        def run():
            pkgs = ["com.vivo.easyshare.demo", "com.oppo.market.demo", "com.coloros.oppodemo"]
            for pkg in pkgs:
                self._run_tool(["adb", "shell", "pm", "disable-user", "--user", "0", pkg], capture_output=True)
            self._run_tool(["adb", "shell", "am", "broadcast", "-a", "com.oppo.demo.exit"], capture_output=True)
            self.logger.success("[✓] Retail Demo Mode Disabled Successfully.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_enable_diag(self):
        self.logger.info("Enabling Qualcomm Diagnostic Port (*#*#diag#*#*)...")
        def run():
            self._run_tool(["adb", "shell", "setprop", "sys.usb.config", "diag,serial_cdev,rmnet,adb"], capture_output=True)
            self._run_tool(["adb", "shell", "setprop", "sys.usb.config", "diag,adb"], capture_output=True)
            self.logger.success("[✓] Diagnostic Port command executed. Check Windows Device Manager for COM port.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_remove_screenlock(self):
        self.logger.warn("Removing Screen Lock / Gesture Database (Root Required)...")
        def run():
            cmds = [
                ["adb", "shell", "rm", "/data/system/gesture.key"],
                ["adb", "shell", "rm", "/data/system/password.key"],
                ["adb", "shell", "rm", "/data/system/locksettings.db"],
                ["adb", "shell", "rm", "/data/system/locksettings.db-shm"],
                ["adb", "shell", "rm", "/data/system/locksettings.db-wal"]
            ]
            for cmd in cmds:
                self._run_tool(cmd, capture_output=True)
            self.logger.success("[✓] Lock keys deleted. Please restart device.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_wipe_cache(self):
        self.logger.info("Wiping Dalvik and System Cache...")
        def run():
            self._run_tool(["adb", "shell", "rm", "-rf", "/data/dalvik-cache/*"], capture_output=True)
            self._run_tool(["adb", "shell", "rm", "-rf", "/cache/*"], capture_output=True)
            self.logger.success("[✓] Cache cleared successfully.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_run_shell_cmd(self):
        cmd = self.adb_cmd_var.get().strip()
        if not cmd:
            self.logger.warn("Please enter a command to execute.")
            return
        self.logger.info(f"[Shell] Executing: adb shell {cmd}")
        def run():
            try:
                res = self._run_tool(["adb", "shell", cmd], capture_output=True, text=True)
                out = res.stdout.strip() or res.stderr.strip()
                if out:
                    for line in out.splitlines():
                        self.logger.info(f"[Shell Output] {line}")
                self.logger.success(f"[Shell] Command finished (Exit: {res.returncode})")
            except Exception as e:
                self.logger.error(f"[Shell] Failed: {str(e)}")
        threading.Thread(target=run, daemon=True).start()

    def _browse_apk(self):
        f = filedialog.askopenfilename(title="Select APK File", filetypes=[("Android Package", "*.apk")])
        if f:
            self.adb_apk_path_var.set(f)
            self.logger.info(f"Selected APK: {os.path.basename(f)}")

    def _adb_install_apk(self):
        apk = self.adb_apk_path_var.get().strip()
        if not apk or not os.path.exists(apk):
            messagebox.showwarning("Select APK", "Please select a valid .apk file first.")
            return
        self.logger.info(f"Installing APK: {os.path.basename(apk)}...")
        def run():
            res = self._run_tool(["adb", "install", "-r", apk], capture_output=True, text=True)
            out = res.stdout.strip() or res.stderr.strip()
            self.logger.info(f"[ADB Install] {out}")
            if "Success" in out:
                self.logger.success(f"[✓] {os.path.basename(apk)} installed successfully!")
            else:
                self.logger.warn(f"[!] Install finished with: {out}")
        threading.Thread(target=run, daemon=True).start()

    def _adb_debloat_carrier(self):
        self.logger.warn("Debloating Known Telemetry / Carrier Bloatware...")
        def run():
            bloat_list = [
                "com.facebook.katana", "com.facebook.system", "com.facebook.appmanager",
                "com.facebook.services", "com.google.android.apps.tachyon", "com.google.android.youtube"
            ]
            for pkg in bloat_list:
                res = self._run_tool(["adb", "shell", "pm", "uninstall", "-k", "--user", "0", pkg], capture_output=True, text=True)
                if "Success" in res.stdout:
                    self.logger.success(f"[Debloat] Removed: {pkg}")
                else:
                    self.logger.info(f"[Debloat] {pkg}: Not installed or already removed.")
            self.logger.success("[✓] Debloating complete.")
        threading.Thread(target=run, daemon=True).start()

    def _adb_list_packages(self):
        self.logger.info("Listing installed third-party packages...")
        def run():
            res = self._run_tool(["adb", "shell", "pm", "list", "packages", "-3"], capture_output=True, text=True)
            out = res.stdout.strip()
            if out:
                for line in out.splitlines():
                    self.logger.info(f"  {line.replace('package:', '')}")
            self.logger.success("[✓] Packages listed.")
        threading.Thread(target=run, daemon=True).start()

    # Fastboot actions
    def _on_slot_changed(self, choice):
        if "Set Active Slot: a" in choice:
            self.logger.info("Setting active slot to _a...")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "--set-active=a"], "Set Slot A"), daemon=True).start()
        elif "Set Active Slot: b" in choice:
            self.logger.info("Setting active slot to _b...")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "--set-active=b"], "Set Slot B"), daemon=True).start()

    def _fb_flash_boot(self):
        f = filedialog.askopenfilename(title="Select boot.img", filetypes=[("Disk Image", "boot*.img;*.img")])
        if f:
            self.logger.info(f"Flashing boot: {f}")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "flash", "boot", f], "Flash Boot"), daemon=True).start()

    def _fb_flash_recovery(self):
        f = filedialog.askopenfilename(title="Select recovery.img", filetypes=[("Disk Image", "recovery*.img;*.img")])
        if f:
            self.logger.info(f"Flashing recovery: {f}")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "flash", "recovery", f], "Flash Recovery"), daemon=True).start()

    def _fb_flash_super(self):
        f = filedialog.askopenfilename(title="Select super.img", filetypes=[("Disk Image", "super*.img;*.img")])
        if f:
            self.logger.info(f"Flashing super (High-Speed Fastboot): {f}")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "flash", "super", f], "Flash Super"), daemon=True).start()

    def _fb_flash_vbmeta(self):
        f = filedialog.askopenfilename(title="Select vbmeta.img", filetypes=[("Disk Image", "vbmeta*.img;*.img")])
        if f:
            self.logger.info(f"Flashing vbmeta with verity disabled: {f}")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "--disable-verity", "--disable-verification", "flash", "vbmeta", f], "Flash Vbmeta"), daemon=True).start()

    def _fb_flash_dtbo(self):
        f = filedialog.askopenfilename(title="Select dtbo.img", filetypes=[("Disk Image", "dtbo*.img;*.img")])
        if f:
            self.logger.info(f"Flashing dtbo: {f}")
            threading.Thread(target=self._run_cmd_log, args=(["fastboot", "flash", "dtbo", f], "Flash DTBO"), daemon=True).start()

    def _fb_unlock_bootloader(self):
        self.logger.warn("Sending OEM Unlock Command (fastboot flashing unlock)...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "flashing", "unlock"], "OEM Unlock"), daemon=True).start()

    def _fb_lock_bootloader(self):
        self.logger.warn("Sending OEM Lock Command (fastboot flashing lock)...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "flashing", "lock"], "OEM Lock"), daemon=True).start()

    def _fb_wipe_userdata(self):
        self.logger.warn("Wiping Userdata via Fastboot (fastboot -w)...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "-w"], "Wipe Userdata"), daemon=True).start()

    def _fb_erase_frp(self):
        self.logger.warn("Erasing FRP partition via Fastboot (fastboot erase frp)...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "erase", "frp"], "Erase FRP"), daemon=True).start()

    def _fb_reboot(self):
        self.logger.info("Rebooting device via Fastboot...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "reboot"], "Reboot"), daemon=True).start()

    def _fb_reboot_edl(self):
        self.logger.brom("Rebooting to Qualcomm EDL (fastboot oem edl / reboot-edl)...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "oem", "edl"], "Reboot EDL"), daemon=True).start()

    def _run_tool(self, cmd_args, **kwargs):
        """Executes adb or fastboot using bundled binaries from resources/platform-tools/"""
        args = list(cmd_args)
        args[0] = get_platform_tool_path(args[0])
        if sys.platform == "win32" and "creationflags" not in kwargs:
            kwargs["creationflags"] = 0x08000000
        return subprocess.run(args, **kwargs)

    def _run_cmd_log(self, cmd_list, tag):
        try:
            cmd = list(cmd_list)
            cmd[0] = get_platform_tool_path(cmd[0])
            cflags = 0x08000000 if sys.platform == "win32" else 0
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=cflags)
            for line in iter(p.stdout.readline, ''):
                line_s = line.strip()
                if line_s:
                    self.logger.info(f"[{tag}] {line_s}")
            p.stdout.close()
            p.wait()
            self.logger.success(f"[{tag}] Finished (Exit Code: {p.returncode})")
        except Exception as e:
            self.logger.error(f"[{tag}] Execution failed: {str(e)}")

    # -------------------------------------------------------------------------
    # INTERACTIVE FASTBOOT COMMAND TERMINAL & DUMP FLASHER
    # -------------------------------------------------------------------------
    def _set_and_run_fb_cmd(self, cmd_str):
        self.fb_custom_cmd_var.set(cmd_str)
        self._fb_run_custom_cmd()

    def _fb_run_custom_cmd(self):
        raw = self.fb_custom_cmd_var.get().strip()
        if not raw:
            return
        # Parse command
        parts = raw.split()
        if parts[0].lower() == "fastboot":
            parts = parts[1:]
        if not parts:
            return
        cmd = ["fastboot"] + parts
        self.logger.info(f"[Fastboot CLI] Executing: {' '.join(cmd)}")
        threading.Thread(target=self._run_cmd_log, args=(cmd, "Fastboot CLI"), daemon=True).start()

    def _detect_partition_name(self, filename: str) -> str:
        """Determines target partition name from image filename."""
        fn = filename.lower()
        patterns = [
            (r'abootbak', 'abootbak'),
            (r'aboot', 'aboot'),
            (r'^boot$|^boot[._]', 'boot'),
            (r'recovery', 'recovery'),
            (r'vbmeta_system', 'vbmeta_system'),
            (r'vbmeta_vendor', 'vbmeta_vendor'),
            (r'vbmeta', 'vbmeta'),
            (r'super', 'super'),
            (r'system_ext', 'system_ext'),
            (r'system', 'system'),
            (r'vendor', 'vendor'),
            (r'product', 'product'),
            (r'odm', 'odm'),
            (r'dtbo', 'dtbo'),
            (r'userdata', 'userdata'),
            (r'cust', 'cust'),
            (r'persist', 'persist'),
            (r'(modem|non-hlos)', 'modem'),
            (r'dsp', 'dsp'),
            (r'splash|logo', 'splash')
        ]
        for pat, p_name in patterns:
            if re.search(pat, fn):
                return p_name
        # Fallback: remove .img
        base = os.path.splitext(filename)[0]
        return base

    def _browse_rom_folder(self):
        """Scans a firmware dump folder and populates partition Treeview."""
        folder = filedialog.askdirectory(title="Select Stock ROM Dump / Firmware Folder")
        if not folder:
            return
        self.fb_rom_folder_var.set(folder)
        self._clear_fb_partitions()

        img_exts = (".img", ".bin", ".sin")
        found = 0
        for root, _, files in os.walk(folder):
            for f in sorted(files):
                if f.lower().endswith(img_exts):
                    p_path = os.path.join(root, f)
                    p_name = self._detect_partition_name(f)
                    f_size = os.path.getsize(p_path)
                    size_str = f"{f_size / (1024 * 1024):.1f} MB"
                    item_data = {
                        "check": True,
                        "partition": p_name,
                        "file": p_path,
                        "filename": f,
                        "size": size_str,
                        "status": "Ready"
                    }
                    self.fb_partitions.append(item_data)
                    found += 1
            break  # Scan top folder first

        self._refresh_fb_tree()
        self.logger.success(f"[Fastboot Flasher] Loaded {found} partition images from: {os.path.basename(folder)}")

    def _add_single_img(self):
        """Adds single or multiple disk image files manually."""
        files = filedialog.askopenfilenames(
            title="Select Partition Images to Flash",
            filetypes=[("Partition Images", "*.img;*.bin;*.sin"), ("All Files", "*.*")]
        )
        if not files:
            return
        for f in files:
            base_fn = os.path.basename(f)
            p_name = self._detect_partition_name(base_fn)
            f_size = os.path.getsize(f)
            size_str = f"{f_size / (1024 * 1024):.1f} MB"
            self.fb_partitions.append({
                "check": True,
                "partition": p_name,
                "file": f,
                "filename": base_fn,
                "size": size_str,
                "status": "Ready"
            })
        self._refresh_fb_tree()

    def _clear_fb_partitions(self):
        self.fb_partitions = []
        for item in self.tree_fb_parts.get_children():
            self.tree_fb_parts.delete(item)

    def _refresh_fb_tree(self):
        for item in self.tree_fb_parts.get_children():
            self.tree_fb_parts.delete(item)
        for i, p in enumerate(self.fb_partitions):
            chk_icon = "[✓]" if p["check"] else "[  ]"
            tag = "even" if i % 2 == 0 else "odd"
            self.tree_fb_parts.insert(
                "", "end",
                iid=str(i),
                values=(chk_icon, p["partition"], p["filename"], p["size"], p["status"]),
                tags=(tag,)
            )

    def _select_all_fb_partitions(self):
        for p in self.fb_partitions:
            p["check"] = True
        self._refresh_fb_tree()

    def _deselect_all_fb_partitions(self):
        for p in self.fb_partitions:
            p["check"] = False
        self._refresh_fb_tree()

    def _on_tree_fb_click(self, event):
        item_id = self.tree_fb_parts.identify_row(event.y)
        if not item_id:
            return
        idx = int(item_id)
        if 0 <= idx < len(self.fb_partitions):
            self.fb_partitions[idx]["check"] = not self.fb_partitions[idx]["check"]
            self._refresh_fb_tree()

    def _fb_flash_selected_partitions(self):
        selected = [p for p in self.fb_partitions if p["check"]]
        if not selected:
            messagebox.showwarning("Fastboot Flasher", "No partitions selected for flashing!\nCheck at least one partition.")
            return

        self.btn_fb_flash_all.configure(state="disabled", text="⚡ FLASHING IN PROGRESS...")
        disable_verity = self.fb_disable_verity_var.get()

        def worker():
            total = len(selected)
            self.logger.info(f"==================================================")
            self.logger.info(f"⚡ STARTING FASTBOOT BATCH FLASH: {total} Partitions")
            self.logger.info(f"==================================================")
            success_count = 0

            for i, p in enumerate(selected):
                part = p["partition"]
                filepath = p["file"]
                self.logger.info(f"[{i+1}/{total}] Flashing {part} -> {os.path.basename(filepath)}...")
                p["status"] = "Flashing..."
                self.tree_fb_parts.after(0, self._refresh_fb_tree)

                if part == "vbmeta" and disable_verity:
                    cmd = ["fastboot", "--disable-verity", "--disable-verification", "flash", "vbmeta", filepath]
                else:
                    cmd = ["fastboot", "flash", part, filepath]

                try:
                    c = list(cmd)
                    c[0] = get_platform_tool_path(c[0])
                    cflags = 0x08000000 if sys.platform == "win32" else 0
                    res = subprocess.run(c, capture_output=True, text=True, creationflags=cflags)
                    if res.returncode == 0:
                        p["status"] = "✓ OK"
                        success_count += 1
                        self.logger.success(f"[✓] Successfully flashed: {part}")
                    else:
                        p["status"] = "✗ Error"
                        err = res.stderr.strip() or res.stdout.strip()
                        self.logger.error(f"[-] Flash failed on {part}: {err}")
                except Exception as ex:
                    p["status"] = "✗ Error"
                    self.logger.error(f"[-] Flash error on {part}: {str(ex)}")

                self.tree_fb_parts.after(0, self._refresh_fb_tree)

            self.logger.info(f"==================================================")
            if success_count == total:
                self.logger.success(f"🎉 FASTBOOT FLASH COMPLETED SUCCESSFULLY! ({success_count}/{total} Partitions)")
                res = messagebox.askyesno("Flashing Complete", "All partitions flashed successfully!\nDo you want to reboot the system now?")
                if res:
                    self._fb_reboot()
            else:
                self.logger.warn(f"[Fastboot] Flashing finished with warnings: {success_count}/{total} succeeded.")
            self.logger.info(f"==================================================")
            self.btn_fb_flash_all.after(0, lambda: self.btn_fb_flash_all.configure(state="normal", text="⚡ FLASH SELECTED PARTITIONS (FASTBOOT)"))

        threading.Thread(target=worker, daemon=True).start()

    def _browse_sideload_zip(self):
        f = filedialog.askopenfilename(
            title="Select OTA / Sideload ZIP Package",
            filetypes=[("ZIP Archive", "*.zip"), ("All Files", "*.*")]
        )
        if f:
            self.sideload_zip_path_var.set(f)
            self.logger.info(f"Selected Sideload Package: {os.path.basename(f)}")

    def _adb_sideload_flash(self):
        zip_path = self.sideload_zip_path_var.get().strip()
        if not zip_path or not os.path.exists(zip_path):
            messagebox.showwarning("Select Package", "Please select a valid .zip file first.")
            return
        self.logger.info(f"Starting ADB Sideload: {os.path.basename(zip_path)}...")
        self.logger.info("Make sure the device is in Recovery mode with 'Apply update from ADB' active.")
        threading.Thread(target=self._run_cmd_log, args=(["adb", "sideload", zip_path], "ADB Sideload"), daemon=True).start()

    def _fb_reboot_fastbootd(self):
        self.logger.info("Rebooting device to FastbootD mode (fastboot reboot fastboot)...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "reboot", "fastboot"], "Reboot FastbootD"), daemon=True).start()

    def _fb_create_logical_part(self):
        pname = self.fb_logical_part_var.get().strip()
        psize = self.fb_logical_size_var.get().strip()
        if not pname or not psize:
            messagebox.showwarning("Missing Params", "Please specify partition name and size.")
            return
        self.logger.info(f"Creating logical partition: {pname} ({psize})...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "create-logical-partition", pname, psize], "Create Logical"), daemon=True).start()

    def _fb_resize_logical_part(self):
        pname = self.fb_logical_part_var.get().strip()
        psize = self.fb_logical_size_var.get().strip()
        if not pname or not psize:
            messagebox.showwarning("Missing Params", "Please specify partition name and size.")
            return
        self.logger.info(f"Resizing logical partition: {pname} to {psize}...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "resize-logical-partition", pname, psize], "Resize Logical"), daemon=True).start()

    def _fb_delete_logical_part(self):
        pname = self.fb_logical_part_var.get().strip()
        if not pname:
            messagebox.showwarning("Missing Params", "Please specify partition name.")
            return
        self.logger.warn(f"Deleting logical partition: {pname}...")
        threading.Thread(target=self._run_cmd_log, args=(["fastboot", "delete-logical-partition", pname], "Delete Logical"), daemon=True).start()

    def _mtp_read_info(self):
        self.logger.info("Scanning Windows Portable Devices (MTP / WPD)...")
        def run():
            try:
                ps_cmd = 'Get-PnpDevice -Class "WPD" | Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json'
                res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
                import json
                raw = res.stdout.strip()
                if raw:
                    try:
                        data = json.loads(raw)
                        devices = data if isinstance(data, list) else [data]
                        found = False
                        for d in devices:
                            fname = d.get("FriendlyName", "Unknown")
                            inst = d.get("InstanceId", "")
                            stat = d.get("Status", "OK")
                            if fname and stat == "OK":
                                found = True
                                self.logger.success(f"[MTP Device Found] {fname}")
                                self.logger.info(f"   Instance: {inst}")
                        if not found:
                            self.logger.warn("[MTP] No active WPD/MTP device found in OK status.")
                    except Exception:
                        self.logger.info(f"[MTP Scan] {raw}")
                else:
                    self.logger.warn("[MTP] No WPD (MTP) devices reported by system.")
            except Exception as e:
                self.logger.error(f"[MTP Scan Error] {str(e)}")
        threading.Thread(target=run, daemon=True).start()

    def _mtp_push_browser(self):
        url = self.mtp_url_var.get().strip()
        if not url:
            url = "https://www.youtube.com"
        self.logger.info(f"Triggering MTP Browser Intent Push for: {url}")
        def run():
            # Method 1: Check if ADB is alive
            adb_res = self._run_tool(["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url], capture_output=True, text=True)
            if "Starting:" in adb_res.stdout:
                self.logger.success("[✓] Browser Intent launched successfully via ADB channel.")
                return

            # Method 2: Check MTP / Modem Serial Port Notification
            self.logger.info("Scanning for USB Modem / Diagnostic interface for MTP intent...")
            try:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                modem_ports = [p.device for p in ports if any(k in (p.description or "").lower() for k in ["modem", "samsung", "huawei", "android"])]
                if modem_ports:
                    pname = modem_ports[0]
                    self.logger.info(f"Connecting to device interface on {pname}...")
                    import serial
                    with serial.Serial(pname, 115200, timeout=2) as ser:
                        ser.write(b"AT\r\n")
                        import time
                        time.sleep(0.3)
                        ser.write(f'AT+CTBL=1,"{url}"\r\n'.encode())
                        time.sleep(0.3)
                    self.logger.success(f"[✓] Push payload sent to {pname}.")
                else:
                    self.logger.warn("[MTP] Connected USB device is in pure MTP mode.")
                    self.logger.info("Tip: If device is at Setup Wizard, connect USB, ensure Samsung/CDC driver is installed.")
            except Exception as e:
                self.logger.error(f"[MTP Push] {str(e)}")
        threading.Thread(target=run, daemon=True).start()

    def _samsung_mtp_test_mode_frp(self):
        self.logger.info("Starting Samsung Factory Test Mode (*#0*#) Service...")
        self.logger.warn("Step 1: On phone Emergency Call screen, dial: *#0*# (or *#88# / *#*#88#*#*)")
        def run():
            import time
            import serial.tools.list_ports
            import serial

            samsung_port = None
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                desc = (p.description or "").lower()
                hwid = (p.hwid or "").lower()
                if "samsung" in desc or "04e8" in hwid or "modem" in desc:
                    samsung_port = p.device
                    break

            if not samsung_port and ports:
                samsung_port = ports[0].device
                self.logger.info(f"Targeting active COM port: {samsung_port}")

            if not samsung_port:
                self.logger.error("[!] No Samsung Modem or COM port detected. Connect phone via USB.")
                return

            self.logger.info(f"[+] Opening Samsung Modem Port ({samsung_port})...")
            try:
                with serial.Serial(samsung_port, 115200, timeout=2) as ser:
                    commands = [
                        b"AT\r\n",
                        b"AT+KSUART=0\r\n",
                        b"AT+SWAT=1\r\n",
                        b"AT+ACTIVATE=1\r\n"
                    ]
                    for cmd in commands:
                        ser.write(cmd)
                        time.sleep(0.4)
                        resp = ser.read(ser.in_waiting or 64)
                        if resp:
                            self.logger.info(f"  [Modem Response] {resp.decode(errors='ignore').strip()}")

                self.logger.success("[+] Diagnostic commands transmitted.")
                self.logger.info("[*] Check phone display: Tap 'Always allow from this computer' -> Allow.")
                time.sleep(3)

                self.logger.info("[*] Applying device setup configuration...")
                adb_res1 = self._run_tool(["adb", "shell", "settings", "put", "secure", "user_setup_complete", "1"], capture_output=True, text=True)
                adb_res2 = self._run_tool(["adb", "shell", "settings", "put", "global", "device_provisioned", "1"], capture_output=True, text=True)
                self._run_tool(["adb", "shell", "am", "start", "-c", "android.intent.category.HOME", "-a", "android.intent.action.MAIN"], capture_output=True)

                if adb_res1.returncode == 0 or adb_res2.returncode == 0:
                    self.logger.success("[✓] Samsung Service Routine Finished Successfully!")
                else:
                    self.logger.info("[*] Completed. If popup did not appear, redial *#0*# and retry.")
            except Exception as e:
                self.logger.error(f"[!] Samsung Test Mode Error: {str(e)}")
        threading.Thread(target=run, daemon=True).start()

    def show(self):
        self.left_panel_fb.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel_fb.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel_fb.grid_forget()
        self.center_panel_fb.grid_forget()
