import subprocess

out = subprocess.check_output('powercfg /q', shell=True, text=True, errors='ignore')
in_pcie = False
for line in out.splitlines():
    if "Subgroup GUID" in line and ("501a4d13" in line.lower() or "pci" in line.lower()):
        in_pcie = True
        print(line)
    elif "Subgroup GUID" in line:
        in_pcie = False
    elif in_pcie:
        print(line)
