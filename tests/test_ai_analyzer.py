"""
Unit Tests for AI Log & Hardware UART Analyzer Engine.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.ai_analyzer.log_analyzer_engine import AILogAnalyzerEngine, DiagnosisReport


def test_ai_analyzer():
    engine = AILogAnalyzerEngine()

    # 1. Test UART DRAM failure log
    uart_ram_log = """
    [0.120] PMIC: VDD_CORE=0.85V OK, VSYS=4.1V OK
    [0.245] BootROM: Handshake starting...
    [0.312] [DRAM] Channel A calibration fail: offset 0x4000 timing mismatch!
    [0.315] ddr_init error: halting boot.
    """
    rep1 = engine.analyze_log(uart_ram_log)
    print(f"[TEST 1 - UART RAM Failure]: {rep1.summary} (Severity: {rep1.severity})")
    assert rep1.subsystem == "RAM / LPDDR"
    assert rep1.severity == "CRITICAL_HARDWARE"
    assert len(rep1.repair_steps) > 0
    assert len(rep1.schematic_test_points) > 0

    # 2. Test MTK RAM Exception
    mtk_log = """
    Connecting to BROM...
    Sending DA...
    DA sent successfully!
    ERROR: STATUS_EXT_RAM_EXCEPTION (0xC0050005) at DA handshake!
    """
    rep2 = engine.analyze_log(mtk_log)
    print(f"[TEST 2 - MTK RAM Exception]: {rep2.summary}")
    assert "0xC0050005" in rep2.summary
    assert rep2.severity == "CRITICAL_HARDWARE"

    # 3. Test Qualcomm Sahara NAK
    qc_log = """
    [10:14:02] Connected to QDLoader 9008 on COM15
    [10:14:03] Sending Sahara Hello packet...
    [10:14:04] Error: Sahara NAK 0x0000000E received from device!
    """
    rep3 = engine.analyze_log(qc_log)
    print(f"[TEST 3 - Qualcomm Sahara NAK]: {rep3.summary}")
    assert "Sahara" in rep3.summary
    assert rep3.subsystem == "Qualcomm Sahara Protocol"

    # 4. Test Samsung SW Rev Check Fail
    samsung_log = """
    <ID:0/004> Added!!
    <ID:0/004> Odin engine v(ID:3.1401)..
    <ID:0/004> File analysis..
    <ID:0/004> SetupConnection..
    <ID:0/004> Initialzation..
    <ID:0/004> Get PIT for mapping..
    <ID:0/004> Firmware update start..
    <ID:0/004> sboot.bin
    <ID:0/004> FAIL! (Auth) SW REV CHECK FAIL : [boot]Fused 5 > Binary 3
    """
    rep4 = engine.analyze_log(samsung_log)
    print(f"[TEST 4 - Samsung SW REV Check]: {rep4.summary}")
    assert "Rollback" in rep4.summary
    assert rep4.severity == "FIRMWARE_CONFIG"

    # 5. Clean / Healthy log
    clean_log = """
    [2026-11-01] Flash boot.img ... OK [4.2s]
    [2026-11-01] Flash recovery.img ... OK [8.1s]
    [2026-11-01] All operations completed with 100% success.
    """
    rep5 = engine.analyze_log(clean_log)
    print(f"[TEST 5 - Clean Log]: {rep5.summary} (Severity: {rep5.severity})")
    assert rep5.severity == "HEALTHY"

    print("\n[ALL AI LOG ANALYZER TESTS PASSED 100%]\n")


if __name__ == "__main__":
    test_ai_analyzer()
