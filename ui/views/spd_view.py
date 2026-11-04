import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from engines.unisoc.pac_parser import PacParser
from core.model_repository import ModelRepository
from ui.theme import Theme
from ui.model_selector import SearchableModelSelector
from core.telemetry import FlashingTelemetry

class UnisocView:
    """Unisoc / Spreadtrum (SPD) PAC Flasher & High-Speed Service View."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.spd_brands = ["Realme", "Infinix", "Tecno", "Motorola", "Samsung Unisoc", "Generic Unisoc"]
        self.spd_brand_var = tk.StringVar(value="Realme")
        self.spd_chip_var = tk.StringVar(value="Realme C21Y (RMX3261)")
        self.spd_pac_path_var = tk.StringVar()
        self.spd_chk_auto_backup_nv_var = tk.BooleanVar(value=True)
        self.spd_chk_reboot_var = tk.BooleanVar(value=True)
        self.telemetry = FlashingTelemetry()
        self.spd_imei1_var = tk.StringVar(value="")
        self.spd_imei2_var = tk.StringVar(value="")

        self.all_spd_partitions = []
        self.current_pac_meta = {}

        self._build_left_panel()
        self._build_center_panel()

    def _build_left_panel(self):
        self.left_panel_spd = ctk.CTkScrollableFrame(self.body_frame, width=285, fg_color="#141418", corner_radius=8)

        # High-Speed Searchable Brand & Model Selector
        self.selector_widget = SearchableModelSelector(
            self.left_panel_spd,
            brand_var=self.spd_brand_var,
            model_var=self.spd_chip_var,
            controller=self.controller,
            on_model_selected=self._on_model_changed,
            on_brand_selected=self._on_brand_changed,
            accent_color="#10B981"
        )
        self.selector_widget.pack(fill="x", padx=10, pady=(6, 8))
        self.spd_brand_menu = self.selector_widget.brand_menu
        self.spd_chip_menu = self.selector_widget.model_menu

        # BSL CONNECTION CARD
        bsl_card = ctk.CTkFrame(self.left_panel_spd, fg_color="#1A1A22", corner_radius=6)
        bsl_card.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkLabel(
            bsl_card, 
            text="BSL / DIAG CONNECTION", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="#C7D2FE"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            bsl_card,
            text="Mode: Unisoc SPRD U2S Diag / BSL\n(Hold Vol- / Both Vol while connecting USB)",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8",
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkCheckBox(
            bsl_card,
            text="🛡️ Auto-Backup NV Guard",
            variable=self.spd_chk_auto_backup_nv_var,
            font=Theme.font_bold(size=11),
            text_color="#10B981",
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # PAC FIRMWARE CONFIG CARD
        cfg_spd_card = ctk.CTkFrame(self.left_panel_spd, fg_color="#1A1A22", corner_radius=6)
        cfg_spd_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            cfg_spd_card, 
            text="PAC FIRMWARE ARCHIVE", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="#C7D2FE"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(cfg_spd_card, text="Select Unisoc .PAC File:", font=ctk.CTkFont(size=10), text_color="#CBD5E1").pack(anchor="w", padx=10, pady=(2, 0))
        pac_row = ctk.CTkFrame(cfg_spd_card, fg_color="transparent")
        pac_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkEntry(
            pac_row, 
            textvariable=self.spd_pac_path_var, 
            placeholder_text="Optional - Universal FDL1/FDL2 Built-in Active (*.pac)...",
            font=ctk.CTkFont(size=10), 
            height=26, 
            fg_color="#0F0F12"
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            pac_row, 
            text="📁", 
            width=28, 
            height=26, 
            fg_color="#4F46E5", 
            hover_color="#4338CA",
            command=self._browse_pac
        ).pack(side="right")

        # Flashing options
        self.chk_spd_reboot = ctk.CTkCheckBox(
            cfg_spd_card,
            text="Auto-Reboot After Flashing",
            variable=self.spd_chk_reboot_var,
            font=ctk.CTkFont(size=10),
            text_color="#E2E8F0"
        )
        self.chk_spd_reboot.pack(anchor="w", padx=10, pady=(4, 10))

    def _build_center_panel(self):
        self.center_panel_spd = ctk.CTkFrame(self.body_frame, fg_color="#141418", corner_radius=8)

        # Tab Segmented Button
        self.center_tab_spd = ctk.CTkSegmentedButton(
            self.center_panel_spd,
            values=["⚡ PAC Flasher", "⚙️ Service / FRP", "📶 IMEI & NVRAM"],
            command=self._on_tab_changed,
            font=ctk.CTkFont(size=12, weight="bold"),
            selected_color="#4F46E5",
            selected_hover_color="#4338CA",
            height=34
        )
        self.center_tab_spd.pack(fill="x", padx=12, pady=(10, 8))
        self.center_tab_spd.set("⚡ PAC Flasher")

        self.tab_container_spd = ctk.CTkFrame(self.center_panel_spd, fg_color="transparent")
        self.tab_container_spd.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # -------------------------------------------------------------
        # Unisoc Tab 1: PAC Flasher
        # -------------------------------------------------------------
        self.frame_spd_flash = ctk.CTkFrame(self.tab_container_spd, fg_color="transparent")

        spd_info = ctk.CTkFrame(self.frame_spd_flash, fg_color="#1C1C24", corner_radius=6)
        spd_info.pack(fill="x", pady=(0, 6))

        self.lbl_pac_meta = ctk.CTkLabel(
            spd_info,
            text="📱 Unisoc / Spreadtrum PAC High-Speed Flasher (Tiger T606/T612/T616, SC9863A)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A5B4FC"
        )
        self.lbl_pac_meta.pack(side="left", padx=12, pady=6)

        ctk.CTkButton(
            spd_info,
            text="✓ Select All",
            width=80,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="#334155",
            command=self._select_all_spd_partitions
        ).pack(side="right", padx=6, pady=4)

        ctk.CTkButton(
            spd_info,
            text="✗ Deselect All",
            width=85,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="#334155",
            command=self._deselect_all_spd_partitions
        ).pack(side="right", padx=4, pady=4)

        spd_tree_frame = ctk.CTkFrame(self.frame_spd_flash, fg_color="transparent")
        spd_tree_frame.pack(fill="both", expand=True)

        cols_spd = ("check", "name", "file", "offset", "size")
        self.tree_spd = ttk.Treeview(spd_tree_frame, columns=cols_spd, show="headings", selectmode="browse")
        self.tree_spd.heading("check", text="[✓]")
        self.tree_spd.heading("name", text="Partition Name")
        self.tree_spd.heading("file", text="Embedded Image")
        self.tree_spd.heading("offset", text="PAC Offset")
        self.tree_spd.heading("size", text="File Size")

        self.tree_spd.column("check", width=40, anchor="center")
        self.tree_spd.column("name", width=140, anchor="w")
        self.tree_spd.column("file", width=220, anchor="w")
        self.tree_spd.column("offset", width=110, anchor="center")
        self.tree_spd.column("size", width=100, anchor="e")

        tree_spd_scroll = ttk.Scrollbar(spd_tree_frame, orient="vertical", command=self.tree_spd.yview)
        self.tree_spd.configure(yscrollcommand=tree_spd_scroll.set)
        self.tree_spd.pack(side="left", fill="both", expand=True)
        tree_spd_scroll.pack(side="right", fill="y")
        self.tree_spd.bind("<ButtonRelease-1>", self._on_tree_spd_click)

        # Unisoc Dual Progress HUD
        spd_hud = ctk.CTkFrame(self.frame_spd_flash, fg_color="#181820", corner_radius=6)
        spd_hud.pack(fill="x", pady=(6, 6))

        self.lbl_spd_status = ctk.CTkLabel(
            spd_hud,
            text="📱 Status: Ready to Flash Unisoc PAC Firmware",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A5B4FC"
        )
        self.lbl_spd_status.pack(anchor="w", padx=12, pady=(6, 2))

        self.lbl_spd_file_progress = ctk.CTkLabel(
            spd_hud,
            text="Active Partition Progress: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_spd_file_progress.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_spd_file = ctk.CTkProgressBar(spd_hud, height=7, fg_color="#27272A", progress_color="#6366F1")
        self.bar_spd_file.pack(fill="x", padx=12, pady=(0, 6))
        self.bar_spd_file.set(0.0)

        self.lbl_spd_overall_progress = ctk.CTkLabel(
            spd_hud,
            text="Overall PAC Firmware Progress: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_spd_overall_progress.pack(anchor="w", padx=12, pady=(0, 2))

        self.bar_spd_overall = ctk.CTkProgressBar(spd_hud, height=7, fg_color="#27272A", progress_color="#10B981")
        self.bar_spd_overall.pack(fill="x", padx=12, pady=(0, 4))
        self.bar_spd_overall.set(0.0)

        # Telemetry & Speedometer Bar
        telemetry_row = ctk.CTkFrame(spd_hud, fg_color="transparent")
        telemetry_row.pack(fill="x", padx=12, pady=(0, 6))

        self.lbl_spd_telemetry = ctk.CTkLabel(
            telemetry_row,
            text="⚡ Speed: -- MB/s | ⏱️ ETA: --:-- (Time: 00:00)",
            font=Theme.font_bold(size=10),
            text_color="#C7D2FE"
        )
        self.lbl_spd_telemetry.pack(side="left")

        self.lbl_spd_bytes = ctk.CTkLabel(
            telemetry_row,
            text="0 MB / 0 MB",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_spd_bytes.pack(side="right")

        # Flasher Action Buttons
        spd_action_bar = ctk.CTkFrame(self.frame_spd_flash, fg_color="transparent")
        spd_action_bar.pack(fill="x", pady=(2, 0))

        self.btn_spd_flash_selected = ctk.CTkButton(
            spd_action_bar,
            text="⚡ FLASH SELECTED (PAC)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            height=36,
            command=self.controller.spd_flash_selected
        )
        self.btn_spd_flash_selected.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_spd_flash_pac = ctk.CTkButton(
            spd_action_bar,
            text="⚡ FLASH FULL PAC FIRMWARE",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=36,
            command=self.controller.spd_flash_pac
        )
        self.btn_spd_flash_pac.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_spd_reboot = ctk.CTkButton(
            spd_action_bar,
            text="🔄 REBOOT DEVICE (NORMAL)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#1E293B",
            height=36,
            command=self.controller.spd_reboot
        )
        self.btn_spd_reboot.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # -------------------------------------------------------------
        # Unisoc Tab 2: Service / FRP (Professional 3-Card Architecture)
        # -------------------------------------------------------------
        self.frame_spd_service = ctk.CTkScrollableFrame(self.tab_container_spd, fg_color="transparent")

        # =========================================================================
        # CARD 1: ONE-CLICK SERVICE & BYPASS (Safe & Universal)
        # =========================================================================
        spd_card1 = ctk.CTkFrame(
            self.frame_spd_service,
            fg_color="#181820",
            corner_radius=8,
            border_width=1,
            border_color="#2D2D3A"
        )
        spd_card1.pack(fill="x", padx=4, pady=(2, 8))

        spd_c1_head = ctk.CTkFrame(spd_card1, fg_color="transparent")
        spd_c1_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            spd_c1_head,
            text="🟢 ONE-CLICK SERVICE & BYPASS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10B981"
        ).pack(side="left")
        ctk.CTkLabel(
            spd_c1_head,
            text="UNIVERSAL MASTER FDL ACTIVE",
            font=ctk.CTkFont(size=9),
            text_color="#38BDF8"
        ).pack(side="right")

        spd_r1 = ctk.CTkFrame(spd_card1, fg_color="transparent")
        spd_r1.pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(
            spd_r1,
            text="🔓 Reset FRP (Google Lock - persist/misc)",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=36,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.controller.spd_reset_frp
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            spd_r1,
            text="🧹 Factory Reset (Format Userdata/Metadata)",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=36,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            command=self.controller.spd_factory_reset
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        spd_r2 = ctk.CTkFrame(spd_card1, fg_color="transparent")
        spd_r2.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            spd_r2,
            text="📱 Read Full Device Info (Unisoc Diag / Flash)",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=34,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.controller.spd_read_info
        ).pack(fill="x")

        # =========================================================================
        # CARD 2: SYSTEM & REBOOT CONTROLS
        # =========================================================================
        spd_card2 = ctk.CTkFrame(
            self.frame_spd_service,
            fg_color="#181820",
            corner_radius=8,
            border_width=1,
            border_color="#2D2D3A"
        )
        spd_card2.pack(fill="x", padx=4, pady=(0, 8))

        spd_c2_head = ctk.CTkFrame(spd_card2, fg_color="transparent")
        spd_c2_head.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            spd_c2_head,
            text="🔄 POWER & REBOOT CONTROLS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F59E0B"
        ).pack(side="left")

        spd_r3 = ctk.CTkFrame(spd_card2, fg_color="transparent")
        spd_r3.pack(fill="x", padx=10, pady=(3, 10))
        ctk.CTkButton(
            spd_r3,
            text="🔄 Reboot Device to Normal System",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=36,
            fg_color="#059669",
            hover_color="#047857",
            command=self.controller.spd_reboot
        ).pack(fill="x")

        # -------------------------------------------------------------
        # Unisoc Tab 3: IMEI & NVRAM Suite
        # -------------------------------------------------------------
        self.frame_spd_nv = ctk.CTkScrollableFrame(self.tab_container_spd, fg_color="transparent")

        ctk.CTkLabel(
            self.frame_spd_nv,
            text="Unisoc / Spreadtrum IMEI & Baseband Calibration Suite",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#A5B4FC"
        ).pack(pady=(4, 8))

        # Card 1: IMEI Repair Inputs
        nv_imei_card = ctk.CTkFrame(self.frame_spd_nv, fg_color="#181820", corner_radius=8)
        nv_imei_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(nv_imei_card, text="UNISOC IMEI REPAIR CONFIGURATION (Auto-Luhn Check)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#C7D2FE").pack(anchor="w", padx=12, pady=(8, 4))

        si_r1 = ctk.CTkFrame(nv_imei_card, fg_color="transparent")
        si_r1.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(si_r1, text="IMEI 1:", width=60, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkEntry(si_r1, textvariable=self.spd_imei1_var, placeholder_text="e.g. 358941091234567", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True)

        si_r2 = ctk.CTkFrame(nv_imei_card, fg_color="transparent")
        si_r2.pack(fill="x", padx=12, pady=(3, 10))
        ctk.CTkLabel(si_r2, text="IMEI 2:", width=60, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkEntry(si_r2, textvariable=self.spd_imei2_var, placeholder_text="e.g. 358941091234568 (Optional)", height=30, fg_color="#0F0F12").pack(side="left", fill="x", expand=True)

        # Dual Repair Action Buttons
        btn_si_row = ctk.CTkFrame(nv_imei_card, fg_color="transparent")
        btn_si_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            btn_si_row,
            text="✍️ Write IMEI (Diag Port Mode)",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.controller.spd_write_diag_imei
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_si_row,
            text="⚡ Write IMEI Direct (FDL Flash Mode)",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=self.controller.spd_write_flash_imei
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 2: NVRAM Backup & Restore
        nv_calib_card = ctk.CTkFrame(self.frame_spd_nv, fg_color="#181820", corner_radius=8)
        nv_calib_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(nv_calib_card, text="PRODNV & RF CALIBRATION BACKUP / RESTORE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#C7D2FE").pack(anchor="w", padx=12, pady=(8, 4))

        nv_cal_row = ctk.CTkFrame(nv_calib_card, fg_color="transparent")
        nv_cal_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            nv_cal_row,
            text="💾 Backup NV (prodnv/fixnv/runtimenv)",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.controller.spd_backup_nv
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            nv_cal_row,
            text="🛡️ Restore NVRAM Calibration",
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self.controller.spd_restore_nv
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 3: Diagnostic Read Controls
        diag_grid = ctk.CTkFrame(self.frame_spd_nv, fg_color="#181820", corner_radius=8)
        diag_grid.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(diag_grid, text="DIAGNOSTIC CHANNEL CONTROLS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#C7D2FE").pack(anchor="w", padx=12, pady=(8, 4))

        sd_r1 = ctk.CTkFrame(diag_grid, fg_color="transparent")
        sd_r1.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(sd_r1, text="📱 Read IMEI & Info (SPRD Diag Port)", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563EB", command=self.controller.spd_read_diag_imei).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(sd_r1, text="🔄 Reboot Device to Normal", height=36, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#334155", command=self.controller.spd_reboot).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._show_tab("⚡ PAC Flasher")

    def _show_tab(self, tab_name):
        self.frame_spd_flash.pack_forget()
        self.frame_spd_service.pack_forget()
        self.frame_spd_nv.pack_forget()

        if tab_name == "⚡ PAC Flasher":
            self.frame_spd_flash.pack(fill="both", expand=True)
        elif tab_name == "⚙️ Service / FRP":
            self.frame_spd_service.pack(fill="both", expand=True)
        elif tab_name == "📶 IMEI & NVRAM":
            self.frame_spd_nv.pack(fill="both", expand=True)

    def _on_tab_changed(self, value):
        self._show_tab(value)

    def _get_spd_models_for_brand(self, brand: str) -> list:
        if "Samsung" in brand:
            unisoc_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "loaders", "unisoc", "samsung")
            loaders = []
            if os.path.exists(unisoc_dir):
                loaders = [f for f in os.listdir(unisoc_dir) if f.endswith(".bin")][:8]
            return ["Galaxy A03 Core (SC9863A)", "Galaxy A03 (T606)"] + loaders

        db_models = [m for m in ModelRepository.get_models_by_brand(brand)
                     if (ModelRepository.get_model_details(brand, m) or {}).get("platform") == "unisoc"]
        chipsets = ["Auto-Detect (BSL Handshake)", "Tiger T606 / T616", "Tiger T612 / T610", "Tiger T700 / T618", "SC9863A / SC7731E"]
        return db_models + [c for c in chipsets if c not in db_models]

    def _on_brand_changed(self, choice):
        self.logger.info(f"Unisoc Brand Selected: {choice}")

    def _on_model_changed(self, choice, details=None):
        brand = self.spd_brand_var.get()
        if not details or not isinstance(details, dict):
            details = ModelRepository.get_model_details(brand, choice)
        if details:
            self.logger.info(f"Unisoc Model Active: {choice} | Chipset: {details.get('chipset', 'Generic')}")

    def _browse_pac(self):
        f = filedialog.askopenfilename(
            title="Select Unisoc PAC Firmware Archive",
            filetypes=[("PAC Firmware Files", "*.pac"), ("All Files", "*.*")]
        )
        if f:
            self.spd_pac_path_var.set(f)
            self.logger.info(f"Unisoc PAC Firmware Attached: {os.path.basename(f)}")
            self.load_pac_details(f)

    def load_pac_details(self, pac_path: str):
        try:
            self.logger.info(f"Parsing Unisoc PAC Archive: {os.path.basename(pac_path)}...")
            parsed = PacParser.parse(pac_path)
            self.current_pac_meta = parsed
            self.all_spd_partitions = parsed.get("partitions", [])

            # Update info banner
            p_name = parsed.get("product_name", "Unknown Product")
            p_ver = parsed.get("product_version", "v1.0")
            count = parsed.get("file_count", len(self.all_spd_partitions))
            self.lbl_pac_meta.configure(
                text=f"📦 PAC: {p_name} | Ver: {p_ver} | Partitions: {count}"
            )

            self.populate_spd_table(self.all_spd_partitions)
            self.logger.success(f"Parsed PAC archive successfully ({count} partitions detected)")
        except Exception as e:
            self.logger.error(f"Failed to parse PAC firmware: {str(e)}")

    def populate_spd_table(self, partitions):
        for item in self.tree_spd.get_children():
            self.tree_spd.delete(item)

        for p in partitions:
            check_str = "✓" if p.get("is_checked", False) else " "
            self.tree_spd.insert(
                "",
                "end",
                values=(
                    check_str,
                    p.get("name", "--"),
                    p.get("filename", "--"),
                    f"0x{p.get('data_offset', 0):X}",
                    p.get("file_size_human", "--")
                )
            )

    def _on_tree_spd_click(self, event):
        item_id = self.tree_spd.identify_row(event.y)
        if not item_id:
            return

        vals = list(self.tree_spd.item(item_id, "values"))
        p_name = vals[1]

        for p in self.all_spd_partitions:
            if p.get("name") == p_name:
                p["is_checked"] = not p.get("is_checked", False)
                vals[0] = "✓" if p["is_checked"] else " "
                self.tree_spd.item(item_id, values=vals)
                break

    def _select_all_spd_partitions(self):
        for p in self.all_spd_partitions:
            if "fdl" not in p.get("name", "").lower():
                p["is_checked"] = True
        self.populate_spd_table(self.all_spd_partitions)
        self.logger.info("All flashable PAC partitions selected.")

    def _deselect_all_spd_partitions(self):
        for p in self.all_spd_partitions:
            p["is_checked"] = False
        self.populate_spd_table(self.all_spd_partitions)
        self.logger.info("All PAC partitions deselected.")

    def update_hud(self, overall, file_pct, part_name, status_text):
        self.bar_spd_file.set(file_pct)
        self.bar_spd_overall.set(overall)
        self.lbl_spd_status.configure(text=f"📱 {status_text}")
        self.lbl_spd_file_progress.configure(text=f"Active Partition ({part_name}): {int(file_pct * 100)}%")
        self.lbl_spd_overall_progress.configure(text=f"Overall PAC Progress: {int(overall * 100)}%")
        m = self.telemetry.update(overall)
        self.lbl_spd_telemetry.configure(text=m["summary"])
        self.lbl_spd_bytes.configure(text=m["transferred_text"])

    def show(self):
        self.left_panel_spd.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel_spd.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel_spd.grid_forget()
        self.center_panel_spd.grid_forget()
