import os
import shutil

src_dirs = [r"c:\BSLab_Tool\dist_clean", r"c:\BSLab_Tool\dist_new", r"c:\BSLab_Tool"]
dest = r"c:\BSLab_Tool\dist_release"

asset_folders = ["resources", "engines", "dumps", "backups", "screenshots"]

for folder in asset_folders:
    dest_folder = os.path.join(dest, folder)
    if not os.path.exists(dest_folder):
        for s in src_dirs:
            s_folder = os.path.join(s, folder)
            if os.path.exists(s_folder) and os.path.isdir(s_folder):
                try:
                    shutil.copytree(s_folder, dest_folder)
                    print(f"Copied folder {folder} from {s}")
                    break
                except Exception as e:
                    print(f"Error copying {folder}: {e}")

print("Asset setup complete!")
