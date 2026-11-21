import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_su(cmd):
    p = subprocess.run([adb, "shell", f"su -c '{cmd}'"], capture_output=True, text=True, timeout=15)
    return p.stdout.strip()

print("Searching in modemst1 / modemst2...", flush=True)
for part in ["modemst1", "modemst2", "fsg", "persist"]:
    out1 = run_su(f"strings /dev/block/by-name/{part} | grep '0044'")
    out2 = run_su(f"strings /dev/block/by-name/{part} | grep '8633'")
    print(f"Partition {part}:", flush=True)
    if out1: print(f"  found '0044': {out1[:100]}", flush=True)
    if out2: print(f"  found '8633': {out2[:100]}", flush=True)
    if not out1 and not out2: print("  neither string found directly in text.", flush=True)
