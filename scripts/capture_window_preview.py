import ctypes
from ctypes import wintypes
import time
import os

user32 = ctypes.windll.user32

found_hwnd = None
def enum_cb(hwnd, lparam):
    global found_hwnd
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.lower()
            if "bs lab tool" in title:
                found_hwnd = hwnd
                return False
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

if not found_hwnd:
    print("Could not find window.")
else:
    print(f"Found window HWND: {found_hwnd}")
    rect = wintypes.RECT()
    user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
    left = max(0, rect.left)
    top = max(0, rect.top)
    right = rect.right
    bottom = rect.bottom
    print(f"Window bounds: {left}, {top}, {right}x{bottom}")

    from PIL import ImageGrab
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    out_path = r"C:\Users\AndroFixX\.gemini\antigravity\brain\a7b5fbb7-27a4-484b-88df-af3bcd9f6cd1\partition_live_preview.png"
    img.save(out_path)
    print("Saved preview to:", out_path)
