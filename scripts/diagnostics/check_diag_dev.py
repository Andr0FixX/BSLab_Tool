import subprocess

adb = r"C:\BSLab_Tool\resources\platform-tools\adb.exe"

script = """
import os, struct, time

# Check if /dev/diag exists
if not os.path.exists('/dev/diag'):
    print('no /dev/diag')
    exit()

print('/dev/diag exists!')
try:
    fd = os.open('/dev/diag', os.O_RDWR)
    print('opened /dev/diag fd:', fd)
    os.close(fd)
except Exception as e:
    print('error opening /dev/diag:', e)
"""

p = subprocess.run([adb, "shell", f"su -c \"python3 -c \\\"{script}\\\\\"\""], capture_output=True, text=True, timeout=10)
print("output:", p.stdout, p.stderr)
