import os

backup_dir = r"c:\bslab_tool\dist_new\backups\partitions\Pixel_4___4_XL___4a__Qualcomm_Snapdragon_855___730G__20261111_234652"
if os.path.exists(backup_dir):
    print(f"Directory: {backup_dir}", flush=True)
    for f in os.listdir(backup_dir):
        fp = os.path.join(backup_dir, f)
        sz = os.path.getsize(fp)
        print(f"  {f:20s}: {sz} bytes ({sz/1024:.2f} KB)", flush=True)
else:
    print(f"Directory does not exist: {backup_dir}", flush=True)

sec_dir = r"c:\bslab_tool\dist_new\backups\security_nv"
if os.path.exists(sec_dir):
    print(f"\nDirectory: {sec_dir}", flush=True)
    for root, dirs, files in os.walk(sec_dir):
        for f in files:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            print(f"  {fp}: {sz} bytes", flush=True)
