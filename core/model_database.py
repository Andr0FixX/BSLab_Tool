"""
BS Lab Tool v2.0 PRO — Device Model & Hardware Knowledge Base.
Provides Chimera-style automatic identification of phone models, codenames,
marketing names, SoC specifications, and brand visual assets.
"""

import os
import re
from typing import Dict, Any, Optional

class ModelDatabase:
    """
    Intelligent Device Classifier & Hardware Registry.
    Resolves cryptic codenames (e.g. 'bramble') and model numbers (e.g. 'SM-G988B')
    into high-profile marketing titles, SoC details, and device renders.
    """

    # 1. Google Pixel Registry
    PIXELS = {
        "bramble": {"name": "Google Pixel 4a (5G)", "soc": "Snapdragon 765G (SM7250)", "brand": "Google", "family": "Pixel 4 Series"},
        "redfin": {"name": "Google Pixel 5", "soc": "Snapdragon 765G (SM7250)", "brand": "Google", "family": "Pixel 5 Series"},
        "barbet": {"name": "Google Pixel 5a (5G)", "soc": "Snapdragon 765G (SM7250)", "brand": "Google", "family": "Pixel 5 Series"},
        "sunfish": {"name": "Google Pixel 4a", "soc": "Snapdragon 730G (SM7150)", "brand": "Google", "family": "Pixel 4 Series"},
        "coral": {"name": "Google Pixel 4 XL", "soc": "Snapdragon 855 (SM8150)", "brand": "Google", "family": "Pixel 4 Series"},
        "flame": {"name": "Google Pixel 4", "soc": "Snapdragon 855 (SM8150)", "brand": "Google", "family": "Pixel 4 Series"},
        "bonito": {"name": "Google Pixel 3a XL", "soc": "Snapdragon 670 (SDM670)", "brand": "Google", "family": "Pixel 3 Series"},
        "sargo": {"name": "Google Pixel 3a", "soc": "Snapdragon 670 (SDM670)", "brand": "Google", "family": "Pixel 3 Series"},
        "crosshatch": {"name": "Google Pixel 3 XL", "soc": "Snapdragon 845 (SDM845)", "brand": "Google", "family": "Pixel 3 Series"},
        "blueline": {"name": "Google Pixel 3", "soc": "Snapdragon 845 (SDM845)", "brand": "Google", "family": "Pixel 3 Series"},
        "taimen": {"name": "Google Pixel 2 XL", "soc": "Snapdragon 835 (MSM8998)", "brand": "Google", "family": "Pixel 2 Series"},
        "walleye": {"name": "Google Pixel 2", "soc": "Snapdragon 835 (MSM8998)", "brand": "Google", "family": "Pixel 2 Series"},
        "marlin": {"name": "Google Pixel XL", "soc": "Snapdragon 821 (MSM8996)", "brand": "Google", "family": "Pixel 1 Series"},
        "sailfish": {"name": "Google Pixel", "soc": "Snapdragon 821 (MSM8996)", "brand": "Google", "family": "Pixel 1 Series"},
        "bluejay": {"name": "Google Pixel 6a", "soc": "Google Tensor G1", "brand": "Google", "family": "Pixel 6 Series"},
        "oriole": {"name": "Google Pixel 6", "soc": "Google Tensor G1", "brand": "Google", "family": "Pixel 6 Series"},
        "raven": {"name": "Google Pixel 6 Pro", "soc": "Google Tensor G1", "brand": "Google", "family": "Pixel 6 Series"},
        "panther": {"name": "Google Pixel 7", "soc": "Google Tensor G2", "brand": "Google", "family": "Pixel 7 Series"},
        "cheetah": {"name": "Google Pixel 7 Pro", "soc": "Google Tensor G2", "brand": "Google", "family": "Pixel 7 Series"},
        "lynx": {"name": "Google Pixel 7a", "soc": "Google Tensor G2", "brand": "Google", "family": "Pixel 7 Series"},
        "felix": {"name": "Google Pixel Fold", "soc": "Google Tensor G2", "brand": "Google", "family": "Pixel Fold Series"},
        "tangorpro": {"name": "Google Pixel Tablet", "soc": "Google Tensor G2", "brand": "Google", "family": "Pixel Tablet"},
        "shiba": {"name": "Google Pixel 8", "soc": "Google Tensor G3", "brand": "Google", "family": "Pixel 8 Series"},
        "husky": {"name": "Google Pixel 8 Pro", "soc": "Google Tensor G3", "brand": "Google", "family": "Pixel 8 Series"},
        "akita": {"name": "Google Pixel 8a", "soc": "Google Tensor G3", "brand": "Google", "family": "Pixel 8 Series"},
        "tokay": {"name": "Google Pixel 9", "soc": "Google Tensor G4", "brand": "Google", "family": "Pixel 9 Series"},
        "caiman": {"name": "Google Pixel 9 Pro", "soc": "Google Tensor G4", "brand": "Google", "family": "Pixel 9 Series"},
        "komodo": {"name": "Google Pixel 9 Pro XL", "soc": "Google Tensor G4", "brand": "Google", "family": "Pixel 9 Series"},
        "comet": {"name": "Google Pixel 9 Pro Fold", "soc": "Google Tensor G4", "brand": "Google", "family": "Pixel 9 Series"},
    }

    # 2. Samsung Galaxy Models Registry
    SAMSUNG = {
        "SM-G998": {"name": "Samsung Galaxy S21 Ultra 5G", "soc": "Exynos 2100 / Snapdragon 888", "brand": "Samsung", "family": "Galaxy S21"},
        "SM-G996": {"name": "Samsung Galaxy S21+ 5G", "soc": "Exynos 2100 / Snapdragon 888", "brand": "Samsung", "family": "Galaxy S21"},
        "SM-G991": {"name": "Samsung Galaxy S21 5G", "soc": "Exynos 2100 / Snapdragon 888", "brand": "Samsung", "family": "Galaxy S21"},
        "SM-G988": {"name": "Samsung Galaxy S20 Ultra", "soc": "Exynos 990 / Snapdragon 865", "brand": "Samsung", "family": "Galaxy S20"},
        "SM-G986": {"name": "Samsung Galaxy S20+", "soc": "Exynos 990 / Snapdragon 865", "brand": "Samsung", "family": "Galaxy S20"},
        "SM-G981": {"name": "Samsung Galaxy S20", "soc": "Exynos 990 / Snapdragon 865", "brand": "Samsung", "family": "Galaxy S20"},
        "SM-G980": {"name": "Samsung Galaxy S20 LTE", "soc": "Exynos 990", "brand": "Samsung", "family": "Galaxy S20"},
        "SM-G780": {"name": "Samsung Galaxy S20 FE", "soc": "Exynos 990 / Snapdragon 865", "brand": "Samsung", "family": "Galaxy S20"},
        "SM-G781": {"name": "Samsung Galaxy S20 FE 5G", "soc": "Snapdragon 865", "brand": "Samsung", "family": "Galaxy S20"},
        "SM-S908": {"name": "Samsung Galaxy S22 Ultra 5G", "soc": "Exynos 2200 / Snapdragon 8 Gen 1", "brand": "Samsung", "family": "Galaxy S22"},
        "SM-S906": {"name": "Samsung Galaxy S22+ 5G", "soc": "Exynos 2200 / Snapdragon 8 Gen 1", "brand": "Samsung", "family": "Galaxy S22"},
        "SM-S901": {"name": "Samsung Galaxy S22 5G", "soc": "Exynos 2200 / Snapdragon 8 Gen 1", "brand": "Samsung", "family": "Galaxy S22"},
        "SM-S918": {"name": "Samsung Galaxy S23 Ultra", "soc": "Snapdragon 8 Gen 2 for Galaxy", "brand": "Samsung", "family": "Galaxy S23"},
        "SM-S916": {"name": "Samsung Galaxy S23+", "soc": "Snapdragon 8 Gen 2 for Galaxy", "brand": "Samsung", "family": "Galaxy S23"},
        "SM-S911": {"name": "Samsung Galaxy S23", "soc": "Snapdragon 8 Gen 2 for Galaxy", "brand": "Samsung", "family": "Galaxy S23"},
        "SM-S928": {"name": "Samsung Galaxy S24 Ultra", "soc": "Snapdragon 8 Gen 3 for Galaxy", "brand": "Samsung", "family": "Galaxy S24"},
        "SM-S926": {"name": "Samsung Galaxy S24+", "soc": "Exynos 2400 / Snapdragon 8 Gen 3", "brand": "Samsung", "family": "Galaxy S24"},
        "SM-S921": {"name": "Samsung Galaxy S24", "soc": "Exynos 2400 / Snapdragon 8 Gen 3", "brand": "Samsung", "family": "Galaxy S24"},
        "SM-N986": {"name": "Samsung Galaxy Note 20 Ultra 5G", "soc": "Exynos 990 / Snapdragon 865+", "brand": "Samsung", "family": "Galaxy Note 20"},
        "SM-N981": {"name": "Samsung Galaxy Note 20 5G", "soc": "Exynos 990 / Snapdragon 865+", "brand": "Samsung", "family": "Galaxy Note 20"},
        "SM-N975": {"name": "Samsung Galaxy Note 10+", "soc": "Exynos 9825 / Snapdragon 855", "brand": "Samsung", "family": "Galaxy Note 10"},
        "SM-N970": {"name": "Samsung Galaxy Note 10", "soc": "Exynos 9825 / Snapdragon 855", "brand": "Samsung", "family": "Galaxy Note 10"},
        "SM-A125": {"name": "Samsung Galaxy A12 (Helio P35)", "soc": "MediaTek Helio P35 (MT6765)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A127": {"name": "Samsung Galaxy A12 Nacho", "soc": "Samsung Exynos 850", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A135": {"name": "Samsung Galaxy A13 4G", "soc": "Samsung Exynos 850", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A137": {"name": "Samsung Galaxy A13 (Helio G80)", "soc": "MediaTek Helio G80 (MT6769)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A145": {"name": "Samsung Galaxy A14 4G", "soc": "MediaTek Helio G80", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A146": {"name": "Samsung Galaxy A14 5G", "soc": "Exynos 1330 / Dimensity 700", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A155": {"name": "Samsung Galaxy A15 4G", "soc": "MediaTek Helio G99", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A156": {"name": "Samsung Galaxy A15 5G", "soc": "MediaTek Dimensity 6100+", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A217": {"name": "Samsung Galaxy A21s", "soc": "Samsung Exynos 850", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A225": {"name": "Samsung Galaxy A22 4G", "soc": "MediaTek Helio G80", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A226": {"name": "Samsung Galaxy A22 5G", "soc": "MediaTek Dimensity 700", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A325": {"name": "Samsung Galaxy A32 4G", "soc": "MediaTek Helio G80", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A326": {"name": "Samsung Galaxy A32 5G", "soc": "MediaTek Dimensity 720", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A515": {"name": "Samsung Galaxy A51", "soc": "Samsung Exynos 9611", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A525": {"name": "Samsung Galaxy A52 4G", "soc": "Snapdragon 720G (SM7125)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A526": {"name": "Samsung Galaxy A52 5G", "soc": "Snapdragon 750G (SM7225)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A528": {"name": "Samsung Galaxy A52s 5G", "soc": "Snapdragon 778G (SM7325)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A536": {"name": "Samsung Galaxy A53 5G", "soc": "Samsung Exynos 1280", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A546": {"name": "Samsung Galaxy A54 5G", "soc": "Samsung Exynos 1380", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A022": {"name": "Samsung Galaxy A02", "soc": "MediaTek MT6739WW", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A025": {"name": "Samsung Galaxy A02s", "soc": "Snapdragon 450 (SDM450)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A032": {"name": "Samsung Galaxy A03 Core", "soc": "Unisoc SC9863A", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A035": {"name": "Samsung Galaxy A03", "soc": "Unisoc T606", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A037": {"name": "Samsung Galaxy A03s", "soc": "MediaTek Helio P35 (MT6765)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A042": {"name": "Samsung Galaxy A04e", "soc": "MediaTek Helio P35 (MT6765)", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A045": {"name": "Samsung Galaxy A04", "soc": "MediaTek Helio P35 / Unisoc SC9863A", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A055": {"name": "Samsung Galaxy A05", "soc": "MediaTek Helio G85", "brand": "Samsung", "family": "Galaxy A Series"},
        "SM-A057": {"name": "Samsung Galaxy A05s", "soc": "Snapdragon 680 (SM6225)", "brand": "Samsung", "family": "Galaxy A Series"},
    }

    # 3. Xiaomi / Redmi / Poco Registry
    XIAOMI = {
        "sweet": {"name": "Xiaomi Redmi Note 10 Pro", "soc": "Snapdragon 732G (SM7150)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "mojito": {"name": "Xiaomi Redmi Note 10", "soc": "Snapdragon 678 (SM6150)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "sunny": {"name": "Xiaomi Redmi Note 10", "soc": "Snapdragon 678 (SM6150)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "vayu": {"name": "Poco X3 Pro (Global)", "soc": "Snapdragon 860 (SM8150-AC)", "brand": "Poco", "family": "Poco X Series"},
        "bhima": {"name": "Poco X3 Pro (India)", "soc": "Snapdragon 860 (SM8150-AC)", "brand": "Poco", "family": "Poco X Series"},
        "surya": {"name": "Poco X3 NFC", "soc": "Snapdragon 732G (SM7150)", "brand": "Poco", "family": "Poco X Series"},
        "karna": {"name": "Poco X3 (India)", "soc": "Snapdragon 732G (SM7150)", "brand": "Poco", "family": "Poco X Series"},
        "alioth": {"name": "Poco F3 / Redmi K40", "soc": "Snapdragon 870 (SM8250-AC)", "brand": "Poco", "family": "Poco F Series"},
        "apollo": {"name": "Xiaomi Mi 10T / 10T Pro", "soc": "Snapdragon 865 (SM8250)", "brand": "Xiaomi", "family": "Mi 10 Series"},
        "gauguin": {"name": "Xiaomi Mi 10T Lite 5G", "soc": "Snapdragon 750G (SM7225)", "brand": "Xiaomi", "family": "Mi 10 Series"},
        "curtana": {"name": "Redmi Note 9S / 9 Pro (India)", "soc": "Snapdragon 720G (SM7125)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "joyeuse": {"name": "Redmi Note 9 Pro (Global)", "soc": "Snapdragon 720G (SM7125)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "merlin": {"name": "Redmi Note 9 (Helio G85)", "soc": "MediaTek Helio G85 (MT6768)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "begonia": {"name": "Redmi Note 8 Pro", "soc": "MediaTek Helio G90T (MT6785)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "ginkgo": {"name": "Redmi Note 8", "soc": "Snapdragon 665 (SM6125)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "tissot": {"name": "Xiaomi Mi A1 (Android One)", "soc": "Snapdragon 625 (MSM8953)", "brand": "Xiaomi", "family": "Mi A Series"},
        "jasmine": {"name": "Xiaomi Mi A2 (Android One)", "soc": "Snapdragon 660 (SDM660)", "brand": "Xiaomi", "family": "Mi A Series"},
        "laurel": {"name": "Xiaomi Mi A3 (Android One)", "soc": "Snapdragon 665 (SM6125)", "brand": "Xiaomi", "family": "Mi A Series"},
        "mido": {"name": "Xiaomi Redmi Note 4", "soc": "Snapdragon 625 (MSM8953)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "santoni": {"name": "Xiaomi Redmi 4X", "soc": "Snapdragon 435 (MSM8940)", "brand": "Xiaomi", "family": "Redmi 4 Series"},
        "rolex": {"name": "Xiaomi Redmi 4A", "soc": "Snapdragon 425 (MSM8917)", "brand": "Xiaomi", "family": "Redmi 4 Series"},
        "rosy": {"name": "Xiaomi Redmi 5", "soc": "Snapdragon 450 (SDM450)", "brand": "Xiaomi", "family": "Redmi 5 Series"},
        "vince": {"name": "Xiaomi Redmi 5 Plus", "soc": "Snapdragon 625 (MSM8953)", "brand": "Xiaomi", "family": "Redmi 5 Series"},
        "whyred": {"name": "Xiaomi Redmi Note 5 Pro", "soc": "Snapdragon 636 (SDM636)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "tulip": {"name": "Xiaomi Redmi Note 6 Pro", "soc": "Snapdragon 636 (SDM636)", "brand": "Xiaomi", "family": "Redmi Note Series"},
        "lavender": {"name": "Xiaomi Redmi Note 7", "soc": "Snapdragon 660 (SDM660)", "brand": "Xiaomi", "family": "Redmi Note Series"},
    }

    # 4. OnePlus Registry
    ONEPLUS = {
        "kebab": {"name": "OnePlus 8T", "soc": "Snapdragon 865 (SM8250)", "brand": "OnePlus", "family": "OnePlus 8 Series"},
        "instantnoodle": {"name": "OnePlus 8", "soc": "Snapdragon 865 (SM8250)", "brand": "OnePlus", "family": "OnePlus 8 Series"},
        "instantnoodlep": {"name": "OnePlus 8 Pro", "soc": "Snapdragon 865 (SM8250)", "brand": "OnePlus", "family": "OnePlus 8 Series"},
        "lemonade": {"name": "OnePlus 9", "soc": "Snapdragon 888 (SM8350)", "brand": "OnePlus", "family": "OnePlus 9 Series"},
        "lemonadep": {"name": "OnePlus 9 Pro", "soc": "Snapdragon 888 (SM8350)", "brand": "OnePlus", "family": "OnePlus 9 Series"},
        "guacamole": {"name": "OnePlus 7 Pro", "soc": "Snapdragon 855 (SM8150)", "brand": "OnePlus", "family": "OnePlus 7 Series"},
        "hotdog": {"name": "OnePlus 7T Pro", "soc": "Snapdragon 855+ (SM8150-AC)", "brand": "OnePlus", "family": "OnePlus 7 Series"},
        "hotdogg": {"name": "OnePlus 7T Pro 5G", "soc": "Snapdragon 855+ (SM8150-AC)", "brand": "OnePlus", "family": "OnePlus 7 Series"},
        "fajita": {"name": "OnePlus 6T", "soc": "Snapdragon 845 (SDM845)", "brand": "OnePlus", "family": "OnePlus 6 Series"},
        "enchilada": {"name": "OnePlus 6", "soc": "Snapdragon 845 (SDM845)", "brand": "OnePlus", "family": "OnePlus 6 Series"},
        "dumpling": {"name": "OnePlus 5T", "soc": "Snapdragon 835 (MSM8998)", "brand": "OnePlus", "family": "OnePlus 5 Series"},
        "cheeseburger": {"name": "OnePlus 5", "soc": "Snapdragon 835 (MSM8998)", "brand": "OnePlus", "family": "OnePlus 5 Series"},
    }

    # 5. Huawei / Honor HiSilicon Kirin Registry
    HUAWEI = {
        "rne-l21": {"name": "Huawei Mate 10 Lite (RNE-L21)", "soc": "HiSilicon Kirin 659 (Octa-Core)", "brand": "Huawei", "family": "Mate Series"},
        "rne-lx1": {"name": "Huawei Mate 10 Lite (RNE-LX1)", "soc": "HiSilicon Kirin 659", "brand": "Huawei", "family": "Mate Series"},
        "rne-l01": {"name": "Huawei Mate 10 Lite (RNE-L01)", "soc": "HiSilicon Kirin 659", "brand": "Huawei", "family": "Mate Series"},
        "rne-l22": {"name": "Huawei Nova 2i (RNE-L22)", "soc": "HiSilicon Kirin 659", "brand": "Huawei", "family": "Nova Series"},
        "rne-l23": {"name": "Huawei Mate 10 Lite (RNE-L23)", "soc": "HiSilicon Kirin 659", "brand": "Huawei", "family": "Mate Series"},
        "pra-lx1": {"name": "Huawei P8 Lite 2017 / P9 Lite", "soc": "HiSilicon Kirin 655", "brand": "Huawei", "family": "P Series"},
        "pra-la1": {"name": "Huawei P9 Lite 2017", "soc": "HiSilicon Kirin 655", "brand": "Huawei", "family": "P Series"},
        "vog-l29": {"name": "Huawei P30 Pro", "soc": "HiSilicon Kirin 980", "brand": "Huawei", "family": "P Series"},
        "ele-l29": {"name": "Huawei P30", "soc": "HiSilicon Kirin 980", "brand": "Huawei", "family": "P Series"},
        "hma-l29": {"name": "Huawei Mate 20", "soc": "HiSilicon Kirin 980", "brand": "Huawei", "family": "Mate Series"},
        "lya-l29": {"name": "Huawei Mate 20 Pro", "soc": "HiSilicon Kirin 980", "brand": "Huawei", "family": "Mate Series"},
        "jsn-l21": {"name": "Honor 8X", "soc": "HiSilicon Kirin 710", "brand": "Honor", "family": "Honor Series"},
        "stk-l21": {"name": "Huawei Y9 Prime 2019", "soc": "HiSilicon Kirin 710F", "brand": "Huawei", "family": "Y Series"},
        "ine-lx1": {"name": "Huawei Nova 3i", "soc": "HiSilicon Kirin 710", "brand": "Huawei", "family": "Nova Series"},
        "mar-lx1a": {"name": "Huawei P30 Lite", "soc": "HiSilicon Kirin 710", "brand": "Huawei", "family": "P Series"},
        "pot-lx1": {"name": "Huawei P Smart 2019", "soc": "HiSilicon Kirin 710", "brand": "Huawei", "family": "P Smart Series"},
        "sne-lx1": {"name": "Huawei Mate 20 Lite", "soc": "HiSilicon Kirin 710", "brand": "Huawei", "family": "Mate Series"},
        "fig-lx1": {"name": "Huawei P Smart", "soc": "HiSilicon Kirin 659", "brand": "Huawei", "family": "P Smart Series"},
        "lld-l21": {"name": "Honor 9 Lite", "soc": "HiSilicon Kirin 659", "brand": "Honor", "family": "Honor Series"},
        "bkl-l09": {"name": "Honor View 10", "soc": "HiSilicon Kirin 970", "brand": "Honor", "family": "Honor Series"},
        "clt-l29": {"name": "Huawei P20 Pro", "soc": "HiSilicon Kirin 970", "brand": "Huawei", "family": "P Series"},
        "eml-l29": {"name": "Huawei P20", "soc": "HiSilicon Kirin 970", "brand": "Huawei", "family": "P Series"},
        "vtr-l29": {"name": "Huawei P10", "soc": "HiSilicon Kirin 960", "brand": "Huawei", "family": "P Series"},
        "bla-l29": {"name": "Huawei Mate 10 Pro", "soc": "HiSilicon Kirin 970", "brand": "Huawei", "family": "Mate Series"},
        "alp-l29": {"name": "Huawei Mate 10", "soc": "HiSilicon Kirin 970", "brand": "Huawei", "family": "Mate Series"},
    }

    # 6. MediaTek SoC Hardware Codes
    MTK_CHIPS = {
        "MT6580": "MediaTek MT6580 (Quad-Core 32-bit)",
        "MT6735": "MediaTek MT6735 (Quad-Core A53)",
        "MT6737": "MediaTek MT6737 (Quad-Core A53)",
        "MT6739": "MediaTek MT6739 (Quad-Core A53 1.5GHz)",
        "MT6750": "MediaTek MT6750 (Octa-Core A53)",
        "MT6755": "MediaTek Helio P10 (MT6755)",
        "MT6757": "MediaTek Helio P20 / P25 (MT6757)",
        "MT6761": "MediaTek Helio A22 (MT6761)",
        "MT6762": "MediaTek Helio P22 / G25 (MT6762)",
        "MT6763": "MediaTek Helio P23 (MT6763)",
        "MT6765": "MediaTek Helio P35 / G35 (MT6765)",
        "MT6768": "MediaTek Helio P65 / G85 (MT6768)",
        "MT6769": "MediaTek Helio G80 / G88 (MT6769)",
        "MT6771": "MediaTek Helio P60 / P70 (MT6771)",
        "MT6779": "MediaTek Helio P90 (MT6779)",
        "MT6781": "MediaTek Helio G96 (MT6781)",
        "MT6785": "MediaTek Helio G90 / G95 (MT6785)",
        "MT6789": "MediaTek Helio G99 / G99 Ultra (MT6789)",
        "MT6833": "MediaTek Dimensity 700 / 6020 (MT6833)",
        "MT6853": "MediaTek Dimensity 720 (MT6853)",
        "MT6873": "MediaTek Dimensity 800 (MT6873)",
        "MT6877": "MediaTek Dimensity 900 / 1080 (MT6877)",
        "MT6885": "MediaTek Dimensity 1000L (MT6885)",
        "MT6889": "MediaTek Dimensity 1000+ (MT6889)",
        "MT6891": "MediaTek Dimensity 1100 (MT6891)",
        "MT6893": "MediaTek Dimensity 1200 (MT6893)",
        "MT6895": "MediaTek Dimensity 8100 (MT6895)",
        "MT6983": "MediaTek Dimensity 9000 (MT6983)",
        "MT6985": "MediaTek Dimensity 9200 (MT6985)",
        "MT6989": "MediaTek Dimensity 9300 (MT6989)",
    }

    @classmethod
    def resolve(cls, identifier: str, mode: str = "", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Classifies any input identifier (codename, model, port description, product)
        and returns a rich device profile.
        """
        details = details or {}
        raw = (identifier or "").strip().lower()
        clean_upper = (identifier or "").strip().upper()

        # 1. Match Google Pixels
        if raw in cls.PIXELS:
            info = cls.PIXELS[raw].copy()
            info["codename"] = raw
            info["category"] = "pixel"
            info["icon_badge"] = "Google"
            return info

        # Check if codename is inside identifier
        for code, info in cls.PIXELS.items():
            if code == raw or code in raw.split() or f"({code})" in raw:
                res = info.copy()
                res["codename"] = code
                res["category"] = "pixel"
                res["icon_badge"] = "Google"
                return res

        # 2. Match Xiaomi / Redmi / Poco Codenames
        if raw in cls.XIAOMI:
            info = cls.XIAOMI[raw].copy()
            info["codename"] = raw
            info["category"] = "xiaomi"
            info["icon_badge"] = info.get("brand", "Xiaomi")
            return info

        for code, info in cls.XIAOMI.items():
            if code == raw or code in raw.split():
                res = info.copy()
                res["codename"] = code
                res["category"] = "xiaomi"
                res["icon_badge"] = info.get("brand", "Xiaomi")
                return res

        # 3. Match OnePlus Codenames
        if raw in cls.ONEPLUS:
            info = cls.ONEPLUS[raw].copy()
            info["codename"] = raw
            info["category"] = "oneplus"
            info["icon_badge"] = "OnePlus"
            return info

        # 4. Match Samsung Model Codes (e.g. SM-G988B, SM-A125F, G988, A125)
        for sm_prefix, info in cls.SAMSUNG.items():
            if sm_prefix in clean_upper or sm_prefix.replace("-", "") in clean_upper:
                res = info.copy()
                res["codename"] = clean_upper
                res["category"] = "samsung"
                res["icon_badge"] = "Samsung"
                return res

        # 4.5. Match Huawei / Honor Model Codes
        for hw_code, info in cls.HUAWEI.items():
            if hw_code in raw or hw_code in clean_upper.lower():
                res = info.copy()
                res["codename"] = hw_code
                res["category"] = "huawei"
                res["icon_badge"] = info.get("brand", "Huawei")
                return res

        # 5. Check if MediaTek SoC was detected
        for mtk_code, mtk_desc in cls.MTK_CHIPS.items():
            if mtk_code.lower() in raw or mtk_code in clean_upper:
                return {
                    "name": f"MediaTek Dynamic Device ({mtk_code})",
                    "soc": mtk_desc,
                    "brand": "MediaTek",
                    "family": "MTK Helio / Dimensity Platform",
                    "codename": mtk_code,
                    "category": "mediatek",
                    "icon_badge": "MediaTek"
                }

        # 6. Mode-based intelligent heuristics
        if mode == "FASTBOOT":
            product = details.get("product") or identifier or "Android Fastboot"
            return {
                "name": f"Android Fastboot ({clean_upper or product})",
                "soc": "Qualcomm Snapdragon / Google Tensor / MediaTek",
                "brand": "Android Bootloader",
                "family": "Universal Fastboot Client",
                "codename": raw or "fastboot",
                "category": "generic_phone",
                "icon_badge": "Fastboot"
            }
        elif mode == "ADB":
            model = details.get("model") or identifier or "Android Device"
            b_brand = details.get("brand") or "Android"
            b_soc = details.get("soc") or "Android Smart Platform"
            category = "generic_phone"
            if "huawei" in b_brand.lower() or "honor" in b_brand.lower():
                category = "huawei"
            elif "pixel" in model.lower() or "google" in b_brand.lower():
                category = "pixel"
            elif "samsung" in b_brand.lower():
                category = "samsung"
            elif "xiaomi" in b_brand.lower() or "redmi" in b_brand.lower():
                category = "xiaomi"
            return {
                "name": f"{model}",
                "soc": b_soc,
                "brand": b_brand.title(),
                "family": f"{b_brand.title()} ADB Interface",
                "codename": raw,
                "category": category,
                "icon_badge": b_brand.title()
            }
        elif mode == "SAMSUNG":
            return {
                "name": f"Samsung Galaxy ({clean_upper or 'Odin Mode'})",
                "soc": "Samsung Exynos / Qualcomm Snapdragon",
                "brand": "Samsung",
                "family": "Galaxy Series",
                "codename": "samsung_odin",
                "category": "samsung",
                "icon_badge": "Samsung"
            }
        elif mode == "QUALCOMM":
            return {
                "name": "Qualcomm Snapdragon Device (EDL 9008)",
                "soc": "Qualcomm Snapdragon MSM / SM Platform",
                "brand": "Qualcomm",
                "family": "Snapdragon EDL Station",
                "codename": "edl_9008",
                "category": "qualcomm",
                "icon_badge": "Qualcomm"
            }
        elif mode == "MTK":
            return {
                "name": "MediaTek Device (BROM / Preloader VCOM)",
                "soc": "MediaTek Helio / Dimensity BROM Engine",
                "brand": "MediaTek",
                "family": "MTK Platform",
                "codename": "mtk_brom",
                "category": "mediatek",
                "icon_badge": "MediaTek"
            }
        elif mode == "HUAWEI":
            return {
                "name": "Huawei / Honor Device (USB COM 1.0)",
                "soc": "HiSilicon Kirin (710 / 659 / 970 / 980 / 990)",
                "brand": "Huawei",
                "family": "HiSilicon Kirin Series",
                "codename": "kirin_com1",
                "category": "huawei",
                "icon_badge": "Huawei"
            }
        elif mode == "HUAWEI_PCUI":
            return {
                "name": "Huawei Handset (Manufacture Mode PCUI)",
                "soc": "HiSilicon Kirin Baseband Processor",
                "brand": "Huawei",
                "family": "HiSilicon Kirin Series",
                "codename": "huawei_pcui",
                "category": "huawei",
                "icon_badge": "Huawei"
            }
        elif mode == "SPD":
            return {
                "name": "Unisoc / Spreadtrum Device (BSL Mode)",
                "soc": "Unisoc Tiger / SC Series (SC9863A / T606 / T616)",
                "brand": "Unisoc",
                "family": "Spreadtrum Platform",
                "codename": "spd_bsl",
                "category": "generic_phone",
                "icon_badge": "Unisoc"
            }

        # Fallback Generic
        return {
            "name": clean_upper or "Universal Mobile Terminal",
            "soc": "Smart Mobile SoC",
            "brand": "Universal",
            "family": "Mobile Platform",
            "codename": raw,
            "category": "generic_phone",
            "icon_badge": "USB"
        }
