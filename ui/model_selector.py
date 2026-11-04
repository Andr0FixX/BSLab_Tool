import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional, Dict, Any, List
from core.model_repository import ModelRepository
from ui.theme import Theme
from ui.dialogs.testpoint_dialog import TestPointDialog


class SearchableModelSelector(ctk.CTkFrame):
    """
    High-Performance Searchable Brand & Model Selector Component (UnlockTool Style).
    Supports:
    1. '🌟 ALL BRANDS (Global Search)': Type any model across 11,720 models without picking a brand.
    2. Sub-millisecond instant in-memory filtering.
    3. Auto-detects Brand, Platform, and Chipset.
    4. Auto-switches the application to the matching Platform Module (MTK / Qualcomm / Unisoc / Samsung).
    5. Displays dynamic visual badge.
    """

    def __init__(
        self,
        parent,
        brand_var: tk.StringVar,
        model_var: tk.StringVar,
        controller=None,
        platform_filter: Optional[str] = None,
        on_model_selected: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        on_brand_selected: Optional[Callable[[str], None]] = None,
        accent_color: str = "#0284C7",
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.brand_var = brand_var
        self.model_var = model_var
        self.controller = controller
        self.platform_filter = platform_filter.lower() if platform_filter else None
        self.on_model_selected = on_model_selected
        self.on_brand_selected = on_brand_selected
        self.accent_color = accent_color

        self._debounce_timer = None
        self._current_search_results: List[Dict[str, Any]] = []
        self._label_to_item: Dict[str, Dict[str, Any]] = {}
        self._is_switching = False

        self._build_ui()
        self._sync_models()

    def _build_ui(self):
        # 1. BRAND SELECTION HEADER & DROPDOWN
        lbl_brand = ctk.CTkLabel(
            self,
            text="BRAND SELECTION",
            font=Theme.font_bold(size=11),
            text_color=self.accent_color
        )
        lbl_brand.pack(anchor="w", padx=2, pady=(2, 2))

        all_brands = ModelRepository.get_all_brands()
        cur_brand = self.brand_var.get()
        if not cur_brand or cur_brand not in all_brands:
            cur_brand = ModelRepository.GLOBAL_BRAND
            self.brand_var.set(cur_brand)

        self.brand_menu = ctk.CTkOptionMenu(
            self,
            values=all_brands,
            variable=self.brand_var,
            fg_color="#1E293B",
            button_color="#334155",
            button_hover_color="#475569",
            height=30,
            command=self._handle_brand_changed
        )
        self.brand_menu.pack(fill="x", padx=2, pady=(0, 6))

        # 2. MODEL SEARCH & SELECTION HEADER
        lbl_model = ctk.CTkLabel(
            self,
            text="MODEL (LIVE SEARCH)",
            font=Theme.font_bold(size=11),
            text_color=self.accent_color
        )
        lbl_model.pack(anchor="w", padx=2, pady=(2, 2))

        # Live Search Entry Box
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Type model (e.g. Redmi 12, Hot 12, A53, Y20)...",
            height=28,
            fg_color="#0F172A",
            border_color="#334155",
            font=Theme.font_ui(size=11)
        )
        self.search_entry.pack(fill="x", padx=2, pady=(0, 4))
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)

        # Model OptionMenu / Dropdown
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=["Loading..."],
            variable=self.model_var,
            fg_color="#1E293B",
            button_color="#334155",
            button_hover_color="#475569",
            height=30,
            command=self._handle_model_changed
        )
        self.model_menu.pack(fill="x", padx=2, pady=(0, 6))

        # 3. CHIPSET & PLATFORM BADGE
        self.badge_frame = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=6, border_width=1, border_color="#334155")
        self.badge_frame.pack(fill="x", padx=2, pady=(0, 6))

        self.lbl_platform_badge = ctk.CTkLabel(
            self.badge_frame,
            text="CHIP: Auto-Detect",
            font=Theme.font_bold(size=10),
            text_color="#94A3B8"
        )
        self.lbl_platform_badge.pack(side="left", padx=8, pady=3)

        self.lbl_count_badge = ctk.CTkLabel(
            self.badge_frame,
            text="",
            font=Theme.font_ui(size=9),
            text_color="#64748B"
        )
        self.lbl_count_badge.pack(side="right", padx=8, pady=3)

        # 4. PINOUT & TEST POINT SHORTCUT BUTTON
        self.btn_pinout = ctk.CTkButton(
            self,
            text="📍 View Pinout / Test Point",
            font=Theme.font_bold(size=11),
            height=28,
            fg_color="#1E293B",
            hover_color="#0284C7",
            border_width=1,
            border_color="#38BDF8",
            text_color="#38BDF8",
            command=self.open_testpoint_dialog
        )
        self.btn_pinout.pack(fill="x", padx=2, pady=(0, 6))

    def open_testpoint_dialog(self):
        """Opens interactive motherboard test point diagram for the active model."""
        try:
            brand = self.brand_var.get()
            model = self.model_var.get()
            plat = self.platform_filter
            dialog = TestPointDialog(
                master=self.winfo_toplevel(),
                brand=brand,
                model=model,
                platform=plat,
                controller=self.controller
            )
        except Exception as e:
            if self.controller and hasattr(self.controller, "logger"):
                self.controller.logger.error(f"Failed to open Test Point dialog: {e}")

    def _on_search_key_release(self, event):
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        self._debounce_timer = self.after(50, self._perform_live_search)

    def _perform_live_search(self):
        query = self.search_entry.get().strip()
        brand = self.brand_var.get()
        results = ModelRepository.search_models_fast(brand=brand, query=query, limit=50)

        # Apply platform filter if strictly requested
        if self.platform_filter and brand != ModelRepository.GLOBAL_BRAND:
            filtered = [r for r in results if r.get("platform") == self.platform_filter]
            if filtered:
                results = filtered

        self._current_search_results = results
        self._label_to_item = {}

        values = []
        for r in results:
            label = r.get("display_label") or r["label"]
            values.append(label)
            self._label_to_item[label] = r

        if not values:
            values = [f"No matching models found for '{query}'"]

        self.model_menu.configure(values=values)
        if values and values[0] != self.model_var.get():
            self.model_var.set(values[0])
            self._handle_model_changed(values[0])

        self.lbl_count_badge.configure(text=f"{len(results)} matches")

    def _sync_models(self):
        brand = self.brand_var.get()
        results = ModelRepository.search_models_fast(brand=brand, query="", limit=50)

        if self.platform_filter and brand != ModelRepository.GLOBAL_BRAND:
            filtered = [r for r in results if r.get("platform") == self.platform_filter]
            if filtered:
                results = filtered

        self._current_search_results = results
        self._label_to_item = {}

        values = []
        for r in results:
            label = r.get("display_label") or r["label"]
            values.append(label)
            self._label_to_item[label] = r

        if not values:
            values = ["Auto-Detect (Universal)"]

        self.model_menu.configure(values=values)
        if not self.model_var.get() or self.model_var.get() not in values:
            self.model_var.set(values[0])

        self.lbl_count_badge.configure(text=f"{len(results)} models")
        self._update_badge(self.model_var.get())

    def _handle_brand_changed(self, choice):
        self.search_entry.delete(0, "end")
        self._sync_models()
        cur_model = self.model_var.get()
        self._handle_model_changed(cur_model)
        if self.on_brand_selected:
            self.on_brand_selected(choice)

    def _handle_model_changed(self, choice):
        if self._is_switching:
            return

        brand = self.brand_var.get()
        matched_item = self._label_to_item.get(choice)
        details = None

        if matched_item:
            details = {
                "brand": matched_item["brand"],
                "chipset": f"{matched_item['cpu']} ({matched_item['code_name']})" if matched_item.get("code_name") else matched_item.get("cpu", ""),
                "platform": matched_item.get("platform", "qualcomm"),
                "cpu_family": matched_item.get("cpu", ""),
                "loader_file": "Auto-Select (Optimized)",
                "testpoint": "Standard EDL / BROM Testpoint or Hardware Volume Key",
                "features": ["Flash", "FRP Reset", "Factory Reset", "Read Info", "Partition Manager"]
            }
            actual_brand = matched_item["brand"]
        else:
            details = ModelRepository.get_model_details(brand, choice)
            actual_brand = details.get("brand", brand)

        self._update_badge(choice, details)

        # Trigger model selected callback
        if self.on_model_selected:
            self.on_model_selected(actual_brand, choice, details)

        # Smart Platform Auto-Switch (UnlockTool behavior)
        if self.controller and hasattr(self.controller, "switch_to_platform"):
            target_platform = (details.get("platform") or "").lower()
            if actual_brand.lower() == "samsung" and target_platform != "unisoc":
                target_platform = "samsung"

            active_module = getattr(self.controller, "active_platform_module", "")

            # Map platform to module keys
            plat_to_module = {
                "mtk": "mtk",
                "mediatek": "mtk",
                "qualcomm": "qc",
                "qc": "qc",
                "unisoc": "spd",
                "spd": "spd",
                "spreadtrum": "spd",
                "samsung": "samsung"
            }

            target_module = plat_to_module.get(target_platform)
            if target_module and active_module and target_module != active_module:
                try:
                    self._is_switching = True
                    self.controller.switch_to_platform(target_module)
                    if hasattr(self.controller, "logger"):
                        self.controller.logger.success(
                            f"⚡ [Smart Hub] Auto-Switched to {target_platform.upper()} Platform for {actual_brand} {choice}"
                        )
                finally:
                    self._is_switching = False

    def _update_badge(self, model_name: str, details: Optional[Dict[str, Any]] = None):
        if not details:
            details = ModelRepository.get_model_details(self.brand_var.get(), model_name)

        platform = (details.get("platform") or "").upper()
        cpu = details.get("cpu_family") or details.get("chipset") or ""

        if platform == "MTK" or "MEDIATEK" in platform or "HELIO" in cpu.upper():
            plat_color = "#38BDF8"  # Cyan
            plat_icon = "⚡ MTK"
        elif platform == "QUALCOMM" or "SNAPDRAGON" in cpu.upper():
            plat_color = "#F59E0B"  # Gold
            plat_icon = "🐉 QC"
        elif platform == "UNISOC" or "SPREADTRUM" in platform or "TIGER" in cpu.upper():
            plat_color = "#10B981"  # Emerald Green
            plat_icon = "📱 UNISOC"
        elif platform == "SAMSUNG" or "EXYNOS" in cpu.upper():
            plat_color = "#60A5FA"  # Blue
            plat_icon = "🟡 SAMSUNG"
        else:
            plat_color = "#94A3B8"
            plat_icon = "⚙️ Universal"

        chip_short = cpu[:20] + ".." if len(cpu) > 20 else cpu
        display_text = f"{plat_icon} {chip_short}".strip()
        self.lbl_platform_badge.configure(text=display_text, text_color=plat_color)
