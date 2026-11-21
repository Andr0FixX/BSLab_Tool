import os
import zipfile
import time
import shutil

src_dir = r"c:\BSLab_Tool\dist_new"
zip_20261120 = r"c:\BSLab_Tool\BSLab_Tool_v2.5_PRO_dist_new_2026-11-20.zip"
zip_20261119 = r"c:\BSLab_Tool\BSLab_Tool_v2.5_PRO_dist_new_2026-11-19.zip"

print(f"[*] Packaging {src_dir} into {zip_20261120}...")
t0 = time.time()
file_count = 0

with zipfile.ZipFile(zip_20261120, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as zf:
    for root, dirs, files in os.walk(src_dir):
        # Exclude temp or git files
        dirs[:] = [d for d in dirs if not d.startswith('.git') and d not in ['obj', 'bin']]
        for f in files:
            if f.endswith('.tmp') or f.endswith('.log'):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, src_dir)
            zf.write(full_path, rel_path)
            file_count += 1

sz_mb = os.path.getsize(zip_20261120) / (1024 * 1024)
print(f"[+] Successfully created {zip_20261120}: {sz_mb:.2f} MB ({file_count} files) in {time.time() - t0:.1f}s")

# Sync to 2026-11-19 as well
try:
    shutil.copy2(zip_20261120, zip_20261119)
    print(f"[+] Synced to {zip_20261119}")
except Exception as e:
    print(f"[-] Warning syncing to 2026-11-19: {e}")

print("[+] Distribution packaging completed successfully!")
