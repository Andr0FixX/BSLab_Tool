"""
BSLab Tool PRO - Surgical Partition Doctor Engine
Package initialization
"""

from .signatures import PartitionSignatures, MagicType
from .header_parser import (
    PartitionHealthInspector,
    BootHeaderParser,
    AVBHeaderParser,
    DTBOHeaderParser,
    ELFHeaderParser
)
from .fastboot_reader import FastbootPartitionReader
from .gpt_parser import GPTParser, GPTPartitionEntry
from .edl_reader import EDLPartitionReader

__all__ = [
    "PartitionSignatures",
    "MagicType",
    "PartitionHealthInspector",
    "BootHeaderParser",
    "AVBHeaderParser",
    "DTBOHeaderParser",
    "ELFHeaderParser",
    "FastbootPartitionReader",
    "GPTParser",
    "GPTPartitionEntry",
    "EDLPartitionReader"
]
