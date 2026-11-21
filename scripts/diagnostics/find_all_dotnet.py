import os

for drive in ["C:\\", "D:\\"]:
    if not os.path.exists(drive): continue
    for root, dirs, files in os.walk(drive):
        if "dotnet.exe" in files:
            print(os.path.join(root, "dotnet.exe"), flush=True)
        # Prune heavy non-relevant directories
        dirs[:] = [d for d in dirs if d.lower() not in ["windows", "$recycle.bin", "system volume information", "node_modules", "vendor", ".git", "appdata"]]
