"""
BSLab Tool PRO - Fastboot Partition & Variable Doctor
Reads fastboot variables, inspects A/B slots, verifies partition existence and sizes,
and detects boot failures or corrupted slots.
"""

import subprocess
from typing import Dict, Any, List, Optional
from core.path_utils import get_platform_tool_path

class FastbootPartitionReader:
    """
    Interrogates connected fastboot devices via 'fastboot getvar' commands
    to assess bootloader health, slot health, and partition state.
    """

    _CREATE_NO_WINDOW = 0x08000000

    def __init__(self, serial: Optional[str] = None):
        self.serial = serial
        self.fastboot_bin = get_platform_tool_path("fastboot")

    def _run_cmd(self, args: List[str], timeout: int = 4) -> str:
        cmd = [self.fastboot_bin]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=self._CREATE_NO_WINDOW
            )
            # Fastboot writes getvar outputs to stderr on many versions!
            return (res.stdout or "") + "\n" + (res.stderr or "")
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_all_variables(self) -> Dict[str, str]:
        """
        Runs 'fastboot getvar all' and parses key-value pairs.
        """
        out = self._run_cmd(["getvar", "all"])
        variables = {}
        for line in out.splitlines():
            line = line.strip()
            if not line or "finished. total time:" in line.lower():
                continue
            # Strip '(bootloader) ' prefix if present
            if line.startswith("(bootloader)"):
                line = line[len("(bootloader)"):].strip()
            
            if ":" in line:
                parts = line.split(":", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                variables[k] = v
        return variables

    def inspect_device_health(self) -> Dict[str, Any]:
        """
        Performs a full fastboot partition and slot diagnostic.
        Returns health score, slot status, corrupted partitions, and instant unbrick recommendations.
        """
        vars_map = self.get_all_variables()
        if not vars_map:
            return {
                "connected": False,
                "error": "No fastboot response or device not detected in fastboot mode."
            }

        product = vars_map.get("product", "Unknown")
        unlocked_str = vars_map.get("unlocked", "").lower()
        is_unlocked = unlocked_str in ["yes", "true", "1"]
        is_userspace = vars_map.get("is-userspace", "").lower() in ["yes", "true"] # Fastbootd vs Bootloader
        current_slot = vars_map.get("current-slot", "").strip() # e.g. "a" or "b" or empty

        slot_report = {}
        if current_slot:
            # Device is A/B slot-aware!
            for s in ["a", "b"]:
                succ = vars_map.get(f"slot-successful:{s}", vars_map.get(f"slot-successful:_{s}", "unknown")).lower()
                unboot = vars_map.get(f"slot-unbootable:{s}", vars_map.get(f"slot-unbootable:_{s}", "unknown")).lower()
                retry = vars_map.get(f"slot-retry-count:{s}", vars_map.get(f"slot-retry-count:_{s}", "unknown"))
                
                is_healthy = (succ in ["yes", "true", "1"]) and (unboot not in ["yes", "true", "1"])
                slot_report[s] = {
                    "is_current": (s == current_slot),
                    "successful": succ,
                    "unbootable": unboot,
                    "retry_count": retry,
                    "healthy": is_healthy
                }

        # Inspect critical partitions
        critical_parts = ["boot", "vbmeta", "dtbo", "super", "system", "vendor", "recovery"]
        partitions_health = {}

        for part in critical_parts:
            # Check slot variant if A/B
            candidates = [part]
            if current_slot:
                candidates.insert(0, f"{part}_{current_slot}")

            for c in candidates:
                size_hex = vars_map.get(f"partition-size:{c}", None)
                ptype = vars_map.get(f"partition-type:{c}", "raw")
                if size_hex is not None:
                    try:
                        size_int = int(size_hex, 16) if size_hex.startswith("0x") else int(size_hex)
                    except Exception:
                        size_int = 0
                    
                    partitions_health[c] = {
                        "size_bytes": size_int,
                        "size_mb": round(size_int / (1024 * 1024), 2),
                        "type": ptype,
                        "healthy": (size_int > 0)
                    }

        # Anomaly Diagnosis Logic
        anomalies = []
        recommendations = []

        # Check A/B slot health
        if current_slot and current_slot in slot_report:
            curr_state = slot_report[current_slot]
            other_slot = "b" if current_slot == "a" else "a"
            other_state = slot_report.get(other_slot, {})

            if not curr_state["healthy"]:
                anomalies.append(
                    f"CRITICAL: Active slot '{current_slot}' marked unbootable or failed (successful: {curr_state['successful']}, unbootable: {curr_state['unbootable']})."
                )
                if other_state.get("healthy", False):
                    recommendations.append(
                        f"INSTANT FIX: Other slot '{other_slot}' is healthy! Run 'fastboot set_active {other_slot}' to unbrick instantly without data loss."
                    )
                else:
                    recommendations.append(
                        f"Both slots exhausted. Reflash clean boot_{current_slot} and vbmeta_{current_slot} images."
                    )

        # Check partition size anomalies
        for p, info in partitions_health.items():
            if not info["healthy"]:
                anomalies.append(f"CRITICAL: Partition '{p}' has size 0 or is invalid!")
                recommendations.append(f"Reflash '{p}' from matching factory firmware.")

        return {
            "connected": True,
            "product": product,
            "is_unlocked": is_unlocked,
            "is_fastbootd": is_userspace,
            "has_ab_slots": bool(current_slot),
            "current_slot": current_slot,
            "slot_report": slot_report,
            "partitions": partitions_health,
            "anomalies": anomalies,
            "recommendations": recommendations,
            "is_overall_healthy": (len(anomalies) == 0)
        }
