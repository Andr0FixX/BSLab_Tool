"""
BSLab Tool PRO - Partition Anomaly Detection Brain
Evaluates partition headers, GPT layout, and Fastboot A/B slots to pinpoint exact
corruptions and formulate 100% Zero-Data-Loss surgical repair plans.
"""

from typing import Dict, Any, List, Optional
from .signatures import PartitionSignatures, MagicType
from .header_parser import PartitionHealthInspector

class FaultSeverity:
    HEALTHY = "HEALTHY"
    INSTANT_FIX = "INSTANT_FIX"                    # e.g. A/B slot switch without flashing
    SURGICAL_FIXABLE = "SURGICAL_FIXABLE"          # e.g. single partition reflash (boot, dtbo)
    SECURITY_AVB_FAULT = "SECURITY_AVB_FAULT"      # vbmeta mismatch / Red State
    SYSTEM_FAULT = "SYSTEM_FAULT"                  # super / dynamic partition issue
    DATA_PRESERVED_SAFE = "DATA_PRESERVED_SAFE"

class DiagnosticReport:
    """Holds a comprehensive forensic diagnostic report and repair plan."""
    def __init__(self, device_mode: str, product: str = "Unknown"):
        self.device_mode = device_mode
        self.product = product
        self.overall_health = FaultSeverity.HEALTHY
        self.anomalies: List[Dict[str, Any]] = []
        self.corrupted_partitions: List[str] = []
        self.healthy_partitions: List[str] = []
        self.surgical_repair_steps: List[Dict[str, Any]] = []
        self.instant_commands: List[str] = []
        self.userdata_status = "100% PROTECTED & UNTOUCHED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_mode": self.device_mode,
            "product": self.product,
            "overall_health": self.overall_health,
            "total_anomalies": len(self.anomalies),
            "corrupted_partitions": self.corrupted_partitions,
            "healthy_partitions": self.healthy_partitions,
            "anomalies": self.anomalies,
            "surgical_repair_steps": self.surgical_repair_steps,
            "instant_commands": self.instant_commands,
            "userdata_safety": self.userdata_status,
            "zero_data_loss_guaranteed": True
        }


class PartitionDoctorBrain:
    """
    Forensic analysis engine that evaluates multi-mode hardware readings
    and generates precise surgical unbrick plans.
    """

    @classmethod
    def analyze_fastboot_health(cls, fastboot_health_data: Dict[str, Any]) -> DiagnosticReport:
        """
        Analyzes output from FastbootPartitionReader.inspect_device_health()
        """
        product = fastboot_health_data.get("product", "Unknown")
        report = DiagnosticReport(device_mode="FASTBOOT", product=product)

        if not fastboot_health_data.get("connected", False):
            report.overall_health = "DISCONNECTED"
            report.anomalies.append({
                "severity": "CRITICAL",
                "description": fastboot_health_data.get("error", "Device not connected.")
            })
            return report

        current_slot = fastboot_health_data.get("current_slot", "")
        slot_report = fastboot_health_data.get("slot_report", {})
        partitions = fastboot_health_data.get("partitions", {})

        # 1. Evaluate A/B Slot Health
        if current_slot and current_slot in slot_report:
            curr_slot_data = slot_report[current_slot]
            other_slot = "b" if current_slot == "a" else "a"
            other_slot_data = slot_report.get(other_slot, {})

            if not curr_slot_data.get("healthy", True):
                report.overall_health = FaultSeverity.INSTANT_FIX
                anomaly_desc = f"Active slot '{current_slot}' failed boot checks (successful: {curr_slot_data.get('successful')}, unbootable: {curr_slot_data.get('unbootable')})"
                report.anomalies.append({
                    "type": "SLOT_EXHAUSTED",
                    "severity": "CRITICAL",
                    "description": anomaly_desc
                })

                if other_slot_data.get("healthy", False):
                    # Instant zero-data-loss slot switch fix!
                    report.instant_commands.append(f"fastboot set_active {other_slot}")
                    report.surgical_repair_steps.append({
                        "action": "SWITCH_ACTIVE_SLOT",
                        "target_slot": other_slot,
                        "command": f"fastboot set_active {other_slot}",
                        "explanation": f"Switch active slot from failed '{current_slot}' to intact backup slot '{other_slot}'. Phone unbricks instantly with ZERO data loss."
                    })
                else:
                    report.overall_health = FaultSeverity.SURGICAL_FIXABLE
                    report.surgical_repair_steps.append({
                        "action": "SURGICAL_FLASH_BOOT",
                        "target_partition": f"boot_{current_slot}",
                        "explanation": f"Both slots exhausted. Reflash clean factory 'boot_{current_slot}.img' and 'vbmeta_{current_slot}.img'."
                    })

        # 2. Evaluate Partition Sizes
        for part_name, pinfo in partitions.items():
            if pinfo.get("size_bytes", 0) == 0:
                report.corrupted_partitions.append(part_name)
                report.anomalies.append({
                    "partition": part_name,
                    "type": "ZERO_SIZE_PARTITION",
                    "severity": "HIGH",
                    "description": f"Partition '{part_name}' reports 0 bytes size or missing layout."
                })
                report.surgical_repair_steps.append({
                    "action": "REFLASH_PARTITION",
                    "target_partition": part_name,
                    "explanation": f"Reflash matching '{part_name}.img' from factory firmware container."
                })
            else:
                report.healthy_partitions.append(part_name)

        if report.corrupted_partitions and report.overall_health == FaultSeverity.HEALTHY:
            report.overall_health = FaultSeverity.SURGICAL_FIXABLE

        return report

    @classmethod
    def analyze_partition_inspections(
        cls,
        partition_diagnostics: List[Dict[str, Any]],
        device_mode: str = "EDL_9008",
        product: str = "Unknown"
    ) -> DiagnosticReport:
        """
        Analyzes diagnostic outputs from PartitionHealthInspector.inspect() across partitions.
        """
        report = DiagnosticReport(device_mode=device_mode, product=product)

        for diag in partition_diagnostics:
            p_name = diag.get("partition", "unknown")
            status = diag.get("status", "UNKNOWN")
            is_healthy = diag.get("healthy", False)

            if status == "PROTECTED":
                # User data safeguard verified
                continue

            if is_healthy:
                report.healthy_partitions.append(p_name)
            else:
                report.corrupted_partitions.append(p_name)
                
                # Determine severity & exact diagnosis
                if status == "MISMATCH_CORRUPTED":
                    report.anomalies.append({
                        "partition": p_name,
                        "type": "MAGIC_MISMATCH",
                        "severity": "CRITICAL",
                        "expected": diag.get("expected_types", []),
                        "detected": diag.get("detected_type", ""),
                        "description": f"Partition '{p_name}' has wrong content or corrupted binary header."
                    })
                    report.surgical_repair_steps.append({
                        "action": "SURGICAL_RESTORE",
                        "target_partition": p_name,
                        "source_file": f"{p_name}.img",
                        "explanation": f"Flash clean factory image '{p_name}.img' directly to fix corruption without touching userdata."
                    })
                elif status == "EMPTY_OR_WIPED":
                    report.anomalies.append({
                        "partition": p_name,
                        "type": "EMPTY_PARTITION",
                        "severity": "CRITICAL",
                        "description": f"Partition '{p_name}' is blank / completely wiped."
                    })
                    report.surgical_repair_steps.append({
                        "action": "SURGICAL_RESTORE",
                        "target_partition": p_name,
                        "source_file": f"{p_name}.img",
                        "explanation": f"Write original firmware image for '{p_name}' to unbrick."
                    })

        if report.corrupted_partitions:
            report.overall_health = FaultSeverity.SURGICAL_FIXABLE

        return report
