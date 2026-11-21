import os
import shutil
import subprocess
import time

print("[1] Checking running processes...")
try:
    subprocess.run(["taskkill", "/F", "/IM", "bslabtool.exe", "/T"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "bslab_tool.exe", "/T"], capture_output=True)
except Exception as e:
    print("taskkill error:", e)

time.sleep(1)

src = r"c:\BSLab_Tool\dist_clean"
dist_new = r"c:\BSLab_Tool\dist_new"
root = r"c:\BSLab_Tool"

print("[2] Syncing to dist_new...")
copied_new = 0
failed_new = 0
for f in os.listdir(src):
    s_path = os.path.join(src, f)
    d_path = os.path.join(dist_new, f)
    if os.path.isfile(s_path):
        try:
            shutil.copy2(s_path, d_path)
            copied_new += 1
        except Exception as ex:
            print(f"Failed to copy {f} to dist_new: {ex}")
            failed_new += 1

print(f"dist_new: Copied {copied_new}, Failed {failed_new}")

print("[3] Syncing to root BSLab_Tool.exe...")
try:
    shutil.copy2(os.path.join(src, "BSLabTool.exe"), os.path.join(root, "BSLab_Tool.exe"))
    print("Root BSLab_Tool.exe updated successfully!")
except Exception as ex:
    print(f"Failed to copy to root BSLab_Tool.exe: {ex}")

try:
    shutil.copy2(os.path.join(src, "BSLabTool.dll"), os.path.join(root, "BSLabTool.dll"))
    print("Root BSLabTool.dll updated successfully!")
except Exception as ex:
    print(f"Failed to copy root BSLabTool.dll: {ex}")
