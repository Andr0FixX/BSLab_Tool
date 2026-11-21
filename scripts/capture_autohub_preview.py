import time
import os
import ctypes
from ctypes import wintypes
from PIL import ImageGrab

# Let's find window handle of BSLabTool
user32 = ctypes.windll.user32

found_hwnd = []
def enum_cb(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            if "BS LAB TOOL" in buff.value.upper():
                found_hwnd.append((hwnd, buff.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

print("Found windows:", found_hwnd)

artifact_dir = r"C:\Users\AndroFixX\.gemini\antigravity\brain\a7b5fbb7-27a4-484b-88df-af3bcd9f6cd1"
preview_path = os.path.join(artifact_dir, "autohub_ai_separated_preview.png")

if found_hwnd:
    hwnd, title = found_hwnd[0]
    # bring to front
    user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
    user32.SetForegroundWindow(hwnd)
    time.sleep(1)

# Capture primary screen
img = ImageGrab.grab()
img.save(preview_path)
print(f"Saved screenshot to {preview_path} ({img.size})")
