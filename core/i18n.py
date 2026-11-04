"""
BS Lab Tool v2.0 PRO - Multi-Language Localization Subsystem (i18n)
Provides seamless language toggling between English (EN) and Urdu (UR / اردو).
"""

from typing import Dict, Callable, List
from config.settings_manager import SettingsManager

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Ribbon & Platforms
        "mod_mtk": "⚡ MEDIATEK (MTK)",
        "mod_qc": "🐉 QUALCOMM (EDL 9008)",
        "mod_spd": "📱 UNISOC / SPD",
        "mod_samsung": "🟡 SAMSUNG (ODIN / MTP)",
        "mod_fastboot": "🤖 FASTBOOT & ADB",
        "mod_tp": "📌 TEST POINTS",
        "mod_unpacker": "📦 FIRMWARE UNPACKER",
        "mod_analyzer": "🧠 AI LOG ANALYZER",
        "platform_module": "❖ PLATFORM MODULE:",

        # Common Actions
        "btn_start_flash": "⚡ START FLASH",
        "btn_stop_abort": "🛑 STOP / ABORT",
        "btn_refresh": "🔄 Refresh",
        "btn_drivers": "🔧 Drivers",
        "btn_clear": "Clear",
        "btn_copy": "Copy",
        "btn_export": "💾 Export Log",
        "btn_check_adb": "🔍 Check ADB",
        "btn_fastboot": "🔍 Fastboot",
        "btn_reboot_system": "🔄 Reboot System",
        "btn_read_info": "📱 Read Full Info",
        "btn_reset_frp": "🔒 Reset FRP (One-Click)",

        # Hub & Controls
        "lbl_auto_switch": "🔄 Auto-Switch Hub",
        "lbl_sound": "🔊 Sound Cues",
        "lbl_console_title": "LIVE DIAGNOSTICS & PROCESS LOG",
        "lbl_device_ports": "DEVICE DETECTION & PORTS",
        "lbl_power_mode": "⚡ POWER & MODE SWITCHER",

        # Status
        "status_ready": "● ENGINE READY",
        "status_busy": "● OPERATION ACTIVE (BUSY)",
        "status_waiting": "🔴 Waiting / No Device Connected",
        "status_connected": "🟢 Device Connected"
    },
    "ur": {
        # Ribbon & Platforms
        "mod_mtk": "⚡ میڈیاٹیک (MTK)",
        "mod_qc": "🐉 کوالکوم (EDL 9008)",
        "mod_spd": "📱 یونی سوک (SPD)",
        "mod_samsung": "🟡 سیمسنگ (ODIN / MTP)",
        "mod_fastboot": "🤖 فاسٹ بوٹ اور ADB",
        "mod_tp": "📌 ٹیسٹ پوائنٹس (TP)",
        "mod_unpacker": "📦 فِرم ویئر اَن پیکر",
        "mod_analyzer": "🧠 اے آئی لاگ اینالائزر",
        "platform_module": "❖ پلیٹ فارم منتخب کریں:",

        # Common Actions
        "btn_start_flash": "⚡ فلیشنگ شروع کریں",
        "btn_stop_abort": "🛑 روکیں (Abort)",
        "btn_refresh": "🔄 ریفریش",
        "btn_drivers": "🔧 ڈرائیورز",
        "btn_clear": "صاف کریں",
        "btn_copy": "کاپی کریں",
        "btn_export": "💾 لاگ محفوظ کریں",
        "btn_check_adb": "🔍 چیک ADB",
        "btn_fastboot": "🔍 فاسٹ بوٹ",
        "btn_reboot_system": "🔄 سسٹم ری بوٹ",
        "btn_read_info": "📱 معلومات پڑھیں",
        "btn_reset_frp": "🔒 ایف آر پی ری سیٹ",

        # Hub & Controls
        "lbl_auto_switch": "🔄 آٹو سوئچ ہب",
        "lbl_sound": "🔊 آواز (Sound)",
        "lbl_console_title": "لائیو ڈائیگنوسٹک اور پروسیس لاگ",
        "lbl_device_ports": "ڈیوائس کا پتہ اور پورٹس",
        "lbl_power_mode": "⚡ پاور اور موڈ سوئچر",

        # Status
        "status_ready": "● انجن تیار ہے",
        "status_busy": "● کام جاری ہے (Busy)",
        "status_waiting": "🔴 کوئی ڈیوائس منسلک نہیں ہے",
        "status_connected": "🟢 فون منسلک ہو چکا ہے"
    }
}


class I18N:
    """Internationalization and UI Localization Controller."""

    _current_lang = "en"
    _listeners: List[Callable[[], None]] = []

    @classmethod
    def init(cls):
        cls._current_lang = SettingsManager.get("language", "en")
        if cls._current_lang not in TRANSLATIONS:
            cls._current_lang = "en"

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def set_language(cls, lang_code: str):
        if lang_code in TRANSLATIONS:
            cls._current_lang = lang_code
            SettingsManager.set("language", lang_code)
            cls._notify_listeners()

    @classmethod
    def toggle_language(cls) -> str:
        new_lang = "ur" if cls._current_lang == "en" else "en"
        cls.set_language(new_lang)
        return new_lang

    @classmethod
    def t(cls, key: str, default: str = "") -> str:
        """Translate a key into active language."""
        lang_dict = TRANSLATIONS.get(cls._current_lang, TRANSLATIONS["en"])
        if key in lang_dict:
            return lang_dict[key]
        return TRANSLATIONS["en"].get(key, default or key)

    @classmethod
    def add_listener(cls, callback: Callable[[], None]):
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def _notify_listeners(cls):
        for cb in cls._listeners:
            try:
                cb()
            except Exception:
                pass


# Auto-initialize
I18N.init()
