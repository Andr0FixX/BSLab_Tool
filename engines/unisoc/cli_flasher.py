import sys
import os
import argparse
import time

# Ensure repository root is in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from engines.unisoc.spd_engine import UnisocEngine
from engines.unisoc.pac_parser import PacParser

class ConsoleLogger:
    """Standardized logger routing engine output to stdout for UI capture."""
    def info(self, msg):
        print(f"[*] {msg}", flush=True)

    def success(self, msg):
        print(f"[+] {msg}", flush=True)

    def error(self, msg):
        print(f"[-] ERROR: {msg}", flush=True)

    def warn(self, msg):
        print(f"[!] WARNING: {msg}", flush=True)

    def brom(self, msg):
        print(f"[*] {msg}", flush=True)

def main():
    parser = argparse.ArgumentParser(description="BSLab Tool - Unisoc Physical PAC Flasher & Servicing Engine")
    parser.add_argument("--port", required=True, help="COM port name (e.g. COM36)")
    parser.add_argument("--pac", default=None, help="Path to .PAC firmware archive (optional for service routines)")
    parser.add_argument("--action", default="flash", choices=["flash", "reset-frp", "factory-reset", "read-info", "erase-partition"], help="Action to execute")
    parser.add_argument("--partitions", default="", help="Comma-separated list of partitions to flash (or empty for all)")
    parser.add_argument("--partition-name", default="persist", help="Single partition name for erase-partition action")
    parser.add_argument("--erase-userdata", action="store_true", help="Format userdata after flashing")
    parser.add_argument("--keep-calib", action="store_true", default=True, help="Preserve NVRAM/RF calibration")
    parser.add_argument("--no-reboot", action="store_true", help="Do not reboot phone after flashing")

    args = parser.parse_args()

    port = args.port.strip()
    action = args.action.strip().lower()
    pac_path = os.path.abspath(args.pac.strip('\"')) if args.pac else None

    print("══════════════════════════════════════════════════════════════", flush=True)
    print("🚀 [BS LAB TOOL] UNISOC HARDWARE FLASH & SERVICE ENGINE ONLINE", flush=True)
    print(f"[*] Port Target     : {port}", flush=True)
    print(f"[*] Active Routine  : {action.upper()}", flush=True)
    if pac_path:
        print(f"[*] Firmware Archive: {os.path.basename(pac_path)}", flush=True)
    print("══════════════════════════════════════════════════════════════", flush=True)

    if action == "flash":
        if not pac_path or not os.path.exists(pac_path):
            print(f"[-] ERROR: PAC file does not exist: {pac_path}", flush=True)
            sys.exit(1)

    logger = ConsoleLogger()
    engine = UnisocEngine(logger=logger)

    def progress_callback(overall_pct, part_pct, part_name, status_text):
        overall_int = int(overall_pct * 100) if overall_pct <= 1.0 else int(overall_pct)
        part_int = int(part_pct * 100) if part_pct <= 1.0 else int(part_pct)
        print(f"[PROGRESS: {overall_int}%] [{part_name}] {status_text} ({part_int}%)", flush=True)

    try:
        reboot = not args.no_reboot
        if action == "reset-frp":
            print("[*] Committing 1-Click Unisoc FRP Lock Erase...", flush=True)
            success = engine.reset_frp(port_name=port, pac_path=pac_path, progress_cb=lambda pct, msg: print(f"[PROGRESS: {int(pct*100)}%] {msg}", flush=True))
        elif action == "factory-reset":
            print("[*] Committing 1-Click Unisoc Factory Reset (Userdata Wipe)...", flush=True)
            success = engine.factory_reset(port_name=port, pac_path=pac_path, progress_cb=lambda pct, msg: print(f"[PROGRESS: {int(pct*100)}%] {msg}", flush=True))
        elif action == "read-info":
            info = engine.read_device_info(port_name=port, pac_path=pac_path)
            success = info is not None
        elif action == "erase-partition":
            part = args.partition_name
            print(f"[*] Committing Direct Partition Erase for '{part}'...", flush=True)
            if not engine.connect(port, pac_path):
                print(f"[-] Failed to establish FDL connection on {port}.", flush=True)
                sys.exit(1)
            success = engine.fdl_engine.erase_partition(part)
            if reboot:
                engine.fdl_engine.reboot()
        else: # flash
            selected_names = [p.strip().lower() for p in args.partitions.split(",") if p.strip()]
            partitions_to_flash = None
            if selected_names and "all" not in selected_names:
                partitions_to_flash = [{"name": name} for name in selected_names]
                print(f"[*] Selective Mode Active: Flashing {len(partitions_to_flash)} requested partitions.", flush=True)
            else:
                print("[*] Full Flash Mode Active: Flashing all enabled firmware partitions.", flush=True)

            success = engine.flash_pac(
                port_name=port,
                pac_path=pac_path,
                partitions_to_flash=partitions_to_flash,
                reboot_after=reboot,
                dual_progress_cb=progress_callback
            )

            if success and args.erase_userdata and engine.fdl_engine:
                print("[*] Formatting Userdata partition for fresh start...", flush=True)
                engine.fdl_engine.erase_partition("userdata")

        if success:
            print("══════════════════════════════════════════════════════════════", flush=True)
            print(f"[✅] UNISOC {action.upper()} COMPLETED WITH ZERO ERRORS!", flush=True)
            print("══════════════════════════════════════════════════════════════", flush=True)
            sys.exit(0)
        else:
            print(f"[-] Operation '{action}' failed or stopped by device controller.", flush=True)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[-] Operation aborted by technician.", flush=True)
        engine.abort()
        sys.exit(2)
    except Exception as e:
        print(f"[-] Fatal Exception in {action}: {str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
