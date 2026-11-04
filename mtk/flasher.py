import os
import sys
import re
import subprocess
import threading
import time

def format_bytes(num_bytes: int) -> str:
    """Converts raw byte count into human-readable string (KB, MB, GB)."""
    if num_bytes <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


class ScatterParser:
    """Parses MTK Android scatter files to extract partition table and image mappings."""
    @staticmethod
    def parse(scatter_path):
        if not os.path.exists(scatter_path):
            raise FileNotFoundError(f"Scatter file not found: {scatter_path}")

        partitions = []
        current_part = {}
        firmware_dir = os.path.dirname(scatter_path)

        with open(scatter_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('- partition_index:'):
                    if current_part and "name" in current_part:
                        ScatterParser._finalize_partition(current_part, firmware_dir)
                        partitions.append(current_part)
                    current_part = {}
                    continue

                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == "partition_name":
                        current_part["name"] = val
                    elif key == "file_name":
                        current_part["file_name"] = val
                    elif key == "is_download":
                        current_part["is_download"] = (val.lower() == "true")
                    elif key == "linear_start_addr":
                        current_part["start_addr"] = val
                        try:
                            current_part["start_addr_int"] = int(val, 16)
                        except Exception:
                            current_part["start_addr_int"] = 0
                    elif key == "partition_size":
                        current_part["size_hex"] = val

        if current_part and "name" in current_part:
            ScatterParser._finalize_partition(current_part, firmware_dir)
            partitions.append(current_part)

        return partitions

    @staticmethod
    def _finalize_partition(part, firmware_dir):
        file_name = part.get("file_name", "NONE")
        if file_name and file_name != "NONE":
            file_path = os.path.join(firmware_dir, file_name)
            part["file_path"] = file_path
            part["exists"] = os.path.exists(file_path)
            if part["exists"]:
                part["file_size"] = os.path.getsize(file_path)
                part["file_size_human"] = format_bytes(part["file_size"])
            else:
                part["file_size"] = 0
                part["file_size_human"] = "Missing"
        else:
            part["file_path"] = None
            part["exists"] = False
            part["file_size"] = 0
            part["file_size_human"] = "--"

        # Calculate partition size
        size_hex = part.get("size_hex", "0x0")
        try:
            part["size_bytes"] = int(size_hex, 16)
            part["size_human"] = format_bytes(part["size_bytes"])
        except Exception:
            part["size_bytes"] = 0
            part["size_human"] = size_hex


class MtkFirmwareFlasher:
    """Handles flashing operations, partition reads/writes, and Preloader crash using mtkclient backend."""
    def __init__(self, logger):
        self.logger = logger
        self.is_flashing = False
        self.current_process = None

    def _find_preloader(self, firmware_dir, custom_preloader=None):
        if custom_preloader and os.path.exists(custom_preloader):
            return custom_preloader

        if not firmware_dir or not os.path.exists(firmware_dir):
            return None

        # Prioritize known Infinix/Tecno preloader
        preloader_bin = os.path.join(firmware_dir, "preloader_x6816_xq683.bin")
        if os.path.exists(preloader_bin):
            return preloader_bin

        for f in os.listdir(firmware_dir):
            if f.startswith("preloader") and f.endswith(".bin"):
                return os.path.join(firmware_dir, f)
        return None

    def crash_preloader_to_brom(self, custom_da=None, custom_preloader=None, port=None, progress_callback=None):
        """Forces preloader to crash and enter BROM mode."""
        self.logger.brom("Initiating Software Preloader Crash Engine...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "crash"]
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
        if custom_preloader and os.path.exists(custom_preloader):
            cmd.extend(["--preloader", custom_preloader])

        return self._run_command_stream(cmd, progress_callback, "Preloader Crash to BROM")

    def flash_partition_list(self, partitions_to_flash, firmware_dir=None,
                             custom_da=None, custom_preloader=None, port=None,
                             dual_progress_callback=None, restart_after_job=False):
        """Flashes a list of partition dictionaries using explicit partition mapping (w part1,part2 file1,file2)."""
        valid_items = []
        for p in partitions_to_flash:
            fpath = p.get("file_path")
            if fpath and os.path.exists(fpath):
                valid_items.append((p.get("name"), fpath, p.get("file_size", 0)))

        if not valid_items:
            self.logger.error("No valid partitions with existing image files were selected!")
            return False

        part_names = [item[0] for item in valid_items]
        file_paths = [item[1] for item in valid_items]
        total_bytes = sum(item[2] for item in valid_items)

        self.logger.info(f"Target Partitions ({len(valid_items)}): {', '.join(part_names[:8])}{'...' if len(part_names) > 8 else ''}")
        self.logger.info(f"Total Payload Size: {format_bytes(total_bytes)}")
        self.logger.brom("Preparing MediaTek Partition Writer via DA...")

        cmd = [sys.executable, "-m", "mtkclient.mtk", "w", ",".join(part_names), ",".join(file_paths)]

        # Attach preloader
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
            self.logger.success(f"Attached Hardware Preloader: {os.path.basename(preloader_bin)}")

        # Attach custom DA
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
            self.logger.success(f"Attached Custom DA: {os.path.basename(custom_da)}")

        success = self._run_flashing_stream(
            cmd=cmd,
            dual_progress_callback=dual_progress_callback,
            op_name="Firmware Flashing",
            partition_names=part_names,
            total_parts_count=len(valid_items)
        )

        if success and restart_after_job:
            self.logger.success("Flashing Finished. Restart After Job Active -> Sending Reboot command...")
            time.sleep(1.0)
            self.reboot_device(firmware_dir=firmware_dir, custom_da=custom_da, custom_preloader=custom_preloader)

        return success

    def print_gpt(self, firmware_dir=None, custom_da=None, custom_preloader=None, port=None, progress_callback=None):
        """Reads and prints GUID Partition Table (GPT) to console."""
        cmd = [sys.executable, "-m", "mtkclient.mtk", "printgpt"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, "Read Partition Table (GPT)")

    def read_gpt_structured(self, firmware_dir=None, custom_da=None, custom_preloader=None, port=None):
        """Executes printgpt and parses lines into structured partition dictionaries."""
        cmd = [sys.executable, "-m", "mtkclient.mtk", "printgpt"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        self.logger.brom("Querying eMMC / UFS Live Partition Table from Device...")
        self.logger.brom("WAITING FOR PHONE... (Connect Test Point to Ground, plug USB cable)")

        partitions = []
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            pattern1 = re.compile(r'(\d+):\s+([\w\-\.]+)\s+\(Offset\s+(0x[0-9a-fA-F]+),\s+Length\s+(0x[0-9a-fA-F]+)\)')
            pattern2 = re.compile(r'([\w\-\.]+):\s+Offset\s+(0x[0-9a-fA-F]+),\s+Length\s+(0x[0-9a-fA-F]+)')

            idx = 0
            for line in iter(self.current_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue

                if "error" in line.lower() or "failed" in line.lower():
                    self.logger.error(line)
                elif "gpt" in line.lower() or "partition" in line.lower() or "da" in line.lower():
                    self.logger.brom(line)
                else:
                    self.logger.info(line)

                m1 = pattern1.search(line)
                if m1:
                    p_idx = int(m1.group(1))
                    name = m1.group(2)
                    offset = m1.group(3)
                    length = m1.group(4)
                    size_bytes = int(length, 16)
                    partitions.append({
                        "index": p_idx,
                        "name": name,
                        "offset": offset,
                        "length": length,
                        "size_bytes": size_bytes,
                        "size_human": format_bytes(size_bytes)
                    })
                    continue

                m2 = pattern2.search(line)
                if m2:
                    name = m2.group(1)
                    offset = m2.group(2)
                    length = m2.group(3)
                    size_bytes = int(length, 16)
                    partitions.append({
                        "index": idx,
                        "name": name,
                        "offset": offset,
                        "length": length,
                        "size_bytes": size_bytes,
                        "size_human": format_bytes(size_bytes)
                    })
                    idx += 1

            self.current_process.stdout.close()
            ret = self.current_process.wait()
            if partitions:
                self.logger.success(f"Live GPT Extracted Successfully! ({len(partitions)} partitions identified).")
            return partitions
        except Exception as e:
            self.logger.error(f"Failed to read live GPT table: {str(e)}")
            return []
        finally:
            self.current_process = None

    def read_partition_to_file(self, part_name, out_path, firmware_dir=None, custom_da=None, custom_preloader=None, port=None, progress_callback=None):
        """Dumps a single partition from phone to a local file."""
        self.logger.info(f"Reading Partition: {part_name} -> {out_path}...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "r", part_name, out_path]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, f"Read Partition {part_name}")

    def write_partition_from_file(self, part_name, in_path, firmware_dir=None, custom_da=None, custom_preloader=None, port=None, progress_callback=None):
        """Flashes a single partition from a file to phone."""
        self.logger.info(f"Writing Partition: {part_name} <- {in_path}...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "w", part_name, in_path]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, f"Write Partition {part_name}")

    def erase_partition(self, part_name, firmware_dir=None, custom_da=None, custom_preloader=None, port=None, progress_callback=None):
        """Erases/formats a specific partition (e.g. frp, userdata)."""
        self.logger.info(f"Erasing partition: {part_name}...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "e", part_name]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, f"Erase {part_name}")

    def reboot_device(self, firmware_dir=None, custom_da=None, custom_preloader=None, port=None, progress_callback=None):
        """Sends reset command to reboot phone from BROM/DA."""
        self.logger.info("Sending Hardware Reset command to device...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "reset"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, "Reboot Device")

    # -------------------------------------------------------------------------
    # GSM OPERATIONS (Matching TFM Tool Pro / UnlockTool functionality)
    # -------------------------------------------------------------------------
    def reset_frp(self, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None, restart_after_job=True):
        """Erases frp partition to remove Google Factory Reset Protection."""
        self.logger.info("Starting Reset FRP (Google Lock Bypass)...")
        success = self.erase_partition("frp", firmware_dir, custom_da, custom_preloader, progress_callback=progress_callback)
        if success:
            self.logger.success("FRP Partition Formatted Successfully! Google Lock Removed.")
            if restart_after_job:
                self.reboot_device(firmware_dir, custom_da, custom_preloader)
        return success

    def factory_reset(self, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None, restart_after_job=True):
        """Erases userdata & metadata partitions to wipe PIN / Pattern / Screen Lock."""
        self.logger.info("Starting Factory Reset (Userdata Wipe)...")
        success = self.erase_partition("userdata,metadata", firmware_dir, custom_da, custom_preloader, progress_callback=progress_callback)
        if success:
            self.logger.success("Factory Reset Completed Successfully! Screen Lock Removed.")
            if restart_after_job:
                self.reboot_device(firmware_dir, custom_da, custom_preloader)
        return success

    def unlock_bootloader(self, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None, restart_after_job=True):
        """Unlocks device bootloader via mtkclient seccfg."""
        self.logger.info("Starting Bootloader Unlock Sequence...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "da", "seccfg", "unlock"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        success = self._run_command_stream(cmd, progress_callback, "Bootloader Unlock")
        if success:
            self.logger.success("Bootloader Unlocked Successfully! Fastboot flash enabled.")
            if restart_after_job:
                self.reboot_device(firmware_dir, custom_da, custom_preloader)
        return success

    def relock_bootloader(self, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None, restart_after_job=True):
        """Relocks device bootloader via mtkclient seccfg."""
        self.logger.info("Starting Bootloader Relock Sequence...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "da", "seccfg", "lock"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        success = self._run_command_stream(cmd, progress_callback, "Bootloader Relock")
        if success:
            self.logger.success("Bootloader Relocked Successfully.")
            if restart_after_job:
                self.reboot_device(firmware_dir, custom_da, custom_preloader)
        return success

    def patch_dm_verity(self, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None):
        """Disables AVB verification on vbmeta to fix Red State."""
        self.logger.info("Fixing DM-Verity / Red State Bootloop...")
        # Erasing or writing empty vbmeta flags
        cmd = [sys.executable, "-m", "mtkclient.mtk", "e", "vbmeta,vbmeta_system,vbmeta_vendor"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, "Patch DM-Verity / Red State")

    def read_rpmb(self, out_path, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None):
        """Reads/dumps RPMB partition."""
        self.logger.brom("Reading RPMB partition dump from device...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "r", "rpmb", out_path, "--parttype", "rpmb"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
        return self._run_command_stream(cmd, progress_callback, "Read RPMB")

    def write_rpmb(self, in_path, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None):
        """Writes/flashes RPMB partition."""
        self.logger.warn("Writing RPMB partition to device...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "w", "rpmb", in_path, "--parttype", "rpmb"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])
        return self._run_command_stream(cmd, progress_callback, "Write RPMB")

    def erase_rpmb(self, firmware_dir=None, custom_da=None, custom_preloader=None, progress_callback=None):
        """Erases RPMB partition key."""
        self.logger.warn("Erasing RPMB partition key (Requires unlocked DA)...")
        cmd = [sys.executable, "-m", "mtkclient.mtk", "e", "rpmb", "--parttype", "rpmb"]
        preloader_bin = self._find_preloader(firmware_dir, custom_preloader)
        if preloader_bin:
            cmd.extend(["--preloader", preloader_bin])
        if custom_da and os.path.exists(custom_da):
            cmd.extend(["--loader", custom_da])

        return self._run_command_stream(cmd, progress_callback, "Erase RPMB")

    def abort(self):
        """Terminates ongoing flash operation."""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.logger.warn("Operation forcibly stopped by user.")
            except Exception:
                pass
        self.is_flashing = False

    def _run_flashing_stream(self, cmd, dual_progress_callback, op_name, partition_names=None, total_parts_count=1):
        """Flashing execution stream with real-time Dual Progress & Active File tracking."""
        self.is_flashing = True
        part_list = partition_names if partition_names else []
        current_part_idx = 0
        current_part_name = part_list[0] if part_list else "Initializing..."
        overall_pct = 0.0
        file_pct = 0.0

        try:
            self.logger.info(f"Starting {op_name}...")
            self.logger.brom("WAITING FOR PHONE... (Connect Test Point to Ground, plug USB cable)")

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Patterns to detect partition writing
            # e.g.: Writing partition boot_a from boot.img
            # or: Writing partition: boot_a
            # or: Writing boot_a
            write_part_pattern = re.compile(r'Writing\s+(?:partition\s+)?([\w\-\.]+)', re.IGNORECASE)
            # mtkclient progress pattern: 3.5% Write: (0xDC00000/0x187E7C400), 1.39 MB/s 05h:22m:57s left
            progress_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%\s*Write:\s*\((0x[0-9a-fA-F]+)/(0x[0-9a-fA-F]+)\)(?:,\s*([^\s]+)\s*([^\s]+))?', re.IGNORECASE)

            for line in iter(self.current_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue

                # Detect active partition
                m_part = write_part_pattern.search(line)
                if m_part:
                    detected_name = m_part.group(1).lower()
                    if detected_name in [p.lower() for p in part_list]:
                        current_part_name = detected_name
                        try:
                            current_part_idx = [p.lower() for p in part_list].index(detected_name)
                        except Exception:
                            pass
                        file_pct = 0.0

                # Log routing
                if "error" in line.lower() or "failed" in line.lower() or "couldn't" in line.lower():
                    self.logger.error(line)
                elif "success" in line.lower() or "done" in line.lower() or "ok" in line.lower():
                    self.logger.success(line)
                elif "waiting for" in line.lower() or "reconnect" in line.lower():
                    self.logger.brom(line)
                elif "brom" in line.lower() or "preloader" in line.lower() or "da" in line.lower() or "handshake" in line.lower():
                    self.logger.brom(line)
                else:
                    self.logger.info(line)

                # Parse detailed write progress
                m_prog = progress_pattern.search(line)
                if m_prog:
                    try:
                        pct_val = float(m_prog.group(1))
                        file_pct = pct_val / 100.0
                        total_parts = max(len(part_list), 1)
                        part_weight = 1.0 / total_parts
                        overall_pct = min(1.0, (current_part_idx * part_weight) + (file_pct * part_weight))

                        speed_str = ""
                        if m_prog.group(4) and m_prog.group(5):
                            speed_str = f" | {m_prog.group(4)} {m_prog.group(5)}"

                        status_msg = f"Writing {current_part_name}: {pct_val:.1f}%{speed_str}"
                        if dual_progress_callback:
                            dual_progress_callback(overall_pct, file_pct, current_part_name, status_msg)
                    except Exception:
                        pass
                elif "%" in line:
                    try:
                        raw_pct = line.split("%")[0].split()[-1]
                        val = float(raw_pct)
                        file_pct = val / 100.0
                        total_parts = max(len(part_list), 1)
                        part_weight = 1.0 / total_parts
                        overall_pct = min(1.0, (current_part_idx * part_weight) + (file_pct * part_weight))

                        if dual_progress_callback:
                            dual_progress_callback(overall_pct, file_pct, current_part_name, f"Writing {current_part_name}: {val:.1f}%")
                    except Exception:
                        pass

            self.current_process.stdout.close()
            return_code = self.current_process.wait()

            if return_code == 0:
                self.logger.success(f"{op_name} Completed Successfully (100%)!")
                if dual_progress_callback:
                    dual_progress_callback(1.0, 1.0, "Done", "Flashing Finished 100%!")
                return True
            else:
                self.logger.error(f"❌ {op_name} FAILED! Process stopped (Exit Code {return_code}).")
                if dual_progress_callback:
                    dual_progress_callback(0.0, 0.0, "Failed", f"Stopped: Code {return_code}")
                return False

        except Exception as e:
            self.logger.error(f"Error during {op_name}: {str(e)}")
            return False
        finally:
            self.is_flashing = False
            self.current_process = None

    def _run_command_stream(self, cmd, progress_callback, op_name):
        self.is_flashing = True
        try:
            self.logger.info(f"Starting {op_name}...")
            self.logger.brom("WAITING FOR PHONE... (Connect Test Point to Ground, plug USB cable)")

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in iter(self.current_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue

                if "error" in line.lower() or "failed" in line.lower():
                    self.logger.error(line)
                elif "success" in line.lower() or "done" in line.lower() or "ok" in line.lower():
                    self.logger.success(line)
                elif "waiting for" in line.lower() or "reconnect" in line.lower():
                    self.logger.brom(line)
                elif "brom" in line.lower() or "preloader" in line.lower() or "da" in line.lower() or "handshake" in line.lower():
                    self.logger.brom(line)
                else:
                    self.logger.info(line)

                if "%" in line:
                    try:
                        part = line.split("%")[0].split()[-1]
                        pct = float(part) / 100.0
                        if progress_callback:
                            progress_callback(pct)
                    except Exception:
                        pass

            self.current_process.stdout.close()
            return_code = self.current_process.wait()

            if return_code == 0:
                self.logger.success(f"{op_name} Completed Successfully!")
                if progress_callback:
                    progress_callback(1.0)
                return True
            else:
                self.logger.error(f"❌ {op_name} FAILED! Process stopped (Exit Code {return_code}).")
                if progress_callback:
                    progress_callback(0.0)
                return False

        except Exception as e:
            self.logger.error(f"Error during {op_name}: {str(e)}")
            return False
        finally:
            self.is_flashing = False
            self.current_process = None
