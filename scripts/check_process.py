import subprocess
import os

try:
    res = subprocess.run(["tasklist"], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if "bslab" in line.lower() or "dotnet" in line.lower():
            print(line)
except Exception as e:
    print(e)
