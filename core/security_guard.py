"""
BS Lab Tool v2.0 PRO — Automated Security Guard & NVRAM / EFS Safeguard Engine
Protects critical RF calibration, IMEI, Baseband, and NV partitions before
destructive flash/wipe operations to eliminate null IMEI and dead boot risks.
"""

import os
import json
import time
from datetime import datetime

class SecurityGuard:
    """Automated security partition shield for MTK, Qualcomm, and Unisoc."""

    BACKUP_ROOT = os.path.join(os.getcwd(), "backups", "security")
    HISTORY_FILE = os.path.join(BACKUP_ROOT, "backup_history.json")

    @classmethod
    def get_backup_dir(cls, platform: str, brand: str, model: str) -> str:
        """Generates a timestamped safe folder for backing up device radio/security partitions."""
        clean_p = "".join(c for c in platform if c.isalnum() or c in ("_", "-")) or "PLATFORM"
        clean_b = "".join(c for c in brand if c.isalnum() or c in ("_", "-")) or "BRAND"
        clean_m = "".join(c for c in model if c.isalnum() or c in ("_", "-")) or "MODEL"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = os.path.join(cls.BACKUP_ROOT, f"{clean_p}_{clean_b}_{clean_m}_{ts}")
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    @classmethod
    def record_history(cls, entry: dict):
        """Appends a backup manifest entry to backup_history.json."""
        try:
            os.makedirs(cls.BACKUP_ROOT, exist_ok=True)
            history = []
            if os.path.exists(cls.HISTORY_FILE):
                try:
                    with open(cls.HISTORY_FILE, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    history = []
            history.insert(0, entry)
            # Keep top 100 entries
            history = history[:100]
            with open(cls.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    @classmethod
    def auto_backup_mtk(cls, meta_engine, brand: str, model: str, custom_da=None, custom_pl=None, logger=None) -> str:
        """
        Automatically backs up MediaTek nvram, nvdata, nvcfg, protect1, protect2, proinfo.
        Returns backup directory path if successful, empty string if skipped or failed.
        """
        if not meta_engine:
            return ""

        out_dir = cls.get_backup_dir("MTK", brand, model)
        if logger:
            logger.info("==================================================")
            logger.info("🛡️ [SAFEGUARD] INITIATING AUTO-BACKUP OF SECURITY / NVRAM")
            logger.info(f"🛡️ Target Directory: {out_dir}")
            logger.info("==================================================")

        try:
            ok = meta_engine.backup_nvram_data(
                out_dir=out_dir,
                custom_da=custom_da,
                custom_preloader=custom_pl,
                progress_callback=None
            )
            if ok:
                files = os.listdir(out_dir)
                cls.record_history({
                    "platform": "MediaTek",
                    "brand": brand,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "folder": out_dir,
                    "files": files
                })
                if logger:
                    logger.success(f"🛡️ [SAFEGUARD] Backup Successful! {len(files)} partitions secured.")
                return out_dir
            else:
                if logger:
                    logger.warning("🛡️ [SAFEGUARD] Auto-backup did not return files. Continuing safely...")
                return ""
        except Exception as e:
            if logger:
                logger.warning(f"🛡️ [SAFEGUARD] Note during auto-backup: {e}")
            return ""

    @classmethod
    def auto_backup_qc(cls, qc_engine, port: str, prog: str, rawprog: str, brand: str, model: str, logger=None) -> str:
        """
        Automatically dumps Qualcomm modemst1, modemst2, fsg, fsc, persist partitions.
        """
        if not qc_engine or not rawprog or not os.path.exists(rawprog):
            return ""

        out_dir = cls.get_backup_dir("QC", brand, model)
        if logger:
            logger.info("==================================================")
            logger.info("🛡️ [SAFEGUARD] INITIATING AUTO-BACKUP OF QUALCOMM EFS / MODEM")
            logger.info(f"🛡️ Target Directory: {out_dir}")
            logger.info("==================================================")

        try:
            ok = qc_engine.backup_efs(
                port=port,
                prog_path=prog,
                rawprog_path=rawprog,
                out_dir=out_dir,
                progress_cb=None
            )
            if ok:
                files = os.listdir(out_dir)
                cls.record_history({
                    "platform": "Qualcomm",
                    "brand": brand,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "folder": out_dir,
                    "files": files
                })
                if logger:
                    logger.success(f"🛡️ [SAFEGUARD] Qualcomm EFS Backup Successful! {len(files)} partitions secured.")
                return out_dir
        except Exception as e:
            if logger:
                logger.warning(f"🛡️ [SAFEGUARD] Note during Qualcomm EFS backup: {e}")
        return ""

    @classmethod
    def auto_backup_spd(cls, spd_nv_engine, port: str, pac: str, brand: str, model: str, logger=None) -> str:
        """
        Automatically dumps Unisoc prodnv, fixnv, runtimenv calibration partitions.
        """
        if not spd_nv_engine:
            return ""

        out_dir = cls.get_backup_dir("UNISOC", brand, model)
        if logger:
            logger.info("==================================================")
            logger.info("🛡️ [SAFEGUARD] INITIATING AUTO-BACKUP OF UNISOC PRODNV / CALIBRATION")
            logger.info(f"🛡️ Target Directory: {out_dir}")
            logger.info("==================================================")

        try:
            ok = spd_nv_engine.backup_nv_partitions(
                port=port,
                pac_path=pac,
                out_dir=out_dir,
                progress_cb=None
            )
            if ok:
                files = os.listdir(out_dir)
                cls.record_history({
                    "platform": "Unisoc",
                    "brand": brand,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "folder": out_dir,
                    "files": files
                })
                if logger:
                    logger.success(f"🛡️ [SAFEGUARD] Unisoc NV Backup Successful! {len(files)} partitions secured.")
                return out_dir
        except Exception as e:
            if logger:
                logger.warning(f"🛡️ [SAFEGUARD] Note during Unisoc NV backup: {e}")
        return ""
