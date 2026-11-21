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

log_path = r"C:\BSLab_Tool\scripts\optimization_result.log"
if os.path.exists(log_path):
    try: os.remove(log_path)
    except: pass

sei = SHELLEXECUTEINFO()
sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
sei.fMask = SEE_MASK_NOCLOSEPROCESS
sei.hwnd = None
sei.lpVerb = "runas"
sei.lpFile = "cmd.exe"
sei.lpParameters = r"/c C:\BSLab_Tool\scripts\run_optimize.bat"
sei.lpDirectory = r"C:\BSLab_Tool\scripts"
sei.nShow = SW_HIDE

print("Triggering elevated execution of run_optimize.bat...")
res = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
if not res:
    err = ctypes.windll.kernel32.GetLastError()
    print(f"ShellExecuteExW failed: {err}")
else:
    print(f"Process spawned. Handle: {sei.hProcess}")
    if sei.hProcess:
        ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 60000)
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)
        print("Batch execution finished.")

time.sleep(1)
if os.path.exists(log_path):
    print("\n--- OPTIMIZATION RESULT LOG ---")
    with open(log_path, "r", errors="ignore") as f:
        print(f.read())
else:
    print("Log file still not found.")
