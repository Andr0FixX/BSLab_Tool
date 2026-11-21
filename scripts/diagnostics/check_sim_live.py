import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

def run_adb(args):
    p = subprocess.run([adb] + args, capture_output=True, text=True, timeout=10)
    return p.stdout.strip()

out = run_adb(["shell", "dumpsys", "telephony.registry"])
for line in out.splitlines():
    if any(k in line for k in ["mSimState", "mCardId", "mSubId", "carrierId", "displayName", "mRadioPowerState", "mVoiceRegState", "mDataRegState"]):
        print(line.strip(), flush=True)
