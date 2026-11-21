import customtkinter as ctk
from ui.theme import Theme

class ModuleRibbon(ctk.CTkFrame):
    """Platform Switcher Ribbon (MediaTek, Qualcomm, Unisoc, Fastboot & ADB)."""

    def __init__(self, master, on_module_changed=None):
        super().__init__(master, height=44, corner_radius=0, fg_color=Theme.BG_HEADER, border_width=1, border_color=Theme.BORDER_CARD)
        self.pack(fill="x", side="top", padx=0, pady=(0, 2))

        self.on_module_changed = on_module_changed
        self._build_ui()

    def _build_ui(self):
        # Left label
        lbl_mod = ctk.CTkLabel(
            self,
            text="❖ PLATFORM MODULE:",
            font=Theme.font_bold(size=11),
            text_color=Theme.ACCENT_CYAN
        )
        lbl_mod.pack(side="left", padx=(14, 10), pady=6)

        # Module Segmented Ribbon
        self.module_selector = ctk.CTkSegmentedButton(
            self,
            values=[
                "🛡️ SMART AUTO-HUB",
                "⚡ MEDIATEK (MTK)",
                "🐉 QUALCOMM (EDL 9008)",
                "📱 UNISOC / SPD",
                "🟡 SAMSUNG (ODIN / MTP)",
                "🔴 GOOGLE PIXEL",
                "🤖 ANDROID",
                "📌 TEST POINTS",
                "🧠 AI LOG ANALYZER",
                "🩺 PARTITION DOCTOR"
            ],
            command=self.on_module_changed,
            font=Theme.font_bold(size=11),
            selected_color=Theme.ACCENT_BLUE,
            selected_hover_color=Theme.ACCENT_BLUE_HOVER,
            unselected_color=Theme.SURFACE_INPUT,
            unselected_hover_color=Theme.SURFACE_CARD,
            text_color=Theme.TEXT_PRIMARY,
            height=32
        )
        self.module_selector.pack(side="left", padx=4, pady=6)
        self.module_selector.set("🛡️ SMART AUTO-HUB")

        # Right status capsule
        self.lbl_ribbon_status = ctk.CTkLabel(
            self,
            text="● MTK BROM / PRELOADER ENGINE ACTIVE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#34D399",
            fg_color="#064E3B",
            corner_radius=4,
            padx=10,
            pady=3
        )
        self.lbl_ribbon_status.pack(side="right", padx=16, pady=6)

    def set_status(self, text: str, fg_color: str, text_color: str):
        self.lbl_ribbon_status.configure(text=text, fg_color=fg_color, text_color=text_color)

    def select_platform(self, platform_key: str):
        mapping = {
            "smart": "🛡️ SMART AUTO-HUB",
            "hub": "🛡️ SMART AUTO-HUB",
            "autohub": "🛡️ SMART AUTO-HUB",
            "mtk": "⚡ MEDIATEK (MTK)",
            "qc": "🐉 QUALCOMM (EDL 9008)",
            "spd": "📱 UNISOC / SPD",
            "samsung": "🟡 SAMSUNG (ODIN / MTP)",
            "pixel": "🔴 GOOGLE PIXEL",
            "google": "🔴 GOOGLE PIXEL",
            "tensor": "🔴 GOOGLE PIXEL",
            "android": "🤖 ANDROID",
            "fastboot": "🤖 ANDROID",
            "adb": "🤖 ANDROID",
            "unpacker": "🤖 ANDROID",
            "extractor": "🤖 ANDROID",
            "tp": "📌 TEST POINTS",
            "analyzer": "🧠 AI LOG ANALYZER",
            "ai": "🧠 AI LOG ANALYZER",
            "doctor": "🩺 PARTITION DOCTOR",
            "partition": "🩺 PARTITION DOCTOR"
        }
        val = mapping.get(platform_key.lower())
        if val:
            self.module_selector.set(val)
