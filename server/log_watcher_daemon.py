#!/usr/bin/env python3
"""
BS LAB TOOL™ - AI Log Ingestion Daemon (Step 1)
==============================================
Continuously monitors C:\\BSLab_Tool\\logs\\ for new workshop servicing logs,
extracts real device hardware profiles, and streams them into the
AI Autonomous Database Updater.
"""

import os
import sys
import time
import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to sys.path to allow imports
SERVER_DIR = Path(__file__).resolve().parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from auto_database_updater import AutoDatabaseUpdater

LOGS_DIR = Path(r"c:\BSLab_Tool\logs")
DATA_DIR = SERVER_DIR / "data"
PROCESSED_LOGS_FILE = DATA_DIR / "processed_logs.json"
ACTIVITY_LOG_FILE = DATA_DIR / "daemon_activity.log"

DATA_DIR.mkdir(parents=True, exist_ok=True)

def log_activity(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted)
    try:
        with open(ACTIVITY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

class LogIngestionDaemon:
    def __init__(self, logs_dir: Path = LOGS_DIR):
        self.logs_dir = logs_dir
        self.updater = AutoDatabaseUpdater()
        self.processed_cache = self.load_processed_cache()

    def load_processed_cache(self) -> Dict[str, Any]:
        if PROCESSED_LOGS_FILE.exists():
            try:
                with open(PROCESSED_LOGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log_activity(f"[-] Warning: Failed to read processed cache: {e}")
        return {}

    def save_processed_cache(self):
        try:
            with open(PROCESSED_LOGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.processed_cache, f, indent=2)
        except Exception as e:
            log_activity(f"[-] Error saving processed cache: {e}")

    def parse_log_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Parses ADB, Fastboot, or Console log files into structured telemetry"""
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            log_activity(f"[-] Error reading {filepath.name}: {e}")
            return None

        telemetry: Dict[str, Any] = {
            "source_file": filepath.name,
            "file_size": filepath.stat().st_size,
            "mtime": filepath.stat().st_mtime,
            "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 1. Parse Key-Value Standard ADB format (Model : ..., Hardware : ...)
        for line in content.splitlines():
            line_str = line.strip()
            if ":" not in line_str:
                continue

            parts = line_str.split(":", 1)
            key = parts[0].strip().upper()
            val = parts[1].strip()

            if not val or val in ("Unknown", "N/A", "null"):
                continue

            if key in ("MODEL", "PRODUCT MODEL"):
                telemetry["model"] = val
            elif key in ("BRAND", "MANFCID", "MANUFACTURER"):
                if "brand" not in telemetry or telemetry["brand"] == "UNKNOWN":
                    telemetry["brand"] = val
            elif key in ("HARDWARE", "BOARD", "CHIPSET"):
                telemetry["hardware"] = val
            elif key in ("MODEM", "BASEBAND", "VERSION-BASEBAND"):
                telemetry["modem"] = val
            elif key in ("ANDROID VER", "VERSION-RELEASE", "OS VERSION"):
                telemetry["android_ver"] = val
            elif key in ("BUILD ID", "VERSION-BOOTLOADER", "BUILD"):
                telemetry["build_id"] = val
            elif key in ("SEC PATCH", "SECURITY PATCH"):
                telemetry["sec_patch"] = val
            elif key in ("FLAVOR ID", "FLAVOR"):
                telemetry["flavor_id"] = val
            elif key in ("REGION", "VENDORCOUNTRY"):
                telemetry["region"] = val
            elif key in ("LOCKSTATE", "BL UNLOCKED", "UNLOCKED"):
                telemetry["lock_state"] = val
            elif key in ("BOOTSTATE", "SECURE BOOT"):
                telemetry["boot_state"] = val
            elif "VER" in key or "UI" in key or "XOS" in key or "HIOS" in key or "ONEUI" in key:
                telemetry["ui_flavor"] = f"{parts[0].strip()}: {val}"

        # 2. Parse Fastboot specific lines (if AOSP getvar all format)
        if "model" not in telemetry:
            m_prod = re.search(r"Product\s*:\s*([^\r\n]+)", content, re.IGNORECASE)
            if m_prod:
                telemetry["model"] = m_prod.group(1).strip()
            else:
                m_mod = re.search(r"Model\s*:\s*([^\r\n]+)", content, re.IGNORECASE)
                if m_mod:
                    telemetry["model"] = m_mod.group(1).strip()

        # 3. Parse AutoHub Console lines (e.g. Selected Target Device : Infinix -> Alpha (X570))
        if "model" not in telemetry:
            m_target = re.search(r"Selected Target Device\s*:\s*([^->\r\n]+)\s*->\s*([^\r\n]+)", content, re.IGNORECASE)
            if m_target:
                telemetry["brand"] = m_target.group(1).strip()
                telemetry["model"] = m_target.group(2).strip()

        # 4. Smart Brand Auto-Inference for Fastboot and Minimal ADB logs
        if "model" in telemetry and telemetry["model"]:
            m_up = telemetry["model"].upper()
            region_up = telemetry.get("region", "").upper()
            hw_up = telemetry.get("hardware", "").upper()
            fw_up = telemetry.get("build_id", "").upper()
            extra_up = content.upper()

            if "brand" not in telemetry or telemetry["brand"] in ("UNKNOWN", "Unknown", ""):
                if any(x in m_up for x in ["RNE-", "ANE-", "POT-", "JNY-", "FIG-", "VTR-", "EML-", "CLT-", "HWI-", "PRA-", "STK-", "Y9", "Y7", "Y6"]) or "HW/" in region_up or "KIRIN" in hw_up or "HI6250" in hw_up or "HI3660" in hw_up or "HUAWEI" in extra_up:
                    telemetry["brand"] = "HUAWEI"
                elif any(x in m_up for x in ["CPH", "PCH", "PCK", "PAC", "PCD", "PEA", "PEC", "PEN"]) or "OPPO" in m_up or "COLOROS" in fw_up or "OPPO" in extra_up:
                    telemetry["brand"] = "OPPO"
                elif any(x in m_up for x in ["RMX", "REALME"]) or "REALME" in extra_up:
                    telemetry["brand"] = "REALME"
                elif any(x in m_up for x in ["X6", "X5", "INFINIX"]) or "INFINIX" in extra_up or "XOS" in extra_up:
                    telemetry["brand"] = "INFINIX"
                elif any(x in m_up for x in ["KG", "KF", "CG", "CK", "CD", "TECNO"]) or "TECNO" in extra_up or "HIOS" in extra_up:
                    telemetry["brand"] = "TECNO"
                elif any(x in m_up for x in ["SM-", "GT-", "SAMSUNG"]) or "SAMSUNG" in extra_up or "ONEUI" in extra_up:
                    telemetry["brand"] = "SAMSUNG"
                elif any(x in m_up for x in ["REDMI", "POCO", "M20", "M21", "220", "221", "230", "231", "240", "241"]) or "XIAOMI" in extra_up or "MIUI" in extra_up or "HYPEROS" in extra_up:
                    telemetry["brand"] = "XIAOMI"
                elif any(x in m_up for x in ["V20", "V21", "V22", "V23", "V19", "V18", "V17", "VIVO"]) or "VIVO" in extra_up or "FUNTOUCH" in extra_up:
                    telemetry["brand"] = "VIVO"
                elif any(x in m_up for x in ["CORAL", "FLAME", "SUNFISH", "BRAMBLE", "REDBIN", "BARBET", "ORIOLE", "RAVEN", "BLUEJAY", "PANTHER", "CHEETAH", "FELIX", "TANGORPRO", "LYNX", "AKITA", "SHIBA", "HUSKY"]) or "PIXEL" in extra_up:
                    telemetry["brand"] = "PIXEL"
                elif any(x in m_up for x in ["XT", "MOTO"]) or "MOTOROLA" in extra_up:
                    telemetry["brand"] = "MOTOROLA"
                elif any(x in m_up for x in ["ONEPLUS", "KB200", "IN20", "NE22", "CPH24", "CPH25"]) or "ONEPLUS" in extra_up or "OXYGENOS" in extra_up:
                    telemetry["brand"] = "ONEPLUS"

        # Check validity
        if "model" in telemetry and telemetry["model"] and "brand" in telemetry and telemetry["brand"]:
            return telemetry

        return None

    def process_file(self, filepath: Path, force: bool = False) -> bool:
        """Processes a single log file and streams to updater"""
        fname = filepath.name
        mtime = filepath.stat().st_mtime
        fsize = filepath.stat().st_size

        # Check if already processed (re-attempt if previously marked SKIPPED_NO_TELEMETRY)
        cached = self.processed_cache.get(fname)
        if cached and not force:
            if cached.get("mtime") == mtime and cached.get("size") == fsize and cached.get("status") != "SKIPPED_NO_TELEMETRY":
                return False

        telemetry = self.parse_log_file(filepath)
        if not telemetry:
            self.processed_cache[fname] = {
                "mtime": mtime,
                "size": fsize,
                "status": "SKIPPED_NO_TELEMETRY",
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            return False

        brand = telemetry.get("brand", "Unknown")
        model = telemetry.get("model", "Unknown")
        hardware = telemetry.get("hardware", "N/A")

        log_activity(f"[*] Ingested Log: {fname} => {brand} -> {model} [Chipset: {hardware}]")

        ok, msg = self.updater.learn_device(telemetry)
        log_activity(f"    └── AI Database Result: {msg}")

        self.processed_cache[fname] = {
            "mtime": mtime,
            "size": fsize,
            "brand": brand,
            "model": model,
            "hardware": hardware,
            "status": "LEARNED" if ok else "FAILED",
            "action": msg,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return True

    def scan_all(self, force: bool = False) -> int:
        """Scans all log files in logs directory"""
        if not self.logs_dir.exists():
            log_activity(f"[-] Logs directory does not exist: {self.logs_dir}")
            return 0

        log_files = sorted(
            list(self.logs_dir.glob("*.log")) + list(self.logs_dir.glob("*.txt")),
            key=lambda p: p.stat().st_mtime
        )
        log_activity(f"[*] Scanning {len(log_files)} total log files in {self.logs_dir}...")

        processed_count = 0
        for lf in log_files:
            if self.process_file(lf, force=force):
                processed_count += 1

        self.save_processed_cache()
        log_activity(f"[+] Scan Complete: {processed_count} new log files learned and ingested.")
        return processed_count

    def run_daemon(self, poll_interval: int = 5):
        """Continuous background daemon watcher loop"""
        log_activity(f"[*] 🚀 BS LAB AI Log Ingestion Daemon Started (Polling every {poll_interval}s)...")
        log_activity(f"[*] Listening on directory: {self.logs_dir}")
        try:
            while True:
                new_items = self.scan_all(force=False)
                if new_items > 0:
                    log_activity(f"[+] Synced {new_items} new devices to central model definitions.")
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            log_activity("[!] Daemon stopped by technician.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BS LAB TOOL AI Log Ingestion Daemon")
    parser.add_argument("--once", action="store_true", help="Scan existing logs once and exit")
    parser.add_argument("--watch", action="store_true", help="Run continuous background daemon")
    parser.add_argument("--force", action="store_true", help="Force re-processing of already processed logs")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds (default: 5)")

    args = parser.parse_args()
    daemon = LogIngestionDaemon()

    if args.watch:
        daemon.run_daemon(poll_interval=args.interval)
    else:
        daemon.scan_all(force=args.force)
