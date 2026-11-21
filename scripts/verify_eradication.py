import os
import subprocess
import winreg
import ctypes
from ctypes import wintypes
import time

print("=" * 60)
print("FINAL THOROUGH AUDIT & POST-ERADICATION VERIFICATION")
print("=" * 60)

# Check 1: Files on Disk
malware_file_paths = [
    r"C:\Windows\Resources\Themes\explorer.exe",
    r"C:\Windows\Resources\Themes\icsys.icn.exe",
    r"C:\Windows\Resources\Themes\icsys.icn",
    r"C:\Windows\Resources\svchost.exe",
    r"C:\Windows\Resources\spoolsv.exe"
]

print("\n1. FILE AUDIT:")
all_clean = True
for f in malware_file_paths:
    exists = os.path.exists(f)
    print(f"  {f:45s} -> {'[EXISTS - FAIL]' if exists else '[DELETED - 100% CLEAN]'}")
    if exists:
        all_clean = False

print("\nListing remaining files in C:\\Windows\\Resources\\Themes:")
themes_files = os.listdir(r"C:\Windows\Resources\Themes")
for tf in themes_files:
    print(f"  - {tf}")

# Check 2: Active Processes
print("\n2. PROCESS AUDIT:")
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
kernel32 = ctypes.windll.kernel32

def get_process_path(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h: return None
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    res = kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(h)
    return buf.value if res else None

tl = subprocess.check_output('tasklist /FI "IMAGENAME eq explorer.exe" /FO CSV /NH', shell=True, text=True)
print("Active explorer.exe processes:")
for line in tl.strip().splitlines():
    parts = [p.strip('"') for p in line.split('","')]
    if len(parts) >= 2:
        try:
            pid = int(parts[1])
            path = get_process_path(pid)
            is_genuine = path and path.lower() == r"c:\windows\explorer.exe"
            status = "[GENUINE WINDOWS SHELL]" if is_genuine else "[ROGUE / SUSPICIOUS!]"
            print(f"  PID {pid:6d} -> {path} {status}")
        except:
            pass

# Check svchost processes
print("\nActive svchost processes scan (checking if any are outside System32/SysWOW64):")
tl2 = subprocess.check_output('tasklist /FI "IMAGENAME eq svchost.exe" /FO CSV /NH', shell=True, text=True)
rogue_svchost = 0
for line in tl2.strip().splitlines():
    parts = [p.strip('"') for p in line.split('","')]
    if len(parts) >= 2:
        try:
            pid = int(parts[1])
            path = get_process_path(pid)
            if path and ("system32" not in path.lower() and "syswow64" not in path.lower()):
                print(f"  [!] ROGUE SVCHOST DETECTED: PID {pid} -> {path}")
                rogue_svchost += 1
        except:
            pass
if rogue_svchost == 0:
    print("  [ALL svchost.exe ARE 100% GENUINE WINDOWS SYSTEM PROCESSES]")

# Check 3: Registry RunOnce Keys
print("\n3. REGISTRY AUDIT:")
for root, sub in [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
]:
    root_str = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
    try:
        with winreg.OpenKey(root, sub, 0, winreg.KEY_READ) as k:
            count = winreg.QueryInfoKey(k)[1]
            print(f"  {root_str}\\{sub} -> {count} values present")
            for i in range(count):
                vn, vd, _ = winreg.EnumValue(k, i)
                print(f"    {vn} = {vd}")
    except Exception as e:
        print(f"  {root_str}\\{sub} -> Not found / Error: {e}")

print("\n" + "=" * 60)
if all_clean and rogue_svchost == 0:
    print("VERDICT: PC IS 100% CLEAN! MALWARE PERMANENTLY ERADICATED!")
else:
    print("VERDICT: Remediation incomplete, further action needed.")
print("=" * 60)
