import customtkinter as ctk
from ui.theme import Theme

class ConsolePanel(ctk.CTkFrame):
    """Live Diagnostics & Process Log Console with tag styling and controls."""

    def __init__(self, master, logger=None):
        super().__init__(master, width=380, fg_color=Theme.BG_PANEL, corner_radius=8, border_width=1, border_color=Theme.BORDER_CARD)
        self.logger = logger
        self._build_ui()
        self._setup_tags()

        if self.logger:
            self.logger.set_widget(self.console_text)

    def _build_ui(self):
        # Console Header
        console_hdr = ctk.CTkFrame(self, height=36, fg_color=Theme.SURFACE_CARD, corner_radius=6)
        console_hdr.pack(fill="x", padx=8, pady=(8, 6))

        ctk.CTkLabel(
            console_hdr,
            text="LIVE DIAGNOSTICS & PROCESS LOG",
            font=Theme.font_bold(size=11),
            text_color=Theme.ACCENT_CYAN
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            console_hdr,
            text="Clear",
            width=50,
            height=22,
            font=Theme.font_ui(size=10),
            fg_color="#334155",
            command=self.clear_console
        ).pack(side="right", padx=(2, 6))

        ctk.CTkButton(
            console_hdr,
            text="Copy",
            width=50,
            height=22,
            font=Theme.font_ui(size=10),
            fg_color="#334155",
            command=self.copy_console
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            console_hdr,
            text="💾 Export",
            width=62,
            height=22,
            font=Theme.font_bold(size=10),
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.ACCENT_BLUE_HOVER,
            command=self.export_log
        ).pack(side="right", padx=2)

        # Console Text Box
        self.console_text = ctk.CTkTextbox(
            self,
            font=Theme.font_mono(size=10),
            fg_color=Theme.SURFACE_INPUT,
            text_color=Theme.TEXT_PRIMARY,
            wrap="word",
            corner_radius=6
        )
        self.console_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _setup_tags(self):
        self.console_text.tag_config("INFO", foreground=Theme.TEXT_SECONDARY)
        self.console_text.tag_config("SUCCESS", foreground="#34D399")
        self.console_text.tag_config("ERROR", foreground="#F87171")
        self.console_text.tag_config("WARN", foreground="#FBBF24")
        self.console_text.tag_config("BROM", foreground=Theme.ACCENT_CYAN)

    def copy_console(self):
        text = self.console_text.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(text)
        if self.logger:
            self.logger.info("Log content copied to clipboard.")

    def clear_console(self):
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")

    def export_log(self):
        text = self.console_text.get("1.0", "end").strip()
        if not text:
            if self.logger:
                self.logger.warn("Console log is empty. Nothing to export.")
            return

        import datetime
        from tkinter import filedialog
        
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"BSLab_Log_{now_str}.txt"
        
        fpath = filedialog.asksaveasfilename(
            title="Export Diagnostic Process Log",
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text Document", "*.txt"), ("All Files", "*.*")]
        )
        if not fpath:
            return

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write("  BS LAB TOOL v2.0 PRO — DIAGNOSTIC PROCESS LOG\n")
                f.write(f"  Export Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("  Platform: Windows x64\n")
                f.write("=" * 70 + "\n\n")
                f.write(text)
                f.write("\n\n" + "=" * 70 + "\n")
                f.write("  [END OF LOG FILE]\n")
                f.write("=" * 70 + "\n")
            if self.logger:
                self.logger.success(f"[✓] Log exported successfully: {fpath}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"[!] Failed to export log: {str(e)}")
