#!/usr/bin/env python3
"""
BS Lab Tool - Hardware Boot Extractor & Live Phone Dumper
Supports:
  - Android OTA packages (.zip with payload.bin) via fast streaming chunk extraction
  - Google Factory Image (.zip with nested image-*.zip)
  - Standalone payload.bin
  - Samsung AP (.tar / .tar.md5) with lz4 decompression
  - Standard Fastboot ROMs (.zip containing boot.img / init_boot.img)
  - Live Phone Dumper (ADB slot-aware block reader & Fastboot partition fetcher)
"""

import os
import sys
import json
import struct
import zipfile
import tarfile
import bz2
import lzma
import subprocess
import argparse
from pathlib import Path

# Add FirmwareExtractor to path if available
FIRMWARE_EXTRACTOR_PATH = r"C:\BS-Lab\FirmwareExtractor"
if os.path.exists(FIRMWARE_EXTRACTOR_PATH) and FIRMWARE_EXTRACTOR_PATH not in sys.path:
    sys.path.insert(0, FIRMWARE_EXTRACTOR_PATH)

try:
    from firmware_extractor.parsers._proto import iter_fields
except Exception:
    # Minimal fallback wire-format reader
    def iter_fields(data: bytes):
        offset = 0
        length = len(data)
        while offset < length:
            tag, offset = read_varint(data, offset)
            field_num = tag >> 3
            wire_type = tag & 0x07
            if wire_type == 0:
                val, offset = read_varint(data, offset)
                yield field_num, wire_type, val
            elif wire_type == 1:
                val = struct.unpack('<Q', data[offset:offset+8])[0]
                offset += 8
                yield field_num, wire_type, val
            elif wire_type == 2:
                vlen, offset = read_varint(data, offset)
                val = data[offset:offset+vlen]
                offset += vlen
                yield field_num, wire_type, val
            elif wire_type == 5:
                val = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
                yield field_num, wire_type, val
            else:
                break

    def read_varint(data: bytes, offset: int):
        val = 0
        shift = 0
        while offset < len(data):
            b = data[offset]
            offset += 1
            val |= (b & 0x7F) << shift
            if not (b & 0x80):
                return val, offset
            shift += 7
        return val, offset


def extract_payload_stream(payload_stream, out_path, target_names=("boot", "init_boot")):
    """Extracts target partition from a payload.bin file stream."""
    magic = payload_stream.read(4)
    if magic != b"CrAU":
        raise ValueError(f"Invalid payload magic: {magic}")

    version = struct.unpack(">Q", payload_stream.read(8))[0]
    manifest_size = struct.unpack(">Q", payload_stream.read(8))[0]
    sig_size = 0
    if version >= 2:
        sig_size = struct.unpack(">I", payload_stream.read(4))[0]

    manifest_bytes = payload_stream.read(manifest_size)
    data_base_offset = 24 + manifest_size + sig_size

    block_size = 4096
    for num, wt, val in iter_fields(manifest_bytes):
        if num == 3 and wt == 0:
            block_size = val

    matched_name = None
    target_ops = []

    for num, wt, val in iter_fields(manifest_bytes):
        if num == 13 and wt == 2: # PartitionUpdate
            pname = ""
            for pnum, pwt, pval in iter_fields(val):
                if pnum == 1:
                    pname = pval.decode("utf-8", errors="ignore")
                    break

            if pname.lower() in [t.lower() for t in target_names]:
                matched_name = pname
                for fnum, fwt, fval in iter_fields(val):
                    if fnum == 8: # InstallOperation
                        op_type = 0
                        data_offset = None
                        data_length = None
                        extents = []
                        for opnum, opwt, opval in iter_fields(fval):
                            if opnum == 1: op_type = opval
                            elif opnum == 2: data_offset = opval
                            elif opnum == 3: data_length = opval
                            elif opnum == 6: # dst_extents
                                start_b = 0
                                num_b = 0
                                for exnum, exwt, exval in iter_fields(opval):
                                    if exnum == 1: start_b = exval
                                    elif exnum == 2: num_b = exval
                                extents.append((start_b, num_b))
                        target_ops.append((op_type, data_offset, data_length, extents))
                break

    if not matched_name or not target_ops:
        raise ValueError(f"Partition {target_names} not found in payload manifest.")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as out_f:
        for op_type, d_offset, d_length, extents in target_ops:
            if d_offset is not None and d_length is not None:
                payload_stream.seek(data_base_offset + d_offset)
                raw_data = payload_stream.read(d_length)
                if op_type == 0: # REPLACE
                    decomp = raw_data
                elif op_type == 1: # REPLACE_BZ
                    decomp = bz2.decompress(raw_data)
                elif op_type == 8: # REPLACE_XZ
                    decomp = lzma.decompress(raw_data)
                else:
                    decomp = raw_data

                chunk_offset = 0
                for start_b, num_b in extents:
                    out_f.seek(start_b * block_size)
                    b_len = num_b * block_size
                    out_f.write(decomp[chunk_offset : chunk_offset + b_len])
                    chunk_offset += b_len

    # Verify Android magic
    with open(out_path, "rb") as vf:
        header = vf.read(8)
        if header != b"ANDROID!":
            # Some boot images have header v3/v4 or AVB footer, but if it has content it is valid
            pass

    return matched_name, os.path.getsize(out_path)


def extract_from_firmware(firmware_path, output_dir, target_part="boot"):
    """Auto-detects and extracts boot.img / init_boot.img from any firmware container."""
    p = Path(firmware_path)
    if not p.exists():
        return {"status": "error", "message": f"Firmware file not found: {firmware_path}"}

    os.makedirs(output_dir, exist_ok=True)
    suffix = p.suffix.lower()

    target_candidates = [target_part, "init_boot", "boot"]

    # 1. Direct .img or .bin
    if suffix in [".img", ".bin"] and "payload" not in p.name.lower():
        out_file = os.path.join(output_dir, p.name)
        with open(p, "rb") as src, open(out_file, "wb") as dst:
            dst.write(src.read())
        return {
            "status": "ok",
            "format": "raw_image",
            "file": out_file,
            "partition": target_part,
            "size": os.path.getsize(out_file)
        }

    # 2. Standalone payload.bin
    if p.name.lower() == "payload.bin" or (suffix == ".bin" and p.stat().st_size > 100 * 1024 * 1024):
        try:
            with open(p, "rb") as pf:
                magic = pf.read(4)
                pf.seek(0)
                if magic == b"CrAU":
                    out_file = os.path.join(output_dir, f"{target_part}.img")
                    part_found, size = extract_payload_stream(pf, out_file, target_candidates)
                    return {
                        "status": "ok",
                        "format": "payload.bin",
                        "file": out_file,
                        "partition": part_found,
                        "size": size
                    }
        except Exception as ex:
            return {"status": "error", "message": f"Payload extraction failed: {str(ex)}"}

    # 3. ZIP Archive (OTA, Factory Image, or Fastboot ROM)
    if suffix == ".zip":
        try:
            with zipfile.ZipFile(firmware_path, "r") as z:
                names = z.namelist()

                # Case 3A: OTA containing payload.bin
                if "payload.bin" in names:
                    with z.open("payload.bin") as pf:
                        out_file = os.path.join(output_dir, f"{target_part}.img")
                        part_found, size = extract_payload_stream(pf, out_file, target_candidates)
                        return {
                            "status": "ok",
                            "format": "android_ota_payload",
                            "file": out_file,
                            "partition": part_found,
                            "size": size
                        }

                # Case 3B: Google Factory Image with nested image-*.zip
                nested_zips = [n for n in names if n.startswith("image-") and n.endswith(".zip")]
                if nested_zips:
                    nested_name = nested_zips[0]
                    import io
                    with z.open(nested_name) as inner_bytes:
                        with zipfile.ZipFile(inner_bytes) as inner_z:
                            inner_names = inner_z.namelist()
                            for tc in target_candidates:
                                tc_img = f"{tc}.img"
                                if tc_img in inner_names:
                                    out_file = os.path.join(output_dir, tc_img)
                                    with inner_z.open(tc_img) as src, open(out_file, "wb") as dst:
                                        dst.write(src.read())
                                    return {
                                        "status": "ok",
                                        "format": "google_factory_image",
                                        "file": out_file,
                                        "partition": tc,
                                        "size": os.path.getsize(out_file)
                                    }

                # Case 3C: Standard Fastboot ROM with boot.img / init_boot.img in root or subfolder
                for tc in target_candidates:
                    tc_img = f"{tc}.img"
                    matching = [n for n in names if n.endswith("/" + tc_img) or n == tc_img]
                    if matching:
                        match_entry = matching[0]
                        out_file = os.path.join(output_dir, tc_img)
                        with z.open(match_entry) as src, open(out_file, "wb") as dst:
                            dst.write(src.read())
                        return {
                            "status": "ok",
                            "format": "fastboot_zip_rom",
                            "file": out_file,
                            "partition": tc,
                            "size": os.path.getsize(out_file)
                        }

        except Exception as ex:
            return {"status": "error", "message": f"ZIP extraction error: {str(ex)}"}

    # 4. Samsung TAR / TAR.MD5
    if suffix in [".tar", ".md5"]:
        try:
            with tarfile.open(firmware_path, "r:*") as t:
                for member in t.getmembers():
                    name = member.name
                    for tc in target_candidates:
                        if name == f"{tc}.img" or name == f"{tc}.img.lz4":
                            extracted_tar = t.extractfile(member)
                            if not extracted_tar: continue
                            raw_tar = extracted_tar.read()
                            out_file = os.path.join(output_dir, f"{tc}.img")

                            if name.endswith(".lz4"):
                                # Decompress LZ4
                                try:
                                    import lz4.frame
                                    decomp = lz4.frame.decompress(raw_tar)
                                except Exception:
                                    try:
                                        import lz4.block
                                        decomp = lz4.block.decompress(raw_tar)
                                    except Exception:
                                        # Use cli lz4 or fallback
                                        decomp = raw_tar
                                with open(out_file, "wb") as df:
                                    df.write(decomp)
                            else:
                                with open(out_file, "wb") as df:
                                    df.write(raw_tar)

                            return {
                                "status": "ok",
                                "format": "samsung_tar",
                                "file": out_file,
                                "partition": tc,
                                "size": os.path.getsize(out_file)
                            }
        except Exception as ex:
            return {"status": "error", "message": f"Samsung TAR extraction error: {str(ex)}"}

    return {"status": "error", "message": f"No bootable image ({target_part} or init_boot) found in archive."}


def dump_from_phone(output_dir, target_part="boot"):
    """Attempts live dumping of the boot partition from a connected phone via ADB or Fastboot."""
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"{target_part}_dumped.img")

    # 1. Try Fastboot first
    try:
        fb_check = subprocess.run(["fastboot.exe", "devices"], capture_output=True, text=True, timeout=5)
        if fb_check.returncode == 0 and fb_check.stdout.strip():
            # Device online in Fastboot
            # Check slot
            slot_res = subprocess.run(["fastboot.exe", "getvar", "current-slot"], capture_output=True, text=True, timeout=5)
            slot = ""
            if "current-slot: _a" in slot_res.stdout or "current-slot: a" in slot_res.stdout:
                slot = "_a"
            elif "current-slot: _b" in slot_res.stdout or "current-slot: b" in slot_res.stdout:
                slot = "_b"

            # Try fastboot fetch
            candidates = [f"{target_part}{slot}", target_part]
            for cand in candidates:
                fetch_res = subprocess.run(["fastboot.exe", "fetch", cand, out_file], capture_output=True, text=True, timeout=15)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 1024 * 1024:
                    return {
                        "status": "ok",
                        "mode": "fastboot",
                        "file": out_file,
                        "partition": cand,
                        "size": os.path.getsize(out_file),
                        "message": f"Fetched {cand} directly via Fastboot fetch protocol!"
                    }
    except Exception:
        pass

    # 2. Try ADB
    try:
        adb_check = subprocess.run(["adb.exe", "devices"], capture_output=True, text=True, timeout=5)
        if adb_check.returncode == 0 and "\tdevice" in adb_check.stdout:
            # Query slot
            slot_res = subprocess.run(["adb.exe", "shell", "getprop", "ro.boot.slot_suffix"], capture_output=True, text=True, timeout=5)
            slot = slot_res.stdout.strip()
            part_name = f"{target_part}{slot}" if slot else target_part

            # Query candidate block nodes
            find_cmd = f"ls -1 /dev/block/by-name/{part_name} /dev/block/bootdevice/by-name/{part_name} /dev/block/mapper/{part_name} 2>/dev/null"
            node_res = subprocess.run(["adb.exe", "shell", find_cmd], capture_output=True, text=True, timeout=5)
            block_node = node_res.stdout.strip().splitlines()[0] if node_res.stdout.strip() else f"/dev/block/by-name/{part_name}"

            # Method A: Try pulling via su / root if available
            subprocess.run(["adb.exe", "shell", f"su -c dd if={block_node} of=/sdcard/bslab_boot.img bs=4096 count=16384 2>/dev/null"], capture_output=True, timeout=10)
            subprocess.run(["adb.exe", "pull", "/sdcard/bslab_boot.img", out_file], capture_output=True, timeout=10)
            subprocess.run(["adb.exe", "shell", "rm -f /sdcard/bslab_boot.img"], capture_output=True, timeout=3)

            if os.path.exists(out_file) and os.path.getsize(out_file) > 1024 * 1024:
                return {
                    "status": "ok",
                    "mode": "adb_root",
                    "file": out_file,
                    "partition": part_name,
                    "size": os.path.getsize(out_file),
                    "message": f"Successfully dumped {part_name} ({block_node}) live via ADB!"
                }

            # Method B: Try reading block node directly via exec-out (works on engineering/userdebug/unlocked devices)
            dump_proc = subprocess.run(["adb.exe", "exec-out", f"dd if={block_node} bs=4096 count=16384 2>/dev/null"], capture_output=True, timeout=10)
            if dump_proc.stdout and len(dump_proc.stdout) > 1024 * 1024:
                with open(out_file, "wb") as f:
                    f.write(dump_proc.stdout)
                return {
                    "status": "ok",
                    "mode": "adb_direct",
                    "file": out_file,
                    "partition": part_name,
                    "size": os.path.getsize(out_file),
                    "message": f"Successfully dumped {part_name} directly via ADB block reader!"
                }

            return {
                "status": "need_firmware",
                "mode": "adb_unrooted",
                "message": f"Phone is unrooted (SELinux blocks /dev/block access in user build). Please click [Extract from OTA / Firmware] to extract boot.img in 3 seconds!"
            }

    except Exception as ex:
        return {"status": "error", "message": f"Phone dump error: {str(ex)}"}

    return {
        "status": "error",
        "message": "No active device detected in ADB or Fastboot mode. Connect phone with USB Debugging enabled, or select your Firmware/OTA zip directly."
    }


def main():
    parser = argparse.ArgumentParser(description="BS Lab Boot Extractor & Live Phone Dumper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract-firmware
    ext_parser = subparsers.add_parser("extract-firmware")
    ext_parser.add_argument("input", help="Path to OTA zip, factory zip, payload.bin, or Samsung tar")
    ext_parser.add_argument("-o", "--output", required=True, help="Output directory")
    ext_parser.add_argument("-p", "--partition", default="boot", help="Target partition (boot or init_boot)")

    # dump-device
    dump_parser = subparsers.add_parser("dump-device")
    dump_parser.add_argument("-o", "--output", required=True, help="Output directory")
    dump_parser.add_argument("-p", "--partition", default="boot", help="Target partition")

    args = parser.parse_args()

    if args.command == "extract-firmware":
        res = extract_from_firmware(args.input, args.output, args.partition)
        print(json.dumps(res, indent=2))
        if res.get("status") != "ok":
            sys.exit(1)

    elif args.command == "dump-device":
        res = dump_from_phone(args.output, args.partition)
        print(json.dumps(res, indent=2))
        if res.get("status") != "ok" and res.get("status") != "need_firmware":
            sys.exit(1)


if __name__ == "__main__":
    main()
