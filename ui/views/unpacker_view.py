import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from engines.unpackers import SamsungTarUnpacker, SuperSparseUnpacker, OfpOpsUnpacker, PayloadUnpacker
from utils.file_utils import format_bytes
from ui.theme import Theme

class FirmwareUnpackerView:
    """Universal Firmware Unpacker View (.ofp, .ops, Samsung .tar.md5, Android super.img)."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.format_var = tk.StringVar(value="Samsung (.tar.md5 + LZ4)")
        self.input_file_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "unpacked"))
        self.chk_lz4_var = tk.BooleanVar(value=True)

        self.extracted_files = []
        self.is_unpacking = False

        self._build_left_panel()
        self._build_center_panel()

    def _build_left_panel(self):
        self.left_panel_unp = ctk.CTkScrollableFrame(
            self.body_frame, 
            width=300, 
            fg_color=Theme.BG_PANEL, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        ctk.CTkLabel(
            self.left_panel_unp,
            text="📦 FIRMWARE UNPACKER",
            font=Theme.font_bold(size=12),
            text_color=Theme.ACCENT_CYAN
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Format Selector
        ctk.CTkLabel(self.left_panel_unp, text="Select Archive Format:", font=Theme.font_ui(size=10), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=12, pady=(2, 0))
        self.format_menu = ctk.CTkOptionMenu(
            self.left_panel_unp,
            values=[
                "Android OTA (payload.bin)",
                "Samsung (.tar.md5 + LZ4)",
                "Oppo / Realme (.ofp)",
                "OnePlus (.ops)",
                "Android super.img (Dynamic)",
                "Android Sparse (.img to Raw)"
            ],
            variable=self.format_var,
            fg_color=Theme.ACCENT_BLUE,
            button_hover_color=Theme.ACCENT_BLUE_HOVER,
            height=32
        )
        self.format_menu.pack(fill="x", padx=12, pady=(2, 10))

        # Input Archive Picker
        in_card = ctk.CTkFrame(
            self.left_panel_unp, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        in_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(in_card, text="SOURCE ARCHIVE FILE", font=Theme.font_bold(size=11), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(8, 4))
        
        in_row = ctk.CTkFrame(in_card, fg_color="transparent")
        in_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkEntry(in_row, textvariable=self.input_file_var, font=Theme.font_ui(size=10), height=28, fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER_CARD).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(in_row, text="📁", width=30, height=28, fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, command=self._browse_input).pack(side="right")

        # Output Folder Picker
        out_card = ctk.CTkFrame(
            self.left_panel_unp, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        out_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(out_card, text="EXTRACTION DIRECTORY", font=Theme.font_bold(size=11), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(8, 4))

        out_row = ctk.CTkFrame(out_card, fg_color="transparent")
        out_row.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkEntry(out_row, textvariable=self.output_dir_var, font=Theme.font_ui(size=10), height=28, fg_color=Theme.SURFACE_INPUT, border_color=Theme.BORDER_CARD).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(out_row, text="📁", width=30, height=28, fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, command=self._browse_output).pack(side="right")

        # Options Card
        opt_card = ctk.CTkFrame(
            self.left_panel_unp, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        opt_card.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkLabel(opt_card, text="UNPACK OPTIONS", font=Theme.font_bold(size=11), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(8, 4))
        ctk.CTkCheckBox(opt_card, text="Decompress LZ4 (.img.lz4 -> .img)", variable=self.chk_lz4_var, font=Theme.font_ui(size=10)).pack(anchor="w", padx=10, pady=(2, 8))

        # Big Unpack Button
        self.btn_start_unpack = ctk.CTkButton(
            self.left_panel_unp,
            text="⚡ START EXTRACTION",
            font=Theme.font_bold(size=13),
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            height=42,
            command=self._start_unpacking
        )
        self.btn_start_unpack.pack(fill="x", padx=10, pady=(0, 10))

    def _build_center_panel(self):
        self.center_panel_unp = ctk.CTkFrame(
            self.body_frame, 
            fg_color=Theme.BG_PANEL, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # Header Info Bar
        top_bar = ctk.CTkFrame(
            self.center_panel_unp, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        top_bar.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            top_bar,
            text="📦 Universal High-Speed Firmware & Partition Extractor",
            font=Theme.font_bold(size=13),
            text_color=Theme.ACCENT_CYAN
        ).pack(side="left", padx=14, pady=8)

        ctk.CTkButton(
            top_bar,
            text="📂 Open Output Folder",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._open_output_folder
        ).pack(side="right", padx=10, pady=8)

        # Partition Treeview
        tree_frame = ctk.CTkFrame(self.center_panel_unp, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        cols = ("idx", "name", "size", "status")
        self.tree_unp = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.tree_unp.heading("idx", text="#")
        self.tree_unp.heading("name", text="Extracted Partition / File Name")
        self.tree_unp.heading("size", text="File Size")
        self.tree_unp.heading("status", text="Status")

        self.tree_unp.column("idx", width=40, anchor="center")
        self.tree_unp.column("name", width=340, anchor="w")
        self.tree_unp.column("size", width=120, anchor="e")
        self.tree_unp.column("status", width=120, anchor="center")

        unp_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_unp.yview)
        self.tree_unp.configure(yscrollcommand=unp_scroll.set)
        self.tree_unp.pack(side="left", fill="both", expand=True)
        unp_scroll.pack(side="right", fill="y")
        self.tree_unp.tag_configure("even", background=Theme.TABLE_ROW_EVEN)
        self.tree_unp.tag_configure("odd", background=Theme.TABLE_ROW_ODD)

        # Progress HUD
        hud_frame = ctk.CTkFrame(
            self.center_panel_unp, 
            fg_color=Theme.SURFACE_CARD, 
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        hud_frame.pack(fill="x", padx=10, pady=(6, 10))

        self.lbl_unp_status = ctk.CTkLabel(
            hud_frame,
            text="Status: Ready to Unpack Firmware",
            font=Theme.font_bold(size=11),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_unp_status.pack(anchor="w", padx=12, pady=(6, 2))

        self.bar_unp = ctk.CTkProgressBar(hud_frame, height=8, fg_color="#27272A", progress_color="#059669")
        self.bar_unp.pack(fill="x", padx=12, pady=(0, 8))
        self.bar_unp.set(0.0)

    def _browse_input(self):
        fmt = self.format_var.get()
        if "payload.bin" in fmt:
            f = filedialog.askopenfilename(title="Select Android OTA Payload File", filetypes=[("Payload Binary", "payload.bin;*.bin"), ("All Files", "*.*")])
        elif "Samsung" in fmt:
            f = filedialog.askopenfilename(title="Select Samsung .tar.md5 Firmware", filetypes=[("Samsung TAR", "*.tar.md5;*.tar"), ("All Files", "*.*")])
        elif "Oppo" in fmt:
            f = filedialog.askopenfilename(title="Select Oppo/Realme .ofp Firmware", filetypes=[("OFP Files", "*.ofp"), ("All Files", "*.*")])
        elif "OnePlus" in fmt:
            f = filedialog.askopenfilename(title="Select OnePlus .ops Firmware", filetypes=[("OPS Files", "*.ops"), ("All Files", "*.*")])
        elif "super.img" in fmt or "Sparse" in fmt:
            f = filedialog.askopenfilename(title="Select Android Image", filetypes=[("Image Files", "*.img;super*.img"), ("All Files", "*.*")])
        else:
            f = filedialog.askopenfilename(title="Select Firmware File")

        if f:
            self.input_file_var.set(f)
            self.logger.info(f"Target Firmware Attached: {os.path.basename(f)}")

    def _browse_output(self):
        d = filedialog.askdirectory(title="Select Output Directory for Extracted Files")
        if d:
            self.output_dir_var.set(d)

    def _open_output_folder(self):
        d = self.output_dir_var.get().strip()
        if os.path.exists(d):
            os.startfile(d)
        else:
            messagebox.showwarning("Folder Not Found", "Output directory does not exist yet.")

    def _start_unpacking(self):
        if self.is_unpacking:
            return

        in_file = self.input_file_var.get().strip()
        out_dir = self.output_dir_var.get().strip()
        fmt = self.format_var.get()

        if not in_file or not os.path.exists(in_file):
            messagebox.showerror("File Missing", "Please select a valid input firmware file first.")
            return

        os.makedirs(out_dir, exist_ok=True)
        for item in self.tree_unp.get_children():
            self.tree_unp.delete(item)

        self.is_unpacking = True
        self.btn_start_unpack.configure(state="disabled", text="⏳ UNPACKING ACTIVE...")

        import threading
        def run():
            try:
                def prog_cb(pct, status_text="Unpacking..."):
                    self.center_panel_unp.after(0, lambda: self.bar_unp.set(pct))
                    self.center_panel_unp.after(0, lambda: self.lbl_unp_status.configure(text=f"Status: {status_text} ({int(pct*100)}%)"))

                def log_cb(msg):
                    self.logger.info(f"[UNPACK] {msg}")

                files = []
                if "payload.bin" in fmt:
                    unpacker = PayloadUnpacker(logger=self.logger)
                    extracted_paths = unpacker.unpack(
                        payload_path=in_file,
                        output_dir=out_dir,
                        progress_cb=lambda pct, msg: prog_cb(pct / 100.0, msg)
                    )
                    for ep in extracted_paths:
                        sz = os.path.getsize(ep) if os.path.exists(ep) else 0
                        files.append({
                            "name": os.path.basename(ep),
                            "path": ep,
                            "size": sz,
                            "size_human": format_bytes(sz)
                        })
                elif "Samsung" in fmt:
                    files = SamsungTarUnpacker.unpack_samsung_tar(
                        tar_path=in_file,
                        out_dir=out_dir,
                        decompress_lz4=self.chk_lz4_var.get(),
                        progress_cb=prog_cb,
                        log_cb=log_cb
                    )
                elif "Oppo" in fmt:
                    files = OfpOpsUnpacker.unpack_ofp(
                        ofp_path=in_file,
                        out_dir=out_dir,
                        progress_cb=prog_cb,
                        log_cb=log_cb
                    )
                elif "OnePlus" in fmt:
                    files = OfpOpsUnpacker.unpack_ops(
                        ops_path=in_file,
                        out_dir=out_dir,
                        progress_cb=prog_cb,
                        log_cb=log_cb
                    )
                elif "super.img" in fmt:
                    files = SuperSparseUnpacker.unpack_super_image(
                        super_path=in_file,
                        out_dir=out_dir,
                        progress_cb=prog_cb,
                        log_cb=log_cb
                    )
                elif "Sparse" in fmt:
                    raw_out = os.path.join(out_dir, "raw_image.img")
                    ok = SuperSparseUnpacker.unsparse_image(
                        sparse_path=in_file,
                        out_raw_path=raw_out,
                        progress_cb=prog_cb,
                        log_cb=log_cb
                    )
                    if ok:
                        files = [{"name": "raw_image.img", "path": raw_out, "size": os.path.getsize(raw_out), "size_human": format_bytes(os.path.getsize(raw_out))}]

                # Populate treeview
                self.center_panel_unp.after(0, lambda: self._populate_results(files))
                self.logger.success(f"Extraction Completed! {len(files)} files extracted to: {out_dir}")

            except Exception as e:
                self.logger.error(f"Unpacking failed: {str(e)}")
                messagebox.showerror("Error", f"Failed to unpack firmware:\n{str(e)}")
            finally:
                self.is_unpacking = False
                self.center_panel_unp.after(0, lambda: self.btn_start_unpack.configure(state="normal", text="⚡ START EXTRACTION"))
                self.center_panel_unp.after(0, lambda: self.lbl_unp_status.configure(text="Status: Extraction Finished (100%)"))
                self.center_panel_unp.after(0, lambda: self.bar_unp.set(1.0))

        threading.Thread(target=run, daemon=True).start()

    def _populate_results(self, files: list):
        for idx, f in enumerate(files, start=1):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree_unp.insert(
                "",
                "end",
                values=(
                    idx,
                    f.get("name", "--"),
                    f.get("size_human", "--"),
                    "✓ Extracted (OK)"
                ),
                tags=(tag,)
            )

    def show(self):
        self.left_panel_unp.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel_unp.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel_unp.grid_forget()
        self.center_panel_unp.grid_forget()
