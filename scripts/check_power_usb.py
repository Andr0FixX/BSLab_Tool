import subprocess

out = subprocess.check_output('powercfg /q', shell=True, text=True, errors='ignore')
in_usb = False
for line in out.splitlines():
    if "Subgroup GUID" in line and ("2a737441" in line.lower() or "usb" in line.lower()):
        in_usb = True
        print(line)
    elif "Subgroup GUID" in line:
        in_usb = False
    elif in_usb:
        print(line)
        if "Power Setting GUID" in line and not any(x in line.lower() for x in ["usb", "selective"]):
            pass
