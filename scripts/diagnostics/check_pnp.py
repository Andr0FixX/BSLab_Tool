import subprocess

ps_script = """
Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like "*05C6*" } | Select-Object FriendlyName, InstanceId, Status, Class | Format-Table -AutoSize
"""

p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=10)
print(p.stdout)
