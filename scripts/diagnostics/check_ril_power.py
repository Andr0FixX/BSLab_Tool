import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_cmd(cmd):
    p = subprocess.run([adb, "shell", f"su -c '{cmd}'"], capture_output=True, text=True, timeout=15)
    return p.stdout.strip()

print("--- Telephony Radio State Logs ---", flush=True)
out = run_cmd("logcat -b radio -d | grep -iE 'setradiopower|radiostate|radiopowerstate|modem|ril'")
for line in out.splitlines()[-40:]:
    print(line, flush=True)
