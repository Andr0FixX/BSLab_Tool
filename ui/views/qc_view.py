import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from engines.qualcomm.xml_parser import QualcommXMLParser
from core.model_repository import ModelRepository
from ui.theme import Theme
from ui.model_selector import SearchableModelSelector
from core.telemetry import FlashingTelemetry

class QualcommView:
    """Qualcomm Snapdragon (EDL 9008) Servicing, Flashing, and QCN/EFS View."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.BRAND_MAP = {
            "Xiaomi / Redmi": "xiaomi",
            "Samsung": "samsung",
            "Oppo / Realme": "oppo",
            "Vivo": "vivo",
            "Lenovo / Motorola": "lenovo_motorola",
            "OnePlus": "oneplus",
            "ZTE / RedMagic": "zte",
            "Nokia / HMD": "nokia_foxconn",
            "Asus / ROG": "asus_wingtech",
            "Schok": "schok",
            "Universal Qualcomm": "qualcomm"
        }
        self.qc_brand_var = tk.StringVar(value="Xiaomi / Redmi")
        self.qc_model_var = tk.StringVar(value="Auto-Detect (Sahara Handshake)")
        self.qc_prog_path_var = tk.StringVar()
        self.qc_rawprog_path_var = tk.StringVar()
        self.qc_patch_path_var = tk.StringVar()
        self.qc_chk_auto_backup_efs_var = tk.BooleanVar(value=True)
        self.qc_chk_reboot_var = tk.BooleanVar(value=True)
        self.telemetry = FlashingTelemetry()
        self.qc_qcn_path_var = tk.StringVar()
        self.qc_imei1_var = tk.StringVar(value="")
        self.qc_imei2_var = tk.StringVar(value="")
        self.qc_lun_filter_var = tk.StringVar(value="All LUNs")

        self.all_qc_partitions = []

        self._build_left_panel()
        self._build_center_panel()

    def _build_left_panel(self):
        self.left_panel_qc = ctk.CTkScrollableFrame(
            self.body_frame, 
            width=285, 
            fg_color=Theme.BG_PANEL, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # High-Speed Searchable Brand & Model Selector
        self.selector_widget = SearchableModelSelector(
            self.left_panel_qc,
            brand_var=self.qc_brand_var,
            model_var=self.qc_model_var,
            controller=self.controller,
            on_model_selected=self._on_model_changed,
            on_brand_selected=self._on_brand_changed,
            accent_color=Theme.ACCENT_GOLD
        )
        self.selector_widget.pack(fill="x", padx=10, pady=(6, 8))
        self.qc_brand_menu = self.selector_widget.brand_menu
        self.qc_model_menu = self.selector_widget.model_menu

        # EDL 9008 CARD
        edl_card = ctk.CTkFrame(
            self.left_panel_qc, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        edl_card.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkLabel(
            edl_card, 
            text="EDL 9008 CONNECTION", 
            font=Theme.font_bold(size=11), 
            text_color="#FDE68A"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            edl_card,
            text="Mode: Qualcomm HS-USB QDLoader 9008\n(Connect via Test Point or EDL Cable)",
            font=Theme.font_ui(size=10),
            text_color=Theme.TEXT_SECONDARY,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkCheckBox(
            edl_card,
            text="🛡️ Auto-Backup EFS Guard",
            variable=self.qc_chk_auto_backup_efs_var,
            font=Theme.font_bold(size=11),
            text_color="#10B981",
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # CONFIGURATION CARD
        cfg_qc_card = ctk.CTkFrame(
            self.left_panel_qc, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        cfg_qc_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            cfg_qc_card, 
            text="FIREHOSE & XML CONFIG", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="#FDE68A"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Programmer (MBN/ELF)
        ctk.CTkLabel(cfg_qc_card, text="Programmer (Firehose MBN/ELF):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        prog_row = ctk.CTkFrame(cfg_qc_card, fg_color="transparent")
        prog_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(prog_row, textvariable=self.qc_prog_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(prog_row, text="📁", width=28, height=26, fg_color="#D97706", command=self._browse_prog).pack(side="right")

        # RawProgram XML
        ctk.CTkLabel(cfg_qc_card, text="RawProgram XML:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        raw_row = ctk.CTkFrame(cfg_qc_card, fg_color="transparent")
        raw_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(raw_row, textvariable=self.qc_rawprog_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(raw_row, text="📁", width=28, height=26, fg_color="#D97706", command=self._browse_rawprog).pack(side="right")

        # Patch XML
        ctk.CTkLabel(cfg_qc_card, text="Patch XML:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        patch_row = ctk.CTkFrame(cfg_qc_card, fg_color="transparent")
        patch_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkEntry(patch_row, textvariable=self.qc_patch_path_var, font=ctk.CTkFont(size=10), height=26, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(patch_row, text="📁", width=28, height=26, fg_color="#D97706", command=self._browse_patch).pack(side="right")

        ctk.CTkButton(
            cfg_qc_card,
            text="📂 Load Firmware Directory (Auto-Detect XML)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            height=28,
            command=self._browse_firmware_dir
        ).pack(fill="x", padx=10, pady=(4, 6))

        ctk.CTkCheckBox(
            cfg_qc_card,
            text="Reboot to System After Job",
            variable=self.qc_chk_reboot_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FBBF24",
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=(6, 12))

    def _build_center_panel(self):
        self.center_panel_qc = ctk.CTkFrame(
            self.body_frame, 
            fg_color=Theme.BG_PANEL, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        self.center_tab_qc = ctk.CTkSegmentedButton(
            self.center_panel_qc,
            values=["⚡ EDL Flasher", "⚙️ Service / FRP", "💾 Backup QCN / EFS"],
            command=self._on_tab_changed,
            font=Theme.font_bold(size=12),
            selected_color=Theme.ACCENT_GOLD_HOVER,
            selected_hover_color=Theme.ACCENT_GOLD,
            unselected_color=Theme.SURFACE_INPUT,
            unselected_hover_color=Theme.SURFACE_CARD,
            height=34
        )
        self.center_tab_qc.pack(fill="x", padx=12, pady=(10, 8))
        self.center_tab_qc.set("⚡ EDL Flasher")

        self.tab_container_qc = ctk.CTkFrame(self.center_panel_qc, fg_color="transparent")
        self.tab_container_qc.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # -------------------------------------------------------------
        # QC Tab 1: EDL Flasher
        # -------------------------------------------------------------
        self.frame_qc_flash = ctk.CTkFrame(self.tab_container_qc, fg_color="transparent")
        qc_info = ctk.CTkFrame(
            self.frame_qc_flash, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        qc_info.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            qc_info,
            text="🐉 Qualcomm Snapdragon EDL 9008 High-Speed Partition Flasher",
            font=Theme.font_bold(size=12),
            text_color=Theme.ACCENT_GOLD
        ).pack(side="left", padx=12, pady=6)

        ctk.CTkButton(
            qc_info,
            text="✓ Select All",
            width=80,
            height=26,
            font=Theme.font_ui(size=10),
            fg_color="#334155",
            hover_color="#475569",
            command=self._select_all_qc_partitions
        ).pack(side="right", padx=6, pady=4)

        ctk.CTkButton(
            qc_info,
            text="✗ Deselect All",
            width=85,
            height=26,
            font=Theme.font_ui(size=10),
            fg_color="#334155",
            hover_color="#475569",
            command=self._deselect_all_qc_partitions
        ).pack(side="right", padx=4, pady=4)

        # UFS Multi-LUN Storage Filter
        lun_bar = ctk.CTkFrame(
            self.frame_qc_flash, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        lun_bar.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(lun_bar, text="💾 UFS LUN Storage:", font=Theme.font_bold(size=10), text_color="#A5B4FC").pack(side="left", padx=10, pady=4)
        
        self.lun_menu = ctk.CTkSegmentedButton(
            lun_bar,
            values=["All LUNs", "LUN 0", "LUN 1", "LUN 2", "LUN 3", "LUN 4", "LUN 5"],
            variable=self.qc_lun_filter_var,
            font=Theme.font_bold(size=10),
            selected_color=Theme.ACCENT_GOLD_HOVER,
            unselected_color=Theme.SURFACE_INPUT,
            unselected_hover_color=Theme.SURFACE_CARD,
            command=self._on_lun_filter_changed
        )
        self.lun_menu.pack(side="left", fill="x", expand=True, padx=8, pady=4)

        qc_tree_frame = ctk.CTkFrame(self.frame_qc_flash, fg_color="transparent")
        qc_tree_frame.pack(fill="both", expand=True)

        cols_qc = ("check", "name", "file", "lun", "sector", "num_sectors", "size")
        self.tree_qc = ttk.Treeview(qc_tree_frame, columns=cols_qc, show="headings", selectmode="browse")
        self.tree_qc.heading("check", text="[✓]")
        self.tree_qc.heading("name", text="Partition Name")
        self.tree_qc.heading("file", text="Image Filename")
        self.tree_qc.heading("lun", text="LUN")
        self.tree_qc.heading("sector", text="Start Sector")
        self.tree_qc.heading("num_sectors", text="Sectors")
        self.tree_qc.heading("size", text="File Size")

        self.tree_qc.column("check", width=36, anchor="center")
        self.tree_qc.column("name", width=135, anchor="w")
        self.tree_qc.column("file", width=160, anchor="w")
        self.tree_qc.column("lun", width=55, anchor="center")
        self.tree_qc.column("sector", width=95, anchor="center")
        self.tree_qc.column("num_sectors", width=85, anchor="center")
        self.tree_qc.column("size", width=80, anchor="e")

        tree_qc_scroll = ttk.Scrollbar(qc_tree_frame, orient="vertical", command=self.tree_qc.yview)
        self.tree_qc.configure(yscrollcommand=tree_qc_scroll.set)
        self.tree_qc.pack(side="left", fill="both", expand=True)
        tree_qc_scroll.pack(side="right", fill="y")
        self.tree_qc.tag_configure("even", background=Theme.TABLE_ROW_EVEN)
        self.tree_qc.tag_configure("odd", background=Theme.TABLE_ROW_ODD)
        self.tree_qc.bind("<ButtonRelease-1>", self._on_tree_qc_click)

        # QC Dual Progress HUD
        qc_hud = ctk.CTkFrame(
            self.frame_qc_flash, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        qc_hud.pack(fill="x", pady=(6, 6))

        self.lbl_qc_status = ctk.CTkLabel(
            qc_hud,
            text="🐉 Status: Ready to Flash Qualcomm EDL 9008",
            font=Theme.font_bold(size=12),
            text_color=Theme.ACCENT_GOLD
        )
        self.lbl_qc_status.pack(anchor="w", padx=12, pady=(6, 2))

        self.lbl_qc_file_progress = ctk.CTkLabel(
            qc_hud,
            text="Active Partition Progress: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_qc_file_progress.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_qc_file = ctk.CTkProgressBar(qc_hud, height=7, fg_color="#27272A", progress_color="#D97706")
        self.bar_qc_file.pack(fill="x", padx=12, pady=(0, 6))
        self.bar_qc_file.set(0.0)

        self.lbl_qc_overall_progress = ctk.CTkLabel(
            qc_hud,
            text="Overall Firmware Progress: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_qc_overall_progress.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_qc_overall = ctk.CTkProgressBar(qc_hud, height=7, fg_color="#27272A", progress_color="#10B981")
        self.bar_qc_overall.pack(fill="x", padx=12, pady=(0, 4))
        self.bar_qc_overall.set(0.0)

        # Telemetry & Speedometer Bar
        telemetry_row = ctk.CTkFrame(qc_hud, fg_color="transparent")
        telemetry_row.pack(fill="x", padx=12, pady=(0, 6))

        self.lbl_qc_telemetry = ctk.CTkLabel(
            telemetry_row,
            text="⚡ Speed: -- MB/s | ⏱️ ETA: --:-- (Time: 00:00)",
            font=Theme.font_bold(size=10),
            text_color="#FDE68A"
        )
        self.lbl_qc_telemetry.pack(side="left")

        self.lbl_qc_bytes = ctk.CTkLabel(
            telemetry_row,
            text="0 MB / 0 MB",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_qc_bytes.pack(side="right")

        # Action Buttons
        qc_action_bar = ctk.CTkFrame(self.frame_qc_flash, fg_color="transparent")
        qc_action_bar.pack(fill="x", pady=(2, 0))

        self.btn_qc_flash_selected = ctk.CTkButton(
            qc_action_bar,
            text="⚡ FLASH SELECTED (EDL)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#D97706",
            hover_color="#B45309",
            height=36,
            command=self.controller.qc_flash_selected
        )
        self.btn_qc_flash_selected.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_qc_flash_all = ctk.CTkButton(
            qc_action_bar,
            text="⚡ FLASH ALL RAWPROGRAM",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            command=self.controller.qc_flash_all
        )
        self.btn_qc_flash_all.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_qc_reboot = ctk.CTkButton(
            qc_action_bar,
            text="🔄 REBOOT DEVICE (NORMAL)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=36,
            command=self.controller.qc_reboot
        )
        self.btn_qc_reboot.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # -------------------------------------------------------------
        # QC Tab 2: Service / FRP (Professional 3-Card Architecture)
        # -------------------------------------------------------------
        self.frame_qc_service = ctk.CTkScrollableFrame(self.tab_container_qc, fg_color="transparent")

        # =========================================================================
        # CARD 1: ONE-CLICK SERVICE & BYPASS (Safe & Universal)
        # =========================================================================
        qc_card1 = ctk.CTkFrame(
            self.frame_qc_service,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        qc_card1.pack(fill="x", padx=4, pady=(2, 8))

        qc_c1_head = ctk.CTkFrame(qc_card1, fg_color="transparent")
        qc_c1_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            qc_c1_head,
            text="🟢 ONE-CLICK SERVICE & BYPASS",
            font=Theme.font_bold(size=12),
            text_color="#F59E0B"
        ).pack(side="left")
        ctk.CTkLabel(
            qc_c1_head,
            text="SAFE / ZERO DEAD RISK",
            font=Theme.font_ui(size=9),
            text_color="#10B981"
        ).pack(side="right")

        qc_r1 = ctk.CTkFrame(qc_card1, fg_color="transparent")
        qc_r1.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            qc_r1,
            text="🔓 Reset FRP (Google Lock)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.controller.qc_reset_frp
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            qc_r1,
            text="🧹 Factory Reset (Format Userdata)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            command=self.controller.qc_factory_reset
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        qc_r2 = ctk.CTkFrame(qc_card1, fg_color="transparent")
        qc_r2.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            qc_r2,
            text="⚡ Factory Reset With FRP",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#0369A1",
            hover_color="#075985",
            command=self.controller.qc_factory_reset_frp
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            qc_r2,
            text="📱 Read Device Info (EDL 9008)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.controller.qc_read_info
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # =========================================================================
        # CARD 2: EFS & BASEBAND SECURITY (Modem Protection)
        # =========================================================================
        qc_card2 = ctk.CTkFrame(
            self.frame_qc_service,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        qc_card2.pack(fill="x", padx=4, pady=(0, 8))

        qc_c2_head = ctk.CTkFrame(qc_card2, fg_color="transparent")
        qc_c2_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            qc_c2_head,
            text="💾 EFS & BASEBAND SECURITY",
            font=Theme.font_bold(size=12),
            text_color="#10B981"
        ).pack(side="left")
        ctk.CTkLabel(
            qc_c2_head,
            text="NV & IMEI BACKUP",
            font=Theme.font_ui(size=9),
            text_color="#38BDF8"
        ).pack(side="right")

        qc_r3 = ctk.CTkFrame(qc_card2, fg_color="transparent")
        qc_r3.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            qc_r3,
            text="💾 Backup EFS / Modem (modemst1/2)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#059669",
            hover_color="#047857",
            command=self.controller.qc_backup_efs
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            qc_r3,
            text="🛡️ Restore EFS / Network Calibration",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#059669",
            hover_color="#047857",
            command=self.controller.qc_restore_efs
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # =========================================================================
        # CARD 3: BOOTLOADER & SYSTEM CONTROLS (Protected)
        # =========================================================================
        qc_card3 = ctk.CTkFrame(
            self.frame_qc_service,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        qc_card3.pack(fill="x", padx=4, pady=(0, 6))

        qc_c3_head = ctk.CTkFrame(qc_card3, fg_color="transparent")
        qc_c3_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            qc_c3_head,
            text="🔓 BOOTLOADER & POWER CONTROLS",
            font=Theme.font_bold(size=12),
            text_color="#F59E0B"
        ).pack(side="left")
        ctk.CTkLabel(
            qc_c3_head,
            text="CONFIRMATION REQUIRED",
            font=Theme.font_ui(size=9),
            text_color="#F59E0B"
        ).pack(side="right")

        qc_r4 = ctk.CTkFrame(qc_card3, fg_color="transparent")
        qc_r4.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            qc_r4,
            text="🔓 Unlock Bootloader (EDL Method)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#D97706",
            hover_color="#B45309",
            command=self.controller.qc_unlock_bootloader
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            qc_r4,
            text="🔒 Relock Bootloader (DevInfo Verification)",
            font=Theme.font_bold(size=11),
            height=36,
            fg_color="#B45309",
            hover_color="#92400E",
            command=self.controller.qc_relock_bootloader
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        qc_r5 = ctk.CTkFrame(qc_card3, fg_color="transparent")
        qc_r5.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            qc_r5,
            text="🔄 Reboot to Normal System",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.controller.qc_reboot
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            qc_r5,
            text="⚡ Reboot to Fastboot Mode",
            font=Theme.font_bold(size=11),
            height=34,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.controller.qc_reboot_fastboot
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        # -------------------------------------------------------------
        # QC Tab 3: QCN / Network
        # -------------------------------------------------------------
        self.frame_qc_qcn = ctk.CTkScrollableFrame(self.tab_container_qc, fg_color="transparent")

        ctk.CTkLabel(
            self.frame_qc_qcn, 
            text="Qualcomm QCN / Diagnostic Port Network & IMEI Repair", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="#F59E0B"
        ).pack(pady=(4, 8))

        # Card 1: QCN File Config
        qcn_file_card = ctk.CTkFrame(self.frame_qc_qcn, fg_color="#181820", corner_radius=8)
        qcn_file_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(qcn_file_card, text="QCN CALIBRATION ARCHIVE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FDE68A").pack(anchor="w", padx=12, pady=(8, 4))
        
        qcn_row = ctk.CTkFrame(qcn_file_card, fg_color="transparent")
        qcn_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkEntry(qcn_row, textvariable=self.qc_qcn_path_var, placeholder_text="Select stock/backup .qcn file...", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(qcn_row, text="📁", width=30, height=30, fg_color="#D97706", hover_color="#B45309", command=self._browse_qcn).pack(side="right")

        # Card 2: IMEI Repair Input
        qcn_imei_card = ctk.CTkFrame(self.frame_qc_qcn, fg_color="#181820", corner_radius=8)
        qcn_imei_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(qcn_imei_card, text="QUALCOMM IMEI REPAIR (NV Item 550 / Auto-Luhn Check)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FDE68A").pack(anchor="w", padx=12, pady=(8, 4))

        qi_r1 = ctk.CTkFrame(qcn_imei_card, fg_color="transparent")
        qi_r1.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(qi_r1, text="IMEI 1:", width=60, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkEntry(qi_r1, textvariable=self.qc_imei1_var, placeholder_text="e.g. 861234031234567", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True)

        qi_r2 = ctk.CTkFrame(qcn_imei_card, fg_color="transparent")
        qi_r2.pack(fill="x", padx=12, pady=(3, 10))
        ctk.CTkLabel(qi_r2, text="IMEI 2:", width=60, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkEntry(qi_r2, textvariable=self.qc_imei2_var, placeholder_text="e.g. 861234031234568 (Optional)", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True)

        # Card 3: Action Buttons
        qcn_action_card = ctk.CTkFrame(self.frame_qc_qcn, fg_color="#181820", corner_radius=8)
        qcn_action_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(qcn_action_card, text="DIAGNOSTIC & RESTORATION ACTIONS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FDE68A").pack(anchor="w", padx=12, pady=(8, 4))

        qa_r1 = ctk.CTkFrame(qcn_action_card, fg_color="transparent")
        qa_r1.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(qa_r1, text="📱 Read IMEI & Info (Diag Port)", height=38, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8", command=self.controller.qc_read_imei_diag).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(qa_r1, text="📤 Write QCN with Repaired IMEI", height=38, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#059669", hover_color="#047857", command=self.controller.qc_write_qcn_imei).pack(side="left", fill="x", expand=True, padx=(4, 0))

        qa_r2 = ctk.CTkFrame(qcn_action_card, fg_color="transparent")
        qa_r2.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(qa_r2, text="💾 Create Patched QCN File", height=38, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#D97706", hover_color="#B45309", command=self.controller.qc_patch_qcn_file).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(qa_r2, text="🧹 Wipe EFS (Null Baseband Fix / EDL)", height=38, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#DC2626", hover_color="#B91C1C", command=self.controller.qc_wipe_efs).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._show_tab("⚡ EDL Flasher")

    def _show_tab(self, tab_name):
        self.frame_qc_flash.pack_forget()
        self.frame_qc_service.pack_forget()
        self.frame_qc_qcn.pack_forget()

        if tab_name == "⚡ EDL Flasher":
            self.frame_qc_flash.pack(fill="both", expand=True)
        elif tab_name == "⚙️ Service / FRP":
            self.frame_qc_service.pack(fill="both", expand=True)
        elif tab_name == "💾 Backup QCN / EFS":
            self.frame_qc_qcn.pack(fill="both", expand=True)

    def _on_tab_changed(self, value):
        self._show_tab(value)

    GENERIC_SNAPDRAGON_CHIPSETS = [
        "⚡ Generic Qualcomm 215 / QM215 (eMMC)",
        "⚡ Generic Snapdragon 680 (SM6225)",
        "⚡ Generic Snapdragon 695 5G (SM6375)",
        "⚡ Generic Snapdragon 665 / 662 (SM6125 / SM6115)",
        "⚡ Generic Snapdragon 720G / 730G / 732G (SM7125 / SM7150)",
        "⚡ Generic Snapdragon 778G 5G (SM7325)",
        "⚡ Generic Snapdragon 865 / 870 (SM8250)",
        "⚡ Generic Snapdragon 888 / 888+ (SM8350)",
        "⚡ Generic Snapdragon 8 Gen 1 (SM8450)",
        "⚡ Generic Snapdragon 660 / 636 (SDM660 / SDM636)",
        "⚡ Generic Snapdragon 625 / 450 (MSM8953 / SDM450)",
        "⚡ Generic Snapdragon 460 / 439 (SM4250 / SDM439)",
        "⚡ Generic Snapdragon 425 / 430 (MSM8917 / MSM8937)"
    ]

    def _get_models_for_brand(self, brand_display: str) -> list:
        models = ["Auto-Detect (Sahara Handshake)"]

        # 1. Fetch clean, verified human-readable phone models from ModelRepository
        db_brand = brand_display.split(" / ")[0].strip()
        db_models = [m for m in ModelRepository.get_models_by_brand(db_brand) 
                     if (ModelRepository.get_model_details(db_brand, m) or {}).get("platform") == "qualcomm"]
        models.extend(db_models)

        # 2. Append clean Generic Snapdragon Chipsets (NO raw hex filenames!)
        models.extend(self.GENERIC_SNAPDRAGON_CHIPSETS)

        return models

    def _on_brand_changed(self, choice):
        self.logger.info(f"Qualcomm Brand Selected: {choice}")

    def _on_model_changed(self, choice, details=None):
        if choice == "Auto-Detect (Sahara Handshake)":
            self.qc_prog_path_var.set("")
            self.logger.info("Qualcomm Auto-Detect Active: Connect phone in EDL 9008 mode for instant Sahara matching.")
            return

        brand_display = self.qc_brand_var.get()
        db_brand = brand_display.split(" / ")[0].strip()
        if not details or not isinstance(details, dict):
            details = ModelRepository.get_model_details(db_brand, choice)

        if details:
            loader_name = details.get("loader_file")
            chipset_info = details.get("chipset", "")
            self.logger.info(f"Selected: {choice} | Chipset: {chipset_info}")
            if loader_name:
                loader_path = ModelRepository.find_loader_file("qualcomm", loader_name)
                if loader_path and os.path.exists(loader_path):
                    self.qc_prog_path_var.set(loader_path)
                    self.logger.success(f"Attached Firehose Loader: {os.path.basename(loader_path)}")
                    return
            # If named loader file isn't found directly, try matching by SoC
            soc_match = re.search(r'(sm\d{4}|sdm\d{3}|msm\d{4})', chipset_info, re.IGNORECASE)
            if soc_match:
                soc_code = soc_match.group(1).lower()
                brand_slug = self.BRAND_MAP.get(brand_display, "qualcomm")
                loader_path = ModelRepository.match_qualcomm_loader(hwid=soc_code, brand=brand_slug)
                if loader_path and os.path.exists(loader_path):
                    self.qc_prog_path_var.set(loader_path)
                    self.logger.success(f"Auto-bound Firehose for {choice}: {os.path.basename(loader_path)}")
                    return

        # Check Generic Snapdragon Chipsets
        if choice.startswith("⚡ Generic"):
            if "215" in choice.lower() or "qm215" in choice.lower():
                loader_path = ModelRepository.find_loader_file("qualcomm", "prog_emmc_firehose_QM215.mbn")
                if loader_path and os.path.exists(loader_path):
                    self.qc_prog_path_var.set(loader_path)
                    self.logger.success(f"Attached Dedicated QM215 Firehose: {os.path.basename(loader_path)}")
                    return
            soc_match = re.search(r'\((SM\d+|SDM\d+|MSM\d+|QM\d+)', choice, re.IGNORECASE)
            if soc_match:
                soc_str = soc_match.group(1).lower()
                loader_path = ModelRepository.match_qualcomm_loader(hwid=soc_str, brand="qualcomm")
                if not loader_path:
                    loader_path = ModelRepository.match_qualcomm_loader(hwid=soc_str)
                if loader_path and os.path.exists(loader_path):
                    self.qc_prog_path_var.set(loader_path)
                    self.logger.success(f"Attached Reference Firehose for {choice}: {os.path.basename(loader_path)}")
                    return

    def auto_match_device_loader(self, hwid: str, pkhash: str = None) -> bool:
        """Called upon Sahara handshake to automatically load the exact firehose programmer."""
        brand_slug = self.BRAND_MAP.get(self.qc_brand_var.get(), None)
        loader_path = ModelRepository.match_qualcomm_loader(hwid=hwid, pkhash=pkhash, brand=brand_slug)
        if loader_path and os.path.exists(loader_path):
            self.qc_prog_path_var.set(loader_path)
            self.logger.success(f"Sahara Auto-Match: Loaded Firehose -> {os.path.basename(loader_path)}")
            return True
        return False

    def _browse_prog(self):
        f = filedialog.askopenfilename(title="Select Qualcomm Firehose Programmer", filetypes=[("Programmer Files", "*.elf;*.mbn;*.bin"), ("All Files", "*.*")])
        if f:
            self.qc_prog_path_var.set(f)
            self.logger.info(f"Qualcomm Firehose Programmer Attached: {os.path.basename(f)}")

    def _browse_rawprog(self):
        f = filedialog.askopenfilename(title="Select RawProgram XML", filetypes=[("XML Files", "rawprogram*.xml;*.xml"), ("All Files", "*.*")])
        if f:
            self.qc_rawprog_path_var.set(f)
            self.logger.info(f"Qualcomm RawProgram XML Attached: {os.path.basename(f)}")
            self.load_rawprogram_details(f)

    def _browse_patch(self):
        f = filedialog.askopenfilename(title="Select Patch XML", filetypes=[("XML Files", "patch*.xml;*.xml"), ("All Files", "*.*")])
        if f:
            self.qc_patch_path_var.set(f)
            self.logger.info(f"Qualcomm Patch XML Attached: {os.path.basename(f)}")

    def _browse_qcn(self):
        f = filedialog.askopenfilename(title="Select Qualcomm QCN File", filetypes=[("QCN Files", "*.qcn;*.xqcn;*.bin"), ("All Files", "*.*")])
        if f:
            self.qc_qcn_path_var.set(f)
            self.logger.info(f"Qualcomm QCN Calibration File Attached: {os.path.basename(f)}")

    def _browse_firmware_dir(self):
        d = filedialog.askdirectory(title="Select Qualcomm Firmware Directory")
        if d:
            self.logger.info(f"Scanning directory: {d}")
            for root, _, files in os.walk(d):
                for file in files:
                    fl = file.lower()
                    if fl.startswith("prog_firehose") and (fl.endswith(".elf") or fl.endswith(".mbn")):
                        self.qc_prog_path_var.set(os.path.join(root, file))
                    elif fl.startswith("rawprogram") and fl.endswith(".xml"):
                        self.qc_rawprog_path_var.set(os.path.join(root, file))
                        self.load_rawprogram_details(os.path.join(root, file))
                    elif fl.startswith("patch") and fl.endswith(".xml"):
                        self.qc_patch_path_var.set(os.path.join(root, file))
            self.logger.success("Auto-Detected Qualcomm Firehose XML and Programmer files!")

    def load_rawprogram_details(self, xml_path: str):
        try:
            fw_dir = os.path.dirname(xml_path)
            all_parts = QualcommXMLParser.parse_all_rawprograms(fw_dir)
            if all_parts and len(all_parts) > 0:
                parts = all_parts
                msg = f"Auto-Loaded {len(parts)} partitions across all UFS LUNs in directory."
            else:
                parts = QualcommXMLParser.parse_rawprogram(xml_path)
                msg = f"Parsed RawProgram XML: {os.path.basename(xml_path)} ({len(parts)} partitions detected)"

            self.all_qc_partitions = parts
            self._on_lun_filter_changed(self.qc_lun_filter_var.get())
            self.logger.success(msg)
        except Exception as e:
            self.logger.error(f"Failed to parse RawProgram XML: {str(e)}")

    def _on_lun_filter_changed(self, choice: str):
        if not self.all_qc_partitions:
            return
        if choice in ("All LUNs", "All"):
            filtered = self.all_qc_partitions
        else:
            try:
                lun_num = int(choice.replace("LUN", "").strip())
                filtered = [p for p in self.all_qc_partitions if p.get("lun", 0) == lun_num]
            except Exception:
                filtered = self.all_qc_partitions
        self.populate_qc_table(filtered)

    def populate_qc_table(self, partitions):
        for item in self.tree_qc.get_children():
            self.tree_qc.delete(item)

        for idx, p in enumerate(partitions):
            check_str = "✓" if p.get("is_checked", False) else " "
            lun_num = p.get("lun", p.get("physical_partition", 0))
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree_qc.insert(
                "",
                "end",
                values=(
                    check_str,
                    p.get("name"),
                    p.get("filename"),
                    f"LUN {lun_num}",
                    f"0x{p.get('start_sector'):X}",
                    p.get("num_sectors"),
                    p.get("file_size_human", "--")
                ),
                tags=(tag,)
            )

    def _on_tree_qc_click(self, event):
        item_id = self.tree_qc.identify_row(event.y)
        if not item_id:
            return

        vals = list(self.tree_qc.item(item_id, "values"))
        p_name = vals[1]

        for p in self.all_qc_partitions:
            if p.get("name") == p_name:
                p["is_checked"] = not p.get("is_checked", False)
                vals[0] = "✓" if p["is_checked"] else " "
                self.tree_qc.item(item_id, values=vals)
                break

    def _select_all_qc_partitions(self):
        for p in self.all_qc_partitions:
            if p.get("exists", False):
                p["is_checked"] = True
        self.populate_qc_table(self.all_qc_partitions)
        self.logger.info("All existing Qualcomm partitions selected.")

    def _deselect_all_qc_partitions(self):
        for p in self.all_qc_partitions:
            p["is_checked"] = False
        self.populate_qc_table(self.all_qc_partitions)
        self.logger.info("All Qualcomm partitions deselected.")

    def update_hud(self, overall, file_pct, part_name, status_text):
        self.bar_qc_file.set(file_pct)
        self.bar_qc_overall.set(overall)
        self.lbl_qc_status.configure(text=f"🐉 {status_text}")
        self.lbl_qc_file_progress.configure(text=f"Active Partition ({part_name}): {int(file_pct * 100)}%")
        self.lbl_qc_overall_progress.configure(text=f"Overall Flashing Progress: {int(overall * 100)}%")
        m = self.telemetry.update(overall)
        self.lbl_qc_telemetry.configure(text=m["summary"])
        self.lbl_qc_bytes.configure(text=m["transferred_text"])

    def show(self):
        self.left_panel_qc.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel_qc.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel_qc.grid_forget()
        self.center_panel_qc.grid_forget()
