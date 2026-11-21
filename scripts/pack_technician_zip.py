import os, zipfile, time

print("[*] Packing BSLab_Tool_Technician_Setup.zip...")
t0 = time.time()
src_dir = r"C:\BSLab_Tool\dist_release"
zip_out = r"C:\BSLab_Tool\BSLab_Tool_Technician_Setup.zip"

with zipfile.ZipFile(zip_out, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as zf:
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith('.tmp') or f.endswith('.log'):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, src_dir)
            zf.write(full_path, rel_path)

sz = os.path.getsize(zip_out) / (1024 * 1024)
print(f"[+] Technician Zip Created: {sz:.2f} MB in {time.time() - t0:.1f}s")
