import subprocess

res = subprocess.run([r"c:\BSLab_Tool\BSLab_Tool.exe"], cwd=r"c:\BSLab_Tool", capture_output=True, text=True)
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
