import time
import threading
import serial.tools.list_ports

class PortWatcher:
    """Monitors serial / COM ports in real-time with high-speed trapping."""
    def __init__(self, on_device_change_callback, poll_interval=0.5):
        self.callback = on_device_change_callback
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None
        self._known_ports = set()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _monitor_loop(self):
        while self._running:
            try:
                current_ports = self._scan_ports()
                port_names = set(current_ports.keys())
                
                # If ports changed, notify
                if port_names != self._known_ports:
                    self._known_ports = port_names
                    if self.callback:
                        self.callback(current_ports)
            except Exception:
                pass
            time.sleep(self.poll_interval)

    @classmethod
    def _scan_ports(cls):
        results = {}
        ports = serial.tools.list_ports.comports()
        for p in ports:
            vid = p.vid if p.vid is not None else 0
            pid = p.pid if p.pid is not None else 0
            desc = p.description or ""

            mode = "STANDARD"
            # MediaTek BROM
            if (vid == 0x0E8D and pid == 0x0003) or "MTK USB Port" in desc or "MediaTek USB Port" in desc:
                mode = "MTK_BROM"
            # MediaTek Preloader
            elif (vid == 0x0E8D and pid == 0x2000) or "Preloader" in desc or "MTK Preloader" in desc:
                mode = "MTK_PRELOADER"
            # Qualcomm 9008
            elif (vid == 0x05C6 and pid == 0x9008) or "9008" in desc:
                mode = "QUALCOMM_EDL"
            # Huawei / HiSilicon USB COM 1.0
            elif (vid == 0x12D1 and pid == 0x3609) or any(k in desc.lower() for k in ["usb com 1.0", "huawei usb com"]):
                mode = "HUAWEI_KIRIN"
            # Unisoc / Spreadtrum
            elif (vid == 0x1782) or any(k in desc.lower() for k in ["spd", "sprd", "spreadtrum"]):
                mode = "UNISOC_SPRD"
            # Samsung Download / Modem
            elif (vid == 0x04E8) or any(k in desc.lower() for k in ["samsung", "odin"]):
                mode = "SAMSUNG"

            results[p.device] = {
                "port": p.device,
                "description": desc,
                "vid": f"{vid:04X}",
                "pid": f"{pid:04X}",
                "mode": mode
            }
        return results

    @classmethod
    def wait_for_mtk_device(cls, timeout=30, cancel_event=None, logger=None):
        """High-speed trap (every 30ms) to capture MTK Preloader/BROM port before timeout."""
        start_time = time.time()
        if logger:
            logger.brom("WAITING FOR DEVICE... (Turn OFF phone, hold Vol+ & Vol- and insert USB cable)")

        while time.time() - start_time < timeout:
            if cancel_event and cancel_event.is_set():
                if logger:
                    logger.warn("Operation cancelled by user.")
                return None, None

            ports = cls._scan_ports()
            for p, data in ports.items():
                if data["mode"] in ("MTK_BROM", "MTK_PRELOADER"):
                    if logger:
                        logger.success(f"Device Trapped Instantly: {data['mode']} on {p} ({data['description']})")
                    return p, data["mode"]

            time.sleep(0.03)  # Ultra-fast 30ms polling to catch 1-second preloader window

        if logger:
            logger.error("Connection Timeout: No MediaTek device detected within 30 seconds.")
        return None, None

    @staticmethod
    def get_current_ports():
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]
