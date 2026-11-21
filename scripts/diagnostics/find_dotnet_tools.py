import os

for path in [r"C:\Program Files\dotnet", r"C:\Program Files (x86)\dotnet", r"C:\Windows\Microsoft.NET\Framework64"]:
    if os.path.exists(path):
        print("Path exists:", path)
        for root, dirs, files in os.walk(path):
            if "MSBuild.exe" in files or "dotnet.exe" in files or "csc.exe" in files:
                print("  found tool in:", root)
            if "sdk" in dirs:
                print("  found sdk dir:", os.path.join(root, "sdk"))
                print("    subdirs:", os.listdir(os.path.join(root, "sdk")))
