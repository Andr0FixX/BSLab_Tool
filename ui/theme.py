"""
BS Lab Tool v2.0 PRO — Centralized Theme & Comfort View Engine
Studio Obsidian Dark Palette & Typography Design System
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class Theme:
    """Master Design System Tokens for BS Lab Tool PRO."""

    # -------------------------------------------------------------
    # 1. COLOR TOKENS (Obsidian Comfort Dark)
    # -------------------------------------------------------------
    # Canvas & Surfacing (WCAG AAA anti-glare)
    BG_CANVAS = "#0D1117"        # Obsidian deep slate main window canvas
    BG_HEADER = "#161B26"        # Top header & bottom status bar
    BG_PANEL = "#111622"         # Sidebars & container frames
    SURFACE_CARD = "#161D2B"     # Elevated card blocks
    BORDER_CARD = "#232D42"      # 1px Subtle luminous card outlines
    SURFACE_INPUT = "#0A0E17"    # Input fields, textboxes, tree backgrounds

    # Text Contrast Hierarchy (92% luminance soft white, no retina fatigue)
    TEXT_PRIMARY = "#F1F5F9"     # High readability soft slate white
    TEXT_SECONDARY = "#94A3B8"   # Balanced silver slate
    TEXT_MUTED = "#64748B"       # Muted hints and secondary captions

    # Brand & Platform Accents
    ACCENT_CYAN = "#00D2FF"      # Brand Primary (Tool Logo, BROM)
    ACCENT_CYAN_HOVER = "#00B4DB"
    ACCENT_GOLD = "#F59E0B"      # Qualcomm Snapdragon EDL Accent
    ACCENT_GOLD_HOVER = "#D97706"
    ACCENT_GREEN = "#10B981"     # MediaTek & Action Success
    ACCENT_GREEN_HOVER = "#059669"
    ACCENT_BLUE = "#0284C7"      # Samsung Sky Blue & Info
    ACCENT_BLUE_HOVER = "#0369A1"
    ACCENT_PURPLE = "#A855F7"    # Unisoc / Spreadtrum Accent
    ACCENT_RED = "#EF4444"       # Abort & Destructive Action
    ACCENT_RED_HOVER = "#DC2626"

    # Partition Table & Treeview Colors
    TABLE_BG = "#0D1117"
    TABLE_FG = "#E2E8F0"
    TABLE_ROW_EVEN = "#131722"
    TABLE_ROW_ODD = "#181E2C"
    TABLE_HEADER_BG = "#1A2234"
    TABLE_HEADER_FG = "#00D2FF"
    TABLE_ROW_SELECTED = "#0284C7"

    # -------------------------------------------------------------
    # 2. TYPOGRAPHY SYSTEM (Segoe UI Variable + Cascadia Code)
    # -------------------------------------------------------------
    UI_FONT_FAMILY = "Segoe UI Variable Display"
    UI_FONT_FALLBACK = "Segoe UI"
    MONO_FONT_FAMILY = "Cascadia Code"
    MONO_FONT_FALLBACK = "Consolas"

    @classmethod
    def font_ui(cls, size: int = 11, weight: str = "normal") -> ctk.CTkFont:
        """Returns standard UI text font."""
        try:
            return ctk.CTkFont(family=cls.UI_FONT_FAMILY, size=size, weight=weight)
        except Exception:
            return ctk.CTkFont(family=cls.UI_FONT_FALLBACK, size=size, weight=weight)

    @classmethod
    def font_bold(cls, size: int = 11) -> ctk.CTkFont:
        """Returns bold UI header font."""
        return cls.font_ui(size=size, weight="bold")

    @classmethod
    def font_mono(cls, size: int = 10, weight: str = "normal") -> ctk.CTkFont:
        """Returns tabular monospace font for hex offsets, logs, and partition sizes."""
        try:
            return ctk.CTkFont(family=cls.MONO_FONT_FAMILY, size=size, weight=weight)
        except Exception:
            return ctk.CTkFont(family=cls.MONO_FONT_FALLBACK, size=size, weight=weight)

    # -------------------------------------------------------------
    # 3. TTK TREEVIEW STYLING (Partition Lists & Tables)
    # -------------------------------------------------------------
    @classmethod
    def apply_ttk_theme(cls, style: ttk.Style):
        """Applies Comfort Studio styling to all ttk Treeviews."""
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Treeview Base Styling
        style.configure(
            "Treeview",
            background=cls.TABLE_ROW_EVEN,
            foreground=cls.TABLE_FG,
            fieldbackground=cls.TABLE_BG,
            bordercolor=cls.BORDER_CARD,
            borderwidth=0,
            rowheight=28,  # Increased from 25px for better readability and click accuracy
            font=(cls.UI_FONT_FALLBACK, 10)
        )

        # Treeview Column Headings
        style.configure(
            "Treeview.Heading",
            background=cls.TABLE_HEADER_BG,
            foreground=cls.TABLE_HEADER_FG,
            relief="flat",
            borderwidth=0,
            font=(cls.UI_FONT_FALLBACK, 10, "bold")
        )

        style.map(
            "Treeview",
            background=[('selected', cls.TABLE_ROW_SELECTED)],
            foreground=[('selected', '#FFFFFF')]
        )

        style.map(
            "Treeview.Heading",
            background=[('active', '#222C44')]
        )
