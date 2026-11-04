import customtkinter as ctk
from ui.theme import Theme

class HeaderBar(ctk.CTkFrame):
    """Top Header Bar with Branding, Port Selector, Abort, and Live USB Hardware Display."""

    def __init__(self, master, on_port_selected=None, on_refresh_ports=None, on_abort=None, on_refresh_usb=None, on_open_drivers=None, on_toggle_auto_switch=None, on_toggle_sound=None, on_toggle_lang=None, on_cloud_sync=None):
        super().__init__(master, height=54, corner_radius=0, fg_color=Theme.BG_HEADER)
        self.pack(fill="x", side="top")

        self.on_port_selected = on_port_selected
        self.on_refresh_ports = on_refresh_ports
        self.on_abort = on_abort
        self.on_refresh_usb = on_refresh_usb
        self.on_open_drivers = on_open_drivers
        self.on_toggle_auto_switch = on_toggle_auto_switch
        self.on_toggle_sound = on_toggle_sound
        self.on_toggle_lang = on_toggle_lang
        self.on_cloud_sync = on_cloud_sync

        self.auto_switch_active = True
        self.sound_active = True
        self.current_lang = "en"

        self._build_ui()

    def _build_ui(self):
        # 1. Tool Branding
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(side="left", padx=16, pady=8)

        logo_lbl = ctk.CTkLabel(
            brand_frame,
            text="⚡ BS LAB TOOL PRO",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#00D2FF"
        )
        logo_lbl.pack(side="left")

        ver_lbl = ctk.CTkLabel(
            brand_frame,
            text="v2.0",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#0284C7",
            text_color="#FFFFFF",
            corner_radius=4,
            padx=6,
            pady=1
        )
        ver_lbl.pack(side="left", padx=8)

        # 2. Port Selection Controls
        port_frame = ctk.CTkFrame(self, fg_color="transparent")
        port_frame.pack(side="left", padx=20, pady=8)

        ctk.CTkLabel(port_frame, text="COM Port:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.port_menu = ctk.CTkOptionMenu(
            port_frame,
            values=["Auto-Detect / Dynamic (LibUSB)"],
            command=self.on_port_selected,
            width=210,
            height=30,
            fg_color="#2563EB"
        )
        self.port_menu.pack(side="left", padx=4)

        self.btn_refresh = ctk.CTkButton(
            port_frame,
            text="🔄 Refresh",
            width=70,
            height=30,
            fg_color="#3F3F46",
            command=self.on_refresh_ports
        )
        self.btn_refresh.pack(side="left", padx=4)

        self.btn_stop = ctk.CTkButton(
            port_frame,
            text="⏹️ Abort",
            width=65,
            height=30,
            fg_color="#DC2626",
            hover_color="#991B1B",
            command=self.on_abort
        )
        self.btn_stop.pack(side="left", padx=4)

        self.btn_drivers = ctk.CTkButton(
            port_frame,
            text="🔧 Drivers",
            width=75,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.on_open_drivers
        )
        self.btn_drivers.pack(side="left", padx=4)

        # Vertical Divider
        ctk.CTkFrame(port_frame, width=2, height=24, fg_color="#2A2A38").pack(side="left", padx=10)

        # 3. Connected USB Port Display Box
        ctk.CTkLabel(
            port_frame,
            text="Connected USB:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00D2FF"
        ).pack(side="left", padx=(2, 6))

        self.lbl_connected_usb = ctk.CTkLabel(
            port_frame,
            text="⚪ No Device Connected (Listening...)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#181822",
            text_color="#94A3B8",
            corner_radius=6,
            padx=12,
            pady=4
        )
        self.lbl_connected_usb.pack(side="left", padx=2)

        self.btn_refresh_usb = ctk.CTkButton(
            port_frame,
            text="🔄 Refresh",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=70,
            height=28,
            fg_color="#1E293B",
            hover_color="#334155",
            command=self.on_refresh_usb
        )
        self.btn_refresh_usb.pack(side="left", padx=(4, 2))

        # 4. Right Controls Group (Auto-Switch, Sound, Language, Status)
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=16, pady=8)

        self.btn_lang = ctk.CTkButton(
            right_frame,
            text="🌐 EN",
            width=58,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._on_lang_click
        )
        self.btn_lang.pack(side="right", padx=(4, 0))

        self.btn_sync = ctk.CTkButton(
            right_frame,
            text="☁️ Sync DB",
            width=76,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0369A1",
            hover_color="#0284C7",
            command=self._on_sync_click
        )
        self.btn_sync.pack(side="right", padx=(4, 0))

        self.btn_sound = ctk.CTkButton(
            right_frame,
            text="🔊",
            width=36,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._on_sound_click
        )
        self.btn_sound.pack(side="right", padx=(4, 0))

        self.btn_auto_switch = ctk.CTkButton(
            right_frame,
            text="🔄 Hub: ON",
            width=78,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#065F46",
            hover_color="#047857",
            command=self._on_auto_switch_click
        )
        self.btn_auto_switch.pack(side="right", padx=(4, 0))

        self.badge_status = ctk.CTkLabel(
            right_frame,
            text="● ENGINE READY / LIBUSB DISCOVERY",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#064E3B",
            text_color="#34D399",
            corner_radius=6,
            padx=12,
            pady=4
        )
        self.badge_status.pack(side="right", padx=(0, 6))

    def _on_lang_click(self):
        if self.on_toggle_lang:
            new_lang = self.on_toggle_lang()
            self.set_language_display(new_lang)

    def _on_sound_click(self):
        if self.on_toggle_sound:
            new_state = self.on_toggle_sound()
            self.set_sound_display(new_state)

    def _on_auto_switch_click(self):
        if self.on_toggle_auto_switch:
            new_state = self.on_toggle_auto_switch()
            self.set_auto_switch_display(new_state)

    def _on_sync_click(self):
        if self.on_cloud_sync:
            self.on_cloud_sync()

    def set_language_display(self, lang_code: str):
        self.current_lang = lang_code
        self.btn_lang.configure(text="🌐 اردو" if lang_code == "ur" else "🌐 EN")

    def set_sound_display(self, is_enabled: bool):
        self.sound_active = is_enabled
        self.btn_sound.configure(
            text="🔊" if is_enabled else "🔇",
            fg_color="#1E293B" if is_enabled else "#3F3F46"
        )

    def set_auto_switch_display(self, is_enabled: bool):
        self.auto_switch_active = is_enabled
        if is_enabled:
            self.btn_auto_switch.configure(text="🔄 Hub: ON", fg_color="#065F46", hover_color="#047857")
        else:
            self.btn_auto_switch.configure(text="🔄 Hub: OFF", fg_color="#374151", hover_color="#4B5563")

    def set_ports(self, port_list: list):
        self.port_menu.configure(values=port_list)

    def set_connected_usb(self, text: str, is_online: bool):
        if is_online:
            self.lbl_connected_usb.configure(text=text, fg_color="#064E3B", text_color="#34D399")
        else:
            self.lbl_connected_usb.configure(text=text, fg_color="#181822", text_color="#94A3B8")

    def set_badge_status(self, text: str, bg_color: str, text_color: str):
        self.badge_status.configure(text=text, fg_color=bg_color, text_color=text_color)
