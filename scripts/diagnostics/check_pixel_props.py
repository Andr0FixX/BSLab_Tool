import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    p = subprocess.run([adb] + args, capture_output=True, text=True, timeout=10)
    return p.stdout.strip()

props = run_adb(["shell", "getprop"])
for line in props.splitlines():
    if any(k in line.lower() for k in ["imei", "meid", "serial", "radio", "qcom", "modem", "sku", "baseband"]):
        print(line, flush=True)
