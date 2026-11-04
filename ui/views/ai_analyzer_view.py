"""
BS Lab Tool v2.0 PRO - AI Log & Hardware UART Diagnostic Analyzer View.
Features offline GSM pattern matching, UART serial live capture, and step-by-step repair roadmap.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from engines.ai_analyzer.log_analyzer_engine import AILogAnalyzerEngine, DiagnosisReport, UARTStreamListener


class AILogAnalyzerView:
    """Intelligent AI Log & Hardware UART Diagnostic Suite View."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        self.analyzer_engine = AILogAnalyzerEngine(logger=self.logger)
        self.uart_listener = None

        # State Variables
        self.log_source_var = tk.StringVar(value="Auto-Detect Log Type")
        self.uart_port_var = tk.StringVar(value="Select COM")
        self.uart_baud_var = tk.StringVar(value="115200")
        self.is_capturing_uart = False

        self._build_left_panel()
        self._build_center_panel()

    # =========================================================================
    # LEFT PANEL: Log Input, UART Sniffer, Quick Capture Controls
    # =========================================================================
    def _build_left_panel(self):
        self.left_panel = ctk.CTkFrame(self.body_frame, width=420, fg_color="#141418", corner_radius=8)

        # 1. Header
        hdr = ctk.CTkFrame(self.left_panel, fg_color="#1C1C24", corner_radius=6)
        hdr.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            hdr,
            text="📥 LOG INPUT & UART SNIFFER",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=10, pady=8)

        # 2. UART Serial Sniffer Toolbar
        uart_card = ctk.CTkFrame(self.left_panel, fg_color="#181822", corner_radius=6)
        uart_card.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(uart_card, text="LIVE UART BOOT CAPTURE (TX/RX):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=10, pady=(6, 2))

        u_row = ctk.CTkFrame(uart_card, fg_color="transparent")
        u_row.pack(fill="x", padx=10, pady=(0, 6))

        self.opt_uart_port = ctk.CTkOptionMenu(
            u_row,
            values=["Select COM", "COM1", "COM3"],
            variable=self.uart_port_var,
            width=110,
            height=28,
            font=ctk.CTkFont(size=10)
        )
        self.opt_uart_port.pack(side="left", padx=(0, 4))

        ctk.CTkOptionMenu(
            u_row,
            values=["115200", "921600", "460800", "57600"],
            variable=self.uart_baud_var,
            width=85,
            height=28,
            font=ctk.CTkFont(size=10)
        )
        self.opt_uart_port.pack(side="left", padx=(0, 4))

        self.btn_uart_toggle = ctk.CTkButton(
            u_row,
            text="▶ Start Sniff",
            width=90,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=self._toggle_uart_capture
        )
        self.btn_uart_toggle.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            u_row,
            text="🔄",
            width=30,
            height=28,
            fg_color="#334155",
            command=self._refresh_uart_coms
        ).pack(side="right", padx=(4, 0))

        # 3. Log Text Box
        self.txt_log_input = ctk.CTkTextbox(
            self.left_panel,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#0A0A0C",
            text_color="#F8FAFC",
            wrap="word",
            corner_radius=6
        )
        self.txt_log_input.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # 4. Quick Actions Row
        action_row = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        action_row.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(
            action_row,
            text="📋 Capture Tool Log",
            height=30,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            command=self._capture_current_tool_log
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            action_row,
            text="📁 Open File",
            width=75,
            height=30,
            font=ctk.CTkFont(size=10),
            fg_color="#334155",
            command=self._open_log_file
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            action_row,
            text="Clear",
            width=50,
            height=30,
            font=ctk.CTkFont(size=10),
            fg_color="#1E1E28",
            hover_color="#DC2626",
            command=self._clear_input
        ).pack(side="right")

        # 5. Prominent Analyze Button
        self.btn_analyze = ctk.CTkButton(
            self.left_panel,
            text="🔍 ANALYZE LOG (AI تجزیہ کریں)",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self._run_analysis
        )
        self.btn_analyze.pack(fill="x", padx=10, pady=(0, 10))

    # =========================================================================
    # CENTER PANEL: AI Diagnosis & Repair Roadmap HUD
    # =========================================================================
    def _build_center_panel(self):
        self.center_panel = ctk.CTkScrollableFrame(self.body_frame, fg_color="#141418", corner_radius=8)

        # Header Capsule
        top_bar = ctk.CTkFrame(self.center_panel, fg_color="#1C1C24", corner_radius=6)
        top_bar.pack(fill="x", padx=8, pady=(8, 8))

        ctk.CTkLabel(
            top_bar,
            text="💡 AI DIAGNOSIS & REPAIR ROADMAP",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=10, pady=8)

        self.lbl_severity = ctk.CTkLabel(
            top_bar,
            text="⚪ READY FOR ANALYSIS",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#272736",
            text_color="#94A3B8",
            corner_radius=4,
            padx=10,
            pady=3
        )
        self.lbl_severity.pack(side="right", padx=10, pady=6)

        # Card 1: Fault Identification & Summary
        self.card_fault = ctk.CTkFrame(self.center_panel, fg_color="#181822", corner_radius=8)
        self.card_fault.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(self.card_fault, text="PROBLEM SUMMARY & ERROR IDENTIFICATION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_summary = ctk.CTkLabel(
            self.card_fault,
            text="Paste a flashing or UART boot log and click 'Analyze Log' to diagnose.",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F8FAFC",
            wraplength=520,
            justify="left"
        )
        self.lbl_summary.pack(anchor="w", padx=12, pady=(0, 4))

        self.lbl_subsystem_info = ctk.CTkLabel(
            self.card_fault,
            text="Subsystem: None | Confidence: 0%",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8"
        )
        self.lbl_subsystem_info.pack(anchor="w", padx=12, pady=(0, 8))

        # Card 2: Technical Root Cause
        self.card_tech = ctk.CTkFrame(self.center_panel, fg_color="#181822", corner_radius=8)
        self.card_tech.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(self.card_tech, text="TECHNICAL ROOT CAUSE & SIGNATURE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_tech_details = ctk.CTkLabel(
            self.card_tech,
            text="Detailed technical analysis and error signatures will be displayed here.",
            font=ctk.CTkFont(size=10),
            text_color="#E2E8F0",
            wraplength=520,
            justify="left"
        )
        self.lbl_tech_details.pack(anchor="w", padx=12, pady=(0, 8))

        # Card 3: Step-by-Step Action Plan (Technician Roadmap)
        self.card_steps = ctk.CTkFrame(self.center_panel, fg_color="#181822", corner_radius=8)
        self.card_steps.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(self.card_steps, text="🔧 STEP-BY-STEP ACTION PLAN (TECHNICIAN REMEDY)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#34D399").pack(anchor="w", padx=12, pady=(8, 4))

        self.txt_steps = ctk.CTkTextbox(
            self.card_steps,
            height=130,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#0F0F14",
            text_color="#34D399",
            wrap="word"
        )
        self.txt_steps.pack(fill="x", padx=12, pady=(0, 8))
        self.txt_steps.insert("1.0", "1. Awaiting log input...\n2. Run analysis to receive actionable repair steps.")
        self.txt_steps.configure(state="disabled")

        # Card 4: Schematic & Multimeter Probing Points
        self.card_schematics = ctk.CTkFrame(self.center_panel, fg_color="#181822", corner_radius=8)
        self.card_schematics.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(self.card_schematics, text="⚡ SCHEMATIC TEST POINTS & VOLTAGE PROBING", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38BDF8").pack(anchor="w", padx=12, pady=(8, 4))

        self.lbl_test_points = ctk.CTkLabel(
            self.card_schematics,
            text="Key circuit rails, coils, and test points will be listed here.",
            font=ctk.CTkFont(size=10),
            text_color="#93C5FD",
            wraplength=520,
            justify="left"
        )
        self.lbl_test_points.pack(anchor="w", padx=12, pady=(0, 8))

        # Bottom Button: Copy Report
        ctk.CTkButton(
            self.center_panel,
            text="📋 Copy Complete Diagnosis Report to Clipboard",
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._copy_report
        ).pack(fill="x", padx=8, pady=(0, 10))

    # =========================================================================
    # ACTIONS & HANDLERS
    # =========================================================================
    def _run_analysis(self):
        raw_text = self.txt_log_input.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showwarning("Empty Log", "Please paste log text or capture from tool before running analysis.")
            return

        self.logger.info("Executing AI Pattern Analysis on supplied log...")
        report = self.analyzer_engine.analyze_log(raw_text)

        # Update UI with findings
        self.lbl_severity.configure(text=report.severity_badge, fg_color=report.severity_color, text_color="#FFFFFF")
        self.lbl_summary.configure(text=report.summary)
        self.lbl_subsystem_info.configure(text=f"Subsystem: {report.subsystem}  |  Confidence: {int(report.confidence * 100)}%  |  Fault: {report.fault_type}")
        self.lbl_tech_details.configure(text=report.technical_details)

        # Populate Steps
        self.txt_steps.configure(state="normal")
        self.txt_steps.delete("1.0", "end")
        for idx, step in enumerate(report.repair_steps, 1):
            self.txt_steps.insert("end", f"{idx}. {step}\n")
        self.txt_steps.configure(state="disabled")

        # Populate Test Points
        if report.schematic_test_points:
            tp_text = "  ● " + "\n  ● ".join(report.schematic_test_points)
        else:
            tp_text = "No specific hardware test points required for this issue."
        self.lbl_test_points.configure(text=tp_text)

        self.last_report = report
        self.logger.success(f"[AI Diagnosis] {report.summary} (Severity: {report.severity})")

    def _capture_current_tool_log(self):
        """Pulls current console log directly from MainWindow Console."""
        try:
            console_text = self.controller.console_panel.console_text.get("1.0", "end").strip()
            if console_text:
                self.txt_log_input.delete("1.0", "end")
                self.txt_log_input.insert("1.0", console_text)
                self.logger.success("[✓] Successfully captured current session log from console.")
                self._run_analysis()
            else:
                messagebox.showinfo("Empty Console", "Current session console log is empty.")
        except Exception as e:
            self.logger.error(f"Failed to capture console log: {str(e)}")

    def _open_log_file(self):
        f = filedialog.askopenfilename(
            title="Select Log File to Analyze",
            filetypes=[("Text & Log Files", "*.txt;*.log"), ("All Files", "*.*")]
        )
        if f:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
                self.txt_log_input.delete("1.0", "end")
                self.txt_log_input.insert("1.0", content)
                self.logger.info(f"Loaded log file: {os.path.basename(f)}")
                self._run_analysis()
            except Exception as e:
                self.logger.error(f"Failed to read file: {str(e)}")

    def _clear_input(self):
        self.txt_log_input.delete("1.0", "end")

    def _refresh_uart_coms(self):
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["No Ports"]
        self.opt_uart_port.configure(values=ports)
        self.uart_port_var.set(ports[0])
        self.logger.info(f"Refreshed UART COM ports: {', '.join(ports)}")

    def _toggle_uart_capture(self):
        if self.is_capturing_uart:
            # Stop
            if self.uart_listener:
                self.uart_listener.stop()
            self.is_capturing_uart = False
            self.btn_uart_toggle.configure(text="▶ Start Sniff", fg_color="#059669", hover_color="#047857")
            self.logger.info("[UART] Live sniffer stopped.")
        else:
            port = self.uart_port_var.get().strip()
            if not port or "No Ports" in port or "Select" in port:
                messagebox.showwarning("Select Port", "Please select an active UART COM port.")
                return

            baud = int(self.uart_baud_var.get().strip())
            self.logger.info(f"[UART] Starting live serial capture on {port} @ {baud} bps...")

            def on_line(line):
                self.txt_log_input.insert("end", line + "\n")
                self.txt_log_input.see("end")

            self.uart_listener = UARTStreamListener(port=port, baudrate=baud, on_line_cb=on_line)
            self.uart_listener.start()
            self.is_capturing_uart = True
            self.btn_uart_toggle.configure(text="⏹ Stop Sniff", fg_color="#DC2626", hover_color="#B91C1C")

    def _copy_report(self):
        if not hasattr(self, "last_report") or not self.last_report:
            messagebox.showinfo("No Report", "Please run analysis first to generate a report.")
            return

        r = self.last_report
        rep = (
            f"=======================================================\n"
            f"  BS LAB TOOL v2.0 PRO — AI DIAGNOSIS REPORT\n"
            f"=======================================================\n"
            f"Fault Type   : {r.fault_type}\n"
            f"Subsystem    : {r.subsystem}\n"
            f"Severity     : {r.severity_badge}\n"
            f"Confidence   : {int(r.confidence * 100)}%\n"
            f"Summary      : {r.summary}\n\n"
            f"Technical Details:\n{r.technical_details}\n\n"
            f"Step-by-Step Action Plan:\n" +
            "\n".join(f"  {idx}. {s}" for idx, s in enumerate(r.repair_steps, 1)) +
            f"\n\nSchematic / Probing Points:\n" +
            "\n".join(f"  - {tp}" for tp in r.schematic_test_points) +
            f"\n=======================================================\n"
        )
        self.body_frame.clipboard_clear()
        self.body_frame.clipboard_append(rep)
        self.logger.success("[✓] Diagnosis report copied to clipboard.")

    def show(self):
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=4)
        self._refresh_uart_coms()

    def hide(self):
        if self.is_capturing_uart:
            self._toggle_uart_capture()
        self.left_panel.grid_forget()
        self.center_panel.grid_forget()
