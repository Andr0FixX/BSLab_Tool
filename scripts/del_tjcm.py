import subprocess

cmd = r'powershell -Command "Start-Process cmd.exe -ArgumentList \'/c del /f /q /a C:\Windows\Resources\Themes\tjcm.cmn\' -Verb RunAs -Wait"'
subprocess.run(cmd, shell=True)
print("Deleted elevated.")
