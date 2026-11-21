import shutil
import os

src_dir = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\bin\Release\net8.0-windows"
dst_dir = r"C:\BSLab_Tool\dist_new"

print("Copying compiled binaries to dist_new...", flush=True)
for item in os.listdir(src_dir):
    s = os.path.join(src_dir, item)
    d = os.path.join(dst_dir, item)
    if os.path.isfile(s):
        shutil.copy2(s, d)
        print(f"  copied file {item}", flush=True)
print("Dist update completed successfully!", flush=True)
