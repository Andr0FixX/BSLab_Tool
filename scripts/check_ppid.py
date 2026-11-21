import subprocess

pids = [1336, 1120]
for p in pids:
    out = subprocess.run(f'wmic process where "ProcessId={p}" get ParentProcessId,CommandLine,CreationDate /format:list', shell=True, capture_output=True, text=True)
    print(f"PID {p} Info:\n", out.stdout)
