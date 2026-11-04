import tkinter as tk
import customtkinter as ctk
from engines.testpoints.tp_database import TEST_POINT_DATABASE

class TestPointView:
    """Visual Test Point (TP) Pinout Gallery & Interactive Motherboard Schematic Viewer."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.selected_brand_var = tk.StringVar(value="All Brands")
        self.search_model_var = tk.StringVar(value="")
        self.current_model = "Infinix Hot 12 Play (X6816)"
        self.zoom_scale = 1.0

        self.filtered_models = list(TEST_POINT_DATABASE.keys())

        self._build_left_panel()
        self._build_center_panel()

    def _build_left_panel(self):
        self.left_panel_tp = ctk.CTkFrame(self.body_frame, width=300, fg_color="#141418", corner_radius=8)

        ctk.CTkLabel(
            self.left_panel_tp,
            text="📌 HARDWARE TEST POINTS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00D2FF"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Brand Filter
        ctk.CTkLabel(self.left_panel_tp, text="Filter by Brand:", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(2, 0))
        self.brand_menu = ctk.CTkOptionMenu(
            self.left_panel_tp,
            values=["All Brands", "Infinix", "Xiaomi", "Vivo", "Realme", "Tecno", "Samsung"],
            variable=self.selected_brand_var,
            fg_color="#0284C7",
            height=30,
            command=self._on_brand_filter_changed
        )
        self.brand_menu.pack(fill="x", padx=12, pady=(2, 8))

        # Search box
        ctk.CTkLabel(self.left_panel_tp, text="Search Phone Model:", font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(2, 0))
        self.search_entry = ctk.CTkEntry(
            self.left_panel_tp,
            textvariable=self.search_model_var,
            placeholder_text="e.g. Hot 12, 9A, Y21, Note 8...",
            height=30,
            fg_color="#0F0F12"
        )
        self.search_entry.pack(fill="x", padx=12, pady=(2, 8))
        self.search_model_var.trace_add("write", lambda *args: self._on_search_changed())

        # Models List (Scrollable)
        ctk.CTkLabel(self.left_panel_tp, text="SUPPORTED PINOUT DIAGRAMS:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748B").pack(anchor="w", padx=12, pady=(4, 2))

        self.models_scroll = ctk.CTkScrollableFrame(self.left_panel_tp, fg_color="#0E0E12", corner_radius=6)
        self.models_scroll.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        self._populate_models_list()

    def _build_center_panel(self):
        self.center_panel_tp = ctk.CTkFrame(self.body_frame, fg_color="#141418", corner_radius=8)

        # Header Info Bar
        top_bar = ctk.CTkFrame(self.center_panel_tp, fg_color="#181820", corner_radius=6, height=48)
        top_bar.pack(fill="x", padx=10, pady=(10, 6))

        self.lbl_model_title = ctk.CTkLabel(
            top_bar,
            text=f"📱 {self.current_model}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_model_title.pack(side="left", padx=14, pady=8)

        self.lbl_mode_badge = ctk.CTkLabel(
            top_bar,
            text="● BROM / BSL FORCE MODE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#34D399",
            fg_color="#064E3B",
            corner_radius=4,
            padx=10,
            pady=4
        )
        self.lbl_mode_badge.pack(side="right", padx=14, pady=8)

        # Zoom Controls Bar
        zoom_bar = ctk.CTkFrame(self.center_panel_tp, fg_color="transparent")
        zoom_bar.pack(fill="x", padx=12, pady=(0, 4))

        ctk.CTkLabel(
            zoom_bar,
            text="Motherboard Schematic Diagram (Interactive Canvas)",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(side="left")

        ctk.CTkButton(zoom_bar, text="➕ Zoom In", width=70, height=24, font=ctk.CTkFont(size=10), fg_color="#334155", command=self._zoom_in).pack(side="right", padx=3)
        ctk.CTkButton(zoom_bar, text="➖ Zoom Out", width=75, height=24, font=ctk.CTkFont(size=10), fg_color="#334155", command=self._zoom_out).pack(side="right", padx=3)
        ctk.CTkButton(zoom_bar, text="🔄 Reset", width=60, height=24, font=ctk.CTkFont(size=10), fg_color="#334155", command=self._zoom_reset).pack(side="right", padx=3)

        # Interactive Canvas Frame
        canvas_frame = ctk.CTkFrame(self.center_panel_tp, fg_color="#0A0A0D", corner_radius=6)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=4)

        self.canvas = tk.Canvas(canvas_frame, bg="#0A0A0D", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)

        # Bottom Instructions Card
        self.instr_card = ctk.CTkFrame(self.center_panel_tp, fg_color="#181820", corner_radius=6)
        self.instr_card.pack(fill="x", padx=10, pady=(6, 10))

        ctk.CTkLabel(
            self.instr_card,
            text="⚡ STEP-BY-STEP HARDWARE CONNECTION PROCEDURE:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F59E0B"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_instructions = ctk.CTkLabel(
            self.instr_card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#E2E8F0",
            justify="left",
            wraplength=700
        )
        self.lbl_instructions.pack(anchor="w", padx=12, pady=(0, 8))

        # Initial render
        self.load_model(self.current_model)

    def _populate_models_list(self):
        for widget in self.models_scroll.winfo_children():
            widget.destroy()

        for model_name in self.filtered_models:
            is_active = (model_name == self.current_model)
            btn = ctk.CTkButton(
                self.models_scroll,
                text=model_name,
                font=ctk.CTkFont(size=11, weight="bold" if is_active else "normal"),
                fg_color="#0284C7" if is_active else "#16161E",
                hover_color="#0369A1",
                anchor="w",
                height=32,
                command=lambda m=model_name: self.load_model(m)
            )
            btn.pack(fill="x", pady=2)

    def _on_brand_filter_changed(self, choice):
        self._apply_filters()

    def _on_search_changed(self):
        self._apply_filters()

    def _apply_filters(self):
        brand_filter = self.selected_brand_var.get()
        query = self.search_model_var.get().strip().lower()

        filtered = []
        for name, data in TEST_POINT_DATABASE.items():
            if brand_filter != "All Brands" and data.get("brand") != brand_filter:
                continue
            if query and (query not in name.lower() and query not in data.get("chipset", "").lower()):
                continue
            filtered.append(name)

        self.filtered_models = filtered
        self._populate_models_list()

    def load_model(self, model_name: str):
        if model_name not in TEST_POINT_DATABASE:
            return

        self.current_model = model_name
        data = TEST_POINT_DATABASE[model_name]

        self.lbl_model_title.configure(text=f"📱 {model_name} — {data.get('chipset', 'Unknown SoC')}")
        mode_text = data.get("mode", "Test Point Mode")
        self.lbl_mode_badge.configure(text=f"● {mode_text.upper()}")

        instr = data.get("instructions", "No instructions available.")
        tp_type = data.get("tp_type", "Test Point")
        diff = data.get("difficulty", "Normal")
        self.lbl_instructions.configure(text=f"Pinout Type: {tp_type} | Difficulty: {diff}\n{instr}")

        self._populate_models_list()
        self._draw_schematic(data.get("schematic", {}))

    def _draw_schematic(self, sch: dict):
        self.canvas.delete("all")
        if not sch:
            return

        scale = self.zoom_scale
        ox, oy = 40, 20  # Canvas origin

        def sc(val):
            return int(val * scale)

        # 1. Main PCB Motherboard outline
        board_col = sch.get("board_color", "#1A2238")
        self.canvas.create_rectangle(ox, oy, ox + sc(480), oy + sc(440), fill=board_col, outline="#334155", width=2)
        # Motherboard border copper screws
        for sx, sy in [(ox+15, oy+15), (ox+465, oy+15), (ox+15, oy+425), (ox+465, oy+425)]:
            self.canvas.create_oval(sx-8, sy-8, sx+8, sy+8, fill="#F59E0B", outline="#D97706")
            self.canvas.create_oval(sx-4, sy-4, sx+4, sy+4, fill="#0A0A0D", outline="")

        # 2. CPU Chip
        cx, cy, cw, ch = sch.get("cpu_pos", (200, 120, 120, 110))
        self.canvas.create_rectangle(ox + sc(cx), oy + sc(cy), ox + sc(cx+cw), oy + sc(cy+ch), fill="#27272A", outline="#71717A", width=2)
        self.canvas.create_text(ox + sc(cx + cw/2), oy + sc(cy + ch/2), text="SoC / CPU\nPROCESSOR", fill="#E4E4E7", font=("Segoe UI", int(9 * scale), "bold"), justify="center")

        # 3. eMMC / UFS Storage Chip
        mx, my, mw, mh = sch.get("emmc_pos", (200, 260, 110, 100))
        self.canvas.create_rectangle(ox + sc(mx), oy + sc(my), ox + sc(mx+mw), oy + sc(my+mh), fill="#1E293B", outline="#475569", width=2)
        self.canvas.create_text(ox + sc(mx + mw/2), oy + sc(my + mh/2), text="eMMC / UFS\nFLASH STORAGE", fill="#94A3B8", font=("Segoe UI", int(8 * scale), "bold"), justify="center")

        # 4. PMIC Power IC
        px, py, pw, ph = sch.get("pmic_pos", (80, 160, 80, 80))
        self.canvas.create_rectangle(ox + sc(px), oy + sc(py), ox + sc(px+pw), oy + sc(py+ph), fill="#3F3F46", outline="#71717A", width=1)
        self.canvas.create_text(ox + sc(px + pw/2), oy + sc(py + ph/2), text="PMIC", fill="#D4D4D8", font=("Segoe UI", int(8 * scale), "bold"))

        # 5. Battery Connector
        bx, by, bw, bh = sch.get("battery_pos", (80, 360, 110, 50))
        self.canvas.create_rectangle(ox + sc(bx), oy + sc(by), ox + sc(bx+bw), oy + sc(by+bh), fill="#18181B", outline="#EAB308", width=2)
        self.canvas.create_text(ox + sc(bx + bw/2), oy + sc(by + bh/2), text="BATTERY FPC", fill="#FDE047", font=("Segoe UI", int(8 * scale), "bold"))

        # 6. SIM Tray Socket
        sx, sy, sw, sh = sch.get("sim_pos", (350, 110, 90, 150))
        self.canvas.create_rectangle(ox + sc(sx), oy + sc(sy), ox + sc(sx+sw), oy + sc(sy+sh), fill="#334155", outline="#64748B", width=1)
        self.canvas.create_text(ox + sc(sx + sw/2), oy + sc(sy + sh/2), text="SIM / SD TRAY", fill="#CBD5E1", font=("Segoe UI", int(8 * scale)))

        # 7. Draw Test Point Pads & Trace Wires
        pads = sch.get("tp_pads", [])
        pad_coords = []
        for pad in pads:
            px_raw, py_raw = pad["pos"]
            px_draw = ox + sc(px_raw)
            py_draw = oy + sc(py_raw)
            pad_coords.append((px_draw, py_draw))

            color = pad.get("color", "#EF4444")
            # Glowing outer circle
            self.canvas.create_oval(px_draw - 10, py_draw - 10, px_draw + 10, py_draw + 10, outline=color, width=2)
            # Solid inner gold pad
            self.canvas.create_oval(px_draw - 5, py_draw - 5, px_draw + 5, py_draw + 5, fill=color, outline="#FFFFFF", width=1)

            # Label text
            self.canvas.create_text(px_draw, py_draw - 18, text=pad.get("name", "TP"), fill="#FFFFFF", font=("Segoe UI", int(9 * scale), "bold"))

        # Draw red connection jumper bridge if 2 pads exist
        if len(pad_coords) >= 2:
            p1 = pad_coords[0]
            p2 = pad_coords[1]
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#EF4444", width=3, dash=(4, 2))
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            self.canvas.create_text(mid_x + 30, mid_y, text="SHORT HERE", fill="#EF4444", font=("Segoe UI", int(8 * scale), "bold"))

    def _zoom_in(self):
        if self.zoom_scale < 1.8:
            self.zoom_scale += 0.15
            self.load_model(self.current_model)

    def _zoom_out(self):
        if self.zoom_scale > 0.6:
            self.zoom_scale -= 0.15
            self.load_model(self.current_model)

    def _zoom_reset(self):
        self.zoom_scale = 1.0
        self.load_model(self.current_model)

    def show(self):
        self.left_panel_tp.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.center_panel_tp.grid(row=0, column=1, sticky="nsew", padx=4)

    def hide(self):
        self.left_panel_tp.grid_forget()
        self.center_panel_tp.grid_forget()
