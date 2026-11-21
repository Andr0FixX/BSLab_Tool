import ctypes
from ctypes import wintypes
import time
import os

class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", wintypes.LPVOID),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIconOrMonitor", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE)
    ]

SEE_MASK_NOCLOSEPROCESS = 0x00000040
SW_HIDE = 0
SW_SHOW = 5

sei = SHELLEXECUTEINFO()
sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
sei.fMask = SEE_MASK_NOCLOSEPROCESS
sei.hwnd = None
sei.lpVerb = "runas"
sei.lpFile = "cmd.exe"
sei.lpParameters = r"/c C:\BSLab_Tool\scripts\kill_and_clean_admin.bat"
sei.lpDirectory = r"C:\BSLab_Tool\scripts"
sei.nShow = SW_HIDE

print("Triggering elevated execution via ShellExecuteExW(runas)...")
res = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
if not res:
    err = ctypes.windll.kernel32.GetLastError()
    print(f"ShellExecuteExW failed with error code: {err}")
else:
    print(f"Process spawned successfully. Process Handle: {sei.hProcess}")
    if sei.hProcess:
        # Wait up to 30 seconds for completion
        ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 30000)
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)
        print("Elevated process has terminated.")

log_path = r"C:\BSLab_Tool\scripts\cleanup_output.log"
time.sleep(1)
if os.path.exists(log_path):
    print("\n--- CLEANUP OUTPUT LOG ---")
    with open(log_path, "r", errors="ignore") as f:
        print(f.read())
else:
    print("Log file not found.")
