"""
BSLab Tool PRO - Qualcomm EDL (9008) Firehose Partition Reader
Reads GPT partition table via Firehose XML, streams 4KB headers of critical partitions,
and passes them to PartitionHealthInspector for zero-data-loss corruption diagnosis.
"""

from typing import Dict, Any, List, Optional
from .gpt_parser import GPTParser, GPTPartitionEntry
from .header_parser import PartitionHealthInspector

class EDLPartitionReader:
    """
    Interacts with Qualcomm EDL 9008 via Firehose protocol XML commands
    to inspect device partitions and magic byte headers without full ROM dumping.
    """

    CRITICAL_DIAGNOSTIC_PARTITIONS = [
        "boot", "boot_a", "boot_b",
        "recovery", "recovery_a", "recovery_b",
        "vbmeta", "vbmeta_a", "vbmeta_b",
        "dtbo", "dtbo_a", "dtbo_b",
        "abl", "abl_a", "abl_b",
        "xbl", "xbl_a", "xbl_b",
        "super"
    ]

    def __init__(self, qc_engine=None):
        self.qc_engine = qc_engine

    def parse_gpt_from_bytes(self, raw_gpt_bytes: bytes, sector_size: int = 512) -> Dict[str, Any]:
        """
        Parses raw GPT bytes obtained from Firehose read of sectors 0 to 34.
        """
        return GPTParser.parse(raw_gpt_bytes, sector_size=sector_size)

    def diagnose_partitions_from_headers(
        self,
        gpt_result: Dict[str, Any],
        header_stream_callback
    ) -> List[Dict[str, Any]]:
        """
        Takes parsed GPT result and a callback function:
            header_stream_callback(part_name: str, start_lba: int, num_sectors: int) -> bytes
        Reads each critical partition's first 4KB (8 sectors) and returns full forensic diagnosis.
        """
        if not gpt_result.get("valid", False):
            return [{"error": "Invalid GPT table", "status": "FAILED"}]

        part_map = gpt_result.get("partition_map", {})
        diagnostic_reports = []

        for p_name in self.CRITICAL_DIAGNOSTIC_PARTITIONS:
            entry: Optional[GPTPartitionEntry] = part_map.get(p_name.lower())
            if not entry:
                continue

            try:
                # Read first 8 sectors (4096 bytes)
                raw_chunk = header_stream_callback(entry.name, entry.start_lba, 8)
                diag = PartitionHealthInspector.inspect(entry.name, raw_chunk)
                diag["start_lba"] = entry.start_lba
                diag["size_mb"] = entry.size_mb
                diagnostic_reports.append(diag)
            except Exception as e:
                diagnostic_reports.append({
                    "partition": entry.name,
                    "status": "READ_ERROR",
                    "healthy": False,
                    "error": str(e),
                    "safe_to_flash": True
                })

        return diagnostic_reports
