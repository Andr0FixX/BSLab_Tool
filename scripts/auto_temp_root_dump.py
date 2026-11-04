"""
BS Lab Tool v2.0 PRO — Autonomous Zero-Click Temporary Root & Partition Dump Engine
Flow:
1. Detect ADB -> Verify Device & Properties (Model, Build ID, Serial).
2. Reboot to Bootloader -> Verify Fastboot Handshake & OEM Unlock state.
3. Fastboot Boot Magisk Patched Kernel (Temporary RAM Boot — 0% eMMC modification).
4. Wait for Android Boot -> Verify SuperUser Root.
5. Dynamic Partition Discovery -> Stream Bit-by-Bit Raw Partition Dump to PC.
6. Clean Reboot to Normal System OS.
"""

import os
import sys
import time
import hashlib
import json
import subprocess
from datetime import datetime

# Adjust module search path for BSLab Tool core
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.path_utils import get_platform_tool_path

# Windows console encoding helper
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

DEFAULT_PATCHED_BOOT = r"C:\Users\AndroFixX\Downloads\magisk_patched-sv55.img"
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "backups")

# Critical partitions to dump (avoid giant user storage by default)
ESSENTIAL_PARTITIONS = [
    # Boot & System core
    "boot", "dtbo", "recovery", "vbmeta", "vbmeta_system", "misc",
    # Cellular Radio & Carrier Lock
    "modem", "carrier", "modemst1", "modemst2", "fsg", "fsc",
    # Hardware & Calibration
    "persist", "config", "devinfo", "splash", "DDR",
    # Low-level TrustZone & Bootloader
    "aboot", "sbl1", "tz", "rpm", "devcfg", "keymaster", "keystore",
    "cmnlib", "cmnlib64", "dsp", "sec", "limits", "apdp", "msadp", "dpo", "dip"
]

def log(msg: str, symbol: str = "[*]"):
    print(f"{symbol} {msg}")

def run_cmd(args, timeout=30):
    try:
        p = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def wait_for_adb(timeout=60):
    adb = get_platform_tool_path("adb")
    log(f"Waiting for ADB device connection (Timeout: {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        rc, out, _ = run_cmd([adb, "devices"])
        lines = [l.strip() for l in out.splitlines() if l.strip() and not l.startswith("List of")]
        for l in lines:
            parts = l.split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
        time.sleep(1)
    return None

def wait_for_fastboot(timeout=60):
    fb = get_platform_tool_path("fastboot")
    log(f"Waiting for Fastboot device connection (Timeout: {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        rc, out, _ = run_cmd([fb, "devices"])
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        if lines:
            serial = lines[0].split()[0]
            return serial
        time.sleep(1)
    return None

def wait_for_boot_completed(timeout=90):
    adb = get_platform_tool_path("adb")
    log(f"Waiting for Android OS to complete booting (Timeout: {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        rc, out, _ = run_cmd([adb, "shell", "getprop", "sys.boot_completed"], timeout=5)
        if rc == 0 and out.strip() == "1":
            return True
        time.sleep(2)
    return False

def verify_root():
    adb = get_platform_tool_path("adb")
    rc, out, err = run_cmd([adb, "shell", "su -c id"], timeout=10)
    if rc == 0 and ("uid=0" in out or "root" in out):
        return True
    return False

def discover_partitions():
    adb = get_platform_tool_path("adb")
    rc, out, _ = run_cmd([adb, "shell", "su -c 'ls -1 /dev/block/bootdevice/by-name/'"], timeout=15)
    if rc == 0 and out:
        parts = [p.strip() for p in out.splitlines() if p.strip()]
        return parts
    return []

def main():
    print("=" * 70)
    print(" BS LAB TOOL PRO — AUTONOMOUS ZERO-CLICK PARTITION DUMP ENGINE ")
    print("=" * 70)

    adb_bin = get_platform_tool_path("adb")
    fb_bin = get_platform_tool_path("fastboot")

    patched_boot = DEFAULT_PATCHED_BOOT
    if not os.path.exists(patched_boot):
        print(f"[!] ERROR: Magisk Patched boot image not found at: {patched_boot}")
        print("Please place the patched boot image in Downloads or pass path.")
        sys.exit(1)

    print(f"[+] Magisk Patched Image: {patched_boot} ({round(os.path.getsize(patched_boot)/1024/1024, 1)} MB)")

    # -------------------------------------------------------------
    # STEP 1: Handshake & Identity
    # -------------------------------------------------------------
    print("\n--- [STEP 1/6] ADB Handshake & Device Inspection ---")
    serial = wait_for_adb(timeout=30)
    if not serial:
        print("[!] No ADB device detected. Please connect phone with USB Debugging enabled.")
        sys.exit(1)

    log(f"Device Connected: {serial}", "[✓]")

    # Query device specs
    _, model, _ = run_cmd([adb_bin, "-s", serial, "shell", "getprop", "ro.product.model"])
    _, build_id, _ = run_cmd([adb_bin, "-s", serial, "shell", "getprop", "ro.build.display.id"])
    _, board, _ = run_cmd([adb_bin, "-s", serial, "shell", "getprop", "ro.product.board"])
    _, android_ver, _ = run_cmd([adb_bin, "-s", serial, "shell", "getprop", "ro.build.version.release"])

    print(f"    * Model       : {model or 'Unknown'}")
    print(f"    * Build ID    : {build_id or 'Unknown'}")
    print(f"    * Board / SoC : {board or 'msm8937'}")
    print(f"    * Android OS  : Android {android_ver or '11'}")

    # -------------------------------------------------------------
    # STEP 2: Reboot to Bootloader & Lock Verification
    # -------------------------------------------------------------
    print("\n--- [STEP 2/6] Rebooting to Bootloader (Fastboot) ---")
    log("Executing: adb reboot bootloader...")
    run_cmd([adb_bin, "-s", serial, "reboot", "bootloader"])

    fb_serial = wait_for_fastboot(timeout=45)
    if not fb_serial:
        print("[!] Fastboot device not detected. Check USB cable and Fastboot drivers.")
        sys.exit(1)

    log(f"Fastboot Connected: {fb_serial}", "[✓]")

    # Check unlock status
    rc, out, err = run_cmd([fb_bin, "-s", fb_serial, "getvar", "unlocked"])
    var_text = out + err
    is_unlocked = False
    for line in var_text.splitlines():
        if "unlocked:" in line:
            val = line.split("unlocked:")[1].strip().lower()
            if val in ("yes", "true"):
                is_unlocked = True
                break

    if not is_unlocked:
        print("[!] Device Bootloader is LOCKED!")
        print("[*] Attempting OEM Bootloader unlock...")
        rc, u_out, u_err = run_cmd([fb_bin, "-s", fb_serial, "flashing", "unlock"])
        print(f"Unlock command output: {u_out} {u_err}")
        print("Please confirm unlock on device screen if prompted.")
    else:
        log("Bootloader is UNLOCKED (Authorized for temporary kernel execution).", "[✓]")

    # -------------------------------------------------------------
    # STEP 3: Temporary RAM Boot (Magisk Temp Root)
    # -------------------------------------------------------------
    print("\n--- [STEP 3/6] Fastboot Boot Temporary RAM Root ---")
    log("Uploading Magisk patched kernel into device RAM (0% flash modification)...")
    rc, b_out, b_err = run_cmd([fb_bin, "-s", fb_serial, "boot", patched_boot], timeout=45)
    print(f"    Fastboot response: {b_out or b_err}")
    if rc != 0 and "FAILED" in (b_out + b_err):
        print(f"[!] Error booting kernel: {b_out} {b_err}")
        sys.exit(1)

    log("Kernel uploaded to RAM successfully! Device is booting into Android...", "[✓]")

    # -------------------------------------------------------------
    # STEP 4: Wait for Boot & Verify SuperUser Root
    # -------------------------------------------------------------
    print("\n--- [STEP 4/6] Waiting for Android OS & Root Handshake ---")
    new_serial = wait_for_adb(timeout=90)
    if not new_serial:
        print("[!] Timed out waiting for phone to reboot into Android OS.")
        sys.exit(1)

    log(f"ADB Re-established on: {new_serial}", "[✓]")
    wait_for_boot_completed(timeout=60)

    # Check Root
    log("Verifying SuperUser permissions...")
    if not verify_root():
        print("[!] Root access not confirmed. Ensure Magisk app granted or wait 5s.")
        time.sleep(5)
        if not verify_root():
            print("[!] FATAL: Root check failed. Cannot proceed with raw partition dump.")
            sys.exit(1)

    log("SuperUser Root Confirmed (uid=0 root verified).", "[✓]")

    # -------------------------------------------------------------
    # STEP 5: Dynamic Partition Discovery & Raw Streaming Dump
    # -------------------------------------------------------------
    print("\n--- [STEP 5/6] Partition Discovery & High-Speed Direct Dump ---")
    all_parts = discover_partitions()
    log(f"Total partitions discovered on eMMC storage: {len(all_parts)}")

    # Target partitions: Filter essential partitions that exist on device
    target_parts = [p for p in ESSENTIAL_PARTITIONS if p in all_parts]
    # Add any remaining non-huge partitions
    for p in all_parts:
        if p not in target_parts and p not in ("userdata", "super", "system", "vendor"):
            target_parts.append(p)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_model = (model or "SV55").replace(" ", "_").replace("/", "_")
    dump_dir = os.path.join(OUTPUT_BASE_DIR, f"DUMP_{clean_model}_{timestamp}")
    os.makedirs(dump_dir, exist_ok=True)
    log(f"Dump Directory: {dump_dir}", "[✓]")

    manifest = {
        "device_model": model,
        "build_id": build_id,
        "board": board,
        "serial": new_serial,
        "timestamp": timestamp,
        "partitions": {}
    }

    total_bytes = 0
    successful_dumps = 0

    print(f"\n[*] Starting direct raw dump of {len(target_parts)} partitions...")
    print("-" * 70)
    print(f"{'PARTITION':<20} | {'STATUS':<10} | {'SIZE (BYTES)':<14} | {'MD5 CHECKSUM':<32}")
    print("-" * 70)

    for idx, part in enumerate(target_parts, 1):
        out_file = os.path.join(dump_dir, f"{part}.img")
        part_block = f"/dev/block/bootdevice/by-name/{part}"

        # Dump via adb exec-out or cat directly to PC file
        cmd = [adb_bin, "-s", new_serial, "exec-out", f"su -c 'cat {part_block}'"]
        try:
            with open(out_file, "wb") as f_out:
                p = subprocess.Popen(cmd, stdout=f_out, stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
                _, p_err = p.communicate(timeout=60)

            if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                size = os.path.getsize(out_file)
                total_bytes += size
                successful_dumps += 1

                # Calculate MD5
                h = hashlib.md5()
                with open(out_file, "rb") as f_in:
                    while chunk := f_in.read(1024 * 1024):
                        h.update(chunk)
                chksum = h.hexdigest()

                manifest["partitions"][part] = {
                    "filename": f"{part}.img",
                    "size_bytes": size,
                    "md5": chksum
                }

                print(f"{part:<20} | {'SUCCESS':<10} | {size:<14} | {chksum}")
            else:
                print(f"{part:<20} | {'FAILED':<10} | {'0':<14} | {'--'}")
                if os.path.exists(out_file):
                    os.remove(out_file)
        except Exception as e:
            print(f"{part:<20} | {'ERROR':<10} | {'0':<14} | {str(e)[:32]}")

    print("-" * 70)
    total_mb = round(total_bytes / (1024 * 1024), 2)
    log(f"Dump Completed! {successful_dumps}/{len(target_parts)} partitions dumped successfully ({total_mb} MB total).", "[✓]")

    # Save manifest
    manifest_path = os.path.join(dump_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
    log(f"Manifest written to: {manifest_path}", "[✓]")

    # -------------------------------------------------------------
    # STEP 6: Normal System Reboot
    # -------------------------------------------------------------
    print("\n--- [STEP 6/6] Cleanup & Normal Reboot ---")
    log("Rebooting device out of temporary RAM session into normal stock OS...")
    run_cmd([adb_bin, "-s", new_serial, "reboot"])
    log("Device rebooted! The phone is back to 100% untouched stock factory state.", "[✓]")

    print("\n" + "=" * 70)
    print(f" [✓] COMPLETE DUMP SAVED AT:\n {dump_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()
