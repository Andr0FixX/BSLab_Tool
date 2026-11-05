"""
BSLab Tool PRO - GPT (GUID Partition Table) Binary Forensic Parser
Parses primary and backup GPT partition tables to extract partition maps,
sector offsets, sizes, and attributes for low-level surgical repair.
"""

import uuid
import struct
from typing import Dict, Any, List, Optional
from .signatures import PartitionSignatures

class GPTPartitionEntry:
    """Represents a single partition parsed from GPT."""
    def __init__(self, name: str, start_lba: int, end_lba: int, attributes: int, type_guid: str, unique_guid: str, sector_size: int = 512):
        self.name = name.strip()
        self.start_lba = start_lba
        self.end_lba = end_lba
        self.attributes = attributes
        self.type_guid = type_guid
        self.unique_guid = unique_guid
        self.sector_size = sector_size
        self.num_sectors = (end_lba - start_lba + 1) if end_lba >= start_lba else 0
        self.size_bytes = self.num_sectors * sector_size
        self.size_mb = round(self.size_bytes / (1024 * 1024), 2)
        self.size_gb = round(self.size_bytes / (1024 * 1024 * 1024), 2)
        self.is_protected = PartitionSignatures.is_protected(self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_lba": self.start_lba,
            "end_lba": self.end_lba,
            "num_sectors": self.num_sectors,
            "size_bytes": self.size_bytes,
            "size_mb": self.size_mb,
            "size_gb": self.size_gb,
            "is_protected": self.is_protected,
            "type_guid": self.type_guid,
            "unique_guid": self.unique_guid,
            "attributes": hex(self.attributes)
        }

    def __repr__(self):
        return f"<GPT Entry '{self.name}' Start:{self.start_lba} End:{self.end_lba} Size:{self.size_mb}MB Protected:{self.is_protected}>"


class GPTParser:
    """
    Forensic parser for EFI / GUID Partition Tables.
    Accepts raw disk binary data (typically first 34 sectors = 17,408 bytes).
    """

    @staticmethod
    def parse(gpt_binary_data: bytes, sector_size: int = 512) -> Dict[str, Any]:
        """
        Parses GPT header and all partition entries.
        """
        if len(gpt_binary_data) < sector_size * 2:
            return {"valid": False, "error": f"Data too short (<{sector_size * 2} bytes)"}

        # LBA 1: Header starts at offset = sector_size
        hdr_offset = sector_size
        hdr_bytes = gpt_binary_data[hdr_offset:hdr_offset + 92]
        if len(hdr_bytes) < 92:
            return {"valid": False, "error": "Incomplete GPT header"}

        # GPT Header struct:
        # signature (8s), revision (I), header_size (I), crc32 (I), reserved (I),
        # current_lba (Q), backup_lba (Q), first_usable_lba (Q), last_usable_lba (Q),
        # disk_guid (16s), partition_entry_lba (Q), num_entries (I), entry_size (I), entries_crc32 (I)
        sig, rev, hdr_sz, crc, res, cur_lba, bak_lba, first_lba, last_lba, disk_guid_raw, entries_lba, num_entries, entry_sz = struct.unpack_from(
            "<8sIIIIQQQQ16sQII", hdr_bytes, 0
        )

        if sig != PartitionSignatures.GPT_MAGIC:
            return {"valid": False, "error": f"Invalid GPT Signature: {sig}"}

        disk_guid_str = str(uuid.UUID(bytes_le=disk_guid_raw))

        # Calculate partition entry array offset
        # entries_lba is usually 2 (i.e. sector 2 = offset sector_size * 2)
        entries_offset = entries_lba * sector_size
        partitions: List[GPTPartitionEntry] = []

        for i in range(num_entries):
            e_off = entries_offset + (i * entry_sz)
            if e_off + entry_sz > len(gpt_binary_data):
                break

            entry_data = gpt_binary_data[e_off:e_off + entry_sz]
            # Check if entry is empty
            if all(b == 0 for b in entry_data[:32]):
                continue

            type_guid_raw = entry_data[0:16]
            uniq_guid_raw = entry_data[16:32]
            start_lba, end_lba, attrs = struct.unpack_from("<QQQ", entry_data, 32)
            name_raw = entry_data[56:56 + 72] # 36 UTF-16LE characters

            try:
                name_str = name_raw.decode("utf-16le").split("\x00")[0].strip()
            except Exception:
                name_str = f"part_{i}"

            type_guid_str = str(uuid.UUID(bytes_le=type_guid_raw))
            uniq_guid_str = str(uuid.UUID(bytes_le=uniq_guid_raw))

            entry = GPTPartitionEntry(
                name=name_str,
                start_lba=start_lba,
                end_lba=end_lba,
                attributes=attrs,
                type_guid=type_guid_str,
                unique_guid=uniq_guid_str,
                sector_size=sector_size
            )
            partitions.append(entry)

        # Build quick name lookup map
        part_map = {p.name.lower(): p for p in partitions}

        return {
            "valid": True,
            "disk_guid": disk_guid_str,
            "sector_size": sector_size,
            "first_usable_lba": first_lba,
            "last_usable_lba": last_lba,
            "total_partitions": len(partitions),
            "partitions": [p.to_dict() for p in partitions],
            "partition_map": part_map
        }
