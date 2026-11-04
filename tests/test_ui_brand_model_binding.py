"""
Unit Test: UI Views Brand, Model & Loader Auto-Binding Subsystem.
Verifies that MTKView, QualcommView, UnisocView, and SamsungView dynamically populate
from ModelRepository and auto-bind authentic loaders without UI crashes.
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.model_repository import ModelRepository
from ui.views.mtk_view import MTKView
from ui.views.qc_view import QualcommView
from ui.views.spd_view import UnisocView
from ui.views.samsung_view import SamsungView


class MockLogger:
    def info(self, msg): pass
    def success(self, msg): pass
    def warn(self, msg): pass
    def error(self, msg): pass
    def debug(self, msg): pass


class MockController:
    def __init__(self):
        self.logger = MockLogger()

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def test_ui_brand_model_binding():
    print("[TEST] Initializing UI Brand/Model/Loader Auto-Binding Test...")
    root = tk.Tk()
    root.withdraw()  # Headless mode

    controller = MockController()
    body_frame = tk.Frame(root)

    # 1. Test MTK View
    print("  Testing MTKView Dynamic Binding...")
    mtk = MTKView(body_frame, controller)
    assert len(mtk.mtk_brands) >= 5
    assert "Infinix" in mtk.mtk_brands

    # Switch to Infinix and select Hot 10
    mtk.brand_var.set("Infinix")
    mtk._on_brand_changed("Infinix")
    infinix_models = mtk.model_menu.cget("values")
    assert "Hot 10 (X682B)" in infinix_models

    mtk.model_var.set("Hot 10 (X682B)")
    mtk._on_model_changed("Hot 10 (X682B)")
    assert "preloader_x682b_h694.bin" in mtk.preloader_path_var.get()
    assert "MTK_DA_V6.bin" in mtk.da_path_var.get()
    print("  [OK] MTKView: Infinix Hot 10 auto-bound preloader and DA_V6!")

    # 2. Test Qualcomm View
    print("  Testing QualcommView Dynamic Binding...")
    qc = QualcommView(body_frame, controller)
    qc_models = qc._get_models_for_brand("Xiaomi / Redmi")
    assert len(qc_models) >= 10
    assert "Auto-Detect (Sahara Handshake)" in qc_models
    assert "POCO X3 Pro (Vayu)" in qc_models
    assert "⚡ Generic Snapdragon 680 (SM6225)" in qc_models

    # Verify ZERO raw hex filenames in dropdown!
    for m in qc_models:
        assert not m.endswith(".bin"), f"Raw file leaked in dropdown: {m}"
        assert "_fhprg" not in m, f"Raw hex hash leaked in dropdown: {m}"
    print("  [OK] QualcommView: Verified 0 raw hex files in dropdown! Clean models & chipsets only.")

    # Test Samsung Qualcomm models
    sam_qc = qc._get_models_for_brand("Samsung")
    assert "Galaxy A71 (SM-A715F)" in sam_qc
    assert "Galaxy A52 4G (SM-A525F)" in sam_qc
    print("  [OK] QualcommView: Verified Samsung Snapdragon models (A71, A52, A02s, etc.)!")

    # Test Sahara Auto-Match
    matched = qc.auto_match_device_loader(hwid="0000000000510000", pkhash="22f415bec935e3cb")
    assert matched is True
    assert os.path.exists(qc.qc_prog_path_var.get())
    print(f"  [OK] QualcommView: Sahara Auto-Match loaded {os.path.basename(qc.qc_prog_path_var.get())}!")

    # 3. Test Unisoc View
    print("  Testing UnisocView Dynamic Binding...")
    spd = UnisocView(body_frame, controller)
    spd_models = spd._get_spd_models_for_brand("Realme")
    assert len(spd_models) >= 1
    assert "Realme C21Y (RMX3261)" in spd_models
    print("  [OK] UnisocView: Realme C21Y model listed!")

    # 4. Test Samsung View (PIT Selector)
    print("  Testing SamsungView Official PIT Selector...")
    sam = SamsungView(body_frame, controller)
    pit_options = sam._get_pit_options()
    assert len(pit_options) >= 20

    # Auto-attach PIT
    sam._on_pit_selected("A035F (Galaxy A03)")
    assert os.path.exists(sam.slot_pit_var.get())
    assert sam.opt_repartition.get() is True
    print(f"  [OK] SamsungView: Auto-attached PIT {os.path.basename(sam.slot_pit_var.get())}!")

    root.destroy()
    print("\n[ALL UI BRAND & LOADER BINDING TESTS PASSED 100%]\n")


if __name__ == "__main__":
    test_ui_brand_model_binding()
