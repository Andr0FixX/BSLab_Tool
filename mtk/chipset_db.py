class MtkChipsetDatabase:
    """Database mapping MTK Hardware Codes (HW_CODE) to Chipset names and specifications."""

    CHIPSETS = {
        0x0321: {"soc": "MT6735", "name": "Quad-core Cortex-A53 64-bit", "family": "Legacy 4G"},
        0x0335: {"soc": "MT6737", "name": "Entry Quad-core 4G", "family": "Legacy 4G"},
        0x0326: {"soc": "MT6739", "name": "Modern Entry Quad-core", "family": "Helio Series"},
        0x0717: {"soc": "MT6761", "name": "Helio A22 / A20", "family": "Helio Series"},
        0x0658: {"soc": "MT6765", "name": "Helio P35 / G35 / G37", "family": "Helio Series"},
        0x0766: {"soc": "MT6768", "name": "Helio G80 / G85", "family": "Helio Gaming"},
        0x0707: {"soc": "MT6771", "name": "Helio P60 / P70", "family": "Helio Series"},
        0x0679: {"soc": "MT6779", "name": "Helio P90", "family": "Helio High-End"},
        0x0788: {"soc": "MT6785", "name": "Helio G90 / G90T / G95", "family": "Helio Gaming"},
        0x0699: {"soc": "MT6781", "name": "Helio G96 / G99", "family": "Helio Gaming 6nm"},
        0x0816: {"soc": "MT6873", "name": "Dimensity 800 / 800U", "family": "Dimensity 5G"},
        0x0817: {"soc": "MT6877", "name": "Dimensity 900 / 920 / 1080", "family": "Dimensity 5G"},
        0x0842: {"soc": "MT6833", "name": "Dimensity 700 / 6020 / 6080", "family": "Dimensity 5G"},
        0x0866: {"soc": "MT6893", "name": "Dimensity 1200 / 1300", "family": "Dimensity Flagship"},
        0x0922: {"soc": "MT6895", "name": "Dimensity 8100 / 8000", "family": "Dimensity High-End"},
        0x0989: {"soc": "MT6983", "name": "Dimensity 9000 / 9000+", "family": "Dimensity Ultra"},
        0x6572: {"soc": "MT6572", "name": "Dual-Core 3G (Legacy)", "family": "Legacy 3G"},
        0x6580: {"soc": "MT6580", "name": "Quad-Core 3G (Legacy)", "family": "Legacy 3G"},
        0x6582: {"soc": "MT6582", "name": "Quad-Core 3G (Legacy)", "family": "Legacy 3G"},
        0x6592: {"soc": "MT6592", "name": "Octa-Core 3G (Legacy)", "family": "Legacy 3G"},
    }

    @classmethod
    def lookup(cls, hw_code: int):
        if hw_code in cls.CHIPSETS:
            return cls.CHIPSETS[hw_code]
        return {
            "soc": f"MT{hw_code:04X}",
            "name": f"Unknown SoC (0x{hw_code:04X})",
            "family": "MediaTek Universal"
        }
