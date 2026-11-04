"""
BS Lab Tool v2.0 PRO — Antigravity-Style Dark Cyber Login & Registration Window.
Provides commercial-grade authentication, Supabase cloud sync, and Machine HWID binding.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from core.auth_manager import AuthManager
from ui.theme import Theme

class LoginWindow(ctk.CTkToplevel):
    """
    Antigravity-Inspired Sleek Cyberpunk Authentication Window.
    Stops main window execution until valid authentication is confirmed.
    """

    def __init__(self, on_login_success=None):
        super().__init__()

        self.on_login_success = on_login_success
        self.is_authenticated = False
        self.user_data = {}

        # Window Configuration
        self.title("BS Lab Tool PRO — Workstation Authentication")
        self.geometry("520x690")
        self.resizable(False, False)
        self.configure(fg_color="#080B11")

        # Center Window on Primary Display
        self._center_window(520, 690)

        # Force window to stay on top
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # State Variables
        self.active_tab = "signin"
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_pwd_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=True)
        self.show_pwd_var = tk.BooleanVar(value=False)

        self._build_ui()

        # Check existing active session
        self._check_auto_session()

    def _center_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2) - 25
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # 1. Main Outer Frame with Glowing Cyber Border
        self.main_card = ctk.CTkFrame(
            self,
            fg_color="#0D111A",
            corner_radius=12,
            border_width=1,
            border_color="#1E293B"
        )
        self.main_card.pack(fill="both", expand=True, padx=16, pady=16)

        # 2. Header Brand Banner
        hdr_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=20, pady=(20, 10))

        # Glowing Logo Badge
        logo_box = ctk.CTkFrame(hdr_frame, fg_color="#131B2E", corner_radius=8, width=54, height=54, border_width=1, border_color="#38BDF8")
        logo_box.pack(pady=(0, 8))
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="⚡", font=ctk.CTkFont(size=28)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            hdr_frame,
            text="BS LAB TOOL v2.0 PRO",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#F8FAFC"
        ).pack()

        ctk.CTkLabel(
            hdr_frame,
            text="Autonomous GSM Servicing & Repair Workstation",
            font=Theme.font_ui(size=11),
            text_color="#94A3B8"
        ).pack(pady=(2, 6))

        # 3. Machine Hardware ID (HWID) Pill
        hwid_card = ctk.CTkFrame(self.main_card, fg_color="#080C14", corner_radius=6, border_width=1, border_color="#1E293B")
        hwid_card.pack(fill="x", padx=24, pady=(0, 12))

        hwid_left = ctk.CTkFrame(hwid_card, fg_color="transparent")
        hwid_left.pack(side="left", padx=10, pady=6)

        self.current_hwid = AuthManager.get_hwid()
        ctk.CTkLabel(
            hwid_left,
            text=f"🔑 HWID: {self.current_hwid}",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#38BDF8"
        ).pack(anchor="w")

        btn_copy = ctk.CTkButton(
            hwid_card,
            text="📋 Copy",
            width=55,
            height=22,
            font=Theme.font_bold(size=9),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._copy_hwid
        )
        btn_copy.pack(side="right", padx=8, pady=4)

        # 4. Segmented Tab Bar (Sign In / Register)
        self.seg_frame = ctk.CTkFrame(self.main_card, fg_color="#080C14", corner_radius=8, height=36)
        self.seg_frame.pack(fill="x", padx=24, pady=(0, 12))

        self.btn_tab_signin = ctk.CTkButton(
            self.seg_frame,
            text="🔐 SIGN IN",
            font=Theme.font_bold(size=11),
            height=30,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=lambda: self._switch_tab("signin")
        )
        self.btn_tab_signin.pack(side="left", fill="both", expand=True, padx=3, pady=3)

        self.btn_tab_signup = ctk.CTkButton(
            self.seg_frame,
            text="📝 CREATE ACCOUNT",
            font=Theme.font_bold(size=11),
            height=30,
            fg_color="transparent",
            text_color="#94A3B8",
            hover_color="#1E293B",
            command=lambda: self._switch_tab("signup")
        )
        self.btn_tab_signup.pack(side="right", fill="both", expand=True, padx=3, pady=3)

        # 5. Form Container
        self.form_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=24, pady=0)

        # Email Field
        ctk.CTkLabel(self.form_frame, text="ACCOUNT EMAIL", font=Theme.font_bold(size=10), text_color="#94A3B8").pack(anchor="w", pady=(0, 2))
        self.entry_email = ctk.CTkEntry(
            self.form_frame,
            textvariable=self.email_var,
            placeholder_text="Enter your email address...",
            height=34,
            fg_color="#080C14",
            border_color="#1E293B",
            font=Theme.font_ui(size=11)
        )
        self.entry_email.pack(fill="x", pady=(0, 10))

        # Password Field
        ctk.CTkLabel(self.form_frame, text="PASSWORD", font=Theme.font_bold(size=10), text_color="#94A3B8").pack(anchor="w", pady=(0, 2))
        self.entry_pwd = ctk.CTkEntry(
            self.form_frame,
            textvariable=self.password_var,
            placeholder_text="Enter password (min 6 characters)...",
            show="●",
            height=34,
            fg_color="#080C14",
            border_color="#1E293B",
            font=Theme.font_ui(size=11)
        )
        self.entry_pwd.pack(fill="x", pady=(0, 4))

        # Confirm Password Field (Only visible in SignUp)
        self.confirm_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        ctk.CTkLabel(self.confirm_frame, text="CONFIRM PASSWORD", font=Theme.font_bold(size=10), text_color="#94A3B8").pack(anchor="w", pady=(4, 2))
        self.entry_confirm_pwd = ctk.CTkEntry(
            self.confirm_frame,
            textvariable=self.confirm_pwd_var,
            placeholder_text="Re-type password to verify...",
            show="●",
            height=34,
            fg_color="#080C14",
            border_color="#1E293B",
            font=Theme.font_ui(size=11)
        )
        self.entry_confirm_pwd.pack(fill="x", pady=(0, 6))

        # Options Row (Show Password + Remember Me)
        self.opts_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.opts_row.pack(fill="x", pady=(4, 10))

        self.chk_show_pwd = ctk.CTkCheckBox(
            self.opts_row,
            text="Show Password",
            variable=self.show_pwd_var,
            font=Theme.font_ui(size=10),
            checkbox_width=18,
            checkbox_height=18,
            command=self._toggle_password_visibility
        )
        self.chk_show_pwd.pack(side="left")

        self.chk_remember = ctk.CTkCheckBox(
            self.opts_row,
            text="Remember Me",
            variable=self.remember_var,
            font=Theme.font_ui(size=10),
            checkbox_width=18,
            checkbox_height=18
        )
        self.chk_remember.pack(side="right")

        # Dynamic Status Message Bar
        self.lbl_status = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=Theme.font_bold(size=10),
            text_color="#94A3B8",
            wraplength=440
        )
        self.lbl_status.pack(fill="x", pady=(0, 6))

        # Main Action Button (Sign In / Register)
        self.btn_submit = ctk.CTkButton(
            self.form_frame,
            text="🚀 LAUNCH WORKSTATION",
            font=Theme.font_bold(size=12),
            height=40,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self._handle_submit
        )
        self.btn_submit.pack(fill="x", pady=(4, 10))

        # 6. Bottom Utility Footer
        footer = ctk.CTkFrame(self.main_card, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(0, 10))

        btn_supabase = ctk.CTkButton(
            footer,
            text="⚙️ Supabase Cloud Server Config",
            font=Theme.font_ui(size=10),
            fg_color="transparent",
            text_color="#64748B",
            hover_color="#1E293B",
            height=24,
            command=self._open_supabase_config
        )
        btn_supabase.pack(side="left")

        ctk.CTkLabel(
            footer,
            text="Security: SHA-256 + HWID Guard",
            font=Theme.font_ui(size=9),
            text_color="#475569"
        ).pack(side="right")

    def _switch_tab(self, tab: str):
        self.active_tab = tab
        self.lbl_status.configure(text="")
        if tab == "signin":
            self.btn_tab_signin.configure(fg_color="#0284C7", text_color="#FFFFFF")
            self.btn_tab_signup.configure(fg_color="transparent", text_color="#94A3B8")
            self.confirm_frame.pack_forget()
            self.btn_submit.configure(
                text="🚀 LAUNCH WORKSTATION",
                fg_color="#0284C7",
                hover_color="#0369A1"
            )
        else:
            self.btn_tab_signup.configure(fg_color="#059669", text_color="#FFFFFF")
            self.btn_tab_signin.configure(fg_color="transparent", text_color="#94A3B8")
            self.confirm_frame.pack(fill="x", pady=(0, 6))
            self.btn_submit.configure(
                text="🌟 CREATE & ACTIVATE ACCOUNT",
                fg_color="#059669",
                hover_color="#047857"
            )

    def _toggle_password_visibility(self):
        show_char = "" if self.show_pwd_var.get() else "●"
        self.entry_pwd.configure(show=show_char)
        self.entry_confirm_pwd.configure(show=show_char)

    def _copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.current_hwid)
        self._set_status("HWID copied to clipboard!", "#34D399")

    def _set_status(self, msg: str, color: str = "#38BDF8"):
        self.lbl_status.configure(text=msg, text_color=color)

    def _check_auto_session(self):
        session = AuthManager.load_active_session()
        if session:
            email = session.get("email", "")
            self.email_var.set(email)
            self._set_status(f"✓ License Active for {email}. Click Launch to proceed.", "#34D399")

    def _handle_submit(self):
        email = self.email_var.get().strip()
        pwd = self.password_var.get().strip()
        remember = self.remember_var.get()

        if self.active_tab == "signin":
            self._set_status("Authenticating credentials...", "#38BDF8")
            self.btn_submit.configure(state="disabled")
            self.update_idletasks()

            ok, msg, data = AuthManager.sign_in(email, pwd, remember=remember)
            self.btn_submit.configure(state="normal")
            if ok:
                self._set_status(f"✓ {msg}", "#34D399")
                self.after(500, lambda: self._on_auth_success(data, email))
            else:
                self._set_status(f"✗ {msg}", "#F87171")
        else:
            confirm = self.confirm_pwd_var.get().strip()
            self._set_status("Registering account & binding HWID...", "#38BDF8")
            self.btn_submit.configure(state="disabled")
            self.update_idletasks()

            ok, msg, data = AuthManager.sign_up(email, pwd, confirm)
            self.btn_submit.configure(state="normal")
            if ok:
                self._set_status(f"✓ {msg}", "#34D399")
                self.after(1200, lambda: self._switch_tab("signin"))
            else:
                self._set_status(f"✗ {msg}", "#F87171")

    def _on_auth_success(self, user_data: dict, email: str):
        self.is_authenticated = True
        self.user_data = user_data
        if callable(self.on_login_success):
            self.on_login_success(user_data)
        self.destroy()

    def _open_supabase_config(self):
        """Mini modal dialog to enter custom Supabase URL and Anon Key."""
        diag = ctk.CTkToplevel(self)
        diag.title("Supabase Cloud Database Settings")
        diag.geometry("460x280")
        diag.resizable(False, False)
        diag.configure(fg_color="#080B11")
        diag.attributes("-topmost", True)

        cfg = AuthManager.load_config()
        url_var = tk.StringVar(value=cfg.get("supabase_url", ""))
        key_var = tk.StringVar(value=cfg.get("supabase_key", ""))

        card = ctk.CTkFrame(diag, fg_color="#0D111A", corner_radius=10, border_width=1, border_color="#1E293B")
        card.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(card, text="☁️ SUPABASE AUTHENTICATION CONFIG", font=Theme.font_bold(size=11), text_color="#38BDF8").pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkLabel(card, text="Project URL (e.g. https://xyz.supabase.co):", font=Theme.font_ui(size=10), text_color="#94A3B8").pack(anchor="w", padx=14)
        ctk.CTkEntry(card, textvariable=url_var, height=28, fg_color="#080C14", border_color="#1E293B", font=Theme.font_ui(size=10)).pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkLabel(card, text="Anon API Key:", font=Theme.font_ui(size=10), text_color="#94A3B8").pack(anchor="w", padx=14)
        ctk.CTkEntry(card, textvariable=key_var, height=28, fg_color="#080C14", border_color="#1E293B", font=Theme.font_ui(size=10), show="●").pack(fill="x", padx=14, pady=(0, 10))

        def save_and_close():
            AuthManager.save_config(url_var.get(), key_var.get())
            diag.destroy()
            self._set_status("Supabase configuration saved successfully!", "#34D399")

        ctk.CTkButton(card, text="💾 Save Cloud Configuration", font=Theme.font_bold(size=11), height=32, fg_color="#0284C7", hover_color="#0369A1", command=save_and_close).pack(fill="x", padx=14, pady=(4, 10))

    def _on_close(self):
        if not self.is_authenticated:
            # If user closes without logging in, exit app
            sys.exit(0)
        self.destroy()
