@echo off
:: ====================================================================
:: BS LAB TOOL — 1-CLICK SYNC PROJECT TO GOOGLE DRIVE
:: Proprietor: Syed Bisharat Ali (Shah Ji) | Shop #5, Arif Center, Lahore
:: ====================================================================

title BS LAB TOOL — Google Drive Project Syncer
color 0A

echo.
echo ====================================================================
echo  BS LAB TOOL v2.5 PRO ENTERPRISE - CLOUD SYNC ENGINE
echo  Target: Google Drive / BSLab_Project_Sync
echo ====================================================================
echo.

cd /d "C:\BSLab_Tool"

echo [1/3] Refreshing precompiled distribution binaries...
python -c "
import shutil, os
src = r'C:\BSLab_Tool\src\ui\BSLabTool.UI\bin\x64\Release\net8.0-windows'
dst = r'C:\BSLab_Tool\dist_new'
os.makedirs(dst, exist_ok=True)
for f in os.listdir(src):
    s = os.path.join(src, f)
    d = os.path.join(dst, f)
    if os.path.isfile(s):
        shutil.copy2(s, d)
    elif os.path.isdir(s):
        shutil.copytree(s, d, dirs_exist_ok=True)
print('[+] dist_new binaries up to date!')
"

echo.
echo [2/3] Packing fresh BSLab_Tool_Sync_Master.zip...
python -c "
import os, zipfile, time
t0 = time.time()
base = r'C:\BSLab_Tool'
zip_out = r'C:\BSLab_Tool\BSLab_Tool_Sync_Master.zip'
include_dirs = ['src', 'dist_new', 'engines', 'resources', 'drivers', 'tools', 'scripts', 'config']
include_files = ['BSLabTool.sln', 'RUN_NEW_PC.bat', '🚀_SETUP_NEW_PC.bat', 'Launch_BSLab_PRO.bat', 'BSLab_Complete_Roadmap.html', 'BS_LAB_SUPPORTED_MODELS.html', 'BS_LAB_TOOL_CLIENT_DEMO.html']
exclude_exact_dirs = {'w64devkit', '.git', '.vs', '__pycache__', 'backups'}

with zipfile.ZipFile(zip_out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for f in include_files:
        fp = os.path.join(base, f)
        if os.path.isfile(fp):
            zf.write(fp, f)
    for idir in include_dirs:
        dirpath = os.path.join(base, idir)
        if not os.path.isdir(dirpath): continue
        for root, dirs, files in os.walk(dirpath):
            dirs[:] = [d for d in dirs if d not in exclude_exact_dirs and not d.startswith('.git')]
            if os.path.basename(root) == 'obj': continue
            for f in files:
                if os.path.splitext(f)[1].lower() in ['.tmp', '.log']: continue
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, base)
                zf.write(full_p, rel_p)
sz = os.path.getsize(zip_out) / (1024*1024)
print(f'[+] Archive created: {sz:.2f} MB in {time.time()-t0:.1f}s')
"

echo.
echo [3/3] Uploading fresh files to Google Drive (BSLab_Project_Sync)...
gdrive mutate upload "C:\BSLab_Tool\RUN_NEW_PC.bat" --parent 1O8rPTZy3lCZeCvRYMcGHpiH0Wxc6m8HB
gdrive mutate upload "C:\BSLab_Tool\BSLab_Tool_Sync_Master.zip" --parent 1O8rPTZy3lCZeCvRYMcGHpiH0Wxc6m8HB

echo.
echo ====================================================================
echo  [SUCCESS] GOOGLE DRIVE SYNC COMPLETED!
echo  Folder URL: https://drive.google.com/drive/folders/1O8rPTZy3lCZeCvRYMcGHpiH0Wxc6m8HB
echo ====================================================================
echo.
pause
