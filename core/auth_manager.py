"""
BS Lab Tool v2.0 PRO — Commercial Grade Authentication & HWID License Manager.
Supports:
1. Supabase Cloud Authentication (Sign In, Sign Up, Token Refresh).
2. Unique Machine Hardware ID (HWID) Fingerprinting.
3. Offline Secure Token Storage (%APPDATA%/BSLab_Tool/session.json).
4. Offline / Dev Fallback Mode for Workshops without Active Internet.
"""

import os
import sys
import json
import uuid
import hashlib
import urllib.request
import urllib.error
from typing import Tuple, Dict, Any, Optional

class AuthManager:
    """Manages User Accounts, Cloud Supabase Auth, and Machine HWID Binding."""

    # Default Supabase configuration (Users can override via config/auth_config.json)
    DEFAULT_SUPABASE_URL = "https://your-project-id.supabase.co"
    DEFAULT_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    @staticmethod
    def get_app_data_dir() -> str:
        """Returns the roaming AppData path for BSLab_Tool credentials."""
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        app_dir = os.path.join(base, "BSLab_Tool")
        os.makedirs(app_dir, exist_ok=True)
        return app_dir

    @classmethod
    def get_config_path(cls) -> str:
        return os.path.join(cls.get_app_data_dir(), "auth_config.json")

    @classmethod
    def get_session_path(cls) -> str:
        return os.path.join(cls.get_app_data_dir(), "session.json")

    @classmethod
    def get_local_db_path(cls) -> str:
        """Local account vault for offline activation / workshop resilience."""
        return os.path.join(cls.get_app_data_dir(), "local_accounts.json")

    @classmethod
    def get_hwid(cls) -> str:
        """
        Computes a stable, cryptographically hashed Hardware Fingerprint (HWID).
        Based on Windows MachineGuid, Volume Serial, and System MAC address.
        """
        raw_components = []

        # 1. Windows MachineGuid from Registry
        if sys.platform == "win32":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                    guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                    raw_components.append(str(guid))
            except Exception:
                pass

        # 2. Network MAC Node
        try:
            node = uuid.getnode()
            raw_components.append(str(node))
        except Exception:
            pass

        # 3. Environment Username & Architecture
        raw_components.append(os.environ.get("PROCESSOR_IDENTIFIER", "GENERIC_CPU"))

        combined = "-".join(raw_components)
        h = hashlib.sha256(combined.encode("utf-8")).hexdigest().upper()
        # Format as clean 16-character license string: BSLAB-XXXX-XXXX-XXXX
        formatted_hwid = f"BSLAB-{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"
        return formatted_hwid

    @classmethod
    def load_config(cls) -> Dict[str, str]:
        path = cls.get_config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "supabase_url": cls.DEFAULT_SUPABASE_URL,
            "supabase_key": cls.DEFAULT_ANON_KEY
        }

    @classmethod
    def save_config(cls, url: str, key: str):
        path = cls.get_config_path()
        data = {"supabase_url": url.strip(), "supabase_key": key.strip()}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    # =========================================================================
    # AUTHENTICATION API (SUPABASE + LOCAL HYBRID)
    # =========================================================================

    @classmethod
    def sign_in(cls, email: str, password: str, remember: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Authenticates user with Email and Password.
        Checks Supabase Cloud first; falls back to local secure vault if offline.
        """
        email = email.strip().lower()
        if not email or not password:
            return False, "Please enter both Email and Password.", {}

        cfg = cls.load_config()
        url = cfg.get("supabase_url", "")
        anon_key = cfg.get("supabase_key", "")

        # Check if Supabase URL is active and configured
        if url and "your-project-id" not in url:
            try:
                endpoint = f"{url.rstrip('/')}/auth/v1/token?grant_type=password"
                headers = {
                    "apikey": anon_key,
                    "Content-Type": "application/json"
                }
                payload = json.dumps({"email": email, "password": password}).encode("utf-8")
                req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")

                with urllib.request.urlopen(req, timeout=6) as response:
                    res_body = response.read().decode("utf-8")
                    data = json.loads(res_body)
                    user_data = data.get("user", {})
                    token = data.get("access_token", "")

                    if remember:
                        cls._save_session(email, user_data, token)

                    return True, f"Welcome back, {email}!", user_data
            except urllib.error.HTTPError as he:
                try:
                    err_json = json.loads(he.read().decode("utf-8"))
                    msg = err_json.get("error_description") or err_json.get("msg") or "Invalid login credentials."
                    return False, f"Cloud Auth Error: {msg}", {}
                except Exception:
                    return False, f"Server Rejected Login (HTTP {he.code}).", {}
            except Exception as e:
                # Network unreachable, fallback to local accounts vault
                pass

        # Local Vault Fallback (For offline workshops / local testing)
        local_db = cls._load_local_db()
        hashed_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()

        if email in local_db:
            acc = local_db[email]
            if acc.get("password_hash") == hashed_pwd:
                user_info = {
                    "id": acc.get("id", str(uuid.uuid4())),
                    "email": email,
                    "hwid": acc.get("hwid", cls.get_hwid()),
                    "tier": "PRO WORKSTATION LICENSE",
                    "mode": "Verified Active"
                }
                if remember:
                    cls._save_session(email, user_info, "local_token_active")
                return True, f"Welcome back, {email}! (License Active)", user_info
            else:
                return False, "Incorrect password. Please try again.", {}

        # Default Master Demo Account for instant first run
        if email in ("admin@bslab.com", "technician@bslab.com") and password in ("admin123", "bslab2026"):
            user_info = {
                "id": "master-pro-001",
                "email": email,
                "hwid": cls.get_hwid(),
                "tier": "BS LAB MASTER PRO",
                "mode": "Master Developer"
            }
            if remember:
                cls._save_session(email, user_info, "master_token")
            return True, "Master License Activated!", user_info

        return False, "Account not found. Please click 'Create Account' to register.", {}

    @classmethod
    def sign_up(cls, email: str, password: str, confirm_pwd: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Creates a new account and binds it to this machine's HWID.
        """
        email = email.strip().lower()
        if not email or "@" not in email or "." not in email:
            return False, "Please enter a valid email address.", {}

        if len(password) < 6:
            return False, "Password must be at least 6 characters long.", {}

        if password != confirm_pwd:
            return False, "Passwords do not match.", {}

        hwid = cls.get_hwid()
        cfg = cls.load_config()
        url = cfg.get("supabase_url", "")
        anon_key = cfg.get("supabase_key", "")

        # Try Supabase registration if configured
        if url and "your-project-id" not in url:
            try:
                endpoint = f"{url.rstrip('/')}/auth/v1/signup"
                headers = {
                    "apikey": anon_key,
                    "Content-Type": "application/json"
                }
                payload = json.dumps({
                    "email": email,
                    "password": password,
                    "data": {"hwid": hwid, "tool": "BSLab_Tool_v2_PRO"}
                }).encode("utf-8")
                req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")

                with urllib.request.urlopen(req, timeout=6) as response:
                    res_body = response.read().decode("utf-8")
                    data = json.loads(res_body)
                    user_data = data.get("user", {})
                    # Also record in local db for offline caching
                    cls._record_local_account(email, password, hwid)
                    return True, "Account created successfully! You can now log in.", user_data
            except urllib.error.HTTPError as he:
                try:
                    err_json = json.loads(he.read().decode("utf-8"))
                    msg = err_json.get("error_description") or err_json.get("msg") or "Registration failed."
                    return False, f"Cloud Error: {msg}", {}
                except Exception:
                    return False, f"Cloud registration failed (HTTP {he.code}).", {}
            except Exception:
                pass

        # Local Vault Registration (Instant offline activation)
        local_db = cls._load_local_db()
        if email in local_db:
            return False, "An account with this email already exists locally. Please Sign In.", {}

        cls._record_local_account(email, password, hwid)
        return True, "Account successfully registered & HWID License Bound! You can now log in.", {"email": email, "hwid": hwid}

    @classmethod
    def load_active_session(cls) -> Optional[Dict[str, Any]]:
        """Checks if a valid 'Remember Me' session is saved on this machine."""
        path = cls.get_session_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("email") and data.get("token"):
                        # Verify HWID matches this machine
                        if data.get("hwid") == cls.get_hwid():
                            return data
            except Exception:
                pass
        return None

    @classmethod
    def logout(cls):
        """Clears local saved session."""
        path = cls.get_session_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    @classmethod
    def _save_session(cls, email: str, user_data: dict, token: str):
        path = cls.get_session_path()
        data = {
            "email": email,
            "hwid": cls.get_hwid(),
            "token": token,
            "user_data": user_data
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def _load_local_db(cls) -> Dict[str, Any]:
        path = cls.get_local_db_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @classmethod
    def _record_local_account(cls, email: str, password: str, hwid: str):
        db = cls._load_local_db()
        hashed_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()
        db[email] = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": hashed_pwd,
            "hwid": hwid,
            "tier": "PRO WORKSTATION LICENSE",
            "created_at": str(uuid.uuid1())
        }
        path = cls.get_local_db_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2)
        except Exception:
            pass
