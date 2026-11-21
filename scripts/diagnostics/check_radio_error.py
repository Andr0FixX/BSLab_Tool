import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_cmd(cmd):
    p = subprocess.run([adb, "shell", cmd], capture_output=True, text=True, timeout=10)
    return p.stdout.strip(), p.stderr.strip()

print("Restarting vendor.qcrild / radio...", flush=True)
run_cmd("su -c 'stop ril-daemon; stop vendor.qcrild; start vendor.qcrild; start ril-daemon'")

print("Getting logcat for radio...", flush=True)
out, _ = run_cmd("su -c 'logcat -b radio -d -t 100'")
for line in out.splitlines():
    if any(k in line.lower() for k in ["power", "fail", "error", "nv", "imei", "state", "modem", "qmi", "reject", "qcril"]):
        print(line, flush=True)
