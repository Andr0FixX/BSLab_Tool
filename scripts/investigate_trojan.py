import ctypes
from ctypes import wintypes
import os
import winreg
import subprocess
import glob

print("="*60)
print("1. CHECKING RUNNING EXPLORER PROCESSES")
print("="*60)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
kernel32 = ctypes.windll.kernel32

def get_process_path(pid):
    hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not hProcess:
        return f"Access Denied (Error {kernel32.GetLastError()})"
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    res = kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(hProcess)
    if res:
        return buf.value
    return f"Query Failed (Error {kernel32.GetLastError()})"

# Run tasklist to get all explorer.exe PIDs
try:
    tl_out = subprocess.check_output('tasklist /FI "IMAGENAME eq explorer.exe" /FO CSV /NH', shell=True, text=True)
    for line in tl_out.strip().splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            name, pid_str = parts[0], parts[1]
            try:
                pid = int(pid_str)
                path = get_process_path(pid)
                print(f"PID: {pid:6d} | Image: {name} | Path: {path}")
            except Exception as e:
                print(f"Error parsing PID {pid_str}: {e}")
except Exception as e:
    print(f"Tasklist error: {e}")

print("\n" + "="*60)
print("2. CHECKING REGISTRY RUN & STARTUP KEYS")
print("="*60)

reg_locations = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"),
]

for root, subkey in reg_locations:
    root_name = "HKCU" if root == winreg.HKEY_CURRENT_USER else "HKLM"
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as key:
            num_vals = winreg.QueryInfoKey(key)[1]
            print(f"\n--- {root_name}\\{subkey} ({num_vals} values) ---")
            for i in range(num_vals):
                val_name, val_data, val_type = winreg.EnumValue(key, i)
                # Highlight anything suspicious
                suspicious = any(x in str(val_data).lower() or x in str(val_name).lower() for x in ['theme', 'icsys', 'miracle', 'temp', 'roma', 'explorer'])
                flag = " [!] SUSPICIOUS" if suspicious else ""
                print(f"  {val_name} = {val_data}{flag}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  Error reading {root_name}\\{subkey}: {e}")

print("\n" + "="*60)
print("3. CHECKING STARTUP FOLDERS")
print("="*60)

startup_paths = [
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
    os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
]

for sp in startup_paths:
    print(f"\nChecking: {sp}")
    if os.path.exists(sp):
        files = os.listdir(sp)
        for f in files:
            full = os.path.join(sp, f)
            print(f"  - {f} ({os.path.getsize(full)} bytes)")
        if not files:
            print("  (Empty)")
    else:
        print("  (Folder not found)")

print("\n" + "="*60)
print("4. CHECKING C:\\Windows\\Resources\\Themes FOR SUSPICIOUS FILES")
print("="*60)

themes_dir = r"C:\Windows\Resources\Themes"
if os.path.exists(themes_dir):
    for f in os.listdir(themes_dir):
        fp = os.path.join(themes_dir, f)
        if os.path.isfile(fp):
            stat = os.stat(fp)
            print(f"  File: {f:20s} Size: {stat.st_size:10d} bytes | Mode: {oct(stat.st_mode)}")
        else:
            print(f"  Dir : {f}")

print("\n" + "="*60)
print("5. CHECKING SCHEDULED TASKS FOR THEMES OR ICSYS OR EXPLORER")
print("="*60)
try:
    sch = subprocess.check_output('schtasks /query /fo CSV /v', shell=True, text=True, errors='ignore')
    found_tasks = []
    for line in sch.splitlines():
        lower_line = line.lower()
        if 'theme' in lower_line or 'icsys' in lower_line or 'c:\\windows\\resources' in lower_line or 'miracle' in lower_line:
            found_tasks.append(line)
    if found_tasks:
        print(f"Found {len(found_tasks)} matched scheduled task lines:")
        for t in found_tasks:
            print(f"  {t}")
    else:
        print("No suspicious scheduled tasks matching keywords found.")
except Exception as e:
    print(f"Scheduled tasks check error: {e}")
