"""
BS Lab Tool v2.0 PRO - GSM Sound Effects & Audio Cues Subsystem
Uses native Windows sound synthesis (winsound) for zero-dependency, ultra-fast audio feedback.
Provides professional GSM Box style chimes for connect, disconnect, flash start, success, and error.
"""

import threading
import sys
from config.settings_manager import SettingsManager

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class SoundManager:
    """Manages audio cues and sound effects for device connection and flashing states."""

    _sound_enabled = True

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._sound_enabled and SettingsManager.get("sound_enabled", True)

    @classmethod
    def set_enabled(cls, enabled: bool):
        cls._sound_enabled = enabled
        SettingsManager.set("sound_enabled", enabled)

    @classmethod
    def _play_async(cls, tone_sequence):
        if not HAS_WINSOUND or not cls.is_enabled():
            return

        def run():
            try:
                for freq, duration_ms in tone_sequence:
                    winsound.Beep(int(freq), int(duration_ms))
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    @classmethod
    def play_connect(cls):
        """Rising two-tone chime when phone is plugged in (USB / COM detected)."""
        # 1000 Hz for 70ms -> 1500 Hz for 90ms
        cls._play_async([(1000, 70), (1500, 90)])

    @classmethod
    def play_disconnect(cls):
        """Falling two-tone chime when phone is unplugged."""
        # 1500 Hz for 70ms -> 850 Hz for 90ms
        cls._play_async([(1500, 70), (850, 90)])

    @classmethod
    def play_start(cls):
        """Single crisp confirmation beep when flashing starts."""
        # 1250 Hz for 120ms
        cls._play_async([(1250, 120)])

    @classmethod
    def play_success(cls):
        """Melodic victory chime on 100% successful operation (C6 -> E6 -> G6 major chord)."""
        # 1046 Hz (C6), 1318 Hz (E6), 1568 Hz (G6)
        cls._play_async([(1046, 90), (1318, 90), (1568, 180)])

    @classmethod
    def play_error(cls):
        """Low warning buzz on error or operation abort."""
        # 420 Hz for 150ms -> 320 Hz for 220ms
        cls._play_async([(420, 150), (320, 220)])
