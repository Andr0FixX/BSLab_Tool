import subprocess
import os

exe_path = r"c:\BSLab_Tool\BSLab_Tool.exe"
print(f"Checking if {exe_path} exists: {os.path.exists(exe_path)}")
try:
    proc = subprocess.Popen([exe_path], cwd=r"c:\BSLab_Tool", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = proc.communicate(timeout=3)
        print("Exit code:", proc.returncode)
        print("Stdout:", stdout)
        print("Stderr:", stderr)
    except subprocess.TimeoutExpired:
        print("Process is running cleanly! PID:", proc.pid)
except Exception as ex:
    print("Exception running exe:", ex)
