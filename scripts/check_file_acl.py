import subprocess
import os

for f in [r"C:\Windows\Resources\Themes\explorer.exe", r"C:\Windows\Resources\svchost.exe"]:
    print("="*50)
    print("FILE:", f)
    print("Exists:", os.path.exists(f))
    if os.path.exists(f):
        # Check icacls
        ic = subprocess.run(f'icacls "{f}"', shell=True, capture_output=True, text=True)
        print("ICACLS:\n", ic.stdout)
        # Check attrib
        at = subprocess.run(f'attrib "{f}"', shell=True, capture_output=True, text=True)
        print("ATTRIB:\n", at.stdout)
