import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from utils.file_utils import CORE_UNBRICK_PARTS, format_bytes
from core.model_repository import ModelRepository
from ui.theme import Theme
from ui.model_selector import SearchableModelSelector
from core.telemetry import FlashingTelemetry

class MTKView:
    """MediaTek (MTK) Servicing, Flashing, GPT Partition Manager, and META Suite View."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # Available MTK Brands from Repository (Prioritized Top MTK Brands)
        primary_mtk = ["Infinix", "Tecno", "Xiaomi", "Vivo", "Oppo", "Realme", "Samsung", "Motorola", "Lenovo", "Nokia", "Huawei", "Itel", "Blackview", "BLU", "Hisense", "Alcatel", "Generic MTK"]
        all_repo_brands = ModelRepository.get_all_brands()
        self.mtk_brands = [b for b in primary_mtk if b in all_repo_brands] + [b for b in all_repo_brands if b not in primary_mtk]
        if not self.mtk_brands:
            self.mtk_brands = ["Infinix", "Tecno", "Xiaomi", "Vivo", "Oppo", "Samsung", "Generic MTK"]

        default_brand = "Infinix" if "Infinix" in self.mtk_brands else self.mtk_brands[0]
        self.brand_var = tk.StringVar(value=default_brand)

        initial_models = ModelRepository.get_models_by_brand(default_brand)
        default_model = initial_models[0] if initial_models else "Auto-Detect (Universal MTK)"
        self.model_var = tk.StringVar(value=default_model)

        self.scatter_path_var = tk.StringVar()
        self.da_path_var = tk.StringVar()
        self.auth_path_var = tk.StringVar()
        self.preloader_path_var = tk.StringVar()
        self.chk_force_brom_var = tk.BooleanVar(value=True)
        self.chk_server_auth_var = tk.BooleanVar(value=True)
        self.chk_auto_backup_security_var = tk.BooleanVar(value=True)
        self.chk_auto_reboot_var = tk.BooleanVar(value=True)
        self.telemetry = FlashingTelemetry()
        self.search_flash_var = tk.StringVar()
        self.mtk_imei1_var = tk.StringVar(value="")
        self.mtk_imei2_var = tk.StringVar(value="")

        self.all_scatter_partitions = []
        self.live_gpt_partitions = []

        self._build_left_panel()
        self._build_center_panel()

        # Initial auto-bind
        self._on_model_changed(default_model)

    # -------------------------------------------------------------------------
    # LEFT PANEL
    # -------------------------------------------------------------------------
    def _build_left_panel(self):
        self.left_panel = ctk.CTkScrollableFrame(
            self.body_frame, 
            width=285, 
            fg_color=Theme.BG_PANEL, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # High-Speed Searchable Brand & Model Selector
        self.selector_widget = SearchableModelSelector(
            self.left_panel,
            brand_var=self.brand_var,
            model_var=self.model_var,
            controller=self.controller,
            on_model_selected=self._on_model_changed,
            on_brand_selected=self._on_brand_changed,
            accent_color=Theme.ACCENT_CYAN
        )
        self.selector_widget.pack(fill="x", padx=10, pady=(6, 8))
        self.brand_menu = self.selector_widget.brand_menu
        self.model_menu = self.selector_widget.model_menu

        # CONNECTIONS CARD
        conn_card = ctk.CTkFrame(
            self.left_panel, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        conn_card.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkLabel(
            conn_card, 
            text="CONNECTIONS", 
            font=Theme.font_bold(size=11), 
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkCheckBox(
            conn_card,
            text="Force Preloader To Brom",
            variable=self.chk_force_brom_var,
            font=Theme.font_ui(size=11),
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=3)

        ctk.CTkCheckBox(
            conn_card,
            text="User Server Auth / SLA Bypass",
            variable=self.chk_server_auth_var,
            font=Theme.font_ui(size=11),
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=3)

        ctk.CTkCheckBox(
            conn_card,
            text="🛡️ Auto-Backup NVRAM (Safe Shield)",
            variable=self.chk_auto_backup_security_var,
            font=Theme.font_bold(size=11),
            text_color="#10B981",
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=(3, 10))

        # CONFIGURATION CARD
        cfg_card = ctk.CTkFrame(
            self.left_panel, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        cfg_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            cfg_card, 
            text="CONFIGURATION", 
            font=Theme.font_bold(size=11), 
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Scatter File Picker
        ctk.CTkLabel(cfg_card, text="Scatter File:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        sct_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        sct_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(sct_row, textvariable=self.scatter_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(sct_row, text="📁", width=28, height=26, fg_color="#0284C7", command=self._browse_scatter).pack(side="right")

        # Preloader Picker
        ctk.CTkLabel(cfg_card, text="Preloader File:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        pl_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        pl_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(pl_row, textvariable=self.preloader_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(pl_row, text="📁", width=28, height=26, fg_color="#0284C7", command=self._browse_preloader).pack(side="right")

        # Download Agent (DA) Picker
        ctk.CTkLabel(cfg_card, text="Download Agent (DA):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        da_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        da_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(da_row, textvariable=self.da_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(da_row, text="📁", width=28, height=26, fg_color="#0284C7", command=self._browse_da).pack(side="right")

        # Authentication (Auth) Picker
        ctk.CTkLabel(cfg_card, text="Authentication (Auth):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        auth_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        auth_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(auth_row, textvariable=self.auth_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(auth_row, text="📁", width=28, height=26, fg_color="#0284C7", command=self._browse_auth).pack(side="right")

        # Restart After Job Checkbox
        ctk.CTkCheckBox(
            cfg_card,
            text="Restart / Reboot After Job",
            variable=self.chk_auto_reboot_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FBBF24",
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=(6, 12))

    # -------------------------------------------------------------------------
    # CENTER WORK PANEL
    # -------------------------------------------------------------------------
    def _build_center_panel(self):
        self.center_panel = ctk.CTkFrame(
            self.body_frame, 
            fg_color=Theme.BG_PANEL, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # Tab Navigation
        self.center_tab_selector = ctk.CTkSegmentedButton(
            self.center_panel,
            values=["⚡ Flash", "⚙️ Operation", "📋 Partition Manager", "🌐 META Mode"],
            command=self._on_center_tab_changed,
            font=Theme.font_bold(size=12),
            selected_color=Theme.ACCENT_BLUE,
            selected_hover_color=Theme.ACCENT_BLUE_HOVER,
            unselected_color=Theme.SURFACE_INPUT,
            unselected_hover_color=Theme.SURFACE_CARD,
            height=34
        )
        self.center_tab_selector.pack(fill="x", padx=12, pady=(10, 8))
        self.center_tab_selector.set("⚡ Flash")

        # Container for tab frames
        self.tab_container = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Build tabs
        self._build_tab_flash()
        self._build_tab_operation()
        self._build_tab_partition_mgr()
        self._build_tab_meta()

        self._show_tab("⚡ Flash")

    # --- TAB 1: FLASH ---
    def _build_tab_flash(self):
        self.frame_tab_flash = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        # Quick Selection Bar
        quick_bar = ctk.CTkFrame(
            self.frame_tab_flash, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        quick_bar.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            quick_bar,
            text="✓ Select All",
            width=80,
            height=26,
            font=Theme.font_ui(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._select_all_partitions
        ).pack(side="left", padx=6, pady=5)

        ctk.CTkButton(
            quick_bar,
            text="⚡ Select Bootloader Only (Fast Unbrick 20s)",
            height=26,
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            command=self._select_bootloader_only
        ).pack(side="left", padx=6, pady=5)

        ctk.CTkButton(
            quick_bar,
            text="✗ Deselect All",
            width=90,
            height=26,
            font=Theme.font_ui(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._deselect_all_partitions
        ).pack(side="left", padx=6, pady=5)

        # Search Bar
        self.search_flash_var.trace_add("write", lambda *args: self._filter_flash_table())
        ctk.CTkEntry(
            quick_bar,
            textvariable=self.search_flash_var,
            placeholder_text="Search partition...",
            font=Theme.font_ui(size=11),
            fg_color=Theme.SURFACE_INPUT,
            border_color=Theme.BORDER_CARD,
            height=26,
            width=140
        ).pack(side="right", padx=6, pady=5)

        # Treeview Partition Table
        tree_frame = ctk.CTkFrame(self.frame_tab_flash, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True)

        columns = ("check", "name", "file", "size", "offset", "status")
        self.tree_flash = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree_flash.heading("check", text="[✓]")
        self.tree_flash.heading("name", text="Partition")
        self.tree_flash.heading("file", text="Image File")
        self.tree_flash.heading("size", text="File Size")
        self.tree_flash.heading("offset", text="Start Offset")
        self.tree_flash.heading("status", text="Status")

        self.tree_flash.column("check", width=40, anchor="center")
        self.tree_flash.column("name", width=120, anchor="w")
        self.tree_flash.column("file", width=160, anchor="w")
        self.tree_flash.column("size", width=80, anchor="e")
        self.tree_flash.column("offset", width=95, anchor="center")
        self.tree_flash.column("status", width=75, anchor="center")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_flash.yview)
        self.tree_flash.configure(yscrollcommand=tree_scroll.set)
        self.tree_flash.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree_flash.tag_configure("even", background=Theme.TABLE_ROW_EVEN)
        self.tree_flash.tag_configure("odd", background=Theme.TABLE_ROW_ODD)
        self.tree_flash.bind("<ButtonRelease-1>", self._on_tree_flash_click)

        # DUAL PROGRESS HUD
        hud_card = ctk.CTkFrame(
            self.frame_tab_flash, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        hud_card.pack(fill="x", pady=(6, 6))

        self.lbl_flash_status = ctk.CTkLabel(
            hud_card,
            text="⚡ Status: Ready to Flash",
            font=Theme.font_bold(size=12),
            text_color=Theme.ACCENT_CYAN
        )
        self.lbl_flash_status.pack(anchor="w", padx=12, pady=(6, 2))

        self.lbl_file_progress = ctk.CTkLabel(
            hud_card,
            text="Active File Progress: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_file_progress.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_file = ctk.CTkProgressBar(hud_card, height=7, fg_color="#27272A", progress_color="#0284C7")
        self.bar_file.pack(fill="x", padx=12, pady=(0, 6))
        self.bar_file.set(0.0)

        self.lbl_overall_progress = ctk.CTkLabel(
            hud_card,
            text="Overall Firmware Progress: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_overall_progress.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_overall = ctk.CTkProgressBar(hud_card, height=7, fg_color="#27272A", progress_color="#10B981")
        self.bar_overall.pack(fill="x", padx=12, pady=(0, 4))
        self.bar_overall.set(0.0)

        # Telemetry & Speedometer Bar
        telemetry_row = ctk.CTkFrame(hud_card, fg_color="transparent")
        telemetry_row.pack(fill="x", padx=12, pady=(0, 6))

        self.lbl_flash_telemetry = ctk.CTkLabel(
            telemetry_row,
            text="⚡ Speed: -- MB/s | ⏱️ ETA: --:-- (Time: 00:00)",
            font=Theme.font_bold(size=10),
            text_color="#38BDF8"
        )
        self.lbl_flash_telemetry.pack(side="left")

        self.lbl_flash_bytes = ctk.CTkLabel(
            telemetry_row,
            text="0 MB / 0 MB",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_flash_bytes.pack(side="right")

        # ACTION BUTTONS BAR
        btn_action_bar = ctk.CTkFrame(self.frame_tab_flash, fg_color="transparent")
        btn_action_bar.pack(fill="x", pady=(2, 0))

        self.btn_flash_selected = ctk.CTkButton(
            btn_action_bar,
            text="⚡ FLASH SELECTED (UNBRICK)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=36,
            command=self.controller.start_flash_selected
        )
        self.btn_flash_selected.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_flash_all = ctk.CTkButton(
            btn_action_bar,
            text="⚡ FLASH ALL PARTITIONS",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            command=self.controller.start_flash_all
        )
        self.btn_flash_all.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_crash_brom = ctk.CTkButton(
            btn_action_bar,
            text="💥 CRASH TO BROM",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            height=36,
            command=self.controller.start_crash_brom
        )
        self.btn_crash_brom.pack(side="right", fill="x", expand=True, padx=(4, 0))

    # --- TAB 2: OPERATION (Professional 3-Card Architecture) ---
    def _build_tab_operation(self):
        self.frame_tab_op = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")

        # =========================================================================
        # CARD 1: ONE-CLICK SERVICE & BYPASS (Safe & Most Used)
        # =========================================================================
        card1 = ctk.CTkFrame(
            self.frame_tab_op,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        card1.pack(fill="x", padx=4, pady=(2, 8))

        c1_head = ctk.CTkFrame(card1, fg_color="transparent")
        c1_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            c1_head,
            text="🟢 ONE-CLICK SERVICE & BYPASS",
            font=Theme.font_bold(size=12),
            text_color="#38BDF8"
        ).pack(side="left")
        ctk.CTkLabel(
            c1_head,
            text="SAFE / ZERO DEAD RISK",
            font=Theme.font_ui(size=9),
            text_color="#10B981"
        ).pack(side="right")

        # Row 1: FRP & Safe Factory Reset
        c1_r1 = ctk.CTkFrame(card1, fg_color="transparent")
        c1_r1.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            c1_r1,
            text="🔓 Reset FRP (Google Lock)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.controller.op_reset_frp
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            c1_r1,
            text="🧹 Factory Reset (Safe Wipe)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            command=self.controller.op_factory_reset
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 2: Reset + FRP & Keep Data Format
        c1_r2 = ctk.CTkFrame(card1, fg_color="transparent")
        c1_r2.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            c1_r2,
            text="⚡ Factory Reset With FRP",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#0369A1",
            hover_color="#075985",
            command=self.controller.op_factory_reset_frp
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            c1_r2,
            text="🛡️ Safe Format (Keep Photos/Media)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#0891B2",
            hover_color="#0e7490",
            command=self.controller.op_safe_format
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 3: Demo Remove & DM-Verity Patch
        c1_r3 = ctk.CTkFrame(card1, fg_color="transparent")
        c1_r3.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            c1_r3,
            text="🔥 Demo Remove / Vendor Unlock",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.controller.op_demo_remove
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            c1_r3,
            text="🛡️ Patch DM-Verity / Red State",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.controller.op_patch_dm_verity
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 4: Read Info
        c1_r4 = ctk.CTkFrame(card1, fg_color="transparent")
        c1_r4.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            c1_r4,
            text="📱 Read Full Device Specifications & Hardware Info",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#334155",
            hover_color="#475569",
            command=self.controller.op_read_info
        ).pack(fill="x")

        # =========================================================================
        # CARD 2: BOOTLOADER & SYSTEM CONTROLS (Protected)
        # =========================================================================
        card2 = ctk.CTkFrame(
            self.frame_tab_op,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        card2.pack(fill="x", padx=4, pady=(0, 8))

        c2_head = ctk.CTkFrame(card2, fg_color="transparent")
        c2_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            c2_head,
            text="🔓 BOOTLOADER & SYSTEM CONTROLS",
            font=Theme.font_bold(size=12),
            text_color="#F59E0B"
        ).pack(side="left")
        ctk.CTkLabel(
            c2_head,
            text="CONFIRMATION REQUIRED",
            font=Theme.font_ui(size=9),
            text_color="#F59E0B"
        ).pack(side="right")

        c2_r1 = ctk.CTkFrame(card2, fg_color="transparent")
        c2_r1.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            c2_r1,
            text="🔓 Unlock Bootloader (Fastboot/BROM)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#D97706",
            hover_color="#B45309",
            command=self.controller.op_unlock_bootloader
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            c2_r1,
            text="🔒 Relock Bootloader (DevInfo Verification)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#B45309",
            hover_color="#92400E",
            command=self.controller.op_relock_bootloader
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        c2_r2 = ctk.CTkFrame(card2, fg_color="transparent")
        c2_r2.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            c2_r2,
            text="🔄 Reboot Device (Normal Power Cycle)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#059669",
            hover_color="#047857",
            command=self.controller.op_reboot_device
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            c2_r2,
            text="⚡ Reboot to Fastboot Mode",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#047857",
            hover_color="#065F46",
            command=self.controller.op_reboot_fastboot
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # =========================================================================
        # CARD 3: RPMB & LOW-LEVEL HARDWARE (Advanced Operations)
        # =========================================================================
        card3 = ctk.CTkFrame(
            self.frame_tab_op,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        card3.pack(fill="x", padx=4, pady=(0, 6))

        c3_head = ctk.CTkFrame(card3, fg_color="transparent")
        c3_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            c3_head,
            text="⚡ RPMB & LOW-LEVEL HARDWARE",
            font=Theme.font_bold(size=12),
            text_color="#EC4899"
        ).pack(side="left")
        ctk.CTkLabel(
            c3_head,
            text="ENGINEER ONLY",
            font=Theme.font_ui(size=9),
            text_color="#EC4899"
        ).pack(side="right")

        c3_r1 = ctk.CTkFrame(card3, fg_color="transparent")
        c3_r1.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            c3_r1,
            text="💾 Read RPMB",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#334155",
            hover_color="#1E293B",
            command=self.controller.op_read_rpmb
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ctk.CTkButton(
            c3_r1,
            text="✍️ Write RPMB (Fused Key)",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#334155",
            hover_color="#1E293B",
            command=self.controller.op_write_rpmb
        ).pack(side="left", fill="x", expand=True, padx=3)
        ctk.CTkButton(
            c3_r1,
            text="🗑️ Erase RPMB",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#334155",
            hover_color="#1E293B",
            command=self.controller.op_erase_rpmb
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))

    # --- TAB 3: PARTITION MANAGER (GPT) ---
    def _build_tab_partition_mgr(self):
        self.frame_tab_pmgr = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        top_pmgr = ctk.CTkFrame(self.frame_tab_pmgr, fg_color="#1C1C24", corner_radius=6)
        top_pmgr.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            top_pmgr,
            text="🔍 Read Live GPT Table from Phone",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284C7",
            height=28,
            command=self.controller.read_live_gpt
        ).pack(side="left", padx=8, pady=4)

        tree_pmgr_frame = ctk.CTkFrame(self.frame_tab_pmgr, fg_color="transparent")
        tree_pmgr_frame.pack(fill="both", expand=True)

        cols_pm = ("idx", "name", "offset", "length", "size")
        self.tree_pmgr = ttk.Treeview(tree_pmgr_frame, columns=cols_pm, show="headings", selectmode="browse")
        self.tree_pmgr.heading("idx", text="#")
        self.tree_pmgr.heading("name", text="Partition Name")
        self.tree_pmgr.heading("offset", text="Start Offset")
        self.tree_pmgr.heading("length", text="Length (Hex)")
        self.tree_pmgr.heading("size", text="Size")

        self.tree_pmgr.column("idx", width=40, anchor="center")
        self.tree_pmgr.column("name", width=160, anchor="w")
        self.tree_pmgr.column("offset", width=120, anchor="center")
        self.tree_pmgr.column("length", width=120, anchor="center")
        self.tree_pmgr.column("size", width=100, anchor="e")

        pmgr_scroll = ttk.Scrollbar(tree_pmgr_frame, orient="vertical", command=self.tree_pmgr.yview)
        self.tree_pmgr.configure(yscrollcommand=pmgr_scroll.set)
        self.tree_pmgr.pack(side="left", fill="both", expand=True)
        pmgr_scroll.pack(side="right", fill="y")

        pmgr_action = ctk.CTkFrame(self.frame_tab_pmgr, fg_color="transparent")
        pmgr_action.pack(fill="x", pady=(6, 0))

        ctk.CTkButton(pmgr_action, text="📥 Dump Selected Partition", height=34, fg_color="#0284C7", command=self.controller.pmgr_dump_partition).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(pmgr_action, text="📤 Flash Selected Partition", height=34, fg_color="#059669", command=self.controller.pmgr_write_partition).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(pmgr_action, text="🗑️ Erase Selected Partition", height=34, fg_color="#DC2626", command=self.controller.pmgr_erase_partition).pack(side="right", fill="x", expand=True, padx=(4, 0))

    # --- TAB 4: META & GSM REPAIR ---
    def _build_tab_meta(self):
        self.frame_tab_meta = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")

        lbl_info = ctk.CTkLabel(
            self.frame_tab_meta,
            text="MediaTek META & BROM Hardware Repair Suite (IMEI / NVRAM)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00D2FF"
        )
        lbl_info.pack(pady=(4, 8))

        # Card 1: IMEI Repair Inputs
        imei_card = ctk.CTkFrame(self.frame_tab_meta, fg_color="#181820", corner_radius=8)
        imei_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(imei_card, text="IMEI REPAIR CONFIGURATION (15 Digits / Auto-Luhn)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 4))

        i_row1 = ctk.CTkFrame(imei_card, fg_color="transparent")
        i_row1.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(i_row1, text="IMEI 1:", width=60, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkEntry(i_row1, textvariable=self.mtk_imei1_var, placeholder_text="e.g. 358941091234567", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True)

        i_row2 = ctk.CTkFrame(imei_card, fg_color="transparent")
        i_row2.pack(fill="x", padx=12, pady=(3, 8))
        ctk.CTkLabel(i_row2, text="IMEI 2:", width=60, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkEntry(i_row2, textvariable=self.mtk_imei2_var, placeholder_text="e.g. 358941091234568 (Optional)", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True)

        # Dual Repair Action Buttons
        btn_imei_row = ctk.CTkFrame(imei_card, fg_color="transparent")
        btn_imei_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            btn_imei_row,
            text="✍️ Write IMEI (META Mode)",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.controller.meta_write_imei
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_imei_row,
            text="⚡ Write IMEI (BROM Flash Mode)",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=self.controller.brom_write_imei
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 2: NVRAM Backup & Restore
        nv_card = ctk.CTkFrame(self.frame_tab_meta, fg_color="#181820", corner_radius=8)
        nv_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(nv_card, text="NVRAM & RF CALIBRATION BACKUP / RESTORE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 4))

        nv_btn_row = ctk.CTkFrame(nv_card, fg_color="transparent")
        nv_btn_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            nv_btn_row,
            text="💾 Backup NVRAM (nvdata/nvcfg)",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.controller.meta_backup_nvram
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            nv_btn_row,
            text="🛡️ Restore NVRAM Calibration",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.controller.meta_restore_nvram
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 3: META Diagnostic Controls
        meta_grid = ctk.CTkFrame(self.frame_tab_meta, fg_color="#181820", corner_radius=8)
        meta_grid.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(meta_grid, text="META MODE CONTROLS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 4))

        m_r1 = ctk.CTkFrame(meta_grid, fg_color="transparent")
        m_r1.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(m_r1, text="🌐 Connect Device in META Mode", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#4F46E5", command=self.controller.meta_connect).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(m_r1, text="📋 Read Hardware & NVRAM Info", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#4F46E5", command=self.controller.meta_read_info).pack(side="left", fill="x", expand=True, padx=(4, 0))

        m_r2 = ctk.CTkFrame(meta_grid, fg_color="transparent")
        m_r2.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(m_r2, text="🧹 Factory Reset in META Mode", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#7C3AED", command=self.controller.meta_factory_reset).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(m_r2, text="🔄 Reboot Device from META to Normal", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#059669", command=self.controller.meta_reboot).pack(side="left", fill="x", expand=True, padx=(4, 0))

    # -------------------------------------------------------------------------
    # TAB SWITCHING & HELPERS
    # -------------------------------------------------------------------------
    def _show_tab(self, tab_name):
        self.frame_tab_flash.pack_forget()
        self.frame_tab_op.pack_forget()
        self.frame_tab_pmgr.pack_forget()
        self.frame_tab_meta.pack_forget()

        if tab_name == "⚡ Flash":
            self.frame_tab_flash.pack(fill="both", expand=True)
        elif tab_name == "⚙️ Operation":
            self.frame_tab_op.pack(fill="both", expand=True)
        elif tab_name == "📋 Partition Manager":
            self.frame_tab_pmgr.pack(fill="both", expand=True)
        elif tab_name == "🌐 META Mode":
            self.frame_tab_meta.pack(fill="both", expand=True)

    def _on_center_tab_changed(self, value):
        self._show_tab(value)

    def _on_brand_changed(self, choice):
        da_path = ModelRepository.find_brand_da(choice)
        if da_path:
            self.da_path_var.set(da_path)
            self.logger.info(f"Auto-bound Brand DA: {os.path.basename(da_path)}")

    def _on_model_changed(self, choice, details=None):
        brand = self.brand_var.get()
        if not details or not isinstance(details, dict):
            details = ModelRepository.get_model_details(brand, choice)
        if details:
            # 1. Preloader auto-binding
            pl_file = details.get("preloader_file")
            if pl_file:
                pl_path = ModelRepository.find_preloader_file(pl_file)
                if pl_path:
                    self.preloader_path_var.set(pl_path)
                    self.logger.info(f"Auto-bound Preloader: {os.path.basename(pl_path)}")

            # 2. Brand-Specific DA & Universal DA auto-binding
            da_path = ModelRepository.find_brand_da(brand)
            if not da_path:
                loader_name = details.get("loader_file", "MTK_DA_V6.bin")
                da_path = ModelRepository.find_loader_file("mtk", loader_name)
            if not da_path:
                da_path = ModelRepository.get_default_allinone_da()
            if da_path:
                self.da_path_var.set(da_path)
                self.logger.info(f"Auto-bound Download Agent (DA): {os.path.basename(da_path)}")

            # 3. SLA/DAA Auth Payload auto-binding
            chipset_str = details.get("chipset", "")
            m = re.search(r'(mt\d{4})', chipset_str, re.IGNORECASE)
            if m:
                soc_code = m.group(1).lower()
                payload_path = ModelRepository.find_payload_file(soc_code)
                if payload_path:
                    self.auth_path_var.set(payload_path)
                    self.logger.info(f"Auto-bound Auth Payload: {os.path.basename(payload_path)}")

    def _browse_scatter(self):
        fpath = filedialog.askopenfilename(
            title="Select MediaTek Scatter File",
            filetypes=[("Scatter Files", "*scatter*.txt"), ("All Files", "*.*")]
        )
        if fpath:
            self.scatter_path_var.set(fpath)
            self.controller.load_scatter_details(fpath)

    def _browse_preloader(self):
        fpath = filedialog.askopenfilename(
            title="Select Custom Preloader",
            filetypes=[("Preloader Bin", "preloader*.bin"), ("Binary Files", "*.bin"), ("All Files", "*.*")]
        )
        if fpath:
            self.preloader_path_var.set(fpath)
            self.logger.info(f"Custom Preloader Selected: {os.path.basename(fpath)}")

    def _browse_da(self):
        from core.path_utils import get_resource_path
        brand_da_dir = get_resource_path("loaders", "mtk", "brand_da")
        init_dir = brand_da_dir if os.path.exists(brand_da_dir) else None
        fpath = filedialog.askopenfilename(
            initialdir=init_dir,
            title="Select Download Agent (DA)",
            filetypes=[("DA & Loader Files", "*.bin;*.da;*.crp"), ("All Files", "*.*")]
        )
        if fpath:
            self.da_path_var.set(fpath)
            self.logger.info(f"Custom DA Attached: {os.path.basename(fpath)}")

    def _browse_auth(self):
        fpath = filedialog.askopenfilename(
            title="Select Authentication File (Auth)",
            filetypes=[("Auth Files", "*.auth"), ("All Files", "*.*")]
        )
        if fpath:
            self.auth_path_var.set(fpath)
            self.logger.info(f"Custom Auth Attached: {os.path.basename(fpath)}")

    def populate_flash_table(self, partitions):
        for item in self.tree_flash.get_children():
            self.tree_flash.delete(item)

        for idx, p in enumerate(partitions):
            check_str = "✓" if p.get("is_checked", False) else " "
            status = "Ready" if p.get("exists", False) else "Missing"
            fname = p.get("file_name", "NONE")
            fsize = p.get("file_size_human", "--")
            start_addr = p.get("start_addr", "--")
            tag = "even" if idx % 2 == 0 else "odd"

            item_id = self.tree_flash.insert(
                "",
                "end",
                values=(check_str, p.get("name"), fname, fsize, start_addr, status),
                tags=(tag,)
            )
            p["tree_id"] = item_id

    def _filter_flash_table(self):
        query = self.search_flash_var.get().strip().lower()
        if not query:
            self.populate_flash_table(self.all_scatter_partitions)
            return

        filtered = [p for p in self.all_scatter_partitions if query in p.get("name", "").lower() or query in p.get("file_name", "").lower()]
        self.populate_flash_table(filtered)

    def _on_tree_flash_click(self, event):
        region = self.tree_flash.identify_region(event.x, event.y)
        if region == "heading":
            return
        item_id = self.tree_flash.identify_row(event.y)
        if not item_id:
            return

        vals = list(self.tree_flash.item(item_id, "values"))
        p_name = vals[1]

        for p in self.all_scatter_partitions:
            if p.get("name") == p_name:
                p["is_checked"] = not p.get("is_checked", False)
                vals[0] = "✓" if p["is_checked"] else " "
                self.tree_flash.item(item_id, values=vals)
                break

    def _select_all_partitions(self):
        for p in self.all_scatter_partitions:
            if p.get("exists", False):
                p["is_checked"] = True
        self.populate_flash_table(self.all_scatter_partitions)
        self.logger.info("All existing firmware partitions selected.")

    def _deselect_all_partitions(self):
        for p in self.all_scatter_partitions:
            p["is_checked"] = False
        self.populate_flash_table(self.all_scatter_partitions)
        self.logger.info("All partitions deselected.")

    def _select_bootloader_only(self):
        selected_count = 0
        for p in self.all_scatter_partitions:
            name = p.get("name", "").lower()
            if name in [cp.lower() for cp in CORE_UNBRICK_PARTS] and p.get("exists", False):
                p["is_checked"] = True
                selected_count += 1
            else:
                p["is_checked"] = False

        self.populate_flash_table(self.all_scatter_partitions)
        self.logger.success(f"Fast Unbrick Active: Selected {selected_count} Core Bootloader partitions (super.img excluded).")
        self.logger.info("This flashes in ~20 seconds to bring display and logo alive!")

    def populate_pmgr_table(self, partitions):
        for item in self.tree_pmgr.get_children():
            self.tree_pmgr.delete(item)

        for p in partitions:
            self.tree_pmgr.insert(
                "",
                "end",
                values=(p.get("index"), p.get("name"), p.get("offset"), p.get("length"), p.get("size_human"))
            )

    def update_hud(self, overall, file_pct, part_name, status_text):
        self.bar_file.set(file_pct)
        self.bar_overall.set(overall)
        self.lbl_flash_status.configure(text=f"⚡ {status_text}")
        self.lbl_file_progress.configure(text=f"Active Partition ({part_name}): {int(file_pct * 100)}%")
        self.lbl_overall_progress.configure(text=f"Overall Flashing Progress: {int(overall * 100)}%")
        m = self.telemetry.update(overall)
        self.lbl_flash_telemetry.configure(text=m["summary"])
        self.lbl_flash_bytes.configure(text=m["transferred_text"])

    def set_buttons_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_flash_selected.configure(state=state)
        self.btn_flash_all.configure(state=state)
        self.btn_crash_brom.configure(state=state)

    def show(self):
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel.grid_forget()
        self.center_panel.grid_forget()
