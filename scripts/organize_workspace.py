import os
import shutil

ROOT = r"C:\BSLab_Tool"

# Target directories
DIRS = {
    "docs": os.path.join(ROOT, "docs"),
    "archives": os.path.join(ROOT, "archives"),
    "scripts_diag": os.path.join(ROOT, "scripts", "diagnostics"),
    "scripts_migr": os.path.join(ROOT, "scripts", "migrations"),
    "legacy_py": os.path.join(ROOT, "archives", "legacy_python"),
}

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

# Files to move to docs
DOCS_FILES = [
    "BSLab_Complete_Roadmap.html",
    "BS_LAB_SUPPORTED_MODELS.html",
    "BS_LAB_TOOL_CLIENT_DEMO.html",
    "PROMO_VIDEO_SCRIPT_3MIN.md",
]

# Files to move to archives
ARCHIVE_FILES = [
    "BSLab_Tool_Portable_20261111.zip",
    "BSLab_Tool_Sync_Master.zip",
    "BSLab_Tool_Update_Nov14_2026.zip",
    "BSLab_Tool_v2_Scripts_Backup.zip",
]

# Legacy python
LEGACY_PY = [
    "main.py",
    "main_backup.py.bak",
    "BSLab_Tool.spec",
]

# Temp junk to delete safely
JUNK_FILES = [
    "crash_log.txt",
    "nav_tabs_crop.png",
    "query",
]

# Diagnostic prefixes
DIAG_PREFIXES = ("check_", "dump_", "find_", "inspect_", "parse_", "pull_", "restore_", "search_", "test_")

# Migration prefixes
MIGR_PREFIXES = ("apply_ai_", "deploy_", "fix_", "implement_ai_", "patch_", "update_")

print("Starting Professional Organization of C:\\BSLab_Tool...")

moved_count = 0

# Process specific lists
for fname in DOCS_FILES:
    src = os.path.join(ROOT, fname)
    if os.path.exists(src):
        dst = os.path.join(DIRS["docs"], fname)
        shutil.move(src, dst)
        print(f"[DOCS] Moved: {fname} -> docs\\")
        moved_count += 1

for fname in ARCHIVE_FILES:
    src = os.path.join(ROOT, fname)
    if os.path.exists(src):
        dst = os.path.join(DIRS["archives"], fname)
        shutil.move(src, dst)
        print(f"[ARCHIVE] Moved: {fname} -> archives\\")
        moved_count += 1

for fname in LEGACY_PY:
    src = os.path.join(ROOT, fname)
    if os.path.exists(src):
        dst = os.path.join(DIRS["legacy_py"], fname)
        shutil.move(src, dst)
        print(f"[LEGACY] Moved: {fname} -> archives\\legacy_python\\")
        moved_count += 1

for fname in JUNK_FILES:
    src = os.path.join(ROOT, fname)
    if os.path.exists(src):
        try:
            os.remove(src)
            print(f"[CLEANUP] Deleted junk: {fname}")
        except Exception as e:
            print(f"[CLEANUP ERROR] Could not delete {fname}: {e}")

# Scan remaining loose files in root
for fname in os.listdir(ROOT):
    full_path = os.path.join(ROOT, fname)
    if not os.path.isfile(full_path):
        continue

    # Diagnostic scripts
    if fname.startswith(DIAG_PREFIXES) and fname.endswith(".py"):
        dst = os.path.join(DIRS["scripts_diag"], fname)
        shutil.move(full_path, dst)
        print(f"[DIAG] Moved: {fname} -> scripts\\diagnostics\\")
        moved_count += 1

    # Migration scripts
    elif fname.startswith(MIGR_PREFIXES) and fname.endswith(".py"):
        dst = os.path.join(DIRS["scripts_migr"], fname)
        shutil.move(full_path, dst)
        print(f"[MIGR] Moved: {fname} -> scripts\\migrations\\")
        moved_count += 1

print(f"\nOrganization Complete! Successfully organized {moved_count} files.")
