import ctypes
from ctypes import wintypes
import time
import os
import subprocess

crash_log = r"C:\BSLab_Tool\dist_new\crash.log"
if os.path.exists(crash_log):
    os.remove(crash_log)

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
SW_SHOW = 5

target_exe = r"C:\BSLab_Tool\dist_new\BSLabTool.exe"

sei = SHELLEXECUTEINFO()
sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
sei.fMask = SEE_MASK_NOCLOSEPROCESS
sei.hwnd = None
sei.lpVerb = "runas"
sei.lpFile = target_exe
sei.lpParameters = ""
sei.lpDirectory = r"C:\BSLab_Tool\dist_new"
sei.nShow = SW_SHOW

print("Launching BSLabTool.exe...")
res = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
if not res:
    print("ShellExecuteExW failed:", ctypes.windll.kernel32.GetLastError())
else:
    print("ShellExecuteExW succeeded. Process Handle:", sei.hProcess)
    time.sleep(4)
    if os.path.exists(crash_log):
        with open(crash_log, "r", encoding="utf-8") as f:
            print("CRASH LOG DETECTED:\n", f.read())
    else:
        print("SUCCESS: No crash.log detected. App launched normally!")

    # Check tasklist
    output = subprocess.check_output('tasklist /fi "IMAGENAME eq BSLabTool.exe"', shell=True).decode()
    print("Tasklist output:\n", output)
