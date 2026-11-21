import subprocess
import time

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_cmd(cmd):
    p = subprocess.run([adb, "shell", f"su -c '{cmd}'"], capture_output=True, text=True, timeout=15)
    return p.stdout.strip(), p.stderr.strip()

print("Current ro.bootmode:", run_cmd("getprop ro.bootmode")[0], flush=True)

print("Setting ro.bootmode to normal via resetprop...", flush=True)
run_cmd("resetprop ro.bootmode normal")
print("New ro.bootmode:", run_cmd("getprop ro.bootmode")[0], flush=True)

print("Restarting vendor.qcrild...", flush=True)
run_cmd("stop vendor.qcrild; start vendor.qcrild")
time.sleep(3)

print("Checking mRadioPowerState...", flush=True)
out, _ = run_cmd("dumpsys telephony.registry | grep -i mRadioPowerState")
print("dumpsys:", out, flush=True)
