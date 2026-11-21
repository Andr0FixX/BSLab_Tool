import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

p = subprocess.run([adb, "shell", "logcat", "-b", "radio", "-d"], capture_output=True, text=True, timeout=15)
with open(r"C:\BSLab_Tool\scratch\logcat_radio.txt", "w", encoding="utf-8") as f:
    f.write(p.stdout)

print("Saved logcat_radio.txt! Total lines:", len(p.stdout.splitlines()), flush=True)

# Search for critical errors or radio power calls
with open(r"C:\BSLab_Tool\scratch\logcat_radio.txt", "r", encoding="utf-8") as f:
    for line in f:
        if any(k in line.lower() for k in ["power", "radiostate", "error", "fail", "qcril", "vendor.qti", "sim"]):
            # filter out noisy lines
            if not any(skip in line for line in ["pollnetstat", "getactivityinfo", "scree on", "screen off"]):
                print(" ", line.strip(), flush=True)
