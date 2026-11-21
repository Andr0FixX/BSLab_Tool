import os
import shutil
import subprocess
import time

print("[*] Terminating any existing BSLab processes...")
for proc in ["bslabtool.exe", "bslab_tool.exe"]:
    subprocess.run(["taskkill", "/F", "/IM", proc, "/T"], capture_output=True)

time.sleep(1)

bin_dir = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\bin\Release\net8.0-windows"
targets = [
    r"c:\BSLab_Tool",
    r"c:\BSLab_Tool\dist_release",
    r"c:\BSLab_Tool\dist_new",
    r"c:\BSLab_Tool\dist_clean",
    r"c:\BSLab_Tool\src\ui\BSLabTool.UI\bin\Debug\net8.0-windows",
]

files_to_copy = [
    "BSLabTool.dll",
    "BSLabTool.exe",
    "BSLabTool.pdb",
    "BSLabTool.deps.json",
    "BSLabTool.runtimeconfig.json",
    "BSLabCore.dll"
]

for t in targets:
    if os.path.exists(t):
        for f in files_to_copy:
            src = os.path.join(bin_dir, f)
            dst = os.path.join(t, f)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                    print(f"Copied {f} -> {t}")
                except Exception as ex:
                    print(f"Failed {f} -> {t}: {ex}")

# Also copy BSLabTool.exe to BSLab_Tool.exe
for t in targets:
    src_exe = os.path.join(bin_dir, "BSLabTool.exe")
    dst_alias = os.path.join(t, "BSLab_Tool.exe")
    if os.path.exists(src_exe) and os.path.exists(t):
        try:
            shutil.copy2(src_exe, dst_alias)
            print(f"Copied BSLab_Tool.exe alias -> {t}")
        except Exception as ex:
            print(f"Failed BSLab_Tool.exe -> {t}: {ex}")

# Sync drivers repository across distribution targets
drivers_src = r"c:\BSLab_Tool\drivers"
if os.path.exists(drivers_src):
    for dist_target in [r"c:\BSLab_Tool\dist_new", r"c:\BSLab_Tool\dist_release", r"c:\BSLab_Tool\dist_clean"]:
        if os.path.exists(dist_target):
            dist_drivers = os.path.join(dist_target, "drivers")
            try:
                if os.path.exists(dist_drivers):
                    shutil.rmtree(dist_drivers)
                shutil.copytree(drivers_src, dist_drivers)
                print(f"Synced drivers/ -> {dist_drivers}")
            except Exception as ex:
                print(f"Failed drivers -> {dist_target}: {ex}")

# Update Desktop shortcut if it exists
try:
    import win32com.client
    sh = win32com.client.Dispatch("WScript.Shell")
    desktop_lnk = os.path.expandvars(r"%USERPROFILE%\Desktop\BS Lab Tool v2.5 PRO (C# WPF Enterprise).lnk")
    if os.path.exists(desktop_lnk):
        lnk = sh.CreateShortcut(desktop_lnk)
        lnk.TargetPath = r"c:\BSLab_Tool\BSLab_Tool.exe"
        lnk.WorkingDirectory = r"c:\BSLab_Tool"
        lnk.Save()
        print(f"Updated Desktop shortcut target -> c:\\BSLab_Tool\\BSLab_Tool.exe")
except Exception as e:
    pass

print("[+] Binary synchronization completed successfully!")
