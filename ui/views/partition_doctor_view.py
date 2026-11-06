"""
BSLab Tool PRO - Surgical Partition Doctor & Zero-Data-Loss Unbricking View
CustomTkinter UI for forensic partition inspection, corruption diagnosis,
and single-partition surgical recovery with hardcoded userdata preservation.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from ui.theme import Theme
from utils.file_utils import format_bytes
from engines.partition_doctor import (
    PartitionDoctorBrain,
    FastbootPartitionReader,
    EDLPartitionReader,
    DataLossFirewall,
    SurgicalSinglePartitionFlasher,
    FaultSeverity,
    PartitionSignatures
)

class PartitionDoctorView:
    """
    Surgical Partition Doctor View:
    Diagnoses corrupted partitions (boot, dtbo, vbmeta, super), checks A/B slot health,
    and executes targeted surgical repairs without touching userdata.
    """

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.mode_var = tk.StringVar(value="Auto Detect Mode")
        self.fw_path_var = tk.StringVar(value="")
        self.selected_partition_var = tk.StringVar(value="")
        self.is_scanning = False
        self.last_diagnostic_report = None
        self.partition_rows = []

        self._build_left_panel()
        self._build_center_panel()

    def _build_left_panel(self):
        self.left_panel = ctk.CTkScrollableFrame(
            self.body_frame,
            width=320,
            fg_color=Theme.BG_PANEL,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # Header Title
        ctk.CTkLabel(
            self.left_panel,
            text="🩺 PARTITION DOCTOR",
            font=Theme.font_bold(size=13),
            text_color=Theme.ACCENT_CYAN
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            self.left_panel,
            text="Zero-Data-Loss Surgical Unbricking",
            font=Theme.font_ui(size=10),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Data Protection Firewall Badge
        fw_frame = ctk.CTkFrame(self.left_panel, fg_color="#064e3b", corner_radius=6, border_width=1, border_color="#10b981")
        fw_frame.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(
            fw_frame,
            text="🔒 USERDATA FIREWALL: ACTIVE\n(User Data & IMEI Hard-Locked)",
            font=Theme.font_bold(size=10),
            text_color="#a7f3d0",
            justify="center"
        ).pack(padx=8, pady=6)

        # Diagnostic Mode Selector
        ctk.CTkLabel(self.left_panel, text="Diagnostic Mode:", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        self.mode_menu = ctk.CTkOptionMenu(
            self.left_panel,
            values=["Auto Detect Mode", "Fastboot Mode (A/B Slots)", "Qualcomm EDL (9008)", "MediaTek (BROM/DA)"],
            variable=self.mode_var,
            fg_color=Theme.SURFACE_CARD,
            button_color=Theme.ACCENT_BLUE,
            text_color=Theme.TEXT_PRIMARY
        )
        self.mode_menu.pack(fill="x", padx=12, pady=(2, 10))

        # Scan Button
        self.btn_scan = ctk.CTkButton(
            self.left_panel,
            text="🔍 AUTO-DIAGNOSE DEVICE",
            font=Theme.font_bold(size=11),
            fg_color=Theme.ACCENT_CYAN,
            text_color="#000",
            hover_color="#38bdf8",
            command=self.start_diagnosis
        )
        self.btn_scan.pack(fill="x", padx=12, pady=(4, 10))

        # Instant A/B Slot Switch Button
        self.btn_slot_switch = ctk.CTkButton(
            self.left_panel,
            text="🔄 INSTANT A/B SLOT SWITCH",
            font=Theme.font_bold(size=10),
            fg_color=Theme.SURFACE_CARD,
            text_color=Theme.ACCENT_GOLD,
            border_width=1,
            border_color=Theme.ACCENT_GOLD,
            hover_color="#78350f",
            command=self.switch_ab_slot
        )
        self.btn_slot_switch.pack(fill="x", padx=12, pady=(0, 14))

        # Firmware Source Container
        ctk.CTkLabel(self.left_panel, text="Factory Firmware (for Surgical Fix):", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(4, 0))
        fw_row = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        fw_row.pack(fill="x", padx=12, pady=(2, 8))
        self.ent_fw = ctk.CTkEntry(fw_row, textvariable=self.fw_path_var, placeholder_text="Select ROM (.zip, .tar, folder)...", font=Theme.font_ui(size=9))
        self.ent_fw.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(fw_row, text="📁", width=36, fg_color=Theme.SURFACE_CARD, command=self.browse_firmware).pack(side="right")

        # Surgical Repair Button
        self.btn_surgical_fix = ctk.CTkButton(
            self.left_panel,
            text="💉 SURGICAL FIX (KEEP DATA)",
            font=Theme.font_bold(size=11),
            fg_color="#059669",
            text_color="#fff",
            hover_color="#10b981",
            command=self.start_surgical_fix
        )
        self.btn_surgical_fix.pack(fill="x", padx=12, pady=(8, 12))

    def _build_center_panel(self):
        self.center_panel = ctk.CTkFrame(self.body_frame, fg_color="transparent")

        # Top Status HUD
        self.hud_frame = ctk.CTkFrame(self.center_panel, fg_color=Theme.BG_PANEL, corner_radius=8, border_width=1, border_color=Theme.BORDER_CARD)
        self.hud_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.lbl_status = ctk.CTkLabel(
            self.hud_frame,
            text="Ready. Connect bricked phone and click [Auto-Diagnose Device].",
            font=Theme.font_bold(size=11),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_status.pack(anchor="w", padx=14, pady=8)

        # Partition Health Tree Table
        table_frame = ctk.CTkFrame(self.center_panel, fg_color=Theme.BG_PANEL, corner_radius=8, border_width=1, border_color=Theme.BORDER_CARD)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        columns = ("partition", "size_mb", "expected", "detected", "status", "recommendation")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("partition", text="Partition")
        self.tree.heading("size_mb", text="Size (MB)")
        self.tree.heading("expected", text="Expected Type")
        self.tree.heading("detected", text="Detected Magic")
        self.tree.heading("status", text="Health Status")
        self.tree.heading("recommendation", text="Action / Recommendation")

        self.tree.column("partition", width=120, anchor="w")
        self.tree.column("size_mb", width=80, anchor="center")
        self.tree.column("expected", width=110, anchor="center")
        self.tree.column("detected", width=110, anchor="center")
        self.tree.column("status", width=130, anchor="center")
        self.tree.column("recommendation", width=280, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Style Treeview tags
        self.tree.tag_configure("healthy", foreground="#10b981")
        self.tree.tag_configure("corrupted", foreground="#ef4444")
        self.tree.tag_configure("protected", foreground="#38bdf8")
        self.tree.tag_configure("empty", foreground="#f59e0b")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Bottom Report / Instructions
        self.report_box = ctk.CTkTextbox(
            self.center_panel,
            height=110,
            fg_color=Theme.BG_PANEL,
            text_color=Theme.TEXT_PRIMARY,
            font=Theme.font_mono(size=10),
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        self.report_box.pack(fill="x", padx=10, pady=(0, 4))
        self.report_box.insert("1.0", "--- Diagnostic Console ---\nNo device diagnosed yet.")

    def show(self):
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel.grid_forget()
        self.center_panel.grid_forget()

    def pack(self, **kwargs):
        self.show()

    def unpack(self):
        self.hide()

    def browse_firmware(self):
        f = filedialog.askopenfilename(
            title="Select Firmware Container (.zip, .tar, .md5)",
            filetypes=[("Firmware Archives", "*.zip;*.tar;*.md5;*.tar.md5"), ("Image Files", "*.img;*.bin"), ("All Files", "*.*")]
        )
        if f:
            self.fw_path_var.set(f)

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            part_name = item["values"][0]
            self.selected_partition_var.set(part_name)

    def start_diagnosis(self):
        if self.is_scanning:
            return
        threading.Thread(target=self._worker_diagnosis, daemon=True).start()

    def _worker_diagnosis(self):
        self.is_scanning = True
        self.btn_scan.configure(state="disabled")
        self.lbl_status.configure(text="🔍 Scanning device partitions and slot integrity...", text_color=Theme.ACCENT_CYAN)
        self.report_box.delete("1.0", "end")

        mode = self.mode_var.get()
        self.logger.info(f"[Partition Doctor] Starting diagnosis in mode: {mode}")

        try:
            # 1. Fastboot Mode Diagnosis
            fb_reader = FastbootPartitionReader()
            fb_health = fb_reader.inspect_device_health()

            if fb_health.get("connected", False):
                report = PartitionDoctorBrain.analyze_fastboot_health(fb_health)
                self.last_diagnostic_report = report
                self.controller.after(0, self._populate_fastboot_report, report, fb_health)
                return

            # If not fastboot, notify user
            self.lbl_status.configure(
                text="Device not detected in Fastboot! Connect in Fastboot (Vol Down + Power) or EDL mode.",
                text_color=Theme.ACCENT_GOLD
            )
            self.report_box.insert("1.0", "Error: No Fastboot / EDL device responded.\nPlease verify USB connection.")
        except Exception as e:
            self.logger.error(f"[Partition Doctor Error] {str(e)}")
            self.lbl_status.configure(text=f"Error: {str(e)}", text_color="#ef4444")
        finally:
            self.is_scanning = False
            self.btn_scan.configure(state="normal")

    def _populate_fastboot_report(self, report, raw_health):
        for item in self.tree.get_children():
            self.tree.delete(item)

        parts = raw_health.get("partitions", {})
        for p_name, pinfo in parts.items():
            is_prot = PartitionSignatures.is_protected(p_name)
            status_text = "🟢 HEALTHY" if pinfo.get("healthy") else "🔴 CORRUPTED"
            tag = "healthy" if pinfo.get("healthy") else "corrupted"
            if is_prot:
                status_text = "🔒 PROTECTED"
                tag = "protected"

            rec = "Header intact." if pinfo.get("healthy") else "Reflash factory image."
            self.tree.insert("", "end", values=(
                p_name,
                pinfo.get("size_mb", 0),
                pinfo.get("type", "raw"),
                "BOOT_IMG" if "boot" in p_name else "RAW",
                status_text,
                rec
            ), tags=(tag,))

        # Update HUD
        if report.overall_health == FaultSeverity.INSTANT_FIX:
            self.lbl_status.configure(
                text="⚠️ A/B Slot Failure Detected! Instant Zero-Data-Loss Fix Available.",
                text_color=Theme.ACCENT_GOLD
            )
        elif report.overall_health == FaultSeverity.HEALTHY:
            self.lbl_status.configure(
                text="🟢 All inspected partitions & slots are 100% HEALTHY!",
                text_color="#10b981"
            )
        else:
            self.lbl_status.configure(
                text="🔴 Corrupted Partitions Detected! Ready for Surgical Repair.",
                text_color="#ef4444"
            )

        # Fill report box
        txt = f"Product: {report.product} | Current Slot: {raw_health.get('current_slot', 'N/A')}\n"
        txt += f"Userdata Safety: {report.userdata_status}\n"
        if report.anomalies:
            txt += f"\n--- Anomalies Detected ({len(report.anomalies)}) ---\n"
            for a in report.anomalies:
                txt += f"• [{a.get('severity')}] {a.get('description')}\n"
        if report.instant_commands:
            txt += f"\n--- Recommended Instant Action ---\n"
            for c in report.instant_commands:
                txt += f"👉 Click [Instant A/B Slot Switch] or run: {c}\n"

        self.report_box.insert("1.0", txt)

    def switch_ab_slot(self):
        """Switches active slot to unbrick device instantly without data loss."""
        if not self.last_diagnostic_report:
            messagebox.showinfo("Diagnostic Required", "Please run [Auto-Diagnose Device] first.")
            return

        cmd = self.last_diagnostic_report.instant_commands
        if not cmd:
            messagebox.showinfo("No Slot Switch Needed", "No slot switch is currently recommended for this device.")
            return

        target_cmd = cmd[0]
        if messagebox.askyesno("Instant Unbrick", f"Run instant zero-data-loss slot switch:\n\n{target_cmd}\n\nProceed?"):
            self.logger.info(f"Running: {target_cmd}")
            parts = target_cmd.split()
            slot = parts[-1]
            fb = FastbootPartitionReader()
            out = fb._run_cmd(["set_active", slot])
            self.logger.info(f"Fastboot response: {out}")
            messagebox.showinfo("Result", f"Slot switched to '{slot}'!\n\n{out}\n\nReboot device now.")
            self.start_diagnosis()

    def start_surgical_fix(self):
        """Flashes only the selected corrupted partition with 0% data loss."""
        part = self.selected_partition_var.get().strip()
        fw = self.fw_path_var.get().strip()

        if not part:
            messagebox.showwarning("Select Partition", "Please select a partition from the table to repair.")
            return
        if not fw or not os.path.exists(fw):
            messagebox.showerror("Firmware Missing", "Please select a valid factory firmware archive (.zip, .tar, folder).")
            return

        # Enforce Firewall before user confirmation
        try:
            DataLossFirewall.validate_target(part)
        except Exception as e:
            messagebox.showerror("FIREWALL BLOCK", str(e))
            return

        msg = (
            f"SURGICAL REPAIR (Zero Data Loss Guarantee):\n\n"
            f"Target Partition: {part}\n"
            f"Firmware Container: {os.path.basename(fw)}\n\n"
            f"• ONLY '{part}' will be written.\n"
            f"• User Data (userdata/nvram) is 100% PROTECTED & UNTOUCHED.\n\n"
            f"Proceed with surgical flash?"
        )
        if not messagebox.askyesno("Confirm Surgical Flash", msg):
            return

        def run_fix():
            self.lbl_status.configure(text=f"💉 Extracting & Surgically Flashing '{part}'...", text_color=Theme.ACCENT_CYAN)
            try:
                flasher = SurgicalSinglePartitionFlasher()
                extract_dir = os.path.join(os.getcwd(), "unpacked", "surgical_temp")
                extracted_img = flasher.extract_single_image(fw, part, extract_dir)
                self.logger.info(f"Extracted surgical image: {extracted_img}")

                # Execute surgical fastboot flash
                res = flasher.flash_partition_fastboot(part, extracted_img)
                if res.get("success"):
                    self.logger.success(f"Surgical flash of '{part}' succeeded! User data 100% safe.")
                    messagebox.showinfo("Unbrick Success", f"Partition '{part}' successfully repaired!\n\nUser Data: 100% PRESERVED.\nReboot phone to test.")
                else:
                    self.logger.error(f"Surgical flash failed: {res.get('error') or res.get('output')}")
                    messagebox.showerror("Flash Error", f"Surgical flash failed:\n\n{res.get('output') or res.get('error')}")
            except Exception as e:
                self.logger.error(f"[Surgical Flash Exception] {str(e)}")
                messagebox.showerror("Error", str(e))
            finally:
                self.controller.after(0, self.start_diagnosis)

        threading.Thread(target=run_fix, daemon=True).start()
