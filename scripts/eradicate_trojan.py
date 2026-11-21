import os
import sys
import subprocess
import winreg
import ctypes
from ctypes import wintypes
import time

print("=" * 60)
print("BS LAB TOOL - TROJAN / MALWARE ERADICATION SCRIPT")
print("Target: Miracle Loader / Fake explorer.exe / icsys")
print("=" * 60)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
kernel32 = ctypes.windll.kernel32

def get_process_path(pid):
    hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not hProcess:
        return None
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    res = kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(hProcess)
    if res:
        return buf.value
    return None

# Step 1: Find and kill rogue processes
print("\n[STEP 1] Scanning for rogue processes...")
try:
    tl_out = subprocess.check_output('tasklist /FO CSV /NH', shell=True, text=True)
    for line in tl_out.strip().splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            img_name, pid_str = parts[0].lower(), parts[1]
            try:
                pid = int(pid_str)
                path = get_process_path(pid)
                if path:
                    norm_path = path.lower()
                    # Check if rogue
                    is_rogue = False
                    if "explorer.exe" in img_name and "resources\\themes" in norm_path:
                        is_rogue = True
                    elif "svchost.exe" in img_name and "system32" not in norm_path and "syswow64" not in norm_path:
                        is_rogue = True
                    elif "icsys" in img_name or "icsys" in norm_path:
                        is_rogue = True
                    
                    if is_rogue:
                        print(f"  [!] ROGUE PROCESS FOUND: PID {pid} -> {path}")
                        print(f"      Terminating PID {pid}...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True, text=True)
                        time.sleep(0.5)
                        print(f"      [OK] Killed PID {pid}")
            except Exception as e:
                pass
except Exception as e:
    print(f"Error checking processes: {e}")

# Step 2: Clean Registry Persistence (RunOnce & Run)
print("\n[STEP 2] Cleaning Registry Persistence...")

reg_targets = [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce", ["Explorer", "Svchost"]),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", ["Explorer", "Svchost"]),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", ["Explorer", "Svchost"]),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", ["Explorer", "Svchost", "icsys"]),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", ["Explorer", "Svchost", "icsys"]),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", ["Explorer", "Svchost", "icsys"]),
]

for root, subkey, val_names in reg_targets:
    root_name = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            for val_name in val_names:
                try:
                    val_data, _ = winreg.QueryValueEx(key, val_name)
                    print(f"  Found persistence entry: {root_name}\\{subkey} -> {val_name} = {val_data}")
                    winreg.DeleteValue(key, val_name)
                    print(f"  [OK] Successfully deleted registry value: {val_name}")
                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(f"  [!] Failed to delete value {val_name}: {e}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  Note opening {root_name}\\{subkey}: {e}")

# Also check for any values in RunOnce that contain 'resources\themes'
for root, subkey in [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
]:
    root_name = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            num = winreg.QueryInfoKey(key)[1]
            to_delete = []
            for i in range(num):
                vn, vd, _ = winreg.EnumValue(key, i)
                if any(x in str(vd).lower() for x in ['themes\\explorer', 'resources\\svchost', 'icsys']):
                    to_delete.append(vn)
            for vn in to_delete:
                winreg.DeleteValue(key, vn)
                print(f"  [OK] Cleaned rogue entry: {root_name}\\{subkey} -> {vn}")
    except Exception:
        pass

# Step 3: Remove attributes and delete malicious files
print("\n[STEP 3] Deleting Malicious Files...")

files_to_delete = [
    r"C:\Windows\Resources\Themes\explorer.exe",
    r"C:\Windows\Resources\Themes\icsys.icn.exe",
    r"C:\Windows\Resources\Themes\icsys.icn",
    r"C:\Windows\Resources\svchost.exe",
]

# Check directory C:\Windows\Resources for any unexpected files
res_dir = r"C:\Windows\Resources"
if os.path.exists(res_dir):
    for f in os.listdir(res_dir):
        fp = os.path.join(res_dir, f)
        if os.path.isfile(fp):
            if f.lower().endswith(".exe") or f.lower().endswith(".icn") or f.lower().endswith(".bat") or f.lower().endswith(".vbs"):
                if fp not in files_to_delete:
                    files_to_delete.append(fp)

for fpath in files_to_delete:
    if os.path.exists(fpath):
        print(f"  Processing: {fpath}")
        # Strip Read-Only, System, Hidden attributes
        try:
            subprocess.run(f'attrib -r -s -h "{fpath}"', shell=True, capture_output=True)
            time.sleep(0.2)
            os.remove(fpath)
            print(f"  [OK] File deleted: {fpath}")
        except Exception as e:
            # Fallback force delete via cmd
            res = subprocess.run(f'cmd /c del /f /q /a "{fpath}"', shell=True, capture_output=True, text=True)
            if not os.path.exists(fpath):
                print(f"  [OK] File force-deleted via cmd: {fpath}")
            else:
                print(f"  [!] Failed to delete {fpath}: {e} / {res.stderr}")
    else:
        print(f"  Not present (already clean): {fpath}")

# Step 4: Verification
print("\n" + "=" * 60)
print("[STEP 4] POST-CLEANUP VERIFICATION")
print("=" * 60)

remaining_files = [f for f in files_to_delete if os.path.exists(f)]
if remaining_files:
    print("  [!] WARNING: Some files still exist:")
    for rf in remaining_files:
        print(f"      - {rf}")
else:
    print("  [SUCCESS] All malicious files have been completely eliminated from disk!")

# Check running explorer processes
print("\nChecking active Explorer processes:")
tl_out = subprocess.check_output('tasklist /FI "IMAGENAME eq explorer.exe" /FO CSV /NH', shell=True, text=True)
for line in tl_out.strip().splitlines():
    parts = [p.strip('"') for p in line.split('","')]
    if len(parts) >= 2:
        name, pid_str = parts[0], parts[1]
        try:
            pid = int(pid_str)
            path = get_process_path(pid)
            print(f"  PID: {pid:6d} | {name} | Path: {path}")
        except Exception as e:
            pass

print("\nCleanup operation finished.")
