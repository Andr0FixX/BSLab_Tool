import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    p = subprocess.run([adb] + args, capture_output=True, text=True, timeout=10)
    return p.stdout.strip(), p.stderr.strip()

print("Setting radio power true...", flush=True)
out, err = run_adb(["shell", "cmd", "phone", "set-radio-power", "true"])
print("cmd phone:", out, err, flush=True)

print("Checking radio state...", flush=True)
out, _ = run_adb(["shell", "dumpsys", "telephony.registry"])
for line in out.splitlines():
    if "mRadioPowerState" in line:
        print(line, flush=True)
