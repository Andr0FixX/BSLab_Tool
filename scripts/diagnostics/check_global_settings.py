import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    p = subprocess.run([adb] + args, capture_output=True, text=True, timeout=10)
    return p.stdout.strip()

out = run_adb(["shell", "settings", "list", "global"])
for line in out.splitlines():
    if any(k in line.lower() for k in ["radio", "phone", "cell", "sim", "network", "lte", "cdma", "gsm", "carrier"]):
        print(line, flush=True)
