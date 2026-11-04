import os
import xml.etree.ElementTree as ET
from utils.file_utils import format_bytes

class QualcommXMLParser:
    """Parses Qualcomm rawprogram*.xml and patch*.xml files."""

    @staticmethod
    def parse_rawprogram(xml_path: str, firmware_dir: str = None) -> list:
        """
        Parses rawprogram*.xml file.
        Returns a list of partition dictionaries:
        [{
            "name": str,
            "filename": str,
            "file_path": str or None,
            "exists": bool,
            "file_size": int,
            "file_size_human": str,
            "start_sector": int,
            "num_sectors": int,
            "sector_size": int,
            "sparse": bool,
            "physical_partition": int,
            "is_checked": bool
        }, ...]
        """
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"RawProgram XML file not found: {xml_path}")

        if not firmware_dir:
            firmware_dir = os.path.dirname(xml_path)

        partitions = []
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for elem in root.findall("program"):
                attrs = elem.attrib

                label = attrs.get("label", "").strip()
                filename = attrs.get("filename", "").strip()
                if not label:
                    continue

                # Parse sector numbers
                start_sector_str = attrs.get("start_sector", "0").strip()
                num_sectors_str = attrs.get("num_partition_sectors", "0").strip()
                sector_size_str = attrs.get("SECTOR_SIZE_IN_BYTES", "512").strip()

                try:
                    start_sector = int(start_sector_str, 16) if start_sector_str.startswith("0x") else int(start_sector_str)
                except Exception:
                    start_sector = 0

                try:
                    num_sectors = int(num_sectors_str, 16) if num_sectors_str.startswith("0x") else int(num_sectors_str)
                except Exception:
                    num_sectors = 0

                try:
                    sector_size = int(sector_size_str, 16) if sector_size_str.startswith("0x") else int(sector_size_str)
                except Exception:
                    sector_size = 512

                sparse = attrs.get("sparse", "false").lower() == "true"
                raw_lun = attrs.get("physical_partition_number") or attrs.get("lun") or attrs.get("LUN") or "0"
                try:
                    phys_part = int(raw_lun)
                except Exception:
                    phys_part = 0

                # Check file existence
                file_path = None
                exists = False
                file_size = 0
                file_size_human = "--"

                if filename and filename.lower() not in ("", "none", "null"):
                    candidate = os.path.join(firmware_dir, filename)
                    if os.path.exists(candidate):
                        file_path = candidate
                        exists = True
                        file_size = os.path.getsize(candidate)
                        file_size_human = format_bytes(file_size)
                    else:
                        file_size_human = "Missing"

                part_data = {
                    "name": label,
                    "filename": filename if filename else "NONE",
                    "file_path": file_path,
                    "exists": exists,
                    "file_size": file_size,
                    "file_size_human": file_size_human,
                    "start_sector": start_sector,
                    "num_sectors": num_sectors,
                    "sector_size": sector_size,
                    "sparse": sparse,
                    "physical_partition": phys_part,
                    "lun": phys_part,
                    "is_checked": exists and file_size > 0
                }
                partitions.append(part_data)

            return partitions
        except Exception as e:
            raise RuntimeError(f"Failed to parse RawProgram XML: {str(e)}")

    @classmethod
    def parse_all_rawprograms(cls, firmware_dir: str) -> list:
        """
        Scans firmware directory for all rawprogram*.xml files (UFS LUN 0 to 5)
        and parses them into a unified list of partitions with their respective LUN.
        """
        import glob
        if not os.path.isdir(firmware_dir):
            return []

        xml_files = sorted(glob.glob(os.path.join(firmware_dir, "rawprogram*.xml")))
        if not xml_files:
            return []

        all_partitions = []
        seen = set()
        for xml_path in xml_files:
            try:
                parts = cls.parse_rawprogram(xml_path, firmware_dir)
                for p in parts:
                    key = (p["name"], p["lun"], p["start_sector"])
                    if key not in seen:
                        seen.add(key)
                        all_partitions.append(p)
            except Exception:
                continue

        return all_partitions

    @staticmethod
    def parse_patch(patch_path: str) -> list:
        """
        Parses patch*.xml file.
        Returns a list of patch instructions.
        """
        if not os.path.exists(patch_path):
            return []

        patches = []
        try:
            tree = ET.parse(patch_path)
            root = tree.getroot()

            for elem in root.findall("patch"):
                attrs = elem.attrib
                patches.append({
                    "start_sector": attrs.get("start_sector", "0"),
                    "byte_offset": attrs.get("byte_offset", "0"),
                    "value": attrs.get("value", "0"),
                    "size_in_bytes": attrs.get("size_in_bytes", "4"),
                    "filename": attrs.get("filename", "DISK"),
                    "SECTOR_SIZE_IN_BYTES": attrs.get("SECTOR_SIZE_IN_BYTES", "512"),
                    "physical_partition_number": attrs.get("physical_partition_number", "0")
                })
            return patches
        except Exception:
            return []
