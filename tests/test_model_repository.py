"""
Unit Tests for Modular Loaders & Model Repository Subsystem.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.model_repository import ModelRepository


def test_model_repository():
    print("[TEST] Testing ModelRepository Subsystem...")
    ModelRepository.init()

    # 1. Test Brands Listing
    brands = ModelRepository.get_all_brands()
    print(f"  Brands Loaded ({len(brands)}): {brands}")
    assert len(brands) >= 6
    assert "Infinix" in brands
    assert "Xiaomi" in brands
    assert "Samsung" in brands

    # 2. Test Models for Brand
    xiaomi_models = ModelRepository.get_models_by_brand("Xiaomi")
    print(f"  Xiaomi Models ({len(xiaomi_models)}): {xiaomi_models}")
    assert len(xiaomi_models) >= 3

    # 3. Test Model Details
    details = ModelRepository.get_model_details("Xiaomi", "Redmi 10C (Fog / Rain)")
    assert details is not None
    assert details["platform"] == "qualcomm"
    assert "SM6225" in details["chipset"]
    print(f"  Redmi 10C Details: Chipset={details['chipset']}, Loader={details['loader_file']}")

    # 4. Test Search
    results = ModelRepository.search_models("Snapdragon 680")
    print(f"  Search 'Snapdragon 680' found {len(results)} matches.")
    assert len(results) >= 1

    # 5. Test Chipset Info
    chip = ModelRepository.get_chipset_info("mediatek", "0x0658")
    assert chip is not None
    assert chip["soc"] == "MT6765"
    print(f"  Chipset MT6765 Lookup: {chip}")

    # 6. Test Qualcomm Loaders Listing
    loaders = ModelRepository.list_available_loaders("qualcomm")
    print(f"  Qualcomm Loaders count: {len(loaders)}")
    assert len(loaders) >= 870

    # 10. Test Qualcomm Brands & Auto-Matching
    qc_brands = ModelRepository.list_qualcomm_brands()
    print(f"  Qualcomm Brands Count ({len(qc_brands)}): {qc_brands[:10]}...")
    assert len(qc_brands) >= 40
    assert "xiaomi" in qc_brands
    assert "samsung" in qc_brands
    assert "oppo" in qc_brands

    xiaomi_qc = ModelRepository.list_qualcomm_loaders("xiaomi")
    print(f"  Xiaomi Qualcomm Loaders: {len(xiaomi_qc)} files")
    assert len(xiaomi_qc) >= 35

    samsung_qc = ModelRepository.list_qualcomm_loaders("samsung")
    print(f"  Samsung Qualcomm Loaders: {len(samsung_qc)} files")
    assert len(samsung_qc) >= 50

    # Test Sahara Auto-Match by HWID + PK_HASH
    matched_loader = ModelRepository.match_qualcomm_loader(
        hwid="0000000000510000",
        pkhash="22f415bec935e3cb",
        brand="oppo"
    )
    assert matched_loader is not None
    assert "rmx3471" in matched_loader.lower() or "oppo" in matched_loader.lower()
    assert os.path.exists(matched_loader)
    print(f"  Auto-matched Qualcomm Loader: {os.path.basename(matched_loader)}")

    # 7. Test Preloader Listing & Lookup
    preloaders = ModelRepository.list_available_preloaders()
    print(f"  Available Preloaders ({len(preloaders)}): {len(preloaders)} binaries loaded")
    assert len(preloaders) >= 840
    assert "preloader_x682b_h694.bin" in preloaders

    # 8. Test Preloader File Resolution
    pl_path = ModelRepository.find_preloader_file("preloader_x682b_h694.bin")
    assert pl_path is not None
    assert os.path.exists(pl_path)
    print(f"  Resolved Infinix Hot 10 Preloader: {pl_path}")

    # 9. Test Oppo Brand Query
    oppo_models = ModelRepository.get_models_by_brand("Oppo")
    assert len(oppo_models) >= 3
    print(f"  Oppo Models ({len(oppo_models)}): {oppo_models}")

    # 11. Test MediaTek Universal DAs & Auth Bypass Payloads
    mtk_loaders = ModelRepository.list_available_loaders("mtk")
    print(f"  MTK Loaders count: {len(mtk_loaders)}")
    assert "MTK_DA_V6.bin" in mtk_loaders
    assert "MTK_DA_V5.bin" in mtk_loaders

    payloads = ModelRepository.list_available_payloads()
    print(f"  MTK Auth Bypass Payloads ({len(payloads)}): {len(payloads)} files loaded")
    assert len(payloads) >= 55
    assert "da_x.bin" in payloads
    assert "mt6765_payload.bin" in payloads
    assert "mt6877_payload.bin" in payloads

    p_6765 = ModelRepository.find_payload_file("mt6765")
    assert p_6765 is not None
    assert os.path.exists(p_6765)
    print(f"  Resolved MT6765 Payload: {os.path.basename(p_6765)}")

    p_dax = ModelRepository.find_payload_file("da_x")
    assert p_dax is not None
    assert os.path.exists(p_dax)
    print(f"  Resolved Custom DA_X Payload: {os.path.basename(p_dax)}")

    print("\n[ALL MODEL REPOSITORY TESTS PASSED 100%]\n")


if __name__ == "__main__":
    test_model_repository()
