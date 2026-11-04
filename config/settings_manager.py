import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

class SettingsManager:
    """Manages application settings, recent paths, and user configurations."""

    @staticmethod
    def load_settings() -> dict:
        default_settings = {
            "theme": "dark",
            "scaling": 0.90,
            "recent_scatter": "",
            "recent_da": "",
            "recent_preloader": "",
            "recent_auth": "",
            "recent_qc_prog": "",
            "recent_qc_rawprog": "",
            "recent_qc_patch": "",
            "recent_spd_pac": "",
            "auto_reboot": True,
            "force_brom": True,
            "server_auth": True
        }

        if not os.path.exists(SETTINGS_FILE):
            SettingsManager.save_settings(default_settings)
            return default_settings

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all default keys exist
                for k, v in default_settings.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return default_settings

    @staticmethod
    def save_settings(settings: dict):
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def get(key: str, default=None):
        settings = SettingsManager.load_settings()
        return settings.get(key, default)

    @staticmethod
    def set(key: str, value):
        settings = SettingsManager.load_settings()
        settings[key] = value
        SettingsManager.save_settings(settings)
