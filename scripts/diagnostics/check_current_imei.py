import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_su(cmd):
    p = subprocess.run([adb, "shell", f"su -c '{cmd}'"], capture_output=True, text=True, timeout=15)
    return p.stdout.strip()

print("--- IPHONESUBINFO ---", flush=True)
print(run_su("service call iphonesubinfo 1"), flush=True)
print(run_su("service call iphonesubinfo 3"), flush=True)

print("--- DUMPSYS IPHONESUBINFO ---", flush=True)
out = run_su("dumpsys iphonesubinfo")
for line in out.splitlines():
    if any(k in line.lower() for k in ["imei", "device id", "subscriber"]):
        print(" ", line.strip(), flush=True)

print("--- RADIO BOOT LOGCAT ---", flush=True)
out = run_su("logcat -b radio -d | grep -iE 'imei|radiostate|setradiopower|cardstate|icc'")
for line in out.splitlines()[-25:]:
    print(" ", line.strip(), flush=True)
