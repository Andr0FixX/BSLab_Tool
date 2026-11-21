import subprocess
import os

adb_path = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    cmd = [adb_path] + args
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return p.stdout.strip(), p.stderr.strip(), p.returncode
    except Exception as e:
        return "", str(e), -1

print("--- ADB DEVICES ---")
out, err, code = run_adb(["devices"])
print(out)
if err: print("err:", err)

print("--- DEVICE PROPERTIES ---")
for prop in ["ro.product.model", "ro.product.name", "ro.build.version.release", "gsm.version.baseband"]:
    val, _, _ = run_adb(["shell", "getprop", prop])
    print(f"{prop}: {val}")

print("--- RADIO STATE ---")
out, _, _ = run_adb(["shell", "dumpsys", "telephony.registry"])
for line in out.splitlines():
    if any(k in line for k in ["mRadioPowerState", "mVoiceRegState", "mDataRegState", "mServiceState"]):
        print(line.strip())
