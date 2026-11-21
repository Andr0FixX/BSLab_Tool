import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_su(cmd):
    p = subprocess.run([adb, "shell", f"su -c '{cmd}'"], capture_output=True, text=True, timeout=15)
    return p.stdout.strip(), p.stderr.strip()

print("--- Check by-name partitions ---", flush=True)
out, err = run_su("ls -l /dev/block/by-name/")
for line in out.splitlines():
    if any(k in line for k in ["modem", "fsg", "fsc", "persist"]):
        print(line, flush=True)

print("--- Check modemst1 & modemst2 header ---", flush=True)
out, _ = run_su("xxd -l 64 /dev/block/by-name/modemst1")
print("modemst1 (first 64 bytes):", out, flush=True)
out, _ = run_su("xxd -l 64 /dev/block/by-name/modemst2")
print("modemst2 (first 64 bytes):", out, flush=True)

print("--- Check radio logcat / dmesg ---", flush=True)
out, _ = run_su("logcat -b radio -d | tail -n 25")
print(out, flush=True)
