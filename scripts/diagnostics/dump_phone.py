import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

p = subprocess.run([adb, "shell", "dumpsys", "phone"], capture_output=True, text=True, timeout=15)
with open(r"C:\BSLab_Tool\scratch\dumpsys_phone.txt", "w", encoding="utf-8") as f:
    f.write(p.stdout)

print("Saved dumpsys_phone.txt! Lines:", len(p.stdout.splitlines()), flush=True)

with open(r"C:\BSLab_Tool\scratch\dumpsys_phone.txt", "r", encoding="utf-8") as f:
    for line in f:
        if any(k in line for k in ["mRadioPower", "RadioState", "mImei", "mMeid", "cardState", "UiccCard", "mSimState", "mCarrierName"]):
            print(" ", line.strip(), flush=True)
