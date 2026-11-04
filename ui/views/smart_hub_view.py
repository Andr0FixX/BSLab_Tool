"""
BS Lab Tool v2.0 PRO — Smart Auto-Hub (Chimera-Style Zero-Click Architecture)
Automatically detects phone hardware & model, displays real-time device visuals,
eliminates technician guesswork, locks out incompatible operations, and enables
1-click safe servicing tailored to the exact phone connected.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image

from ui.theme import Theme
from core.sound_manager import SoundManager
from core.model_database import ModelDatabase

class SmartHubView:
    """Safe, Context-Aware Device Model Identification and 1-Click Operations Studio."""

    def __init__(self, master_body, controller):
        self.body_frame = master_body
        self.controller = controller
        self.logger = controller.logger

        # State Variables
        self.is_connected = False
        self.current_mode = "NONE"
        self.current_title = "No Device Connected"
        self.current_details = {}
        self.current_profile = {}
        self.active_category_tab = "all"
        self.all_connected_devices = []
        self.selected_device_idx = 0

        # Image Cache
        self._image_cache = {}

        self._build_ui()
        self.set_idle_state()

    def _get_device_image(self, category: str):
        """Loads and caches device render image."""
        if category in self._image_cache:
            return self._image_cache[category]

        asset_map = {
            "pixel": "pixel.png",
            "samsung": "samsung.png",
            "xiaomi": "xiaomi.png",
            "oneplus": "pixel.png",
            "mediatek": "mediatek.png",
            "qualcomm": "qualcomm.png",
            "generic_phone": "generic.png",
        }
        filename = asset_map.get(category, "generic.png")
        possible_dirs = []
        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                possible_dirs.append(sys._MEIPASS)
            possible_dirs.append(os.path.dirname(sys.executable))
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        possible_dirs.append(base_dir)

        img_path = None
        for d in possible_dirs:
            p1 = os.path.join(d, "resources", "devices", filename)
            if os.path.exists(p1):
                img_path = p1
                break
            p2 = os.path.join(d, "_internal", "resources", "devices", filename)
            if os.path.exists(p2):
                img_path = p2
                break

        try:
            if img_path and os.path.exists(img_path):
                pil_img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(105, 185))
                self._image_cache[category] = ctk_img
                return ctk_img
        except Exception:
            pass
        return None

    def _build_ui(self):
        # Master container spanning left and center workspace columns
        self.container = ctk.CTkFrame(
            self.body_frame,
            fg_color=Theme.BG_PANEL,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )

        # 1. Top Panel Container (Fixed at top of container, never scrolls)
        self.top_panel = ctk.CTkFrame(self.container, fg_color="transparent")
        self.top_panel.pack(fill="x", padx=10, pady=(8, 4))

        # 1.1 Header Banner
        self.header_banner = ctk.CTkFrame(self.top_panel, fg_color="#121620", corner_radius=6, height=52)
        self.header_banner.pack(fill="x", pady=(0, 4))

        left_header = ctk.CTkFrame(self.header_banner, fg_color="transparent")
        left_header.pack(side="left", padx=12, pady=6)

        ctk.CTkLabel(
            left_header,
            text="🛡️ SMART AUTO-HUB (CHIMERA-STYLE ZERO-CLICK SAFETY)",
            font=Theme.font_bold(size=12),
            text_color="#00D2FF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_header,
            text="Autonomous Model Classifier • Live Hardware Visuals • Zero Baseband / IMEI Loss Guard",
            font=Theme.font_ui(size=10),
            text_color="#94A3B8"
        ).pack(anchor="w")

        self.lbl_status_badge = ctk.CTkLabel(
            self.header_banner,
            text="● SCANNING USB BUS...",
            font=Theme.font_bold(size=10),
            text_color="#94A3B8",
            fg_color="#1E293B",
            corner_radius=4,
            padx=12,
            pady=5
        )
        self.lbl_status_badge.pack(side="right", padx=12, pady=8)

        # 1.2. Multi-Device Selector Bar (Chimera-Style Multi-USB Support)
        self.multi_device_frame = ctk.CTkFrame(self.top_panel, fg_color="#101726", corner_radius=6, height=42)
        self.multi_device_label = ctk.CTkLabel(
            self.multi_device_frame,
            text="⚡ ACTIVE USB HUBS:",
            font=Theme.font_bold(size=10),
            text_color="#F59E0B"
        )
        self.multi_device_label.pack(side="left", padx=(12, 8), pady=6)
        self.multi_device_buttons_frame = ctk.CTkFrame(self.multi_device_frame, fg_color="transparent")
        self.multi_device_buttons_frame.pack(side="left", fill="x", expand=True, padx=4, pady=4)

        # 2. Main Scrollable Workspace
        self.scroll_area = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # 3. Hero Card (Device Canvas)
        self.hero_card = ctk.CTkFrame(
            self.scroll_area,
            fg_color=Theme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_CARD
        )
        self.hero_card.pack(fill="x", pady=(0, 8))

        # === IDLE FRAME ===
        self.idle_frame = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.lbl_idle_icon = ctk.CTkLabel(self.idle_frame, text="⚡", font=ctk.CTkFont(size=38))
        self.lbl_idle_icon.pack(pady=(16, 2))

        self.lbl_idle_title = ctk.CTkLabel(
            self.idle_frame,
            text="WAITING FOR PHONE CONNECTION",
            font=Theme.font_bold(size=15),
            text_color="#F8FAFC"
        )
        self.lbl_idle_title.pack(pady=(0, 2))

        self.lbl_idle_subtitle = ctk.CTkLabel(
            self.idle_frame,
            text="Plug any phone via USB (Normal Android ON, Fastboot / Bootloader, MTK BROM, Qualcomm EDL 9008, or Samsung Odin).\nThe Smart Hub will automatically identify the exact phone model, load its photo, and unlock verified 1-click servicing actions.",
            font=Theme.font_ui(size=11),
            text_color="#94A3B8",
            justify="center"
        )
        self.lbl_idle_subtitle.pack(padx=20, pady=(0, 16))

        # === CONNECTED FRAME (Chimera-Style Dual Column Showcase) ===
        self.connected_frame = ctk.CTkFrame(self.hero_card, fg_color="transparent")

        # Left Column: Device Image & Brand Badge
        self.left_canvas = ctk.CTkFrame(self.connected_frame, fg_color="#0A0E17", corner_radius=8, border_width=1, border_color="#1E293B", width=140)
        self.left_canvas.pack(side="left", padx=(12, 16), pady=12, fill="y")
        self.left_canvas.pack_propagate(False)

        self.lbl_device_img = ctk.CTkLabel(self.left_canvas, text="", image=None)
        self.lbl_device_img.pack(pady=(12, 6))

        self.lbl_device_brand_badge = ctk.CTkLabel(
            self.left_canvas,
            text="GOOGLE PIXEL",
            font=Theme.font_bold(size=9),
            fg_color="#0284C7",
            text_color="#FFFFFF",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.lbl_device_brand_badge.pack(pady=(0, 10))

        # Right Column: Model Specs & Passport
        self.right_passport = ctk.CTkFrame(self.connected_frame, fg_color="transparent")
        self.right_passport.pack(side="left", fill="both", expand=True, pady=8, padx=(0, 12))

        # Badges Row
        self.badges_row = ctk.CTkFrame(self.right_passport, fg_color="transparent")
        self.badges_row.pack(fill="x", pady=(0, 4))

        self.pill_connection = ctk.CTkLabel(
            self.badges_row,
            text="🟢 HARDWARE SYNCED",
            font=Theme.font_bold(size=9),
            text_color="#34D399",
            fg_color="#064E3B",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.pill_connection.pack(side="left", padx=(0, 6))

        self.pill_mode = ctk.CTkLabel(
            self.badges_row,
            text="⚡ FASTBOOT BOOTLOADER",
            font=Theme.font_bold(size=9),
            text_color="#38BDF8",
            fg_color="#0C4A6E",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.pill_mode.pack(side="left", padx=(0, 6))

        self.pill_lock_state = ctk.CTkLabel(
            self.badges_row,
            text="🔓 BOOTLOADER UNLOCKED",
            font=Theme.font_bold(size=9),
            text_color="#FDE68A",
            fg_color="#78350F",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.pill_lock_state.pack(side="left", padx=(0, 6))

        self.pill_imei_guard = ctk.CTkLabel(
            self.badges_row,
            text="🛡️ NVRAM / IMEI SHIELD ON",
            font=Theme.font_bold(size=9),
            text_color="#A7F3D0",
            fg_color="#065F46",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.pill_imei_guard.pack(side="left")

        # Model Title
        self.lbl_model_title = ctk.CTkLabel(
            self.right_passport,
            text="Google Pixel 4a (5G)",
            font=Theme.font_bold(size=18),
            text_color="#FFFFFF"
        )
        self.lbl_model_title.pack(anchor="w", pady=(2, 0))

        # Hardware Codename & Serial Row
        self.lbl_model_subtitle = ctk.CTkLabel(
            self.right_passport,
            text="Codename: bramble • Serial: 0A131JECB1 • Port: USB High-Speed",
            font=Theme.font_ui(size=10),
            text_color="#94A3B8"
        )
        self.lbl_model_subtitle.pack(anchor="w", pady=(0, 6))

        # Specs Matrix (4-card mini grid)
        self.matrix_frame = ctk.CTkFrame(self.right_passport, fg_color="#0B101B", corner_radius=6, border_width=1, border_color="#1E293B")
        self.matrix_frame.pack(fill="x", pady=(0, 8))

        row1 = ctk.CTkFrame(self.matrix_frame, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(6, 2))
        self.lbl_spec_soc = ctk.CTkLabel(row1, text="⚡ SoC: Snapdragon 765G (SM7250)", font=Theme.font_ui(size=10), text_color="#38BDF8")
        self.lbl_spec_soc.pack(side="left")
        self.lbl_spec_arch = ctk.CTkLabel(row1, text="Architecture: 64-bit ARM v8-A (A/B Dynamic)", font=Theme.font_ui(size=10), text_color="#94A3B8")
        self.lbl_spec_arch.pack(side="right")

        row2 = ctk.CTkFrame(self.matrix_frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(2, 6))
        self.lbl_spec_security = ctk.CTkLabel(row2, text="🔒 Security: Factory FRP Active • Verified Boot", font=Theme.font_ui(size=10), text_color="#F59E0B")
        self.lbl_spec_security.pack(side="left")
        self.lbl_spec_safety = ctk.CTkLabel(row2, text="Safety Guard: 0% Dead Boot Risk Enforced", font=Theme.font_ui(size=10), text_color="#34D399")
        self.lbl_spec_safety.pack(side="right")

        # Action Quick Links
        self.quick_links_row = ctk.CTkFrame(self.right_passport, fg_color="transparent")
        self.quick_links_row.pack(fill="x")

        self.btn_copy_report = ctk.CTkButton(
            self.quick_links_row,
            text="📋 Copy Device Passport",
            font=Theme.font_bold(size=10),
            height=28,
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._copy_device_report
        )
        self.btn_copy_report.pack(side="left", padx=(0, 8))

        self.btn_rescan = ctk.CTkButton(
            self.quick_links_row,
            text="🔄 Re-Scan Device State",
            font=Theme.font_bold(size=10),
            height=28,
            fg_color="#0F2942",
            hover_color="#1B4974",
            text_color="#38BDF8",
            border_width=1,
            border_color="#0284C7",
            command=self._rescan_hardware
        )
        self.btn_rescan.pack(side="left")

        # 4. Action Section Header with Chimera Category Tabs
        self.action_header_frame = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.action_header_frame.pack(fill="x", pady=(8, 4))

        self.lbl_actions_heading = ctk.CTkLabel(
            self.action_header_frame,
            text="⚡ CHIMERA-STYLE VERIFIED 1-CLICK OPERATIONS:",
            font=Theme.font_bold(size=12),
            text_color="#F59E0B"
        )
        self.lbl_actions_heading.pack(side="left")

        self.lbl_action_badge = ctk.CTkLabel(
            self.action_header_frame,
            text="🛡️ CHIPSET ENGINE LOCKED TO CONNECTED MODEL",
            font=Theme.font_bold(size=10),
            text_color="#34D399"
        )
        self.lbl_action_badge.pack(side="right")

        # 4.5. Chimera Category Segmented Filter Ribbon
        self.category_bar_frame = ctk.CTkFrame(self.scroll_area, fg_color="#0E131F", corner_radius=6, height=36)
        self.category_bar_frame.pack(fill="x", pady=(2, 8))

        self.category_selector = ctk.CTkSegmentedButton(
            self.category_bar_frame,
            values=[
                "🌟 ALL SERVICES",
                "🔓 UNLOCK & FRP",
                "⚡ FLASH & DUMP",
                "💾 BACKUP & EFS",
                "🔄 REBOOT & POWER"
            ],
            command=self._on_category_changed,
            font=Theme.font_bold(size=11),
            selected_color="#0284C7",
            selected_hover_color="#0369A1",
            unselected_color="#182030",
            unselected_hover_color="#243048",
            text_color="#F8FAFC",
            height=32
        )
        self.category_selector.pack(fill="x", padx=4, pady=4)
        self.category_selector.set("🌟 ALL SERVICES")

        # 5. Dynamic 2-Column Action Grid
        self.actions_grid = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.actions_grid.pack(fill="x", pady=(0, 10))
        self.actions_grid.grid_columnconfigure(0, weight=1)
        self.actions_grid.grid_columnconfigure(1, weight=1)

        # 6. Guidelines Card
        self.guidelines_card = ctk.CTkFrame(self.scroll_area, fg_color="#101522", corner_radius=8, border_width=1, border_color="#1E293B")
        self.guidelines_card.pack(fill="x", pady=(4, 6))

        ctk.CTkLabel(
            self.guidelines_card,
            text="💡 TECHNICIAN CONNECTION GUIDE & PINOUTS:",
            font=Theme.font_bold(size=11),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        guide_text = (
            "• Google Pixel / Android Fastboot: Hold (Power + Vol-) until bootloader screen appears.\n"
            "• MediaTek (BROM Mode): Power OFF -> Hold (Vol+ and Vol-) OR short Test Point to GND -> Insert Type-C cable.\n"
            "• Qualcomm (EDL 9008): Disconnect battery -> Short 2 Gold EDL Pads with tweezers -> Insert USB cable.\n"
            "• Samsung (Download Mode): Hold (Vol- and Vol+) -> Insert USB cable -> Press Vol+ to enter Odin Mode.\n"
            "• Unisoc / SPRD (BSL Mode): Hold Vol- -> Connect USB cable until SPRD U2S Diag port appears."
        )
        ctk.CTkLabel(
            self.guidelines_card,
            text=guide_text,
            font=Theme.font_ui(size=10),
            text_color="#94A3B8",
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))

    def set_idle_state(self):
        """Resets Hub to waiting state when no phone is plugged in."""
        self.is_connected = False
        self.current_mode = "NONE"
        self.current_title = "NO PHONE CONNECTED (WAITING FOR USB)"
        self.current_details = {}
        self.current_profile = {}
        self.all_connected_devices = []

        self.lbl_status_badge.configure(
            text="● WAITING FOR USB...",
            text_color="#94A3B8",
            fg_color="#1E293B"
        )

        self.multi_device_frame.pack_forget()
        self.connected_frame.pack_forget()
        self.idle_frame.pack(fill="x")

        # Clear actions
        for widget in self.actions_grid.winfo_children():
            widget.destroy()

        empty_box = ctk.CTkFrame(self.actions_grid, fg_color="#121622", corner_radius=6)
        empty_box.pack(fill="x", pady=6)
        ctk.CTkLabel(
            empty_box,
            text="Connect any smartphone via USB to automatically identify model and unlock 1-click servicing actions.",
            font=Theme.font_ui(size=11),
            text_color="#64748B"
        ).pack(pady=22)

    def _update_multi_device_bar(self):
        """Renders interactive multi-device switcher pills when phone(s) are connected."""
        for w in self.multi_device_buttons_frame.winfo_children():
            w.destroy()

        if len(self.all_connected_devices) >= 1:
            self.multi_device_frame.pack(fill="x", pady=(2, 4))
            curr_serial = self.current_details.get("serial")
            curr_port = self.current_details.get("port")

            for idx, dev in enumerate(self.all_connected_devices):
                raw_text = dev.get("text", f"Device {idx+1}")
                clean_name = raw_text.replace("🟢 ", "").replace("🟡 ", "").replace("⚪ ", "")
                dev_serial = dev.get("details", {}).get("serial")
                dev_port = dev.get("details", {}).get("port")

                is_active = False
                if dev_serial and curr_serial:
                    is_active = (dev_serial == curr_serial)
                elif dev_port and curr_port:
                    is_active = (dev_port == curr_port)
                else:
                    is_active = (idx == self.selected_device_idx)

                fg = "#064E3B" if is_active else "#182236"
                txt_color = "#34D399" if is_active else "#94A3B8"
                border = "#10B981" if is_active else "#334155"
                prefix = "● ACTIVE TARGET: " if is_active else "📱 Switch to "

                btn = ctk.CTkButton(
                    self.multi_device_buttons_frame,
                    text=f"{prefix}{clean_name[:36]}",
                    font=Theme.font_bold(size=10),
                    height=28,
                    fg_color=fg,
                    text_color=txt_color,
                    border_width=2 if is_active else 1,
                    border_color=border,
                    hover_color="#065F46" if is_active else "#243350",
                    command=lambda d=dev, i=idx: self._select_active_device(d, i)
                )
                btn.pack(side="left", padx=4)
        else:
            self.multi_device_frame.pack_forget()

    def _select_active_device(self, dev: dict, idx: int):
        self.selected_device_idx = idx
        port = dev.get("details", {}).get("port")
        serial = dev.get("details", {}).get("serial")
        if hasattr(self.controller, "selected_port"):
            self.controller.selected_port = port
        if hasattr(self.controller, "selected_serial"):
            self.controller.selected_serial = serial
        if hasattr(self.controller, "header_bar"):
            self.controller.header_bar.set_connected_usb(dev.get("text", "Device"), True)
        if hasattr(self.controller, "status_bar"):
            soc = dev.get("details", {}).get("soc") or dev.get("details", {}).get("profile", {}).get("soc", "")
            if soc:
                self.controller.status_bar.set_chipset_status(f"⚡ SoC: {soc}")
        self.logger.info(f"[Multi-Device Switch] Active Target: {dev.get('text', 'Device')} (Serial: {serial})")
        self.on_device_state_changed(True, dev.get("mode", "NONE"), dev.get("text", ""), dev.get("details", {}), self.all_connected_devices)

    def on_device_state_changed(self, is_online: bool, mode: str, text: str, details: dict, all_devices: list = None):
        """Called automatically by device detector when hardware state changes."""
        if not is_online:
            self.set_idle_state()
            return

        self.is_connected = True
        self.current_mode = mode.upper()
        self.current_details = details

        if all_devices is not None:
            self.all_connected_devices = all_devices
        self._update_multi_device_bar()

        # 1. Resolve Profile from ModelDatabase
        profile = details.get("profile")
        if not profile:
            identifier = details.get("product") or details.get("model") or details.get("desc") or text
            profile = ModelDatabase.resolve(identifier, mode=self.current_mode, details=details)
        self.current_profile = profile

        # 2. Update Header Status Badge
        badge_colors = {
            "MTK": ("#064E3B", "#34D399", "● MTK BROM DETECTED"),
            "QUALCOMM": ("#78350F", "#FDE68A", "● QUALCOMM 9008 DETECTED"),
            "SPD": ("#312E81", "#A5B4FC", "● UNISOC SPRD DETECTED"),
            "SAMSUNG": ("#1E3A8A", "#60A5FA", "● SAMSUNG ODIN DETECTED"),
            "FASTBOOT": ("#0C4A6E", "#38BDF8", "● ANDROID FASTBOOT DETECTED"),
            "ADB": ("#064E3B", "#34D399", "● ANDROID ADB DETECTED")
        }
        bg_col, text_col, badge_lbl = badge_colors.get(self.current_mode, ("#1E293B", "#38BDF8", f"● {self.current_mode} DETECTED"))
        self.lbl_status_badge.configure(text=badge_lbl, fg_color=bg_col, text_color=text_col)

        # 3. Swap Idle Frame with Connected Frame
        self.idle_frame.pack_forget()
        self.connected_frame.pack(fill="x")

        # 4. Update Device Image Render
        category = profile.get("category", "generic_phone")
        img = self._get_device_image(category)
        if img:
            self.lbl_device_img.configure(image=img, text="")
        else:
            icons = {"pixel": "📱", "samsung": "📱", "xiaomi": "📱", "mediatek": "⚡", "qualcomm": "🐉"}
            self.lbl_device_img.configure(image=None, text=icons.get(category, "📱"), font=ctk.CTkFont(size=48))

        brand_badge_text = (profile.get("brand") or profile.get("family") or "MOBILE").upper()
        self.lbl_device_brand_badge.configure(text=brand_badge_text)

        # 5. Update Model Title & Passport
        model_name = profile.get("name") or text
        self.lbl_model_title.configure(text=model_name)

        serial = details.get("serial") or details.get("port") or "USB"
        codename = profile.get("codename") or details.get("product") or "standard"
        port_name = details.get("port") or "Platform Interface"
        self.lbl_model_subtitle.configure(
            text=f"Codename: {codename} • Identifier: {serial} • Port: {port_name}"
        )

        # 6. Update Badges Row
        self.pill_mode.configure(text=f"⚡ {self.current_mode} MODE")
        unlocked = str(details.get("unlocked", "")).lower()
        if unlocked in ("yes", "true", "unlocked"):
            self.pill_lock_state.configure(text="🔓 BOOTLOADER UNLOCKED", fg_color="#065F46", text_color="#A7F3D0")
        elif unlocked in ("no", "false", "locked"):
            self.pill_lock_state.configure(text="🔒 BOOTLOADER LOCKED", fg_color="#7F1D1D", text_color="#FECACA")
        else:
            self.pill_lock_state.configure(text="🛡️ OEM LOCK DETECTED", fg_color="#78350F", text_color="#FDE68A")

        # 7. Update Specs Matrix
        soc_name = profile.get("soc", "Dynamic Mobile Processor")
        self.lbl_spec_soc.configure(text=f"⚡ SoC: {soc_name}")
        family = profile.get("family", "Smart Servicing Target")
        self.lbl_spec_arch.configure(text=f"Platform: {family}")

        # 8. Populate Contextual Safe Actions
        self._populate_mode_actions(self.current_mode)

    def _copy_device_report(self):
        p = self.current_profile
        d = self.current_details
        report = (
            f"=== BS LAB TOOL PRO - DEVICE PASSPORT ===\n"
            f"Model: {p.get('name', 'Unknown')}\n"
            f"Brand: {p.get('brand', 'Unknown')}\n"
            f"SoC: {p.get('soc', 'Unknown')}\n"
            f"Codename: {p.get('codename', 'Unknown')}\n"
            f"Mode: {self.current_mode}\n"
            f"Identifier / Serial: {d.get('serial') or d.get('port')}\n"
            f"Unlock State: {d.get('unlocked', 'N/A')}\n"
            f"========================================"
        )
        self.body_frame.clipboard_clear()
        self.body_frame.clipboard_append(report)
        self.logger.log("[+] Device Passport copied to clipboard.")

    def _rescan_hardware(self):
        """Triggers hardware port re-scan from Smart Hub."""
        if self.controller and hasattr(self.controller, "_refresh_connected_usb"):
            self.controller._refresh_connected_usb()

    def _on_category_changed(self, choice: str):
        """Filters active operations by Chimera category."""
        mapping = {
            "🌟 ALL SERVICES": "all",
            "🔓 UNLOCK & FRP": "unlock",
            "⚡ FLASH & DUMP": "flash",
            "💾 BACKUP & EFS": "backup",
            "🔄 REBOOT & POWER": "reboot"
        }
        self.active_category_tab = mapping.get(choice, "all")
        if self.is_connected and self.current_mode:
            self._populate_mode_actions(self.current_mode)

    def _populate_mode_actions(self, mode: str):
        for widget in self.actions_grid.winfo_children():
            widget.destroy()

        all_actions = self._get_actions_for_mode(mode)
        if not all_actions:
            return

        # Category Filter
        if self.active_category_tab != "all":
            actions = [act for act in all_actions if act.get("category") == self.active_category_tab or act.get("category") == "all"]
        else:
            actions = all_actions

        if not actions:
            empty_lbl = ctk.CTkLabel(
                self.actions_grid,
                text=f"No operations found in this category for {mode} mode.",
                font=Theme.font_ui(size=11),
                text_color="#64748B"
            )
            empty_lbl.grid(row=0, column=0, columnspan=2, pady=30)
            return

        # 2-Column Responsive Card Grid (Authentic Chimera Architecture)
        for idx, act in enumerate(actions):
            r = idx // 2
            c = idx % 2

            accent_color = act.get("color", "#0284C7")
            card = ctk.CTkFrame(
                self.actions_grid,
                fg_color="#101726",
                corner_radius=8,
                border_width=1,
                border_color="#1E2B45"
            )
            card.grid(row=r, column=c, padx=6, pady=5, sticky="nsew")

            # Top Row: Icon + Title + Status Badge
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 4))

            icon_lbl = ctk.CTkLabel(top_row, text=act.get("icon", "⚡"), font=ctk.CTkFont(size=18))
            icon_lbl.pack(side="left", padx=(0, 6))

            title_lbl = ctk.CTkLabel(top_row, text=act["title"], font=Theme.font_bold(size=11), text_color="#F8FAFC")
            title_lbl.pack(side="left", anchor="w")

            badge_text = act.get("badge", "VERIFIED")
            badge_color = "#34D399" if ("SAFE" in badge_text or "1-CLICK" in badge_text) else ("#F59E0B" if "REPAIR" in badge_text else "#38BDF8")
            badge_bg = "#064E3B" if ("SAFE" in badge_text or "1-CLICK" in badge_text) else ("#78350F" if "REPAIR" in badge_text else "#0C4A6E")
            badge_lbl = ctk.CTkLabel(
                top_row,
                text=badge_text,
                font=Theme.font_bold(size=8),
                text_color=badge_color,
                fg_color=badge_bg,
                corner_radius=4,
                padx=6,
                pady=2
            )
            badge_lbl.pack(side="right")

            # Description
            desc_lbl = ctk.CTkLabel(
                card,
                text=act["desc"],
                font=Theme.font_ui(size=10),
                text_color="#94A3B8",
                justify="left",
                wraplength=340
            )
            desc_lbl.pack(fill="x", padx=14, pady=(2, 8), anchor="w")

            # Bold Action Button
            btn = ctk.CTkButton(
                card,
                text=act.get("btn_text", "⚡ Execute Job"),
                font=Theme.font_bold(size=11),
                height=32,
                fg_color=accent_color,
                hover_color=act.get("hover", "#0369A1"),
                command=act["cmd"]
            )
            btn.pack(fill="x", padx=12, pady=(0, 10))

    def _get_actions_for_mode(self, mode: str):
        c = self.controller
        if mode == "MTK":
            return [
                {
                    "icon": "🟢",
                    "title": "Reset FRP Lock (BROM Auto)",
                    "desc": "Safely wipes Google FRP token with automatic NVRAM security backup.",
                    "btn_text": "🔓 Reset FRP (BROM Auto)",
                    "category": "unlock",
                    "badge": "1-CLICK SAFE",
                    "color": "#059669", "hover": "#047857",
                    "cmd": c.op_reset_frp
                },
                {
                    "icon": "🧹",
                    "title": "Safe Factory Reset (Encryption Guard)",
                    "desc": "Wipes lock screen password & userdata without damaging baseband or IMEI.",
                    "btn_text": "🧹 Wipe Data (Safe)",
                    "category": "unlock",
                    "badge": "ZERO-RISK",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.op_factory_reset
                },
                {
                    "icon": "⚡",
                    "title": "20-Second Fast Unbrick (Bootloader)",
                    "desc": "Flashes essential bootloader partitions to revive dead/hung devices instantly.",
                    "btn_text": "⚡ Fast Unbrick (Bootloader)",
                    "category": "flash",
                    "badge": "20-SEC BOOT",
                    "color": "#0EA5E9", "hover": "#0284C7",
                    "cmd": lambda: self._switch_and_run("mtk", c.mtk_view._select_bootloader_only)
                },
                {
                    "icon": "🔓",
                    "title": "Instant Bootloader Unlock",
                    "desc": "Patches seccfg security configuration to allow custom recovery/root.",
                    "btn_text": "🔓 Instant Bootloader Unlock",
                    "category": "unlock",
                    "badge": "PERMANENT",
                    "color": "#D97706", "hover": "#B45309",
                    "cmd": c.op_unlock_bootloader
                },
                {
                    "icon": "🛡️",
                    "title": "Backup Radio & NVRAM Partitions",
                    "desc": "Dumps nvram, nvdata, nvcfg, protect1/2 calibration into safe folder.",
                    "btn_text": "💾 Backup NVRAM / Radio",
                    "category": "backup",
                    "badge": "IMEI GUARD",
                    "color": "#4F46E5", "hover": "#4338CA",
                    "cmd": c.meta_backup_nvram
                },
                {
                    "icon": "📋",
                    "title": "Read Live GPT Partition Table",
                    "desc": "Inspects storage partition layout directly from phone flash memory.",
                    "btn_text": "📋 Read Live GPT Table",
                    "category": "flash",
                    "badge": "STORAGE MAP",
                    "color": "#334155", "hover": "#475569",
                    "cmd": c.read_live_gpt
                },
                {
                    "icon": "🔄",
                    "title": "Normal System Reboot",
                    "desc": "Safely restarts phone from BROM/Preloader into normal Android OS.",
                    "btn_text": "🔄 Reboot to Normal OS",
                    "category": "reboot",
                    "badge": "SYSTEM REBOOT",
                    "color": "#475569", "hover": "#334155",
                    "cmd": c.op_reboot_device
                }
            ]
        elif mode == "QUALCOMM":
            return [
                {
                    "icon": "⚡",
                    "title": "1-Click Full Firmware Dump (EDL 9008)",
                    "desc": "Autonomous bit-by-bit raw partition dump (boot, modem, carrier, etc.) to PC.",
                    "btn_text": "⚡ 1-Click Firmware Dump",
                    "category": "flash",
                    "badge": "GPT AUTO-DUMP",
                    "color": "#D97706", "hover": "#B45309",
                    "cmd": c.qc_dump_full_firmware
                },
                {
                    "icon": "🟢",
                    "title": "Reset FRP Lock (EDL 9008)",
                    "desc": "Wipes FRP partition with automatic modem / EFS security backup.",
                    "btn_text": "🔓 Reset FRP Lock (EDL)",
                    "category": "unlock",
                    "badge": "1-CLICK SAFE",
                    "color": "#059669", "hover": "#047857",
                    "cmd": c.qc_reset_frp
                },
                {
                    "icon": "🧹",
                    "title": "Factory Reset Userdata (EDL Safe)",
                    "desc": "Wipes userdata partition without touching modemst1, modemst2, or fsg.",
                    "btn_text": "🧹 Factory Reset Userdata",
                    "category": "unlock",
                    "badge": "SCREEN UNLOCK",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.qc_factory_reset
                },
                {
                    "icon": "🛡️",
                    "title": "Backup Baseband Security (modemst1/2, fsg)",
                    "desc": "Extracts radio calibration data into timestamped security backup.",
                    "btn_text": "💾 Backup EFS & NV (Modem)",
                    "category": "backup",
                    "badge": "RADIO SECURITY",
                    "color": "#4F46E5", "hover": "#4338CA",
                    "cmd": c.qc_backup_efs
                },
                {
                    "icon": "📋",
                    "title": "Read Full GPT Storage Map",
                    "desc": "Queries partition header table directly over Sahara/Firehose protocol.",
                    "btn_text": "📋 Read Full GPT Storage Map",
                    "category": "flash",
                    "badge": "STORAGE MAP",
                    "color": "#334155", "hover": "#475569",
                    "cmd": c.qc_read_info
                },
                {
                    "icon": "🔄",
                    "title": "Reboot Qualcomm to Normal OS",
                    "desc": "Sends restart command to Firehose loader to power up phone.",
                    "btn_text": "🔄 Reboot Qualcomm to OS",
                    "category": "reboot",
                    "badge": "NORMAL BOOT",
                    "color": "#475569", "hover": "#334155",
                    "cmd": c.qc_reboot
                }
            ]
        elif mode == "HUAWEI":
            return [
                {
                    "icon": "⚡",
                    "title": "Boot Kirin Rescue Mode (COM 1.0)",
                    "desc": "Injects Kirin xloader & fastboot rescue loader via USB COM 1.0 test point.",
                    "btn_text": "⚡ Boot Kirin Rescue Mode",
                    "category": "flash",
                    "badge": "COM 1.0 RESCUE",
                    "color": "#D97706", "hover": "#B45309",
                    "cmd": c.huawei_boot_rescue
                },
                {
                    "icon": "🔓",
                    "title": "Reset FRP Lock (HiSilicon Kirin)",
                    "desc": "Erases FRP partition token in Kirin Fastboot Rescue Mode.",
                    "btn_text": "🔓 Reset FRP (HiSilicon)",
                    "category": "unlock",
                    "badge": "1-CLICK",
                    "color": "#059669", "hover": "#047857",
                    "cmd": c.huawei_reset_frp
                },
                {
                    "icon": "🛡️",
                    "title": "Remove Huawei ID (Account Bypass)",
                    "desc": "Safely wipes oeminfo account credentials block.",
                    "btn_text": "🛡️ Remove Huawei ID",
                    "category": "unlock",
                    "badge": "ACCOUNT WIPE",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.huawei_remove_id
                },
                {
                    "icon": "📱",
                    "title": "Read Device Chipset & Info",
                    "desc": "Reads Kirin SoC model, board ID, and firmware display version.",
                    "btn_text": "📱 Read Chipset Specs",
                    "category": "all",
                    "badge": "DIAGNOSTIC",
                    "color": "#4F46E5", "hover": "#4338CA",
                    "cmd": c.huawei_read_info
                },
                {
                    "icon": "🔄",
                    "title": "Normal System Reboot",
                    "desc": "Restarts Huawei phone from COM 1.0 / Rescue into normal OS.",
                    "btn_text": "🔄 Reboot Huawei to OS",
                    "category": "reboot",
                    "badge": "NORMAL BOOT",
                    "color": "#475569", "hover": "#334155",
                    "cmd": c.huawei_reboot
                }
            ]
        elif mode == "SAMSUNG":
            return [
                {
                    "icon": "⚡",
                    "title": "Launch 4-File Odin Flasher",
                    "desc": "Transfers BL, AP, CP, CSC, PIT tar.md5 firmware over genuine LOKE protocol.",
                    "btn_text": "⚡ 4-File Odin Flasher",
                    "category": "flash",
                    "badge": "LOKE PROTOCOL",
                    "color": "#059669", "hover": "#047857",
                    "cmd": lambda: self._switch_and_run("samsung", None)
                },
                {
                    "icon": "📋",
                    "title": "Read Samsung PIT Partition Map",
                    "desc": "Extracts exact partition structure from Samsung Odin interface.",
                    "btn_text": "📋 Extract PIT Partition Map",
                    "category": "flash",
                    "badge": "PIT EXTRACT",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.samsung_view._load_pit_file
                },
                {
                    "icon": "🚨",
                    "title": "Fix Soft-Brick / Odin Loop",
                    "desc": "Fixes 'An error has occurred while updating the device software'.",
                    "btn_text": "🚨 Fix Soft-Brick / Loop",
                    "category": "flash",
                    "badge": "ODIN LOOP FIX",
                    "color": "#D97706", "hover": "#B45309",
                    "cmd": c.samsung_view._soft_reset
                },
                {
                    "icon": "🔄",
                    "title": "Exit Download Mode / Reboot",
                    "desc": "Restarts Samsung phone from Odin mode to normal boot.",
                    "btn_text": "🔄 Exit Download / Reboot",
                    "category": "reboot",
                    "badge": "EXIT ODIN",
                    "color": "#475569", "hover": "#334155",
                    "cmd": c.samsung_view._reboot_system
                }
            ]
        elif mode == "SPD":
            return [
                {
                    "icon": "🟢",
                    "title": "Reset FRP Lock (Unisoc Diag/BSL)",
                    "desc": "Wipes FRP partition with automatic PRODNV calibration backup.",
                    "btn_text": "🔓 Reset FRP (Diag/BSL)",
                    "category": "unlock",
                    "badge": "1-CLICK SAFE",
                    "color": "#059669", "hover": "#047857",
                    "cmd": c.spd_reset_frp
                },
                {
                    "icon": "🧹",
                    "title": "Safe Factory Reset",
                    "desc": "Cleans userdata partition safely on Unisoc Tiger/SC chips.",
                    "btn_text": "🧹 Safe Factory Reset",
                    "category": "unlock",
                    "badge": "DATA WIPE",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.spd_factory_reset
                },
                {
                    "icon": "🛡️",
                    "title": "Backup PRODNV & RF Calibration",
                    "desc": "Dumps prodnv, fixnv, and runtimenv partitions to hard drive.",
                    "btn_text": "💾 Backup PRODNV & RF",
                    "category": "backup",
                    "badge": "RF CALIBRATION",
                    "color": "#4F46E5", "hover": "#4338CA",
                    "cmd": c.spd_backup_nv
                },
                {
                    "icon": "🔄",
                    "title": "Reboot Phone to Normal",
                    "desc": "Sends restart command to Unisoc baseband.",
                    "btn_text": "🔄 Reboot Phone to Normal",
                    "category": "reboot",
                    "badge": "NORMAL BOOT",
                    "color": "#475569", "hover": "#334155",
                    "cmd": c.spd_reboot
                }
            ]
        elif mode == "FASTBOOT":
            return [
                {
                    "icon": "📱",
                    "title": "Read Full Hardware Specs & Lock State",
                    "desc": "Queries getvar all, secure boot, unlock status, active slot, and partition variables.",
                    "btn_text": "📱 Check Hardware Specs",
                    "category": "all",
                    "badge": "HARDWARE VARS",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.fastboot_view._fb_check_device
                },
                {
                    "icon": "🔓",
                    "title": "1-Click Bootloader Unlock",
                    "desc": "Executes standard fastboot flashing unlock / oem unlock command safely.",
                    "btn_text": "🔓 Unlock Bootloader (Fastboot)",
                    "category": "unlock",
                    "badge": "1-CLICK",
                    "color": "#D97706", "hover": "#B45309",
                    "cmd": c.fastboot_view._fb_unlock_bootloader
                },
                {
                    "icon": "🧹",
                    "title": "1-Click FRP & Userdata Wipe",
                    "desc": "Safely erases frp config token and clears userdata/cache partitions.",
                    "btn_text": "🧹 Erase FRP Token",
                    "category": "unlock",
                    "badge": "SAFE WIPE",
                    "color": "#059669", "hover": "#047857",
                    "cmd": c.fastboot_view._fb_erase_frp
                },
                {
                    "icon": "🔀",
                    "title": "Toggle Active Slot (Slot A / Slot B)",
                    "desc": "Switches boot slot between A and B to fix bootloops after OTA updates.",
                    "btn_text": "🔀 Switch Active Slot (A/B)",
                    "category": "flash",
                    "badge": "A/B RECOVERY",
                    "color": "#0EA5E9", "hover": "#0284C7",
                    "cmd": lambda: self._switch_and_run("fastboot", None)
                },
                {
                    "icon": "🔄",
                    "title": "Reboot to Qualcomm EDL 9008 Mode",
                    "desc": "Commands bootloader to jump directly into Qualcomm Emergency Download Mode.",
                    "btn_text": "🐉 Jump to Qualcomm EDL 9008",
                    "category": "reboot",
                    "badge": "QUALCOMM EDL",
                    "color": "#4F46E5", "hover": "#4338CA",
                    "cmd": c.fastboot_view._fb_reboot_edl
                },
                {
                    "icon": "⚡",
                    "title": "Reboot to Recovery / Fastbootd",
                    "desc": "Reboots phone into userspace fastbootd or Stock/TWRP Recovery.",
                    "btn_text": "⚡ Reboot Recovery / Fastbootd",
                    "category": "reboot",
                    "badge": "RECOVERY",
                    "color": "#2563EB", "hover": "#1D4ED8",
                    "cmd": c.fastboot_view._fb_reboot_recovery
                },
                {
                    "icon": "🔄",
                    "title": "Normal System Reboot",
                    "desc": "Restarts device out of bootloader into normal Android OS.",
                    "btn_text": "🔄 Normal System Reboot",
                    "category": "reboot",
                    "badge": "NORMAL BOOT",
                    "color": "#475569", "hover": "#334155",
                    "cmd": c.fastboot_view._fb_reboot
                }
            ]
        elif mode == "ADB":
            return [
                {
                    "icon": "📱",
                    "title": "Read Device Model & System Specs",
                    "desc": "Extracts build properties, Android version, patch level, battery status, and IMEI.",
                    "btn_text": "📱 Read Full Device Specs",
                    "category": "all",
                    "badge": "LIVE DIAGNOSTICS",
                    "color": "#0284C7", "hover": "#0369A1",
                    "cmd": c.fastboot_view._adb_read_info
                },
                {
                    "icon": "🟢",
                    "title": "Reset FRP Lock (Setup Wizard Bypass)",
                    "desc": "Cleans persistent Google setup wizard tokens and unlocks home screen.",
                    "btn_text": "🔓 Bypass FRP (1-Click)",
                    "category": "unlock",
                    "badge": "1-CLICK WIZARD",
                    "color": "#059669", "hover": "#047857",
                    "cmd": c.fastboot_view._adb_reset_frp
                },
                {
                    "icon": "🔄",
                    "title": "Reboot to Fastboot / Bootloader",
                    "desc": "Reboots phone directly into Fastboot interface.",
                    "btn_text": "⚡ Jump to Fastboot Mode",
                    "category": "reboot",
                    "badge": "FASTBOOT",
                    "color": "#0EA5E9", "hover": "#0284C7",
                    "cmd": lambda: c.fastboot_view._reboot_device_mode("bootloader")
                },
                {
                    "icon": "🔄",
                    "title": "Reboot to Recovery Mode",
                    "desc": "Reboots device into Recovery menu for hard reset or update.",
                    "btn_text": "🛡️ Jump to Recovery Mode",
                    "category": "reboot",
                    "badge": "RECOVERY",
                    "color": "#4F46E5", "hover": "#4338CA",
                    "cmd": lambda: c.fastboot_view._reboot_device_mode("recovery")
                },
                {
                    "icon": "🔄",
                    "title": "Reboot to EDL 9008 Mode",
                    "desc": "Reboots Qualcomm phone from ADB into Emergency Download 9008 port.",
                    "btn_text": "🐉 Jump to Qualcomm EDL 9008",
                    "category": "reboot",
                    "badge": "QUALCOMM EDL",
                    "color": "#D97706", "hover": "#B45309",
                    "cmd": lambda: c.fastboot_view._reboot_device_mode("edl")
                }
            ]
        return []
        return []

    def _switch_and_run(self, platform: str, func):
        if self.controller and hasattr(self.controller, "switch_to_platform"):
            self.controller.switch_to_platform(platform)
        if callable(func):
            func()

    def _open_in_studio(self):
        """Switches to the full dedicated studio for manual advanced controls."""
        if not self.controller or not hasattr(self.controller, "switch_to_platform"):
            return
        mapping = {
            "MTK": "mtk",
            "QUALCOMM": "qc",
            "SPD": "spd",
            "SAMSUNG": "samsung",
            "FASTBOOT": "fastboot",
            "ADB": "fastboot"
        }
        target = mapping.get(self.current_mode, "mtk")
        self.controller.switch_to_platform(target)

    def show(self):
        self.container.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=(0, 6))

    def hide(self):
        self.container.grid_forget()
