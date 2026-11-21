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

log_path = r"C:\BSLab_Tool\scripts\dual_killer_output.log"
if os.path.exists(log_path):
    try: os.remove(log_path)
    except: pass

cmd_params = f'/c python C:\\BSLab_Tool\\scripts\\dual_watchdog_killer.py > "{log_path}" 2>&1'

sei = SHELLEXECUTEINFO()
sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
sei.fMask = SEE_MASK_NOCLOSEPROCESS
sei.hwnd = None
sei.lpVerb = "runas"
sei.lpFile = "cmd.exe"
sei.lpParameters = cmd_params
sei.lpDirectory = r"C:\BSLab_Tool\scripts"
sei.nShow = SW_HIDE

print("Triggering elevated execution of dual_watchdog_killer.py...")
res = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
if not res:
    err = ctypes.windll.kernel32.GetLastError()
    print(f"ShellExecuteExW failed: {err}")
else:
    print(f"Elevated runner spawned. Process Handle: {sei.hProcess}")
    if sei.hProcess:
        ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 30000)
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)
        print("Elevated execution finished.")

time.sleep(1)
if os.path.exists(log_path):
    print("\n--- DUAL KILLER OUTPUT ---")
    with open(log_path, "r", errors="ignore") as f:
        print(f.read())
else:
    print("Log file was not generated.")
