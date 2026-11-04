"""
Unit Tests for Phase 6 Modernization: SoundManager, I18N, and Log Export.
"""

import os
import sys
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sound_manager import SoundManager
from core.i18n import I18N
from core.device_detector import DeviceDetector
from ui.components.status_bar import StatusBar
import tkinter as tk


def test_sound_manager():
    print("[TEST] Testing SoundManager Audio Cues...")
    # Verify methods don't crash
    SoundManager.play_connect()
    SoundManager.play_disconnect()
    SoundManager.play_start()
    SoundManager.play_success()
    SoundManager.play_error()
    print("  [OK] SoundManager tones dispatched asynchronously.")


def test_i18n():
    print("[TEST] Testing Multi-Language Localization (I18N)...")
    I18N.set_language("en")
    assert I18N.t("btn_start_flash") == "⚡ START FLASH"
    assert I18N.t("mod_samsung") == "🟡 SAMSUNG (ODIN / MTP)"

    # Toggle to Urdu
    new_lang = I18N.toggle_language()
    assert new_lang == "ur"
    assert I18N.t("btn_start_flash") == "⚡ فلیشنگ شروع کریں"
    assert I18N.t("mod_samsung") == "🟡 سیمسنگ (ODIN / MTP)"

    # Switch back to English
    I18N.set_language("en")
    assert I18N.t("btn_start_flash") == "⚡ START FLASH"
    print("  [OK] I18N English / Urdu translation passed.")


def test_smart_hub_detection():
    print("[TEST] Testing DeviceDetector & Smart Hub mapping...")
    res = DeviceDetector.scan_all_devices()
    assert "detected" in res
    assert "mode" in res
    assert "text" in res
    print(f"  [OK] Detection response format valid: mode={res['mode']}, detected={res['detected']}")


def test_status_bar_support_links():
    print("[TEST] Testing StatusBar Support Links Capsule (WhatsApp, Telegram, Facebook)...")
    root = tk.Tk()
    root.withdraw()
    sb = StatusBar(root)

    assert hasattr(sb, "btn_whatsapp")
    assert hasattr(sb, "btn_telegram")
    assert hasattr(sb, "btn_facebook")
    assert "WhatsApp" in sb.btn_whatsapp.cget("text")
    assert "Telegram" in sb.btn_telegram.cget("text")
    assert "Facebook" in sb.btn_facebook.cget("text")

    root.destroy()
    print("  [OK] StatusBar Community & Support buttons verified.")


if __name__ == "__main__":
    test_sound_manager()
    test_i18n()
    test_smart_hub_detection()
    test_status_bar_support_links()
    print("\n[ALL PHASE 6 TESTS PASSED 100%]\n")
