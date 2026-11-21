import ctypes
from ctypes import wintypes
import os
import sys
import time
import winreg

print("=" * 60)
print("DUAL-WATCHDOG SUSPEND-AND-DESTROY MALWARE KILLER")
print("=" * 60)

PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_ALL_ACCESS = 0x1F0FFF

kernel32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll

def get_process_path(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h: return None
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    res = kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(h)
    return buf.value if res else None

# Enumerate all processes
import subprocess
try:
    tl = subprocess.check_output('tasklist /FO CSV /NH', shell=True, text=True)
except Exception as e:
    print(f"Tasklist failed: {e}")
    sys.exit(1)

rogue_pids = []
for line in tl.strip().splitlines():
    parts = [p.strip('"') for p in line.split('","')]
    if len(parts) >= 2:
        try:
            pid = int(parts[1])
            path = get_process_path(pid)
            if path:
                low = path.lower()
                if "themes\\explorer.exe" in low:
                    rogue_pids.append((pid, path, "Fake Explorer"))
                elif "resources\\svchost.exe" in low:
                    rogue_pids.append((pid, path, "Fake Svchost"))
                elif "resources\\spoolsv.exe" in low:
                    rogue_pids.append((pid, path, "Fake Spoolsv"))
                elif "icsys.icn.exe" in low:
                    rogue_pids.append((pid, path, "Fake ICSys"))
        except:
            pass

print(f"Found {len(rogue_pids)} active rogue watchdog processes:")
for pid, path, label in rogue_pids:
    print(f"  PID {pid:6d} [{label}]: {path}")

# Step 1: Suspend ALL rogue processes simultaneously
print("\n[PHASE 1] Freezing (Suspending) all rogue processes...")
suspended_handles = []
for pid, path, label in rogue_pids:
    h = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if h:
        status = ntdll.NtSuspendProcess(h)
        if status == 0:
            print(f"  [+] FROZEN PID {pid} ({label})")
            suspended_handles.append((h, pid, label))
        else:
            print(f"  [-] Failed to freeze PID {pid}, status={status}")
            kernel32.CloseHandle(h)
    else:
        err = kernel32.GetLastError()
        print(f"  [-] OpenProcess failed for PID {pid}, error={err}")

# Step 2: Now that all are completely frozen, delete Registry Persistence
print("\n[PHASE 2] Cleaning Registry Persistence...")
for root, sub in [
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
]:
    root_str = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
    try:
        with winreg.OpenKey(root, sub, 0, winreg.KEY_ALL_ACCESS) as k:
            for vn in ["Explorer", "Svchost", "spoolsv", "icsys"]:
                try:
                    winreg.DeleteValue(k, vn)
                    print(f"  [+] Deleted registry value: {root_str}\\{sub}\\{vn}")
                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(f"  [-] Error deleting {vn} in {root_str}\\{sub}: {e}")
    except Exception as e:
        pass

# Step 3: Terminate all suspended processes
print("\n[PHASE 3] Terminating all frozen processes...")
for h, pid, label in suspended_handles:
    ret = kernel32.TerminateProcess(h, 0)
    print(f"  [+] Terminated PID {pid} ({label}): {'SUCCESS' if ret else 'FAILED'}")
    kernel32.CloseHandle(h)

time.sleep(1)

# Step 4: Delete the files from disk
print("\n[PHASE 4] Deleting malware files from disk...")
targets = [
    r"C:\Windows\Resources\Themes\explorer.exe",
    r"C:\Windows\Resources\Themes\icsys.icn.exe",
    r"C:\Windows\Resources\Themes\icsys.icn",
    r"C:\Windows\Resources\svchost.exe",
    r"C:\Windows\Resources\spoolsv.exe"
]

for t in targets:
    if os.path.exists(t):
        try:
            # Strip attributes
            subprocess.run(f'attrib -r -s -h "{t}"', shell=True, capture_output=True)
            os.remove(t)
            print(f"  [+] DELETED: {t}")
        except Exception as e:
            # Try renaming first then delete
            try:
                trash_path = t + ".deleted_" + str(int(time.time()))
                os.rename(t, trash_path)
                os.remove(trash_path)
                print(f"  [+] DELETED via rename: {t}")
            except Exception as e2:
                print(f"  [-] FAILED to delete {t}: {e} / rename failed: {e2}")
    else:
        print(f"  [+] ALREADY GONE: {t}")

print("\n[PHASE 5] Verification...")
remaining = [t for t in targets if os.path.exists(t)]
if remaining:
    print("  [!] WARNING: Remaining files:")
    for r in remaining:
        print(f"      - {r}")
else:
    print("  [SUCCESS] All malware files completely destroyed!")

print("Eradication script complete.")
