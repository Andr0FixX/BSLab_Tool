import os
import zipfile
import time

print("[*] Starting fast packing of BSLab_Tool_Sync_Master.zip...")
t0 = time.time()
base = r"C:\BSLab_Tool"
zip_out = r"C:\BSLab_Tool\BSLab_Tool_Sync_Master.zip"

include_dirs = [
    'src', 'dist_release', 'dist_new', 'dist_clean', 'engines', 
    'resources', 'drivers', 'tools', 'scripts', 'config', 'server', 'landing_page'
]

include_files = [
    'BSLabTool.sln', 
    'RUN_NEW_PC.bat', 
    '🚀_SETUP_NEW_PC.bat', 
    'START_AI_AUTONOMOUS_SERVER.bat',
    'SYNC_TO_GDRIVE.bat',
    'BSLab_Tool.exe', 
    'BSLabTool.exe', 
    'BSLabTool.dll', 
    'BSLabCore.dll',
    'BSLabTool.deps.json',
    'BSLabTool.runtimeconfig.json',
    'BSLab_Complete_Roadmap.html', 
    'BS_LAB_SUPPORTED_MODELS.html', 
    'BS_LAB_TOOL_CLIENT_DEMO.html'
]

exclude_exact_dirs = {'w64devkit', '.git', '.vs', '__pycache__', 'backups', 'bin', 'obj'}

with zipfile.ZipFile(zip_out, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as zf:
    for f in include_files:
        fp = os.path.join(base, f)
        if os.path.isfile(fp):
            zf.write(fp, f)
            print(f"Added root file: {f}")

    for idir in include_dirs:
        dirpath = os.path.join(base, idir)
        if not os.path.isdir(dirpath): 
            continue
        for root, dirs, files in os.walk(dirpath):
            dirs[:] = [d for d in dirs if d not in exclude_exact_dirs and not d.startswith('.git')]
            if os.path.basename(root) in ['obj', 'bin']: 
                continue
            for f in files:
                if os.path.splitext(f)[1].lower() in ['.tmp', '.log', '.pdb']: 
                    continue
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, base)
                zf.write(full_p, rel_p)

sz = os.path.getsize(zip_out) / (1024 * 1024)
print(f"[+] SUCCESS! Created {zip_out}: {sz:.2f} MB in {time.time() - t0:.1f}s")
