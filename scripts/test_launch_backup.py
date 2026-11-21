import ctypes
from ctypes import wintypes
import time
import os
import subprocess

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

print("Spawning elevated BSLabTool.exe to verify GUI runtime...")
res = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
if not res:
    print("ShellExecuteExW failed:", ctypes.windll.kernel32.GetLastError())
else:
    print("Process handle:", sei.hProcess)
    time.sleep(3)
    # Check if still running
    tl = subprocess.check_output('tasklist /FI "IMAGENAME eq BSLabTool.exe" /FO CSV /NH', shell=True, text=True)
    if "BSLabTool.exe" in tl:
        print("[SUCCESS] BSLabTool.exe is running actively on desktop with 0 crash!")
    else:
        print("[!] BSLabTool exited prematurely. Checking crash.log...")
        crash = r"C:\BSLab_Tool\dist_new\crash.log"
        if os.path.exists(crash):
            with open(crash, 'r') as f: print(f.read())
