import subprocess
import os

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    p = subprocess.run([adb] + args, capture_output=True, text=True, timeout=15)
    return p.stdout.strip()

print("Dumping modemst1 and modemst2 via su...", flush=True)
run_adb(["shell", "su -c 'dd if=/dev/block/by-name/modemst1 of=/data/local/tmp/st1.bin bs=1M'"])
run_adb(["shell", "su -c 'dd if=/dev/block/by-name/modemst2 of=/data/local/tmp/st2.bin bs=1M'"])
run_adb(["shell", "su -c 'chmod 666 /data/local/tmp/st1.bin /data/local/tmp/st2.bin'"])

os.makedirs(r"C:\BSLab_Tool\scratch", exist_ok=True)
run_adb(["pull", "/data/local/tmp/st1.bin", r"C:\BSLab_Tool\scratch\st1.bin"])
run_adb(["pull", "/data/local/tmp/st2.bin", r"C:\BSLab_Tool\scratch\st2.bin"])

for name in ["st1.bin", "st2.bin"]:
    path = os.path.join(r"C:\BSLab_Tool\scratch", name)
    if os.path.exists(path):
        data = open(path, "rb").read()
        print(f"{name}: size={len(data)} bytes", flush=True)
        # Search for 0044 pattern or any IMEI pattern
        # Look for 0x08, 0x0a, 0x40
        for i in range(len(data) - 8):
            if data[i] in (0x08, 0x0A) and data[i+1] == 0x40:
                print(f"  {name} candidate at offset 0x{i:06X}: {data[i:i+10].hex()}", flush=True)
