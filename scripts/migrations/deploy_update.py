import subprocess
import time
import shutil
import os

ps_cmd = 'Get-Process | Where-Object { $_.Path -like "*BSLab*" -or $_.ProcessName -like "*BSLab*" } | Stop-Process -Force'
subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)
time.sleep(1.5)

src = r'C:\BSLab_Tool\src\ui\BSLabTool.UI\bin\Release\net8.0-windows'
dst = r'C:\BSLab_Tool\dist_new'

for fname in os.listdir(src):
    s = os.path.join(src, fname)
    d = os.path.join(dst, fname)
    try:
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
        print(f"Copied {fname}")
    except Exception as e:
        print(f"Error copying {fname}: {e}")

print("[+] Deployment complete!")
