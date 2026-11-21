import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    p = subprocess.run([adb] + args, capture_output=True, text=True, timeout=10)
    return p.stdout.strip()

print("airplane_mode_on:", run_adb(["shell", "settings", "get", "global", "airplane_mode_on"]), flush=True)
print("cell_on:", run_adb(["shell", "settings", "get", "global", "cell_on"]), flush=True)
print("airplane_mode_radios:", run_adb(["shell", "settings", "get", "global", "airplane_mode_radios"]), flush=True)
print("radio imei from service:", run_adb(["shell", "service", "call", "iphonesubinfo", "1"]), flush=True)
print("dumpsys phone / radio:", flush=True)
out = run_adb(["shell", "dumpsys", "phone"])
for line in out.splitlines():
    if any(k in line.lower() for k in ["imei", "radiopower", "radio state", "power state", "cardstate", "subinfo"]):
        print(" ", line.strip(), flush=True)
