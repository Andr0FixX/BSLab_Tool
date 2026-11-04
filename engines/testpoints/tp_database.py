"""
Test Point (TP) Pinout Database for GSM Servicing.
Provides hardware pinout locations, schematic coordinates, chipset types,
connection modes, and step-by-step instructions.
"""

TEST_POINT_DATABASE = {
    # -------------------------------------------------------------------------
    # INFINIX & TECNO (TRANSSION)
    # -------------------------------------------------------------------------
    "Infinix Hot 12 Play (X6816)": {
        "brand": "Infinix",
        "chipset": "Unisoc Tiger T610 / MediaTek MT6765",
        "mode": "BROM / BSL Mode (Force Handshake)",
        "difficulty": "Easy (Pads near SIM Tray)",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Locate the golden CLK test point beside the eMMC shielding can.\n"
            "3. Short the red CLK pad to motherboard ground (GND shield) with tweezers.\n"
            "4. Insert USB cable while holding short for 2 seconds.\n"
            "5. Release tweezers as soon as tool detects BSL / BROM COM port."
        ),
        "schematic": {
            "board_color": "#1E3A2F",
            "cpu_pos": (220, 140, 120, 110),
            "emmc_pos": (220, 270, 110, 100),
            "pmic_pos": (90, 180, 80, 80),
            "battery_pos": (80, 380, 120, 50),
            "sim_pos": (370, 120, 90, 160),
            "tp_pads": [
                {"name": "CLK (Test Point)", "pos": (345, 290), "color": "#EF4444", "is_signal": True},
                {"name": "GND (Shield)", "pos": (330, 335), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },
    "Infinix Smart 6 / 7 / 8": {
        "brand": "Infinix",
        "chipset": "Unisoc SC9863A / MediaTek Helio A22",
        "mode": "BROM / BSL Force Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Remove back glass and motherboard plastic frame.\n"
            "2. Unplug battery flex cable.\n"
            "3. Bridge the marked test point with motherboard copper ground.\n"
            "4. Plug in Type-C / Micro-USB cable to PC."
        ),
        "schematic": {
            "board_color": "#1B2A38",
            "cpu_pos": (200, 130, 130, 120),
            "emmc_pos": (200, 270, 100, 90),
            "pmic_pos": (80, 160, 70, 70),
            "battery_pos": (70, 370, 110, 50),
            "sim_pos": (360, 100, 90, 140),
            "tp_pads": [
                {"name": "CLK Pad", "pos": (315, 260), "color": "#EF4444", "is_signal": True},
                {"name": "GND Ground", "pos": (305, 305), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Tecno Spark 8 / 9 / 10 / Go": {
        "brand": "Tecno",
        "chipset": "MediaTek Helio G37 / Unisoc T606",
        "mode": "Force BROM / BSL",
        "difficulty": "Easy",
        "tp_type": "KCOLO / CLK to GND",
        "instructions": (
            "1. Detach battery flex.\n"
            "2. Short golden round pad KCOLO/CLK to metal shield.\n"
            "3. Connect USB cable. Once COM port connects, release pin."
        ),
        "schematic": {
            "board_color": "#1E3A2F",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (90, 150, 70, 70),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "KCOLO / CLK", "pos": (325, 245), "color": "#EF4444", "is_signal": True},
                {"name": "GND", "pos": (315, 290), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # XIAOMI / REDMI / POCO
    # -------------------------------------------------------------------------
    "Redmi 9A / 9C / 10A": {
        "brand": "Xiaomi",
        "chipset": "MediaTek Helio G25 / G35 (MT6762G/MT6765G)",
        "mode": "Force MTK BROM Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND (Preloader Crash / BROM)",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Locate the single gold pad labeled CLK right next to the PMIC shield.\n"
            "3. Short CLK pad to metal shielding can with tweezers.\n"
            "4. Insert USB cable. Tool triggers MediaTek USB Port (V1632)."
        ),
        "schematic": {
            "board_color": "#1A2238",
            "cpu_pos": (210, 120, 130, 120),
            "emmc_pos": (210, 260, 110, 100),
            "pmic_pos": (80, 170, 80, 80),
            "battery_pos": (80, 370, 120, 50),
            "sim_pos": (360, 130, 90, 150),
            "tp_pads": [
                {"name": "CLK TP", "pos": (330, 240), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (320, 280), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Redmi Note 8 (Ginkgo)": {
        "brand": "Xiaomi",
        "chipset": "Qualcomm Snapdragon 665 (SM6125)",
        "mode": "Qualcomm HS-USB QDLoader 9008 (EDL)",
        "difficulty": "Very Easy",
        "tp_type": "Dual EDL Pads",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Locate the two small round solder test points above the battery connector.\n"
            "3. Short BOTH test points together with curved tweezers.\n"
            "4. Plug in Type-C cable. Device enters Qualcomm 9008 EDL mode immediately."
        ),
        "schematic": {
            "board_color": "#22222E",
            "cpu_pos": (220, 130, 120, 120),
            "emmc_pos": (220, 270, 110, 100),
            "pmic_pos": (90, 160, 80, 80),
            "battery_pos": (90, 360, 120, 50),
            "sim_pos": (360, 120, 90, 150),
            "tp_pads": [
                {"name": "EDL TP 1", "pos": (145, 335), "color": "#EF4444", "is_signal": True},
                {"name": "EDL TP 2", "pos": (160, 335), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },
    "Poco X3 / X3 Pro (Surya/Bhima)": {
        "brand": "Xiaomi",
        "chipset": "Qualcomm Snapdragon 732G / 860",
        "mode": "Qualcomm HS-USB QDLoader 9008 (EDL)",
        "difficulty": "Moderate",
        "tp_type": "Dual EDL Pads",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Peel back black graphite thermal film above CPU shield.\n"
            "3. Short the two adjacent gold pads.\n"
            "4. Plug USB cable to connect Qualcomm 9008 port."
        ),
        "schematic": {
            "board_color": "#1C2430",
            "cpu_pos": (230, 140, 130, 130),
            "emmc_pos": (230, 290, 110, 100),
            "pmic_pos": (85, 170, 90, 85),
            "battery_pos": (85, 370, 120, 50),
            "sim_pos": (380, 120, 90, 160),
            "tp_pads": [
                {"name": "EDL 1", "pos": (205, 275), "color": "#EF4444", "is_signal": True},
                {"name": "EDL 2", "pos": (220, 275), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # VIVO & IQOO
    # -------------------------------------------------------------------------
    "Vivo Y21 / Y21s / Y33s": {
        "brand": "Vivo",
        "chipset": "MediaTek Helio P35 / G80 (MT6765 / MT6769)",
        "mode": "Force MTK BROM Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Locate the CLK resistor/pad beside the SIM card slot.\n"
            "3. Short test point to motherboard ground.\n"
            "4. Insert USB cable to connect MediaTek USB Port."
        ),
        "schematic": {
            "board_color": "#1E2A38",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 75),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "CLK Point", "pos": (335, 255), "color": "#EF4444", "is_signal": True},
                {"name": "GND Ground", "pos": (335, 295), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Vivo Y20 / Y20i (Snapdragon)": {
        "brand": "Vivo",
        "chipset": "Qualcomm Snapdragon 460 (SM4250)",
        "mode": "Qualcomm HS-USB QDLoader 9008",
        "difficulty": "Easy",
        "tp_type": "Dual EDL Pads",
        "instructions": (
            "1. Unplug battery flex.\n"
            "2. Bridge the 2 EDL pads near the sub-board FPC connector.\n"
            "3. Connect USB cable to enter EDL 9008."
        ),
        "schematic": {
            "board_color": "#1E3040",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "TP 1", "pos": (145, 335), "color": "#EF4444", "is_signal": True},
                {"name": "TP 2", "pos": (160, 335), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # OPPO & REALME
    # -------------------------------------------------------------------------
    "Realme C21Y / C25Y (Unisoc)": {
        "brand": "Realme",
        "chipset": "Unisoc Tiger T610 / T618",
        "mode": "Unisoc SPRD BSL / Diag Handshake",
        "difficulty": "Easy",
        "tp_type": "BSL Force TP to GND",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Locate the BSL test point beside the eMMC storage can.\n"
            "3. Short to metal frame GND.\n"
            "4. Insert USB cable to trigger Unisoc SPRD U2S Diag COM port."
        ),
        "schematic": {
            "board_color": "#2A1E38",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "BSL TP", "pos": (325, 270), "color": "#EF4444", "is_signal": True},
                {"name": "GND", "pos": (315, 310), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },
    "Realme C11 / C12 / C15 (MTK)": {
        "brand": "Realme",
        "chipset": "MediaTek Helio G35 (MT6765G)",
        "mode": "Force MTK BROM Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Short CLK pad to GND shield.\n"
            "3. Connect USB cable to enter MTK BROM mode."
        ),
        "schematic": {
            "board_color": "#2A281E",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "CLK", "pos": (330, 250), "color": "#EF4444", "is_signal": True},
                {"name": "GND", "pos": (320, 290), "color": "#10B981", "is_signal": False}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # SAMSUNG (GALAXY)
    # -------------------------------------------------------------------------
    "Samsung Galaxy A03 / A03s / A04": {
        "brand": "Samsung",
        "chipset": "Unisoc SC9863A / MediaTek Helio P35",
        "mode": "EDL / BROM Force",
        "difficulty": "Moderate",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Short CLK pad on motherboard to shielding can.\n"
            "3. Insert Type-C cable to enter flashing mode."
        ),
        "schematic": {
            "board_color": "#1C2A3A",
            "cpu_pos": (220, 140, 120, 110),
            "emmc_pos": (220, 270, 110, 100),
            "pmic_pos": (85, 170, 80, 80),
            "battery_pos": (85, 370, 120, 50),
            "sim_pos": (360, 120, 90, 150),
            "tp_pads": [
                {"name": "CLK", "pos": (335, 270), "color": "#EF4444", "is_signal": True},
                {"name": "GND", "pos": (320, 310), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },
    "Samsung Galaxy A12 / A13 (MTK)": {
        "brand": "Samsung",
        "chipset": "MediaTek Helio P35 (MT6765)",
        "mode": "Force MTK BROM Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Unplug battery flex.\n"
            "2. Short the golden CLK point to ground.\n"
            "3. Plug USB cable to PC."
        ),
        "schematic": {
            "board_color": "#1E2430",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "CLK", "pos": (330, 250), "color": "#EF4444", "is_signal": True},
                {"name": "GND", "pos": (320, 290), "color": "#10B981", "is_signal": False}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # ADDITIONAL POPULAR SMARTPHONES
    # -------------------------------------------------------------------------
    "Xiaomi Redmi Note 10 / 10 Pro": {
        "brand": "Xiaomi",
        "chipset": "Qualcomm Snapdragon 678 / 732G",
        "mode": "Qualcomm HS-USB QDLoader 9008 (EDL)",
        "difficulty": "Moderate",
        "tp_type": "Dual EDL Pads",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Locate the 2 tiny round EDL test points near the front camera flex.\n"
            "3. Bridge the two points together using fine-tip tweezers.\n"
            "4. Insert USB Type-C cable. Device enters EDL 9008."
        ),
        "schematic": {
            "board_color": "#1A2634",
            "cpu_pos": (220, 130, 125, 120),
            "emmc_pos": (220, 270, 110, 100),
            "pmic_pos": (85, 165, 80, 80),
            "battery_pos": (85, 365, 120, 50),
            "sim_pos": (365, 115, 90, 155),
            "tp_pads": [
                {"name": "EDL 1", "pos": (180, 220), "color": "#EF4444", "is_signal": True},
                {"name": "EDL 2", "pos": (195, 220), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },
    "Xiaomi Redmi Note 11 (Spes)": {
        "brand": "Xiaomi",
        "chipset": "Qualcomm Snapdragon 680 (SM6225)",
        "mode": "Qualcomm HS-USB QDLoader 9008 (EDL)",
        "difficulty": "Easy",
        "tp_type": "Dual EDL Pads",
        "instructions": (
            "1. Detach battery connector.\n"
            "2. Short the 2 gold test points right next to the LCD display connector.\n"
            "3. Plug USB Type-C cable to PC to trigger Qualcomm 9008."
        ),
        "schematic": {
            "board_color": "#182838",
            "cpu_pos": (215, 135, 120, 115),
            "emmc_pos": (215, 265, 110, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 120, 50),
            "sim_pos": (355, 115, 90, 150),
            "tp_pads": [
                {"name": "EDL 1", "pos": (160, 310), "color": "#EF4444", "is_signal": True},
                {"name": "EDL 2", "pos": (175, 310), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },
    "Poco M3 / Redmi 9T (Citrus/Lime)": {
        "brand": "Xiaomi",
        "chipset": "Qualcomm Snapdragon 662 (SM6115)",
        "mode": "Qualcomm HS-USB QDLoader 9008 (EDL)",
        "difficulty": "Easy (Solves Dead Boot PMIC bug)",
        "tp_type": "Dual EDL Pads",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Locate the 2 round EDL pads on the top left of motherboard shield.\n"
            "3. Short both pads with tweezers.\n"
            "4. Insert USB cable to connect Qualcomm 9008 port."
        ),
        "schematic": {
            "board_color": "#202830",
            "cpu_pos": (220, 130, 120, 120),
            "emmc_pos": (220, 270, 110, 100),
            "pmic_pos": (85, 160, 80, 80),
            "battery_pos": (85, 360, 120, 50),
            "sim_pos": (360, 115, 90, 150),
            "tp_pads": [
                {"name": "EDL A", "pos": (130, 200), "color": "#EF4444", "is_signal": True},
                {"name": "EDL B", "pos": (145, 200), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },
    "Oppo A53 / A54 (CPH2127 / CPH2239)": {
        "brand": "Oppo",
        "chipset": "Qualcomm Snapdragon 460 / Helio P35",
        "mode": "EDL 9008 / BROM Force",
        "difficulty": "Easy",
        "tp_type": "EDL / CLK to GND",
        "instructions": (
            "1. Unplug battery flex.\n"
            "2. Short the 2 gold test points below the CPU metal shield.\n"
            "3. Plug USB Type-C cable to PC."
        ),
        "schematic": {
            "board_color": "#1C2E2A",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "TP 1", "pos": (190, 250), "color": "#EF4444", "is_signal": True},
                {"name": "TP 2 / GND", "pos": (205, 250), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Vivo Y12 / Y15 / Y17 (MT6765)": {
        "brand": "Vivo",
        "chipset": "MediaTek Helio P35 (MT6765)",
        "mode": "Force MTK BROM Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Short golden CLK pad to metal shield.\n"
            "3. Insert USB cable. Tool detects MediaTek USB Port (V1632)."
        ),
        "schematic": {
            "board_color": "#1F2937",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "CLK", "pos": (330, 250), "color": "#EF4444", "is_signal": True},
                {"name": "GND", "pos": (320, 290), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Infinix Note 11 / Note 12 (Helio G88/G96)": {
        "brand": "Infinix",
        "chipset": "MediaTek Helio G88 / G96 (MT6769 / MT6781)",
        "mode": "Force MTK BROM Mode",
        "difficulty": "Easy",
        "tp_type": "CLK to GND (BROM)",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Locate the CLK test point beside the main eMMC/UFS shield.\n"
            "3. Short to motherboard ground and plug USB cable."
        ),
        "schematic": {
            "board_color": "#183226",
            "cpu_pos": (215, 135, 120, 115),
            "emmc_pos": (215, 265, 110, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 120, 50),
            "sim_pos": (355, 115, 90, 150),
            "tp_pads": [
                {"name": "CLK Pad", "pos": (340, 280), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (325, 320), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Samsung Galaxy A20 / A30 / A50 / A51": {
        "brand": "Samsung",
        "chipset": "Exynos 7904 / 9610 / 9611",
        "mode": "Samsung EUB / Force Download",
        "difficulty": "Moderate",
        "tp_type": "Force EUB Test Point to GND",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Bridge the gold EUB test point to ground.\n"
            "3. Connect USB cable to enter Samsung Exynos USB Boot (EUB) mode."
        ),
        "schematic": {
            "board_color": "#1A2234",
            "cpu_pos": (220, 130, 125, 120),
            "emmc_pos": (220, 270, 110, 100),
            "pmic_pos": (85, 165, 80, 80),
            "battery_pos": (85, 365, 120, 50),
            "sim_pos": (365, 115, 90, 155),
            "tp_pads": [
                {"name": "EUB TP", "pos": (175, 250), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (160, 290), "color": "#10B981", "is_signal": False}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # UNIVERSAL ARCHITECTURAL SCHEMATICS (CHIPSET FALLBACKS)
    # -------------------------------------------------------------------------
    "Universal MediaTek BROM (CLK to GND)": {
        "brand": "MediaTek",
        "chipset": "MediaTek Helio / Dimensity (All SoC)",
        "mode": "Force BROM Mode (Preloader Bypass)",
        "difficulty": "Standard Procedure",
        "tp_type": "CLK / KCOLO to Ground",
        "instructions": (
            "1. Power off device and disconnect battery connector.\n"
            "2. Locate the CLK (Clock) pad near the eMMC/UFS memory IC or KCOLO pad.\n"
            "3. Use fine-tip tweezers to short the CLK pad to the metal shield (GND).\n"
            "4. Insert USB cable while holding short for 2 seconds.\n"
            "5. Release tweezers immediately when PC chimes and detects MediaTek USB Port (COM)."
        ),
        "schematic": {
            "board_color": "#1C3328",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "CLK (Signal)", "pos": (330, 270), "color": "#EF4444", "is_signal": True},
                {"name": "GND (Ground)", "pos": (315, 315), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Universal Qualcomm Snapdragon (EDL 9008)": {
        "brand": "Qualcomm",
        "chipset": "Qualcomm Snapdragon (All MSM/SDM/SM SoC)",
        "mode": "Qualcomm HS-USB QDLoader 9008 (EDL)",
        "difficulty": "Standard Procedure",
        "tp_type": "Dual EDL Gold Pads",
        "instructions": (
            "1. Unplug battery flex cable.\n"
            "2. Identify the 2 adjacent round gold EDL solder pads (usually marked or near CPU/RAM).\n"
            "3. Bridge the two test points together with tweezers.\n"
            "4. Insert USB cable into PC while holding tweezers.\n"
            "5. Release tweezers after 2 seconds. Device registers as Qualcomm HS-USB QDLoader 9008."
        ),
        "schematic": {
            "board_color": "#222533",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "EDL Pad 1", "pos": (150, 330), "color": "#EF4444", "is_signal": True},
                {"name": "EDL Pad 2", "pos": (168, 330), "color": "#F59E0B", "is_signal": True}
            ]
        }
    },
    "Universal Unisoc SPRD (BSL / Diag)": {
        "brand": "Unisoc",
        "chipset": "Unisoc Tiger T606 / T612 / T616 / SC9863A",
        "mode": "SPRD U2S Diag / BSL Handshake",
        "difficulty": "Standard Procedure",
        "tp_type": "BSL Pad to GND",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Find the BSL test point pad situated near the baseband PMIC or storage.\n"
            "3. Short BSL pad to ground shield.\n"
            "4. Insert USB cable to force device into SPRD U2S Diag COM port."
        ),
        "schematic": {
            "board_color": "#282038",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "BSL (Pad)", "pos": (325, 265), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (315, 305), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Universal Samsung Galaxy (Test Point)": {
        "brand": "Samsung",
        "chipset": "Samsung Exynos / Qualcomm / MediaTek",
        "mode": "Force Hardware Emergency Mode (EUB / EDL / BROM)",
        "difficulty": "Standard Procedure",
        "tp_type": "CLK / EUB to Ground",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. For MTK Galaxy: Short CLK pad to ground shield.\n"
            "3. For Qualcomm Galaxy: Bridge 2 EDL pads together.\n"
            "4. For Exynos Galaxy: Short EUB pad to ground.\n"
            "5. Connect USB Type-C cable to enter flashing interface."
        ),
        "schematic": {
            "board_color": "#1C2A3A",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "Signal TP", "pos": (330, 260), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (315, 300), "color": "#10B981", "is_signal": False}
            ]
        }
    },

    # -------------------------------------------------------------------------
    # HUAWEI & HONOR (HISILICON KIRIN)
    # -------------------------------------------------------------------------
    "Huawei Mate 10 Lite (RNE-L21)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 659",
        "mode": "HUAWEI USB COM 1.0 (Hardware Test Point)",
        "difficulty": "Easy (Pads near SIM slot / Upper shield)",
        "tp_type": "Kirin Test Point to GND",
        "instructions": (
            "1. Power off device and disconnect battery cable.\n"
            "2. Locate the golden test point pad on the upper motherboard left of the shielding can.\n"
            "3. Short the TP pad to the shielding can (GND) using precision tweezers.\n"
            "4. Connect USB cable to PC.\n"
            "5. Tool detects HUAWEI USB COM 1.0 (VID: 12D1, PID: 3609) — release tweezers."
        ),
        "schematic": {
            "board_color": "#1A2535",
            "cpu_pos": (200, 120, 120, 110),
            "emmc_pos": (200, 250, 110, 100),
            "pmic_pos": (80, 150, 80, 80),
            "battery_pos": (70, 370, 110, 50),
            "sim_pos": (340, 100, 90, 150),
            "tp_pads": [
                {"name": "TP (Kirin 659)", "pos": (315, 185), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (300, 230), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },
    "Honor 8X (JSN-L21)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 710",
        "mode": "HUAWEI USB COM 1.0 (Force BSL / Kirin Rescue)",
        "difficulty": "Easy (Beside PMIC shielding)",
        "tp_type": "Kirin TP to GND",
        "instructions": (
            "1. Disconnect battery connector.\n"
            "2. Identify the marked test point pinout near the bottom side of the CPU metal shield.\n"
            "3. Bridge the TP point to ground copper / shield.\n"
            "4. Insert USB cable. Tool detects Kirin USB COM 1.0."
        ),
        "schematic": {
            "board_color": "#1E2A38",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 90),
            "pmic_pos": (90, 160, 70, 70),
            "battery_pos": (80, 370, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "TP (Kirin 710)", "pos": (320, 230), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (310, 275), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Huawei Y9 Prime 2019 (STK-L21)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 710F",
        "mode": "HUAWEI USB COM 1.0",
        "difficulty": "Easy",
        "tp_type": "Test Point to Motherboard Ground",
        "instructions": (
            "1. Disassemble back cover and remove plastic shield.\n"
            "2. Unplug battery flex.\n"
            "3. Short the single test point pin beside the battery flex connector to GND shield.\n"
            "4. Insert Type-C cable and hold short for 2 seconds until COM 1.0 is detected."
        ),
        "schematic": {
            "board_color": "#182635",
            "cpu_pos": (220, 130, 120, 110),
            "emmc_pos": (220, 260, 100, 90),
            "pmic_pos": (90, 160, 80, 80),
            "battery_pos": (80, 360, 120, 50),
            "sim_pos": (360, 110, 90, 150),
            "tp_pads": [
                {"name": "TP (STK-L21)", "pos": (330, 270), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (320, 315), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Huawei P30 Lite (MAR-LX1A)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 710",
        "mode": "HUAWEI USB COM 1.0",
        "difficulty": "Easy",
        "tp_type": "Test Point to GND",
        "instructions": (
            "1. Remove rear glass and disconnect battery.\n"
            "2. Locate test point pad next to the camera flex / shield corner.\n"
            "3. Ground test point pad with tweezers.\n"
            "4. Connect Type-C cable; release tweezers once driver binds."
        ),
        "schematic": {
            "board_color": "#1E3045",
            "cpu_pos": (210, 140, 120, 110),
            "emmc_pos": (210, 270, 100, 100),
            "pmic_pos": (90, 170, 70, 70),
            "battery_pos": (80, 370, 110, 50),
            "sim_pos": (350, 120, 90, 150),
            "tp_pads": [
                {"name": "TP (P30 Lite)", "pos": (315, 240), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (300, 285), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },
    "Huawei P20 / P20 Pro (EML / CLT)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 970",
        "mode": "HUAWEI USB COM 1.0 (Kirin 970 Rescue Mode)",
        "difficulty": "Easy",
        "tp_type": "TP Pad to Metal Shield",
        "instructions": (
            "1. Detach battery flex.\n"
            "2. Short the test point pin right under the motherboard metal casing to GND.\n"
            "3. Plug in USB cable.\n"
            "4. Kirin 970 BROM connects as USB COM 1.0."
        ),
        "schematic": {
            "board_color": "#1A2234",
            "cpu_pos": (200, 130, 130, 120),
            "emmc_pos": (200, 270, 110, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (70, 370, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "TP (Kirin 970)", "pos": (325, 210), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (310, 255), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Huawei Nova 3i (INE-LX1)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 710",
        "mode": "HUAWEI USB COM 1.0",
        "difficulty": "Easy",
        "tp_type": "Test Point to GND",
        "instructions": (
            "1. Disconnect battery.\n"
            "2. Locate the test point pad near the LCD flex connector.\n"
            "3. Short to metal ground and insert USB cable."
        ),
        "schematic": {
            "board_color": "#1E2A38",
            "cpu_pos": (210, 130, 120, 110),
            "emmc_pos": (210, 260, 100, 90),
            "pmic_pos": (90, 150, 70, 70),
            "battery_pos": (80, 360, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "TP (Nova 3i)", "pos": (320, 250), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (305, 295), "color": "#F59E0B", "is_signal": False}
            ]
        }
    },
    "Huawei P30 Pro (VOG-L29)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin 980",
        "mode": "HUAWEI USB COM 1.0 (Kirin 980 Bootloader)",
        "difficulty": "Medium (Near Periscope Camera shield)",
        "tp_type": "TP to Shield Ground",
        "instructions": (
            "1. Remove wireless charging coil and disconnect battery.\n"
            "2. Locate the golden test point pad situated beside the main Kirin 980 shielding cover.\n"
            "3. Short to shield ground with tweezers and insert Type-C cable."
        ),
        "schematic": {
            "board_color": "#1B2838",
            "cpu_pos": (190, 120, 140, 130),
            "emmc_pos": (190, 270, 120, 100),
            "pmic_pos": (70, 160, 80, 80),
            "battery_pos": (70, 370, 110, 50),
            "sim_pos": (350, 100, 90, 150),
            "tp_pads": [
                {"name": "TP (Kirin 980)", "pos": (335, 230), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (320, 275), "color": "#10B981", "is_signal": False}
            ]
        }
    },
    "Universal Huawei HiSilicon Kirin (USB COM 1.0)": {
        "brand": "Huawei",
        "chipset": "HiSilicon Kirin (65x / 710 / 960 / 970 / 980 / 990)",
        "mode": "HUAWEI USB COM 1.0 Universal Handshake",
        "difficulty": "Universal Method",
        "tp_type": "Hardware Test Point to Ground (GND)",
        "instructions": (
            "1. Unplug battery completely.\n"
            "2. Locate device model test point (TP) pad from pinout diagram.\n"
            "3. Use curved tweezers to short TP pad to motherboard metal shield / copper ground.\n"
            "4. Connect USB cable to PC while maintaining short for 1.5 - 2 seconds.\n"
            "5. Release short once device manager registers 'HUAWEI USB COM 1.0'."
        ),
        "schematic": {
            "board_color": "#1A253A",
            "cpu_pos": (200, 130, 130, 120),
            "emmc_pos": (200, 270, 110, 100),
            "pmic_pos": (80, 160, 80, 80),
            "battery_pos": (70, 370, 110, 50),
            "sim_pos": (350, 110, 90, 150),
            "tp_pads": [
                {"name": "Kirin TP", "pos": (325, 225), "color": "#EF4444", "is_signal": True},
                {"name": "GND Shield", "pos": (310, 270), "color": "#10B981", "is_signal": False}
            ]
        }
    }
}


def find_testpoint_for_model(brand: str = "", model_name: str = "", platform: str = "") -> tuple[str, dict]:
    """
    Intelligent test point resolver with fuzzy matching and chipset architecture fallback.
    Returns: (matching_model_title, schematic_dict)
    """
    if not brand and not model_name:
        return ("Universal MediaTek BROM (CLK to GND)", TEST_POINT_DATABASE["Universal MediaTek BROM (CLK to GND)"])

    clean_model = model_name.strip()
    # Strip any "[Brand] " global search prefix
    if clean_model.startswith("[") and "] " in clean_model:
        parts = clean_model.split("] ", 1)
        if not brand or brand.startswith("[ALL"):
            brand = parts[0][1:]
        clean_model = parts[1]

    # 1. Exact match in database
    if clean_model in TEST_POINT_DATABASE:
        return (clean_model, TEST_POINT_DATABASE[clean_model])

    # 2. Tokenized Substring Match in database keys
    m_lower = clean_model.lower()
    b_lower = brand.lower() if brand else ""

    # Check for direct contains
    for db_key, data in TEST_POINT_DATABASE.items():
        k_lower = db_key.lower()
        # If both model and brand match
        if b_lower and b_lower in k_lower:
            # Check model tokens (e.g. "hot 12", "note 11", "y20", "a12")
            tokens = [t for t in m_lower.replace("(", " ").replace(")", " ").replace("/", " ").split() if len(t) >= 2]
            if tokens and any(t in k_lower for t in tokens):
                return (db_key, data)

    # Check general match without brand constraint
    tokens = [t for t in m_lower.replace("(", " ").replace(")", " ").replace("/", " ").split() if len(t) >= 3]
    for db_key, data in TEST_POINT_DATABASE.items():
        k_lower = db_key.lower()
        if tokens and all(t in k_lower for t in tokens[:2]):
            return (db_key, data)

    # 3. Platform / Architecture Fallback
    plat_lower = platform.lower() if platform else ""
    if "qualcomm" in plat_lower or "qc" in plat_lower or "snapdragon" in m_lower:
        return ("Universal Qualcomm Snapdragon (EDL 9008)", TEST_POINT_DATABASE["Universal Qualcomm Snapdragon (EDL 9008)"])
    elif "huawei" in b_lower or "honor" in b_lower or "kirin" in plat_lower or "hisi" in plat_lower or "kirin" in m_lower:
        return ("Universal Huawei HiSilicon Kirin (USB COM 1.0)", TEST_POINT_DATABASE["Universal Huawei HiSilicon Kirin (USB COM 1.0)"])
    elif "unisoc" in plat_lower or "spd" in plat_lower or "sprd" in m_lower or "tiger" in m_lower:
        return ("Universal Unisoc SPRD (BSL / Diag)", TEST_POINT_DATABASE["Universal Unisoc SPRD (BSL / Diag)"])
    elif "samsung" in b_lower or "exynos" in plat_lower:
        return ("Universal Samsung Galaxy (Test Point)", TEST_POINT_DATABASE["Universal Samsung Galaxy (Test Point)"])
    else:
        return ("Universal MediaTek BROM (CLK to GND)", TEST_POINT_DATABASE["Universal MediaTek BROM (CLK to GND)"])

