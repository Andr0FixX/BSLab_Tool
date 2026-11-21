import os
import zipfile
import hashlib
import json

dist_dir = r"C:\BSLab_Tool\dist_new"
zip_path = r"C:\BSLab_Tool\BSLab_Update.zip"

include_files = [
    "BSLabTool.exe",
    "BSLab_Tool.exe",
    "BSLabTool.dll",
    "BSLabCore.dll",
    "BSLabUpdater.exe",
    "BSLabTool.runtimeconfig.json",
    "BSLabTool.deps.json",
    "libusb-1.0.dll"
]

print("Packaging lightweight BSLab_Update.zip for fast OTA...")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
    for filename in include_files:
        src = os.path.join(dist_dir, filename)
        if os.path.exists(src):
            zipf.write(src, arcname=filename)
            print(f"  + Added: {filename} ({os.path.getsize(src):,} bytes)")
        else:
            print(f"  ! Missing: {filename}")

# Calculate SHA256 of the zip
sha256 = hashlib.sha256()
with open(zip_path, 'rb') as f:
    while chunk := f.read(65536):
        sha256.update(chunk)
zip_hash = sha256.hexdigest().lower()
zip_size = os.path.getsize(zip_path)

print(f"\nBSLab_Update.zip created successfully!")
print(f"Size: {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")
print(f"SHA256: {zip_hash}")

# Update update_manifest.json
manifest_path = r"C:\BSLab_Tool\resources\ota\update_manifest.json"
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

manifest["app_version"] = "2.5.5"
manifest["version"] = "2.5.5"
manifest["binary_update_url"] = "https://github.com/Andr0FixX/BSLab_Tool/releases/download/v2.5.5/BSLab_Update.zip"
manifest["binary_sha256"] = zip_hash
manifest["change_log"] = (
    "• Smart Samsung PIT Model & Vendor Identification Engine (Vendor, Region, Binary Bit, Build PDA)\n"
    "• Hardware Port Status Box Fix (3-Column Grid Layout with Auto-Ellipsis & Detailed Tooltips)\n"
    "• Dedicated Two-Row PIT Model Search & Full-Width Selector (Live Multi-Keyword Filter)\n"
    "• Seamless PIT Auto-Latching on Right-Panel Samsung Model Selection\n"
    "• Verified Physical Partition Information Tables for Galaxy A01 Series (SM-A015A, SM-A015F, etc.)"
)

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=4)

print(f"\nUpdated {manifest_path} with v2.5.5 and SHA256.")
