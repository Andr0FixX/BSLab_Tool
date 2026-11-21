import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

p = subprocess.run([adb, "shell", "su", "-c", "dmesg"], capture_output=True, text=True, timeout=15)
with open(r"C:\BSLab_Tool\scratch\dmesg.txt", "w", encoding="utf-8") as f:
    f.write(p.stdout)

print("Saved dmesg.txt! Lines:", len(p.stdout.splitlines()), flush=True)

with open(r"C:\BSLab_Tool\scratch\dmesg.txt", "r", encoding="utf-8") as f:
    for line in f:
        l = line.lower()
        if any(k in l for k in ["mpss", "subsys-restart", "modem", "qmi", "qti", "ipa", "rmnet", "esoc"]):
            if not any(skip in l for skip in ["battery", "thermal", "cpu", "gpu"]):
                print(" ", line.strip(), flush=True)
