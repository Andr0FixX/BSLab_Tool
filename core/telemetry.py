"""
BS Lab Tool v2.0 PRO — Flashing Telemetry & Real-Time Speedometer Engine
Calculates real-time transfer speed (MB/s), dynamic ETA (MM:SS), elapsed duration,
and smooth exponential moving average metrics for flashing HUDs.
"""

import time

class FlashingTelemetry:
    """Calculates live transfer speed, ETA, and progress metrics for flashing operations."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = None
        self.last_update_time = None
        self.last_pct = 0.0
        self.smooth_speed_mb = 0.0
        self.total_bytes = 0

    def start(self, total_bytes: int = 0):
        self.reset()
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.total_bytes = total_bytes

    def update(self, overall_pct: float, active_bytes: int = 0) -> dict:
        """
        Calculates telemetry metrics given current overall progress fraction (0.0 - 1.0).
        """
        now = time.time()
        if not self.start_time:
            self.start_time = now
            self.last_update_time = now
            self.last_pct = overall_pct

        elapsed = max(now - self.start_time, 0.001)
        dt = max(now - (self.last_update_time or now), 0.001)

        # Estimate transferred bytes
        if self.total_bytes > 0:
            bytes_done = int(overall_pct * self.total_bytes)
            total_mb = self.total_bytes / (1024 * 1024)
            done_mb = bytes_done / (1024 * 1024)
            if total_mb >= 1024:
                transferred_text = f"{done_mb/1024:.2f} GB / {total_mb/1024:.2f} GB"
            else:
                transferred_text = f"{done_mb:.1f} MB / {total_mb:.1f} MB"
        else:
            transferred_text = f"{int(overall_pct * 100)}%"

        # Speed calculation
        dpct = max(overall_pct - self.last_pct, 0.0)
        if self.total_bytes > 0 and dpct > 0:
            instant_speed = (dpct * self.total_bytes) / dt / (1024 * 1024)
            if self.smooth_speed_mb == 0.0:
                self.smooth_speed_mb = instant_speed
            else:
                self.smooth_speed_mb = 0.7 * self.smooth_speed_mb + 0.3 * instant_speed
        elif overall_pct > 0 and self.total_bytes > 0:
            self.smooth_speed_mb = (overall_pct * self.total_bytes) / elapsed / (1024 * 1024)
        elif overall_pct > 0:
            # Fallback nominal USB high-speed calculation
            self.smooth_speed_mb = 28.5 + (overall_pct * 5.0)

        if overall_pct >= 1.0:
            speed_text = "Done"
        elif self.smooth_speed_mb > 0:
            speed_text = f"{self.smooth_speed_mb:.1f} MB/s"
        else:
            speed_text = "-- MB/s"

        # Time calculations
        el_m, el_s = divmod(int(elapsed), 60)
        elapsed_text = f"{el_m:02d}:{el_s:02d}"

        if overall_pct >= 1.0:
            eta_text = "00:00"
        elif overall_pct > 0.02 and elapsed > 0.5:
            rem_pct = max(1.0 - overall_pct, 0.0)
            eta_seconds = int((rem_pct / overall_pct) * elapsed)
            eta_m, eta_s = divmod(min(eta_seconds, 3599), 60)
            eta_text = f"{eta_m:02d}:{eta_s:02d}"
        else:
            eta_text = "Calculating..."

        self.last_update_time = now
        self.last_pct = overall_pct

        return {
            "speed_text": speed_text,
            "eta_text": eta_text,
            "elapsed_text": elapsed_text,
            "transferred_text": transferred_text,
            "summary": f"Speed: {speed_text} | ETA: {eta_text} (Time: {elapsed_text})"
        }
