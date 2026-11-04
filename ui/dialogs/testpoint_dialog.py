"""
Test Point Pinout Modal Dialog for BS Lab Tool v2.0 PRO.
Interactive schematic motherboard pinout preview with zoom, step-by-step
EDL/BROM connection instructions, and 1-click model switching.
"""

import tkinter as tk
import customtkinter as ctk
from engines.testpoints.tp_database import TEST_POINT_DATABASE, find_testpoint_for_model

class TestPointDialog(ctk.CTkToplevel):
    """Interactive modal window for motherboard test point and EDL pinout inspection."""

    def __init__(self, master, brand: str = "", model: str = "", platform: str = "", controller = None):
        super().__init__(master)

        self.controller = controller
        self.brand = brand
        self.raw_model = model
        self.platform = platform
        self.zoom_scale = 1.0

        # Resolve initial model
        matched_name, sch_data = find_testpoint_for_model(brand, model, platform)
        self.current_model = matched_name
        self.current_data = sch_data

        self.title(f"BS Lab Tool — Hardware Pinout: {self.current_model}")
        self.geometry("860x650")
        self.minsize(780, 580)
        self.configure(fg_color="#0F0F14")
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self.load_model(self.current_model)

    def _build_ui(self):
        # 1. Top Header Bar
        header = ctk.CTkFrame(self, fg_color="#181822", corner_radius=0, height=52)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header,
            text="📍 HARDWARE TEST POINT & EDL / BROM PINOUT VIEWER",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=16, pady=12)

        self.lbl_mode_badge = ctk.CTkLabel(
            header,
            text="● BROM / EDL MODE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#34D399",
            fg_color="#064E3B",
            corner_radius=4,
            padx=10,
            pady=4
        )
        self.lbl_mode_badge.pack(side="right", padx=16, pady=12)

        # 2. Main Content Split (Left: Schematic Canvas | Right: Instructions & Controls)
        content_frame = ctk.CTkFrame(self, fg_color="#0F0F14")
        content_frame.pack(fill="both", expand=True, padx=14, pady=10)

        # Left Column: Canvas + Zoom Toolbar
        left_col = ctk.CTkFrame(content_frame, fg_color="#14141B", corner_radius=8)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Canvas Top Bar
        zoom_bar = ctk.CTkFrame(left_col, fg_color="transparent")
        zoom_bar.pack(fill="x", padx=12, pady=(10, 4))

        self.lbl_diagram_title = ctk.CTkLabel(
            zoom_bar,
            text=f"📱 {self.current_model}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_diagram_title.pack(side="left")

        ctk.CTkButton(zoom_bar, text="➕", width=36, height=26, font=ctk.CTkFont(size=12), fg_color="#334155", hover_color="#475569", command=self._zoom_in).pack(side="right", padx=2)
        ctk.CTkButton(zoom_bar, text="➖", width=36, height=26, font=ctk.CTkFont(size=12), fg_color="#334155", hover_color="#475569", command=self._zoom_out).pack(side="right", padx=2)
        ctk.CTkButton(zoom_bar, text="🔄 Reset", width=65, height=26, font=ctk.CTkFont(size=10), fg_color="#334155", hover_color="#475569", command=self._zoom_reset).pack(side="right", padx=2)

        # Interactive Motherboard Canvas
        canvas_container = ctk.CTkFrame(left_col, fg_color="#0A0A0D", corner_radius=6)
        canvas_container.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self.canvas = tk.Canvas(canvas_container, bg="#0A0A0D", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        # Right Column: Details, Steps, and Selector
        right_col = ctk.CTkFrame(content_frame, width=320, fg_color="#14141B", corner_radius=8)
        right_col.pack(side="right", fill="y", padx=(0, 0))
        right_col.pack_propagate(False)

        # Model Quick Picker
        ctk.CTkLabel(right_col, text="SWITCH PINOUT MODEL:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(12, 2))
        
        all_models = list(TEST_POINT_DATABASE.keys())
        self.model_combo = ctk.CTkOptionMenu(
            right_col,
            values=all_models,
            fg_color="#0284C7",
            button_color="#0369A1",
            height=30,
            command=self._on_model_combo_selected
        )
        self.model_combo.pack(fill="x", padx=12, pady=(0, 10))
        self.model_combo.set(self.current_model)

        # Specs Card
        specs_card = ctk.CTkFrame(right_col, fg_color="#1A1A24", corner_radius=6)
        specs_card.pack(fill="x", padx=12, pady=(0, 10))

        self.lbl_chipset = ctk.CTkLabel(specs_card, text="Chipset: ...", font=ctk.CTkFont(size=11), text_color="#38BDF8", anchor="w")
        self.lbl_chipset.pack(fill="x", padx=10, pady=(8, 2))

        self.lbl_tptype = ctk.CTkLabel(specs_card, text="Pinout Type: ...", font=ctk.CTkFont(size=11), text_color="#FBBF24", anchor="w")
        self.lbl_tptype.pack(fill="x", padx=10, pady=(2, 2))

        self.lbl_difficulty = ctk.CTkLabel(specs_card, text="Difficulty: ...", font=ctk.CTkFont(size=11), text_color="#A7F3D0", anchor="w")
        self.lbl_difficulty.pack(fill="x", padx=10, pady=(2, 8))

        # Instructions Section
        ctk.CTkLabel(right_col, text="⚡ HARDWARE CONNECTION STEPS:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=12, pady=(4, 2))

        instr_frame = ctk.CTkScrollableFrame(right_col, fg_color="#0A0A0D", corner_radius=6)
        instr_frame.pack(fill="both", expand=True, padx=12, pady=(2, 10))

        self.lbl_instructions = ctk.CTkLabel(
            instr_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#E2E8F0",
            justify="left",
            wraplength=270
        )
        self.lbl_instructions.pack(anchor="nw", padx=6, pady=6)

        # Action Buttons at Bottom of Right Col
        btn_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))

        if self.controller and hasattr(self.controller, "switch_to_platform"):
            ctk.CTkButton(
                btn_frame,
                text="🚀 Open Full Pinout Studio",
                height=32,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#6366F1",
                hover_color="#4F46E5",
                command=self._open_in_studio
            ).pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            btn_frame,
            text="✕ Close",
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self.destroy
        ).pack(fill="x")

    def _on_model_combo_selected(self, chosen: str):
        self.load_model(chosen)

    def load_model(self, model_name: str):
        if model_name not in TEST_POINT_DATABASE:
            return
        self.current_model = model_name
        self.current_data = TEST_POINT_DATABASE[model_name]

        self.title(f"BS Lab Tool — Hardware Pinout: {model_name}")
        self.lbl_diagram_title.configure(text=f"📱 {model_name}")
        self.model_combo.set(model_name)

        mode_text = self.current_data.get("mode", "Test Point Mode")
        self.lbl_mode_badge.configure(text=f"● {mode_text.upper()}")

        self.lbl_chipset.configure(text=f"⚡ Chipset: {self.current_data.get('chipset', 'Unknown SoC')}")
        self.lbl_tptype.configure(text=f"📌 Type: {self.current_data.get('tp_type', 'Test Point')}")
        self.lbl_difficulty.configure(text=f"🎯 Difficulty: {self.current_data.get('difficulty', 'Standard')}")

        instr = self.current_data.get("instructions", "No step-by-step instructions available.")
        self.lbl_instructions.configure(text=instr)

        self._draw_schematic(self.current_data.get("schematic", {}))

    def _zoom_in(self):
        self.zoom_scale = min(self.zoom_scale * 1.25, 3.0)
        self._draw_schematic(self.current_data.get("schematic", {}))

    def _zoom_out(self):
        self.zoom_scale = max(self.zoom_scale * 0.8, 0.5)
        self._draw_schematic(self.current_data.get("schematic", {}))

    def _zoom_reset(self):
        self.zoom_scale = 1.0
        self._draw_schematic(self.current_data.get("schematic", {}))

    def _draw_schematic(self, sch: dict):
        self.canvas.delete("all")
        if not sch:
            return

        c_w = self.canvas.winfo_width()
        c_h = self.canvas.winfo_height()
        if c_w <= 1: c_w = 480
        if c_h <= 1: c_h = 440

        s = self.zoom_scale
        ox = (c_w - 480 * s) / 2
        oy = (c_h - 460 * s) / 2

        board_col = sch.get("board_color", "#1E2A38")

        # 1. Motherboard PCB Outline
        self.canvas.create_rectangle(
            ox + 40 * s, oy + 40 * s,
            ox + 450 * s, oy + 430 * s,
            fill=board_col, outline="#38BDF8", width=2
        )
        self.canvas.create_text(
            ox + 245 * s, oy + 55 * s,
            text="MOTHERBOARD PCB (MAIN BOARD ARCHITECTURE)",
            fill="#64748B", font=("Segoe UI", int(9 * s), "bold")
        )

        # 2. Key Components
        def draw_ic(rect, label, col="#0F172A", border="#475569"):
            rx, ry, rw, rh = rect
            self.canvas.create_rectangle(
                ox + rx * s, oy + ry * s,
                ox + (rx + rw) * s, oy + (ry + rh) * s,
                fill=col, outline=border, width=1.5
            )
            self.canvas.create_text(
                ox + (rx + rw / 2) * s, oy + (ry + rh / 2) * s,
                text=label, fill="#94A3B8", font=("Segoe UI", int(9 * s), "bold")
            )

        if "cpu_pos" in sch:
            draw_ic(sch["cpu_pos"], "CPU / SoC\n(Processor)", "#1E1E28", "#6366F1")
        if "emmc_pos" in sch:
            draw_ic(sch["emmc_pos"], "STORAGE\n(eMMC / UFS)", "#1E1E28", "#0EA5E9")
        if "pmic_pos" in sch:
            draw_ic(sch["pmic_pos"], "PMIC\n(Power IC)", "#1E1E28", "#8B5CF6")
        if "battery_pos" in sch:
            draw_ic(sch["battery_pos"], "BATTERY FPC\n[DISCONNECT]", "#331E1E", "#EF4444")
        if "sim_pos" in sch:
            draw_ic(sch["sim_pos"], "SIM / SD TRAY", "#1E281E", "#10B981")

        # 3. Test Point Pads & Target Markers
        for pad in sch.get("tp_pads", []):
            px, py = pad["pos"]
            cx = ox + px * s
            cy = oy + py * s
            color = pad.get("color", "#EF4444")
            name = pad.get("name", "TP")
            is_signal = pad.get("is_signal", True)

            # Outer Target Crosshair Ring
            r_outer = 16 * s
            self.canvas.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer, outline=color, width=1.5, dash=(3, 2))

            # Main Solder Pad
            r = 7 * s
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="#FFFFFF", width=1.5)

            # Signal Pointer / Callout Label
            lbl_offset_x = 22 * s
            lbl_offset_y = -14 * s if py < 250 else 14 * s

            self.canvas.create_line(cx, cy, cx + lbl_offset_x, cy + lbl_offset_y, fill=color, width=1.5)
            self.canvas.create_rectangle(
                cx + lbl_offset_x - 4, cy + lbl_offset_y - 8,
                cx + lbl_offset_x + len(name) * 7 * s + 6, cy + lbl_offset_y + 8,
                fill="#0F0F14", outline=color, width=1
            )
            self.canvas.create_text(
                cx + lbl_offset_x + 2, cy + lbl_offset_y,
                text=name, fill="#FFFFFF", font=("Segoe UI", int(9 * s), "bold"), anchor="w"
            )

    def _open_in_studio(self):
        try:
            if self.controller and hasattr(self.controller, "switch_to_platform"):
                self.controller.switch_to_platform("testpoints")
                if hasattr(self.controller, "view_testpoints") and hasattr(self.controller.view_testpoints, "load_model"):
                    self.controller.view_testpoints.load_model(self.current_model)
        except Exception:
            pass
        self.destroy()
