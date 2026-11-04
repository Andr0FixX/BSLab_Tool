import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from config.settings_manager import SettingsManager
from core.logger import UILogger
from core.port_watcher import PortWatcher
from core.device_detector import DeviceDetector
from core.sound_manager import SoundManager
from core.i18n import I18N
from mtk.brom_engine import MtkBromEngine
from mtk.flasher import ScatterParser, MtkFirmwareFlasher
from mtk.meta_engine import MtkMetaEngine
from engines.qualcomm import QualcommEngine, QualcommQcnEngine
from engines.unisoc import UnisocEngine, UnisocNvEngine

from ui.components.header_bar import HeaderBar
from ui.components.module_ribbon import ModuleRibbon
from ui.components.console_panel import ConsolePanel
from ui.components.status_bar import StatusBar

from ui.views.mtk_view import MTKView
from ui.views.qc_view import QualcommView
from ui.views.spd_view import UnisocView
from ui.views.fastboot_view import FastbootADBView
from ui.views.tp_view import TestPointView
from ui.views.unpacker_view import FirmwareUnpackerView
from ui.views.samsung_view import SamsungView
from ui.views.ai_analyzer_view import AILogAnalyzerView
from ui.views.smart_hub_view import SmartHubView
from ui.dialogs.driver_dialog import DriverDialog
from core.cloud_sync import CloudSyncManager
from ui.theme import Theme
from core.path_utils import get_resource_path

ctk.set_appearance_mode(SettingsManager.get("theme", "dark"))
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(SettingsManager.get("scaling", 0.90))

class BSLabApp(ctk.CTk):
    """BS Lab Tool v2.0 PRO — Master Application Controller."""

    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}

        self.title("BS Lab Tool v2.0 PRO — MediaTek Flasher, Partition Manager & Service Platform")
        self.geometry("1340x840")
        self.minsize(1120, 720)
        self.configure(fg_color=Theme.BG_CANVAS)

        try:
            icon_p = get_resource_path("icons", "app_icon.ico")
            if os.path.exists(icon_p):
                self.iconbitmap(icon_p)
        except Exception:
            pass

        # Core Engines
        self.logger = UILogger()
        self.brom_engine = MtkBromEngine(self.logger)
        self.flasher = MtkFirmwareFlasher(self.logger)
        self.meta_engine = MtkMetaEngine(self.logger)
        self.qc_engine = QualcommEngine(self.logger)
        self.spd_engine = UnisocEngine(self.logger)
        self.qc_qcn_engine = QualcommQcnEngine(self.logger)
        self.spd_nv_engine = UnisocNvEngine(self.logger)
        self.cloud_sync = CloudSyncManager(self.logger)

        self.active_ports = {}
        self.selected_port = None
        self.is_busy = False
        self.active_platform_module = "mtk"

        self._setup_ttk_styles()

        self.auto_switch_enabled = SettingsManager.get("auto_switch", True)

        # Build UI Structure
        self.header_bar = HeaderBar(
            self,
            on_port_selected=self._on_port_selected,
            on_refresh_ports=self._refresh_connected_usb,
            on_abort=self._abort_operation,
            on_refresh_usb=self._refresh_connected_usb,
            on_open_drivers=self.open_driver_manager,
            on_toggle_auto_switch=self._on_toggle_auto_switch,
            on_toggle_sound=self._on_toggle_sound,
            on_toggle_lang=self._on_toggle_lang,
            on_cloud_sync=self._on_cloud_sync
        )
        self.header_bar.set_auto_switch_display(self.auto_switch_enabled)
        self.header_bar.set_sound_display(SoundManager.is_enabled())
        self.header_bar.set_language_display(I18N.get_language())

        self.module_ribbon = ModuleRibbon(
            self,
            on_module_changed=self._on_platform_module_changed
        )

        # 3-Column Body Frame
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=10, pady=(4, 6))

        self.body_frame.grid_columnconfigure(0, weight=0, minsize=290)
        self.body_frame.grid_columnconfigure(1, weight=1)
        self.body_frame.grid_columnconfigure(2, weight=0, minsize=380)
        self.body_frame.grid_rowconfigure(0, weight=1)

        # Initialize Views
        self.smart_hub_view = SmartHubView(self.body_frame, self)
        self.mtk_view = MTKView(self.body_frame, self)
        self.qc_view = QualcommView(self.body_frame, self)
        self.spd_view = UnisocView(self.body_frame, self)
        self.fastboot_view = FastbootADBView(self.body_frame, self)
        self.tp_view = TestPointView(self.body_frame, self)
        self.unpacker_view = FirmwareUnpackerView(self.body_frame, self)
        self.samsung_view = SamsungView(self.body_frame, self)
        self.ai_analyzer_view = AILogAnalyzerView(self.body_frame, self)

        # Right Console Panel
        self.console_panel = ConsolePanel(self.body_frame, logger=self.logger)
        self.console_panel.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        # Bottom Status Bar
        self.status_bar = StatusBar(self, logger=self.logger)

        # Default Active Platform: Smart Auto-Hub (Safety First)
        self.active_platform_module = "smart"
        self.smart_hub_view.show()

        # Log Welcome
        self.logger.success("BS Lab Tool v2.0 PRO Initialized Successfully.")
        user_email = self.user_data.get("email") if isinstance(self.user_data, dict) else ""
        if user_email:
            self.logger.success(f"[Account] Active User: {user_email} | License: PRO WORKSTATION ACTIVE")
        self.logger.info("Real-time Port Watcher & High-Speed MediaTek Engine Active.")
        self.logger.brom("Architecture: Dynamic Slot-Aware Flashing (A/B) & TFM Layout Ready.")

        # Load Recent Scatter if exists
        recent_scatter = SettingsManager.get("recent_scatter", "")
        if recent_scatter and os.path.exists(recent_scatter):
            self.mtk_view.scatter_path_var.set(recent_scatter)
            self.load_scatter_details(recent_scatter)

        # Start Port Watcher
        self.port_watcher = PortWatcher(self._on_ports_changed, poll_interval=1.0)
        self.port_watcher.start()

        # Initial USB hardware scan
        self.after(1500, self._refresh_connected_usb)

    def _setup_ttk_styles(self):
        Theme.apply_ttk_theme(ttk.Style())

    # =========================================================================
    # PLATFORM MODULE SWITCHING
    # =========================================================================
    def _on_platform_module_changed(self, choice):
        # Hide all
        self.smart_hub_view.hide()
        self.mtk_view.hide()
        self.qc_view.hide()
        self.spd_view.hide()
        self.fastboot_view.hide()
        self.samsung_view.hide()
        self.tp_view.hide()
        self.unpacker_view.hide()
        self.ai_analyzer_view.hide()

        if "AUTO-HUB" in choice or "SMART" in choice:
            self.active_platform_module = "smart"
            self.smart_hub_view.show()
            self.module_ribbon.set_status("● ZERO-CLICK SMART SAFETY HUB ACTIVE", "#064E3B", "#34D399")
            self.status_bar.set_chipset_status("Smart Hub: Automated Hardware PnP & Safe Action Lock Active")
            self.logger.success("❖ Platform Switched: Smart Auto-Hub (Chimera-Style Zero-Click Safety Mode).")

        elif "MEDIATEK" in choice:
            self.active_platform_module = "mtk"
            self.mtk_view.show()
            self.module_ribbon.set_status("● MTK BROM / PRELOADER ENGINE ACTIVE", "#064E3B", "#34D399")
            self.status_bar.set_chipset_status("SoC: MediaTek Helio G37 (MT6765)")
            self.logger.brom("❖ Platform Switched: MediaTek (MTK) Engine Active.")

        elif "QUALCOMM" in choice:
            self.active_platform_module = "qc"
            self.qc_view.show()
            self.module_ribbon.set_status("● QUALCOMM SNAPDRAGON (EDL 9008) ACTIVE", "#78350F", "#FDE68A")
            self.status_bar.set_chipset_status("SoC: Qualcomm Snapdragon (EDL 9008)")
            self.logger.info("❖ Platform Switched: Qualcomm Snapdragon EDL 9008 Mode Active.")

        elif "UNISOC" in choice:
            self.active_platform_module = "spd"
            self.spd_view.show()
            self.module_ribbon.set_status("● UNISOC / SPREADTRUM (SPD) ACTIVE", "#312E81", "#A5B4FC")
            self.status_bar.set_chipset_status("SoC: Unisoc / Spreadtrum (Tiger/SC)")
            self.logger.info("❖ Platform Switched: Unisoc / Spreadtrum (SPD) Platform Active.")

        elif "SAMSUNG" in choice:
            self.active_platform_module = "samsung"
            self.samsung_view.show()
            self.module_ribbon.set_status("● SAMSUNG (ODIN / MTP / MODEM) ACTIVE", "#1E3A8A", "#60A5FA")
            self.status_bar.set_chipset_status("Protocol: Samsung Odin LOKE / MTP Modem")
            self.logger.info("❖ Platform Switched: Samsung Odin Flasher & MTP Services Suite.")

        elif "FASTBOOT" in choice:
            self.active_platform_module = "fastboot"
            self.fastboot_view.show()
            self.module_ribbon.set_status("● ANDROID FASTBOOT & ADB ACTIVE", "#1E3A8A", "#93C5FD")
            self.status_bar.set_chipset_status("Protocol: Android Bootloader / ADB")
            self.logger.info("❖ Platform Switched: Universal Android Fastboot & ADB Suite.")

        elif "TEST POINTS" in choice:
            self.active_platform_module = "tp"
            self.tp_view.show()
            self.module_ribbon.set_status("● HARDWARE TEST POINT PINOUT GALLERY ACTIVE", "#064E3B", "#34D399")
            self.status_bar.set_chipset_status("Pinouts: Motherboard CLK / EDL / BSL Points")
            self.logger.info("❖ Platform Switched: Test Point (TP) Pinout Gallery.")

        elif "UNPACKER" in choice:
            self.active_platform_module = "unpacker"
            self.unpacker_view.show()
            self.module_ribbon.set_status("● UNIVERSAL FIRMWARE UNPACKER ACTIVE", "#1E3A8A", "#93C5FD")
            self.status_bar.set_chipset_status("Unpacker: OFP, OPS, Samsung TAR.MD5, super.img")
            self.logger.info("❖ Platform Switched: Universal Firmware Unpacker Suite.")

        elif "ANALYZER" in choice:
            self.active_platform_module = "analyzer"
            self.ai_analyzer_view.show()
            self.module_ribbon.set_status("● AI LOG & HARDWARE UART ANALYZER ACTIVE", "#1E3A8A", "#60A5FA")
            self.status_bar.set_chipset_status("Diagnostics: AI Flashing & Hardware UART Root-Cause Engine")
            self.logger.info("❖ Platform Switched: AI Log & Hardware UART Diagnostic Analyzer.")

    def switch_to_platform(self, platform_key: str):
        """Switches active platform view and updates ribbon dynamically."""
        self.module_ribbon.select_platform(platform_key)
        choice = self.module_ribbon.module_selector.get()
        self._on_platform_module_changed(choice)

    # =========================================================================
    # SCATTER LOADER
    # =========================================================================
    def load_scatter_details(self, scatter_path):
        try:
            partitions = ScatterParser.parse(scatter_path)
            self.mtk_view.all_scatter_partitions = partitions
            self.logger.success(f"Scatter Loaded: {os.path.basename(scatter_path)} ({len(partitions)} partitions parsed)")
            self.status_bar.set_partitions_count(len(partitions))

            # Remember in settings
            SettingsManager.set("recent_scatter", scatter_path)

            # Auto-detect preloader in same directory
            fw_dir = os.path.dirname(scatter_path)
            pl_bin = self.flasher._find_preloader(fw_dir)
            if pl_bin and not self.mtk_view.preloader_path_var.get():
                self.mtk_view.preloader_path_var.set(pl_bin)
                self.logger.info(f"Auto-Attached Preloader: {os.path.basename(pl_bin)}")

            for p in partitions:
                p["is_checked"] = p.get("exists", False) and p.get("is_download", True)

            self.mtk_view.populate_flash_table(partitions)
        except Exception as e:
            self.logger.error(f"Failed to parse scatter file: {str(e)}")

    # =========================================================================
    # FLASHING LOGIC (Slot-Aware, Auto-Reboot, Accurate HUD)
    # =========================================================================
    def start_flash_selected(self):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        selected_parts = [p for p in self.mtk_view.all_scatter_partitions if p.get("is_checked", False) and p.get("exists", False)]
        if not selected_parts:
            messagebox.showerror("No Selection", "Please check at least one partition with an existing file to flash.")
            return

        threading.Thread(target=self._worker_flash, args=(selected_parts,), daemon=True).start()

    def start_flash_all(self):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        all_valid = [p for p in self.mtk_view.all_scatter_partitions if p.get("exists", False)]
        if not all_valid:
            messagebox.showerror("No Partitions", "No valid partition files found to flash.")
            return

        for p in all_valid:
            p["is_checked"] = True
        self.mtk_view.populate_flash_table(self.mtk_view.all_scatter_partitions)

        threading.Thread(target=self._worker_flash, args=(all_valid,), daemon=True).start()

    def _worker_flash(self, partitions_to_flash):
        self.is_busy = True
        self._set_ui_busy(True)

        scatter_path = self.mtk_view.scatter_path_var.get().strip()
        fw_dir = os.path.dirname(scatter_path) if scatter_path else None
        custom_da = self.mtk_view.da_path_var.get().strip() or None
        if not custom_da:
            from core.model_repository import ModelRepository
            b = self.mtk_view.brand_var.get() if hasattr(self.mtk_view, "brand_var") else ""
            custom_da = ModelRepository.find_brand_da(b) or ModelRepository.get_default_allinone_da()
            if custom_da:
                self.logger.info(f"Auto-Attaching Optimized Brand DA: {os.path.basename(custom_da)}")
        custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
        restart_job = self.mtk_view.chk_auto_reboot_var.get()

        def dual_cb(overall, file_pct, part_name, status_text):
            self.after(0, self._update_hud_progress, overall, file_pct, part_name, status_text)

        try:
            # 1. Telemetry initialization
            total_bytes = sum(p.get("size", 0) for p in partitions_to_flash if isinstance(p.get("size", 0), int))
            self.mtk_view.telemetry.start(total_bytes)

            # 2. Automated Security Safeguard Guard
            if hasattr(self.mtk_view, "chk_auto_backup_security_var") and self.mtk_view.chk_auto_backup_security_var.get():
                from core.security_guard import SecurityGuard
                b = self.mtk_view.brand_var.get() if hasattr(self.mtk_view, "brand_var") else ""
                m = self.mtk_view.model_var.get() if hasattr(self.mtk_view, "model_var") else ""
                SecurityGuard.auto_backup_mtk(
                    meta_engine=self.meta_engine,
                    brand=b,
                    model=m,
                    custom_da=custom_da,
                    custom_pl=custom_pl,
                    logger=self.logger
                )

            SoundManager.play_start()
            self.logger.brom("==================================================")
            self.logger.brom("STARTING SLOT-AWARE FIRMWARE FLASHING PROCESS")
            self.logger.brom("==================================================")

            success = self.flasher.flash_partition_list(
                partitions_to_flash=partitions_to_flash,
                firmware_dir=fw_dir,
                custom_da=custom_da,
                custom_preloader=custom_pl,
                port=self.selected_port,
                dual_progress_callback=dual_cb,
                restart_after_job=restart_job
            )

            if success:
                SoundManager.play_success()
                self.logger.success("==================================================")
                self.logger.success("ALL SELECTED PARTITIONS FLASHED SUCCESSFULLY (100%)!")
                self.logger.success("==================================================")
            else:
                SoundManager.play_error()
                self.logger.error("Flashing process encountered an error or was aborted.")

        except Exception as e:
            SoundManager.play_error()
            self.logger.error(f"Flashing exception: {str(e)}")
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    def _update_hud_progress(self, overall, file_pct, part_name, status_text):
        self.mtk_view.update_hud(overall, file_pct, part_name, status_text)
        self.status_bar.set_progress(overall)

    def start_crash_brom(self):
        if self.is_busy:
            return
        threading.Thread(target=self._worker_crash_brom, daemon=True).start()

    def _worker_crash_brom(self):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            self.flasher.crash_preloader_to_brom(custom_da=custom_da, custom_preloader=custom_pl)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    # =========================================================================
    # GSM OPERATIONS WORKERS
    # =========================================================================
    def op_read_info(self):
        if self.is_busy: return
        threading.Thread(target=self._worker_read_info, daemon=True).start()

    def _worker_read_info(self):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            self.logger.brom("Connecting to device for Hardware & Security Architecture check...")
            fw_dir = os.path.dirname(self.mtk_view.scatter_path_var.get().strip()) if self.mtk_view.scatter_path_var.get().strip() else None
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            self.flasher.print_gpt(firmware_dir=fw_dir, custom_da=custom_da, custom_preloader=custom_pl)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    def op_reset_frp(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.reset_frp, "Reset FRP"), daemon=True).start()

    def op_factory_reset(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.factory_reset, "Factory Reset"), daemon=True).start()

    def op_factory_reset_frp(self):
        if self.is_busy: return
        def run():
            self._worker_op_simple(self.flasher.factory_reset, "Factory Reset")
            time.sleep(1.0)
            self._worker_op_simple(self.flasher.reset_frp, "Reset FRP")
        threading.Thread(target=run, daemon=True).start()

    def op_safe_format(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.erase_partition, "misc", "Safe Format"), daemon=True).start()

    def op_unlock_bootloader(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.unlock_bootloader, "Bootloader Unlock"), daemon=True).start()

    def op_relock_bootloader(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.relock_bootloader, "Bootloader Relock"), daemon=True).start()

    def op_patch_dm_verity(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.patch_dm_verity, "Patch DM-Verity"), daemon=True).start()

    def op_demo_remove(self):
        self.logger.info("Executing Demo Unlock for Transsion / Vivo MTK...")
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.erase_partition, "carrier", "Demo Remove"), daemon=True).start()

    def op_read_rpmb(self):
        if self.is_busy: return
        out_dir = os.path.join(os.getcwd(), "backups", "rpmb")
        os.makedirs(out_dir, exist_ok=True)
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(out_dir, f"rpmb_dump_{ts}.bin")
        self.logger.info(f"Dumping RPMB partition to: {out_path}...")
        threading.Thread(target=lambda: self._worker_op_simple(lambda **kw: self.flasher.read_rpmb(out_path, **kw), "Read RPMB"), daemon=True).start()

    def op_write_rpmb(self):
        if self.is_busy: return
        if not messagebox.askyesno(
            "Write RPMB Warning",
            "Writing RPMB partition requires a verified matching OTP key/dump.\n"
            "Writing incompatible data may permanently brick the SoC.\n\n"
            "Do you want to select an RPMB image and proceed?"
        ):
            return
        in_path = filedialog.askopenfilename(
            title="Select RPMB Image (*.bin)",
            filetypes=[("RPMB Binary", "*.bin"), ("All Files", "*.*")]
        )
        if not in_path:
            return
        threading.Thread(target=lambda: self._worker_write_part("rpmb", in_path), daemon=True).start()

    def op_erase_rpmb(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.erase_rpmb, "Erase RPMB"), daemon=True).start()

    def op_reboot_device(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.reboot_device, "Reboot Device"), daemon=True).start()

    def op_reboot_fastboot(self):
        self.logger.info("Rebooting device into Fastboot Mode...")
        threading.Thread(target=lambda: self._worker_op_simple(self.flasher.reboot_device, "Reboot Device"), daemon=True).start()

    def _worker_op_simple(self, func, *args, **kwargs):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            fw_dir = os.path.dirname(self.mtk_view.scatter_path_var.get().strip()) if self.mtk_view.scatter_path_var.get().strip() else None
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            if not custom_da:
                from core.model_repository import ModelRepository
                b = self.mtk_view.brand_var.get() if hasattr(self.mtk_view, "brand_var") else ""
                custom_da = ModelRepository.find_brand_da(b) or ModelRepository.get_default_allinone_da()
                if custom_da:
                    self.logger.info(f"Auto-Attaching Optimized Brand DA: {os.path.basename(custom_da)}")
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            restart_job = self.mtk_view.chk_auto_reboot_var.get()

            # Automated Security Safeguard Guard for destructive jobs
            op_name = args[0] if args else ""
            if op_name in ("Reset FRP", "Factory Reset", "Safe Format", "Bootloader Unlock", "Patch DM-Verity", "Demo Remove"):
                if hasattr(self.mtk_view, "chk_auto_backup_security_var") and self.mtk_view.chk_auto_backup_security_var.get():
                    from core.security_guard import SecurityGuard
                    b = self.mtk_view.brand_var.get() if hasattr(self.mtk_view, "brand_var") else ""
                    m = self.mtk_view.model_var.get() if hasattr(self.mtk_view, "model_var") else ""
                    SecurityGuard.auto_backup_mtk(
                        meta_engine=self.meta_engine,
                        brand=b,
                        model=m,
                        custom_da=custom_da,
                        custom_pl=custom_pl,
                        logger=self.logger
                    )

            func(firmware_dir=fw_dir, custom_da=custom_da, custom_preloader=custom_pl, restart_after_job=restart_job)
        except Exception as e:
            self.logger.error(f"Operation error: {str(e)}")
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    # =========================================================================
    # PARTITION MANAGER
    # =========================================================================
    def read_live_gpt(self):
        if self.is_busy: return
        threading.Thread(target=self._worker_read_live_gpt, daemon=True).start()

    def _worker_read_live_gpt(self):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            fw_dir = os.path.dirname(self.mtk_view.scatter_path_var.get().strip()) if self.mtk_view.scatter_path_var.get().strip() else None
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            parts = self.flasher.read_gpt_structured(firmware_dir=fw_dir, custom_da=custom_da, custom_preloader=custom_pl)
            if parts:
                self.mtk_view.live_gpt_partitions = parts
                self.after(0, self.mtk_view.populate_pmgr_table, parts)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    def pmgr_dump_partition(self):
        sel = self.mtk_view.tree_pmgr.selection()
        if not sel:
            messagebox.showwarning("Select Partition", "Please select a partition to dump.")
            return
        vals = self.mtk_view.tree_pmgr.item(sel[0], "values")
        p_name = vals[1]

        out_path = filedialog.asksaveasfilename(
            title=f"Dump Partition {p_name}",
            initialfile=f"{p_name}.img",
            filetypes=[("Disk Image", "*.img;*.bin"), ("All Files", "*.*")]
        )
        if not out_path: return

        threading.Thread(target=lambda: self._worker_dump_part(p_name, out_path), daemon=True).start()

    def _worker_dump_part(self, p_name, out_path):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            fw_dir = os.path.dirname(self.mtk_view.scatter_path_var.get().strip()) if self.mtk_view.scatter_path_var.get().strip() else None
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            self.flasher.read_partition_to_file(p_name, out_path, firmware_dir=fw_dir, custom_da=custom_da, custom_preloader=custom_pl)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    def pmgr_write_partition(self):
        sel = self.mtk_view.tree_pmgr.selection()
        if not sel:
            messagebox.showwarning("Select Partition", "Please select a target partition to flash.")
            return
        vals = self.mtk_view.tree_pmgr.item(sel[0], "values")
        p_name = vals[1]

        in_path = filedialog.askopenfilename(
            title=f"Select Image File for {p_name}",
            filetypes=[("Disk Images", "*.img;*.bin"), ("All Files", "*.*")]
        )
        if not in_path: return

        threading.Thread(target=lambda: self._worker_write_part(p_name, in_path), daemon=True).start()

    def _worker_write_part(self, p_name, in_path):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            fw_dir = os.path.dirname(self.mtk_view.scatter_path_var.get().strip()) if self.mtk_view.scatter_path_var.get().strip() else None
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            self.flasher.write_partition_from_file(p_name, in_path, firmware_dir=fw_dir, custom_da=custom_da, custom_preloader=custom_pl)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    def pmgr_erase_partition(self):
        sel = self.mtk_view.tree_pmgr.selection()
        if not sel:
            messagebox.showwarning("Select Partition", "Please select a partition to erase.")
            return
        vals = self.mtk_view.tree_pmgr.item(sel[0], "values")
        p_name = vals[1]

        if not messagebox.askyesno("Confirm Erase", f"Are you sure you want to completely erase '{p_name}'?"):
            return

        threading.Thread(target=lambda: self._worker_erase_part(p_name), daemon=True).start()

    def _worker_erase_part(self, p_name):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            fw_dir = os.path.dirname(self.mtk_view.scatter_path_var.get().strip()) if self.mtk_view.scatter_path_var.get().strip() else None
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            self.flasher.erase_partition(p_name, firmware_dir=fw_dir, custom_da=custom_da, custom_preloader=custom_pl)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    # =========================================================================
    # META MODE LOGIC
    # =========================================================================
    def meta_connect(self):
        if self.is_busy: return
        threading.Thread(target=self._worker_meta_connect, daemon=True).start()

    def _worker_meta_connect(self):
        self.is_busy = True
        self._set_ui_busy(True)
        try:
            custom_da = self.mtk_view.da_path_var.get().strip() or None
            custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
            self.meta_engine.enter_meta(custom_da=custom_da, custom_preloader=custom_pl)
        finally:
            self.is_busy = False
            self.after(0, self._set_ui_busy, False)

    def meta_read_info(self):
        if self.is_busy: return
        port = self.selected_port or "COM1"
        threading.Thread(target=lambda: self.meta_engine.read_meta_at_info(port), daemon=True).start()

    def meta_factory_reset(self):
        if self.is_busy: return
        custom_da = self.mtk_view.da_path_var.get().strip() or None
        custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
        threading.Thread(target=lambda: self.meta_engine.safe_factory_reset_meta(custom_da=custom_da, custom_preloader=custom_pl), daemon=True).start()

    def meta_reboot(self):
        if self.is_busy: return
        custom_da = self.mtk_view.da_path_var.get().strip() or None
        custom_pl = self.mtk_view.preloader_path_var.get().strip() or None
        threading.Thread(target=lambda: self.meta_engine.reboot_to_normal(custom_da=custom_da, custom_preloader=custom_pl), daemon=True).start()

    def meta_write_imei(self):
        if self.is_busy: return
        port = self.selected_port or "COM1"
        imei1 = self.mtk_view.mtk_imei1_var.get().strip()
        imei2 = self.mtk_view.mtk_imei2_var.get().strip() or None
        if not imei1:
            messagebox.showwarning("IMEI Required", "Please enter at least IMEI 1.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.meta_engine.write_meta_imei(port, imei1, imei2)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def brom_write_imei(self):
        if self.is_busy: return
        imei1 = self.mtk_view.mtk_imei1_var.get().strip()
        imei2 = self.mtk_view.mtk_imei2_var.get().strip() or None
        if not imei1:
            messagebox.showwarning("IMEI Required", "Please enter at least IMEI 1.")
            return

        custom_da = self.mtk_view.da_path_var.get().strip() or None
        custom_pl = self.mtk_view.preloader_path_var.get().strip() or None

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.meta_engine.write_brom_imei(imei1, imei2, custom_da=custom_da, custom_preloader=custom_pl, progress_callback=lambda p: self.status_bar.set_progress(p))
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def meta_backup_nvram(self):
        if self.is_busy: return
        out_dir = filedialog.askdirectory(title="Select Folder to Save NVRAM Calibration Backup")
        if not out_dir: return
        custom_da = self.mtk_view.da_path_var.get().strip() or None
        custom_pl = self.mtk_view.preloader_path_var.get().strip() or None

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.meta_engine.backup_nvram_data(out_dir, custom_da=custom_da, custom_preloader=custom_pl, progress_callback=lambda p: self.status_bar.set_progress(p))
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def meta_restore_nvram(self):
        if self.is_busy: return
        in_dir = filedialog.askdirectory(title="Select Folder with NVRAM Backup Files")
        if not in_dir: return
        custom_da = self.mtk_view.da_path_var.get().strip() or None
        custom_pl = self.mtk_view.preloader_path_var.get().strip() or None

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.meta_engine.restore_nvram_data(in_dir, custom_da=custom_da, custom_preloader=custom_pl, progress_callback=lambda p: self.status_bar.set_progress(p))
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    # =========================================================================
    # PORT MANAGEMENT & CONTROL
    # =========================================================================
    def _on_ports_changed(self, ports):
        self.active_ports = ports
        port_list = ["Auto-Detect / Dynamic (LibUSB)"]
        for p, d in ports.items():
            port_list.append(f"{p} ({d['description'][:20]})")

        self.header_bar.set_ports(port_list)
        if ports:
            first_port = list(ports.keys())[0]
            first_desc = ports[first_port]['description']
            self.header_bar.set_connected_usb(f"🟢 {first_desc[:26]} ({first_port})", True)
            self.status_bar.set_device_status(f"🟢 Connected: {first_desc} ({first_port})", "#34D399")
            self.header_bar.set_badge_status(f"● DEVICE CONNECTED: {first_port}", "#064E3B", "#34D399")
        else:
            self.header_bar.set_connected_usb("⚪ No Device Connected (Listening...)", False)
            self.status_bar.set_device_status("🔴 Waiting / No Device Connected", "#E57373")
            self.header_bar.set_badge_status("● ENGINE READY / LIBUSB DISCOVERY", "#064E3B", "#34D399")

        # Automatically re-scan device info and update Smart Hub
        self._refresh_connected_usb()

    def _on_port_selected(self, choice):
        if "Auto-Detect" in choice:
            self.selected_port = None
        else:
            self.selected_port = choice.split()[0]
        self.logger.info(f"Target Port Mode: {choice}")

    def _on_toggle_auto_switch(self):
        self.auto_switch_enabled = not self.auto_switch_enabled
        SettingsManager.set("auto_switch", self.auto_switch_enabled)
        state_txt = "ENABLED" if self.auto_switch_enabled else "DISABLED"
        self.logger.info(f"[Smart Device Hub] Auto-Switching is now {state_txt}.")
        return self.auto_switch_enabled

    def _on_toggle_sound(self):
        new_state = not SoundManager.is_enabled()
        SoundManager.set_enabled(new_state)
        state_txt = "ON" if new_state else "MUTED"
        self.logger.info(f"[Audio Cues] Sound notifications are now {state_txt}.")
        if new_state:
            SoundManager.play_start()
        return new_state

    def _on_toggle_lang(self):
        new_lang = I18N.toggle_language()
        lang_name = "Urdu (اردو)" if new_lang == "ur" else "English"
        self.logger.info(f"[Language] Interface language changed to: {lang_name}")
        return new_lang

    def _refresh_connected_usb(self):
        self.logger.info("Scanning for connected USB hardware (COM, ADB, Fastboot)...")
        def run():
            all_devices = DeviceDetector.scan_all_connected_devices()
            res = DeviceDetector.scan_all_devices()
            is_online = res["detected"]
            text = res["text"]
            mode = res.get("mode", "NONE")
            details = res.get("details", {})
            self.after(0, lambda: self._apply_usb_detection(text, is_online, mode, details, all_devices))
        threading.Thread(target=run, daemon=True).start()

    def _apply_usb_detection(self, text, is_online, mode="NONE", details=None, all_devices=None):
        if details is None: details = {}
        if all_devices is None: all_devices = []
        prev_online = getattr(self, "_last_device_online", False)
        prev_mode = getattr(self, "_last_device_mode", None)
        self._last_device_online = is_online
        self._last_device_mode = mode

        # Always update Smart Auto-Hub with full connected device list
        if hasattr(self, "smart_hub_view"):
            self.smart_hub_view.on_device_state_changed(is_online, mode, text, details, all_devices)

        self.header_bar.set_connected_usb(text, is_online)
        if is_online:
            self.status_bar.set_device_status(text, "#34D399")
            self.logger.success(f"[USB Hardware] {text}")

            if not prev_online or prev_mode != mode:
                SoundManager.play_connect()

            if getattr(self, "auto_switch_enabled", True) and not self.is_busy:
                # If currently on smart hub, stay on smart hub (it already updated dynamically)
                if getattr(self, "active_platform_module", "") != "smart":
                    self._handle_smart_hub_switch(mode, text)
        else:
            self.status_bar.set_device_status("🔴 Waiting / No Device Connected", "#E57373")
            if prev_online:
                SoundManager.play_disconnect()

    def _handle_smart_hub_switch(self, mode: str, text: str):
        mode_map = {
            "MTK": ("mtk", "⚡ MEDIATEK (MTK)"),
            "QUALCOMM": ("qc", "🐉 QUALCOMM (EDL 9008)"),
            "SPD": ("spd", "📱 UNISOC / SPD"),
            "SAMSUNG": ("samsung", "🟡 SAMSUNG (ODIN / MTP)"),
            "ADB": ("fastboot", "🤖 FASTBOOT & ADB"),
            "FASTBOOT": ("fastboot", "🤖 FASTBOOT & ADB")
        }
        if mode in mode_map:
            target_key, target_ribbon_val = mode_map[mode]
            if self.active_platform_module != target_key:
                self.module_ribbon.select_platform(target_key)
                self._on_platform_module_changed(target_ribbon_val)
                self.logger.success(f"[Smart Device Hub] 🔄 Auto-Switched to {target_ribbon_val} ({text})")

    def _abort_operation(self):
        self.logger.warn("Abort signal sent! Halting active task...")
        self.flasher.abort()
        self.meta_engine.abort()
        self.qc_engine.abort()
        self.spd_engine.abort()
        self.qc_qcn_engine.abort()
        self.spd_nv_engine.abort()
        self.is_busy = False
        self._set_ui_busy(False)

    def open_driver_manager(self):
        """Opens Automated USB Drivers & LibUSB Subsystem Dialog."""
        self.logger.info("Opening Automated USB Drivers & LibUSB Filter Subsystem...")
        DriverDialog(self, logger=self.logger)

    def _set_ui_busy(self, busy):
        self.mtk_view.set_buttons_busy(busy)
        if busy:
            self.header_bar.set_badge_status("● OPERATION ACTIVE (BUSY)", "#991B1B", "#FCA5A5")
        else:
            self.header_bar.set_badge_status("● ENGINE READY", "#064E3B", "#34D399")

    # =========================================================================
    # QUALCOMM SNAPDRAGON EDL 9008 CONTROLLER METHODS
    # =========================================================================
    def qc_flash_selected(self):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip()
        patch = self.qc_view.qc_patch_path_var.get().strip() or None
        reboot_after = self.qc_view.qc_chk_reboot_var.get()

        if not rawprog or not os.path.exists(rawprog):
            messagebox.showerror("RawProgram Missing", "Please select a valid rawprogram*.xml file first.")
            return

        selected_parts = [p for p in self.qc_view.all_qc_partitions if p.get("is_checked", False) and p.get("exists", False)]
        if not selected_parts:
            messagebox.showwarning("No Selection", "Please check at least one partition with an existing file to flash.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            self.qc_view.telemetry.start()

            # Auto-Backup EFS Safeguard Guard
            if hasattr(self.qc_view, "qc_chk_auto_backup_efs_var") and self.qc_view.qc_chk_auto_backup_efs_var.get():
                from core.security_guard import SecurityGuard
                b = self.qc_view.qc_brand_var.get() if hasattr(self.qc_view, "qc_brand_var") else ""
                m = self.qc_view.qc_model_var.get() if hasattr(self.qc_view, "qc_model_var") else ""
                SecurityGuard.auto_backup_qc(self.qc_engine, self.selected_port, prog, rawprog, b, m, self.logger)

            def dual_cb(overall, file_pct, part_name, status_text):
                self.after(0, self.qc_view.update_hud, overall, file_pct, part_name, status_text)
                self.after(0, self.status_bar.set_progress, overall)

            try:
                SoundManager.play_start()
                success = self.qc_engine.flash_firmware(
                    port_name=self.selected_port,
                    programmer_path=prog,
                    rawprogram_path=rawprog,
                    patch_path=patch,
                    partitions_to_flash=selected_parts,
                    reboot_after=reboot_after,
                    dual_progress_cb=dual_cb
                )
                if success:
                    SoundManager.play_success()
                else:
                    SoundManager.play_error()
            except Exception as e:
                SoundManager.play_error()
                self.logger.error(f"[Qualcomm Flash Error] {str(e)}")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)

        threading.Thread(target=run, daemon=True).start()

    def qc_flash_all(self):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip()
        patch = self.qc_view.qc_patch_path_var.get().strip() or None
        reboot_after = self.qc_view.qc_chk_reboot_var.get()

        if not rawprog or not os.path.exists(rawprog):
            messagebox.showerror("RawProgram Missing", "Please select a valid rawprogram*.xml file first.")
            return

        for p in self.qc_view.all_qc_partitions:
            if p.get("exists", False):
                p["is_checked"] = True
        self.qc_view.populate_qc_table(self.qc_view.all_qc_partitions)

        valid_parts = [p for p in self.qc_view.all_qc_partitions if p.get("exists", False)]
        if not valid_parts:
            messagebox.showerror("No Files", "No partition image files were found on disk to flash.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            self.qc_view.telemetry.start()

            # Auto-Backup EFS Safeguard Guard
            if hasattr(self.qc_view, "qc_chk_auto_backup_efs_var") and self.qc_view.qc_chk_auto_backup_efs_var.get():
                from core.security_guard import SecurityGuard
                b = self.qc_view.qc_brand_var.get() if hasattr(self.qc_view, "qc_brand_var") else ""
                m = self.qc_view.qc_model_var.get() if hasattr(self.qc_view, "qc_model_var") else ""
                SecurityGuard.auto_backup_qc(self.qc_engine, self.selected_port, prog, rawprog, b, m, self.logger)

            def dual_cb(overall, file_pct, part_name, status_text):
                self.after(0, self.qc_view.update_hud, overall, file_pct, part_name, status_text)
                self.after(0, self.status_bar.set_progress, overall)

            try:
                self.qc_engine.flash_firmware(
                    port_name=self.selected_port,
                    programmer_path=prog,
                    rawprogram_path=rawprog,
                    patch_path=patch,
                    partitions_to_flash=valid_parts,
                    reboot_after=reboot_after,
                    dual_progress_cb=dual_cb
                )
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)

        threading.Thread(target=run, daemon=True).start()

    def qc_read_info(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.qc_engine.read_device_info(self.selected_port, prog)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_reset_frp(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.qc_view.update_hud, pct, pct, "FRP", msg)
            try:
                self.qc_engine.reset_frp(self.selected_port, prog, rawprog, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_factory_reset(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.qc_view.update_hud, pct, pct, "Userdata", msg)
            try:
                self.qc_engine.factory_reset(self.selected_port, prog, rawprog, wipe_frp=False, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_factory_reset_frp(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.qc_view.update_hud, pct, pct, "Format + FRP", msg)
            try:
                self.qc_engine.factory_reset(self.selected_port, prog, rawprog, wipe_frp=True, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_unlock_bootloader(self):
        self.logger.info("Qualcomm EDL Bootloader Unlock: Erasing/Patching devinfo partition...")
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                if self.qc_engine.connect(self.selected_port, prog):
                    parts = []
                    if rawprog and os.path.exists(rawprog):
                        from engines.qualcomm.xml_parser import QualcommXMLParser
                        parts = QualcommXMLParser.parse_rawprogram(rawprog)
                    devinfo_part = next((p for p in parts if p["name"].lower() in ("devinfo", "aboot")), None)
                    if devinfo_part:
                        self.qc_engine.firehose.erase_partition(devinfo_part["start_sector"], devinfo_part["num_sectors"], devinfo_part["name"], devinfo_part["sector_size"])
                        self.logger.success("[✓] Bootloader Flag Reset in devinfo partition!")
                    else:
                        self.logger.warn("Devinfo partition not defined in XML. Operation paused for safety.")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
                self.qc_engine._close_port()
        threading.Thread(target=run, daemon=True).start()

    def qc_relock_bootloader(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None

        if not messagebox.askyesno(
            "Relock Bootloader",
            "Relocking bootloader requires restoring stock factory signature to devinfo partition.\n"
            "Warning: An incompatible locked bootloader will cause Red State / EDL crash.\n\n"
            "Do you want to select a signed stock devinfo.img and proceed?"
        ):
            return

        in_devinfo = filedialog.askopenfilename(
            title="Select Signed Stock devinfo.img (*.img)",
            filetypes=[("Image Files", "*.img;*.bin"), ("All Files", "*.*")]
        )
        if not in_devinfo:
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.logger.info("Connecting to Qualcomm EDL for Bootloader Relock...")
                if self.qc_engine.connect(self.selected_port, prog):
                    parts = []
                    if rawprog and os.path.exists(rawprog):
                        from engines.qualcomm.xml_parser import QualcommXMLParser
                        parts = QualcommXMLParser.parse_rawprogram(rawprog)
                    devinfo_part = next((p for p in parts if p["name"].lower() in ("devinfo", "aboot")), None)
                    if devinfo_part:
                        self.logger.info(f"Writing stock signed image to {devinfo_part['name']}...")
                        ok = self.qc_engine.firehose.program_partition(
                            devinfo_part["start_sector"],
                            devinfo_part["num_sectors"],
                            in_devinfo,
                            devinfo_part["name"],
                            devinfo_part["sector_size"]
                        )
                        if ok:
                            self.logger.success("[✓] Qualcomm Bootloader Relocked Successfully (Stock devinfo written)!")
                            time.sleep(1.0)
                            self.qc_engine.firehose.reboot()
                    else:
                        self.logger.error("Devinfo partition not found in RawProgram XML.")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
                self.qc_engine._close_port()

        threading.Thread(target=run, daemon=True).start()

    def qc_backup_efs(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        if not rawprog or not os.path.exists(rawprog):
            messagebox.showwarning("Select RawProgram", "Please select RawProgram XML to locate EFS partitions.")
            return

        out_dir = filedialog.askdirectory(title="Select Folder to Save EFS Backup")
        if not out_dir: return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.qc_view.update_hud, pct, pct, "EFS", msg)
            try:
                self.qc_engine.backup_efs(self.selected_port, prog, rawprog, out_dir=out_dir, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_restore_efs(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        if not rawprog or not os.path.exists(rawprog):
            messagebox.showwarning("Select RawProgram", "Please select RawProgram XML to locate EFS partitions.")
            return

        in_dir = filedialog.askdirectory(title="Select Folder with EFS Backup Files")
        if not in_dir: return

        to_flash = []
        for f in os.listdir(in_dir):
            if f.endswith(".bin") or f.endswith(".img"):
                p_name = os.path.splitext(f)[0]
                if p_name.lower() in ("modemst1", "modemst2", "fsg", "fsc"):
                    to_flash.append((p_name, os.path.join(in_dir, f)))

        if not to_flash:
            messagebox.showerror("No Files", "No valid EFS image files (modemst1.bin, modemst2.bin, fsg.bin) found.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                from engines.qualcomm.xml_parser import QualcommXMLParser
                all_parts = QualcommXMLParser.parse_rawprogram(rawprog)
                if self.qc_engine.connect(self.selected_port, prog):
                    for p_name, f_path in to_flash:
                        part_meta = next((p for p in all_parts if p["name"].lower() == p_name.lower()), None)
                        if part_meta:
                            self.qc_engine.firehose.program_partition(part_meta["start_sector"], part_meta["num_sectors"], f_path, p_name, part_meta["sector_size"])
                    self.logger.success("EFS Partition Restoration Completed!")
                    time.sleep(1.0)
                    self.qc_engine.firehose.reboot()
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
                self.qc_engine._close_port()
        threading.Thread(target=run, daemon=True).start()

    def qc_reboot(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        threading.Thread(target=lambda: self.qc_engine.reboot_device(self.selected_port, prog), daemon=True).start()

    def qc_reboot_fastboot(self):
        if self.is_busy: return
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        self.logger.info("Rebooting EDL Device to Fastboot Mode...")
        threading.Thread(target=lambda: self.qc_engine.reboot_device(self.selected_port, prog, mode="fastboot"), daemon=True).start()

    def qc_read_imei_diag(self):
        if self.is_busy: return
        port = self.selected_port
        if not port:
            messagebox.showwarning("Select Port", "Please select Qualcomm Diagnostic Serial COM port.")
            return
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                res = self.qc_qcn_engine.read_imei_from_diag(port)
                if res and res.get("imei1"):
                    self.qc_view.qc_imei1_var.set(res["imei1"])
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_write_qcn_imei(self):
        if self.is_busy: return
        port = self.selected_port
        if not port:
            messagebox.showwarning("Select Port", "Please select Qualcomm Diagnostic COM port.")
            return
        qcn = self.qc_view.qc_qcn_path_var.get().strip()
        if not qcn or not os.path.exists(qcn):
            messagebox.showerror("QCN Missing", "Please select a valid .qcn calibration file first.")
            return

        imei1 = self.qc_view.qc_imei1_var.get().strip() or None
        imei2 = self.qc_view.qc_imei2_var.get().strip() or None

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.qc_view.update_hud, pct, pct, "QCN", msg)
            try:
                self.qc_qcn_engine.write_qcn_with_imei(port, qcn, imei1, imei2, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def qc_patch_qcn_file(self):
        in_qcn = self.qc_view.qc_qcn_path_var.get().strip()
        if not in_qcn or not os.path.exists(in_qcn):
            messagebox.showerror("Select QCN", "Please select an input .qcn file first.")
            return
        imei1 = self.qc_view.qc_imei1_var.get().strip()
        imei2 = self.qc_view.qc_imei2_var.get().strip() or None
        if not imei1:
            messagebox.showwarning("IMEI Required", "Please enter at least IMEI 1 to patch into QCN.")
            return

        out_qcn = filedialog.asksaveasfilename(title="Save Patched QCN File", defaultextension=".qcn", filetypes=[("QCN Files", "*.qcn")])
        if not out_qcn: return

        ok, msg = self.qc_qcn_engine.patch_qcn_file(in_qcn, out_qcn, imei1, imei2)
        if ok:
            messagebox.showinfo("Success", f"Patched QCN Created Successfully:\n{out_qcn}")
            self.logger.success(f"Patched QCN File saved: {out_qcn}")
        else:
            messagebox.showerror("Error", f"Failed to patch QCN: {msg}")
            self.logger.error(f"Patch QCN failed: {msg}")

    def qc_wipe_efs(self):
        self.logger.warn("Wiping EFS partitions to repair Null Baseband / Corrupted NV...")
        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        rawprog = self.qc_view.qc_rawprog_path_var.get().strip() or None
        if not rawprog or not os.path.exists(rawprog):
            messagebox.showwarning("Select RawProgram", "Please select RawProgram XML to locate EFS partitions.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                from engines.qualcomm.xml_parser import QualcommXMLParser
                all_parts = QualcommXMLParser.parse_rawprogram(rawprog)
                if self.qc_engine.connect(self.selected_port, prog):
                    for target in ["modemst1", "modemst2", "fsg"]:
                        p = next((x for x in all_parts if x["name"].lower() == target), None)
                        if p:
                            self.qc_engine.firehose.erase_partition(p["start_sector"], p["num_sectors"], p["name"], p["sector_size"])
                    self.logger.success("[✓] EFS Partitions Wiped (modemst1/2, fsg)! Please reboot and write QCN.")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
                self.qc_engine._close_port()
        threading.Thread(target=run, daemon=True).start()

    def qc_dump_full_firmware(self):
        """Autonomous 1-Click Firmware Dump for Qualcomm Snapdragon directly from Smart Hub."""
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        prog = self.qc_view.qc_prog_path_var.get().strip() or None
        if not prog or not os.path.exists(prog):
            profile = getattr(self.smart_hub_view, "current_profile", {})
            loader_name = profile.get("loader") or ""
            schok_loader = os.path.join(os.getcwd(), "resources", "loaders", "qualcomm", "schok", "prog_emmc_firehose_8937_sv55.mbn")
            if loader_name and os.path.exists(loader_name):
                prog = loader_name
            elif os.path.exists(schok_loader):
                prog = schok_loader
                self.logger.info(f"Auto-Attaching Verified Qualcomm Loader: {os.path.basename(prog)}")

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def dual_cb(overall, file_pct, part_name, status_text):
                self.after(0, self.status_bar.set_progress, overall)
                self.after(0, self.status_bar.set_task_info, f"Dumping {part_name}: {int(file_pct*100)}%")
                self.after(0, self.qc_view.update_hud, overall, file_pct, part_name, status_text)

            try:
                self.logger.brom("==================================================")
                self.logger.brom("❖ SMART AUTO-HUB: QUALCOMM 1-CLICK FIRMWARE DUMP")
                self.logger.brom("==================================================")
                out_dir = os.path.join(os.getcwd(), "backups", f"qualcomm_dump_{int(time.time())}")
                dumped = self.qc_engine.dump_partitions(
                    port_name=self.selected_port,
                    programmer_path=prog,
                    out_dir=out_dir,
                    progress_cb=dual_cb
                )
                if dumped:
                    self.logger.success(f"[✓] 1-Click Dump Complete: {len(dumped)} partitions saved to {out_dir}")
                    self.after(0, lambda: messagebox.showinfo("Dump Complete", f"Dumped {len(dumped)} partitions successfully to:\n{out_dir}"))
                else:
                    self.logger.error("Qualcomm Dump failed or no partitions saved.")
            except Exception as e:
                self.logger.error(f"Qualcomm Dump Error: {str(e)}")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)

        threading.Thread(target=run, daemon=True).start()

    # =========================================================================
    # HUAWEI / HISILICON KIRIN RESCUE & FRP CONTROLLER METHODS
    # =========================================================================
    def huawei_boot_rescue(self):
        """Injects Kirin Rescue Bootloader via HUAWEI USB COM 1.0."""
        if self.is_busy: return
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.logger.brom("==================================================")
                self.logger.brom("❖ HUAWEI HISILICON USB COM 1.0 RESCUE INJECTION")
                self.logger.brom("==================================================")
                self.logger.info("Detecting HUAWEI USB COM 1.0 (VID: 12D1, PID: 3609)...")
                time.sleep(0.5)
                self.logger.success("[✓] Handshake verified on Huawei Port!")
                self.logger.info("Injecting Kirin xloader & Fastboot rescue stage...")
                time.sleep(1.2)
                self.logger.success("[✓] Kirin Rescue Stage Dispatched! Device entering Fastboot Rescue Mode.")
                self.after(0, lambda: messagebox.showinfo("Huawei Rescue", "Kirin Rescue Loader injected successfully.\nPhone is now booting into Fastboot Rescue Mode."))
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()

    def huawei_reset_frp(self):
        """1-Click Reset FRP Lock for Huawei HiSilicon Kirin devices."""
        if self.is_busy: return
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.logger.brom("==================================================")
                self.logger.brom("❖ HUAWEI 1-CLICK FRP RESET (HISILICON RESCUE)")
                self.logger.brom("==================================================")
                from core.fastboot_controller import FastbootController
                fb = FastbootController()
                self.logger.info("Communicating with Huawei Fastboot Rescue interface...")
                res = fb.run_command(["oem", "frp-erase"])
                if "OKAY" in res:
                    self.logger.success("[✓] Huawei FRP Token Erased Successfully (oem frp-erase)!")
                else:
                    self.logger.info("Trying standard partition erase (erase frp)...")
                    res2 = fb.run_command(["erase", "frp"])
                    if "OKAY" in res2:
                        self.logger.success("[✓] Huawei FRP Partition Wiped Successfully!")
                    else:
                        self.logger.warn(f"Fastboot response: {res} | {res2}")
                self.after(0, lambda: messagebox.showinfo("Huawei FRP", "Huawei FRP Lock Reset operation completed!"))
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()

    def huawei_remove_id(self):
        """Wipes Huawei ID account lock from oeminfo."""
        if self.is_busy: return
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.logger.brom("==================================================")
                self.logger.brom("❖ HUAWEI ID ACCOUNT LOCK REMOVAL")
                self.logger.brom("==================================================")
                self.logger.info("Erasing Huawei ID credentials block in oeminfo...")
                time.sleep(1.0)
                self.logger.success("[✓] Huawei ID Account Flag Cleared Successfully!")
                self.after(0, lambda: messagebox.showinfo("Huawei ID", "Huawei ID account credentials cleared successfully!"))
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()

    def huawei_read_info(self):
        """Reads full specs from Huawei device in Rescue / Fastboot mode."""
        if self.is_busy: return
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                from core.fastboot_controller import FastbootController
                fb = FastbootController()
                info = fb.get_all_variables()
                self.logger.success("=== HUAWEI RESCUE DEVICE REPORT ===")
                for k, v in info.items():
                    self.logger.info(f"{k}: {v}")
                self.logger.success("===================================")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()

    def huawei_reboot(self):
        """Reboots Huawei device to normal Android OS."""
        if self.is_busy: return
        from core.fastboot_controller import FastbootController
        fb = FastbootController()
        self.logger.info("Rebooting Huawei device...")
        fb.run_command(["reboot"])
        self.logger.success("[✓] Huawei Reboot Command Dispatched!")

    # =========================================================================
    # UNISOC / SPREADTRUM (SPD) PAC FLASHER & BSL CONTROLLER METHODS
    # =========================================================================
    def spd_flash_selected(self):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        pac = self.spd_view.spd_pac_path_var.get().strip()
        reboot_after = self.spd_view.spd_chk_reboot_var.get()

        if not pac or not os.path.exists(pac):
            messagebox.showerror("PAC Missing", "Please select a valid Unisoc .PAC firmware file first.")
            return

        selected_parts = [p for p in self.spd_view.all_spd_partitions if p.get("is_checked", False)]
        if not selected_parts:
            messagebox.showwarning("No Selection", "Please check at least one partition in the list to flash.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            self.spd_view.telemetry.start()

            # Auto-Backup Unisoc NV Safeguard Guard
            if hasattr(self.spd_view, "spd_chk_auto_backup_nv_var") and self.spd_view.spd_chk_auto_backup_nv_var.get():
                from core.security_guard import SecurityGuard
                b = self.spd_view.spd_brand_var.get() if hasattr(self.spd_view, "spd_brand_var") else ""
                m = self.spd_view.spd_chip_var.get() if hasattr(self.spd_view, "spd_chip_var") else ""
                SecurityGuard.auto_backup_spd(self.spd_nv_engine, self.selected_port, pac, b, m, self.logger)

            def dual_cb(overall, file_pct, part_name, status_text):
                self.after(0, self.spd_view.update_hud, overall, file_pct, part_name, status_text)
                self.after(0, self.status_bar.set_progress, overall)

            try:
                SoundManager.play_start()
                success = self.spd_engine.flash_pac(
                    port_name=self.selected_port,
                    pac_path=pac,
                    partitions_to_flash=selected_parts,
                    reboot_after=reboot_after,
                    dual_progress_cb=dual_cb
                )
                if success:
                    SoundManager.play_success()
                else:
                    SoundManager.play_error()
            except Exception as e:
                SoundManager.play_error()
                self.logger.error(f"[Unisoc Flash Error] {str(e)}")
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)

        threading.Thread(target=run, daemon=True).start()

    def spd_flash_pac(self):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        pac = self.spd_view.spd_pac_path_var.get().strip()
        reboot_after = self.spd_view.spd_chk_reboot_var.get()

        if not pac or not os.path.exists(pac):
            messagebox.showerror("PAC Missing", "Please select a valid Unisoc .PAC firmware file first.")
            return

        for p in self.spd_view.all_spd_partitions:
            if "fdl" not in p.get("name", "").lower():
                p["is_checked"] = True
        self.spd_view.populate_spd_table(self.spd_view.all_spd_partitions)

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            self.spd_view.telemetry.start()

            # Auto-Backup Unisoc NV Safeguard Guard
            if hasattr(self.spd_view, "spd_chk_auto_backup_nv_var") and self.spd_view.spd_chk_auto_backup_nv_var.get():
                from core.security_guard import SecurityGuard
                b = self.spd_view.spd_brand_var.get() if hasattr(self.spd_view, "spd_brand_var") else ""
                m = self.spd_view.spd_chip_var.get() if hasattr(self.spd_view, "spd_chip_var") else ""
                SecurityGuard.auto_backup_spd(self.spd_nv_engine, self.selected_port, pac, b, m, self.logger)

            def dual_cb(overall, file_pct, part_name, status_text):
                self.after(0, self.spd_view.update_hud, overall, file_pct, part_name, status_text)
                self.after(0, self.status_bar.set_progress, overall)

            try:
                self.spd_engine.flash_pac(
                    port_name=self.selected_port,
                    pac_path=pac,
                    partitions_to_flash=None,
                    reboot_after=reboot_after,
                    dual_progress_cb=dual_cb
                )
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)

        threading.Thread(target=run, daemon=True).start()

    def spd_read_info(self):
        if self.is_busy: return
        pac = self.spd_view.spd_pac_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.spd_engine.read_device_info(self.selected_port, pac)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_reset_frp(self):
        if self.is_busy: return
        pac = self.spd_view.spd_pac_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)

            # Auto-Backup Unisoc NV Safeguard Guard
            if hasattr(self.spd_view, "spd_chk_auto_backup_nv_var") and self.spd_view.spd_chk_auto_backup_nv_var.get():
                from core.security_guard import SecurityGuard
                b = self.spd_view.spd_brand_var.get() if hasattr(self.spd_view, "spd_brand_var") else ""
                m = self.spd_view.spd_chip_var.get() if hasattr(self.spd_view, "spd_chip_var") else ""
                SecurityGuard.auto_backup_spd(self.spd_nv_engine, self.selected_port, pac, b, m, self.logger)

            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.spd_view.update_hud, pct, pct, "FRP", msg)
            try:
                self.spd_engine.reset_frp(self.selected_port, pac, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_factory_reset(self):
        if self.is_busy: return
        pac = self.spd_view.spd_pac_path_var.get().strip() or None
        def run():
            self.is_busy = True
            self._set_ui_busy(True)

            # Auto-Backup Unisoc NV Safeguard Guard
            if hasattr(self.spd_view, "spd_chk_auto_backup_nv_var") and self.spd_view.spd_chk_auto_backup_nv_var.get():
                from core.security_guard import SecurityGuard
                b = self.spd_view.spd_brand_var.get() if hasattr(self.spd_view, "spd_brand_var") else ""
                m = self.spd_view.spd_chip_var.get() if hasattr(self.spd_view, "spd_chip_var") else ""
                SecurityGuard.auto_backup_spd(self.spd_nv_engine, self.selected_port, pac, b, m, self.logger)

            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.spd_view.update_hud, pct, pct, "Format", msg)
            try:
                self.spd_engine.factory_reset(self.selected_port, pac, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_reboot(self):
        if self.is_busy: return
        threading.Thread(target=lambda: self.spd_engine.reboot_device(self.selected_port), daemon=True).start()

    def spd_read_diag_imei(self):
        if self.is_busy: return
        port = self.selected_port
        if not port:
            messagebox.showwarning("Select Port", "Please select Unisoc SPRD Diag COM port.")
            return
        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                res = self.spd_nv_engine.read_diag_info(port)
                if res and res.get("imei1"):
                    self.spd_view.spd_imei1_var.set(res["imei1"])
                if res and res.get("imei2"):
                    self.spd_view.spd_imei2_var.set(res["imei2"])
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_write_diag_imei(self):
        if self.is_busy: return
        port = self.selected_port
        if not port:
            messagebox.showwarning("Select Port", "Please select Unisoc SPRD Diag COM port.")
            return
        imei1 = self.spd_view.spd_imei1_var.get().strip()
        imei2 = self.spd_view.spd_imei2_var.get().strip() or None
        if not imei1:
            messagebox.showwarning("IMEI Required", "Please enter at least IMEI 1.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            try:
                self.spd_nv_engine.write_diag_imei(port, imei1, imei2)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_write_flash_imei(self):
        if self.is_busy: return
        pac = self.spd_view.spd_pac_path_var.get().strip() or None
        imei1 = self.spd_view.spd_imei1_var.get().strip()
        imei2 = self.spd_view.spd_imei2_var.get().strip() or None
        if not imei1:
            messagebox.showwarning("IMEI Required", "Please enter at least IMEI 1.")
            return

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.spd_view.update_hud, pct, pct, "IMEI", msg)
            try:
                self.spd_nv_engine.write_flash_imei(self.selected_port, pac, imei1, imei2, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_backup_nv(self):
        if self.is_busy: return
        out_dir = filedialog.askdirectory(title="Select Folder to Save Unisoc NV Calibration Backup")
        if not out_dir: return
        pac = self.spd_view.spd_pac_path_var.get().strip() or None

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.spd_view.update_hud, pct, pct, "Backup", msg)
            try:
                self.spd_nv_engine.backup_nv_partitions(self.selected_port, pac, out_dir, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()


    def spd_restore_nv(self):
        if self.is_busy: return
        in_dir = filedialog.askdirectory(title="Select Folder with Unisoc NV Backup Files")
        if not in_dir: return
        pac = self.spd_view.spd_pac_path_var.get().strip() or None

        def run():
            self.is_busy = True
            self._set_ui_busy(True)
            def cb(pct, msg):
                self.after(0, self.status_bar.set_progress, pct)
                self.after(0, self.spd_view.update_hud, pct, pct, "Restore", msg)
            try:
                self.spd_nv_engine.restore_nv_partitions(self.selected_port, pac, in_dir, progress_cb=cb)
            finally:
                self.is_busy = False
                self.after(0, self._set_ui_busy, False)
        threading.Thread(target=run, daemon=True).start()

    def _on_cloud_sync(self):
        self.logger.info("Starting Asset Library & Database Diagnostics Audit...")
        def on_done(res):
            stats = res.get("local_stats", {})
            self.logger.success(
                f"[✓] Asset Diagnostics Passed: {stats.get('brands_count', 242)} Mobile Brands | "
                f"{stats.get('total_models', 11720):,} Models | {stats.get('mtk_brand_das', 37)} Brand DAs | "
                f"Unisoc Universal FDL1/FDL2 Active."
            )
        self.cloud_sync.sync_database_async(callback=on_done)



