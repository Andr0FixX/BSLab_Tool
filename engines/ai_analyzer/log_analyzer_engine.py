"""
BS Lab Tool v2.0 PRO - AI Log & Hardware UART Diagnostic Analyzer Engine
Performs offline pattern matching and technical root-cause diagnostics on GSM flashing logs,
tool exceptions, and hardware motherboard UART serial boot logs.
"""

import re
import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

@dataclass
class DiagnosisReport:
    fault_type: str
    subsystem: str
    severity: str  # "CRITICAL_HARDWARE", "FIRMWARE_CONFIG", "DRIVER_CONNECTION", "HEALTHY"
    confidence: float
    signature_matched: str
    summary: str
    technical_details: str
    repair_steps: List[str] = field(default_factory=list)
    schematic_test_points: List[str] = field(default_factory=list)

    @property
    def severity_color(self) -> str:
        colors = {
            "CRITICAL_HARDWARE": "#EF4444",   # Red
            "FIRMWARE_CONFIG": "#F59E0B",     # Yellow
            "DRIVER_CONNECTION": "#3B82F6",   # Blue
            "HEALTHY": "#10B981"              # Green
        }
        return colors.get(self.severity, "#94A3B8")

    @property
    def severity_badge(self) -> str:
        badges = {
            "CRITICAL_HARDWARE": "🔴 HARDWARE REPAIR REQUIRED",
            "FIRMWARE_CONFIG": "🟡 FIRMWARE / CONFIG FIX",
            "DRIVER_CONNECTION": "🔵 DRIVER / USB CONNECTION ISSUE",
            "HEALTHY": "🟢 LOG NORMAL / HEALTHY"
        }
        return badges.get(self.severity, "⚪ UNKNOWN ISSUE")


class AILogAnalyzerEngine:
    """Intelligent offline GSM & UART Log Diagnostic Engine."""

    # Rule Patterns: (Regex Pattern, Fault Type, Subsystem, Severity, Confidence, Summary, Details, Steps, TestPoints)
    RULES = [
        # ---------------------------------------------------------------------
        # 1. HARDWARE UART SERIAL BOOT LOG PATTERNS
        # ---------------------------------------------------------------------
        (
            r"(dram[_\s]*calibration[_\s]*fail|ddr[_\s]*init[_\s]*error|lpddr[0-9]*[_\s]*init[_\s]*fail|channel[_\s]*[ab][_\s]*training[_\s]*timeout)",
            "Hardware Fault",
            "RAM / LPDDR",
            "CRITICAL_HARDWARE",
            0.98,
            "LPDDR RAM Initialization & Calibration Failure (RAM or CPU Cold Solder)",
            "The Application Processor failed to train and calibrate memory timing channels with the LPDDR RAM chip. Common on dropped devices or thermal stress.",
            [
                "Perform thermal inspection around CPU & RAM sandwich package.",
                "Probe VDD_DRAM (1.1V) and VDDQ (0.6V) buck coils near PMIC.",
                "Check RAM CLK and CMD signal lines with oscilloscope or multimeter.",
                "If voltages are stable, RAM / CPU reballing is required."
            ],
            ["VDD_DRAM (1.1V)", "VDDQ (0.6V)", "VREF_CA (0.6V)", "DRAM_CLK Test Point"]
        ),
        (
            r"(ufs[_\s]*link[_\s]*startup[_\s]*fail|emmc[_\s]*init[_\s]*timeout|cmd1[_\s]*timeout|mmc[_\s]*card[_\s]*not[_\s]*found|storage[_\s]*probe[_\s]*fail)",
            "Hardware Fault",
            "eMMC / UFS Storage",
            "CRITICAL_HARDWARE",
            0.96,
            "Internal Flash Storage (eMMC / UFS) Link Startup Failure",
            "The CPU BootROM or secondary bootloader cannot establish high-speed link with the storage chip. Storage IC may have lost power, data lines damaged, or chip is dead.",
            [
                "Measure VCC (2.8V / 3.3V) and VCCQ (1.8V) supply lines for flash memory.",
                "Verify CLK line pull-up / series resistor continuity to ground.",
                "Inspect motherboard for bending near storage IC shield.",
                "Reball or replace eMMC/UFS BGA chip with pre-programmed RPMB."
            ],
            ["VCC_FLASH (2.8V - 3.3V)", "VCCQ_FLASH (1.8V)", "EMMC_CLK", "EMMC_CMD / UFS_RX_P"]
        ),
        (
            r"(pmic[_\s]*init[_\s]*fail|regulator[_\s]*enable[_\s]*timeout|buck[0-9]*[_\s]*drop|vsys[_\s]*undervoltage)",
            "Hardware Fault",
            "PMIC / Power Management",
            "CRITICAL_HARDWARE",
            0.95,
            "PMIC Power Rail Failure / Voltage Drop Detected",
            "The Power Management IC (PMIC) reported power sequence failure, missing Power Good signal, or buck regulator shutdown due to short circuit.",
            [
                "Check battery connector voltage and VSYS rail (3.8V - 4.2V).",
                "Probe VDD_CORE (0.75V - 0.85V) for short to ground.",
                "Inspect PMIC peripheral capacitors for heating using thermal camera.",
                "Replace main PMIC (e.g., MT6357, PMI632, SC2721)."
            ],
            ["VSYS (4.0V)", "VDD_CORE (0.8V)", "VIO18 (1.8V)", "PMIC_RESET_N"]
        ),
        (
            r"(kernel[_\s]*panic|watchdog[_\s]*bite|oops:[_\s]*fatal[_\s]*exception|subsystem[_\s]*restart[_\s]*failed)",
            "Hardware / System Crash",
            "Kernel & SoC Watchdog",
            "CRITICAL_HARDWARE",
            0.90,
            "SoC Kernel Panic / Hardware Watchdog Bite Reset (Bootloop)",
            "The device CPU encountered an unrecoverable kernel panic or hardware peripheral freeze, causing watchdog hardware reset timer to bite.",
            [
                "Check log for the exact faulting address or driver (e.g. WiFi/BT, Audio codec, Modem).",
                "Disconnect external flex cables (cameras, fingerprint, sub-board).",
                "Flash stock clean boot.img and vendor.img firmware.",
                "If problem persists, check modem baseband power rail."
            ],
            ["WDOG_RST_N", "VBAT_MODEM", "WIFI_VDD (1.8V)"]
        ),

        # ---------------------------------------------------------------------
        # 2. MEDIATEK (MTK) FLASHING LOG ERRORS
        # ---------------------------------------------------------------------
        (
            r"(status[_\s]*ext[_\s]*ram[_\s]*exception|0xc0050005|s_ft_enable_dram_fail|err_dram_init)",
            "Hardware Fault",
            "MediaTek EMI / DRAM",
            "CRITICAL_HARDWARE",
            0.99,
            "MediaTek BROM Error: STATUS_EXT_RAM_EXCEPTION [0xC0050005]",
            "The DA (Download Agent) successfully connected, but failed to initialize external DDR RAM. This is 95% a physical hardware fault (cracked solder or dead RAM coil).",
            [
                "Check 1.1V VDD_DRAM and 0.6V VTT coils near MTK PMIC.",
                "Ensure scatter file contains correct RAM preloader timings.",
                "Apply gentle heat (320°C) with flux around RAM/CPU to reflow.",
                "If issue remains, remove shielding and reball MTK CPU/RAM sandwich."
            ],
            ["VDD_DRAM (1.1V)", "VDD2 (1.2V)", "VREF (0.6V)", "PMIC MT6357 / MT6358"]
        ),
        (
            r"(status[_\s]*sec[_\s]*auth[_\s]*file[_\s]*needed|0xc0020002|sla_challenge_fail|s_security_secure_usb_dl_image_sign_check_fail)",
            "Firmware / Security",
            "BROM SLA / DAA Auth",
            "FIRMWARE_CONFIG",
            0.97,
            "MediaTek Security Error: BROM Authentication (SLA/DAA) Required",
            "The target device has secure boot and authorization enabled. Standard DA cannot write partitions without OEM cryptographic signature.",
            [
                "Switch to MTK Tab and click '⚡ Disable SLA / DAA (Auth Bypass)'.",
                "Hold Volume Up + Volume Down and insert USB cable to exploit BROM.",
                "Ensure 'Bypass SLA/DAA' checkbox is checked before starting flash."
            ],
            ["BROM USB D+ / D-", "Force BROM via Test Point (CLK to GND)"]
        ),
        (
            r"(status[_\s]*da[_\s]*exceed[_\s]*max[_\s]*image[_\s]*count|da_hash_mismatch|s_da_handshake_fail)",
            "Configuration Error",
            "Download Agent (DA)",
            "FIRMWARE_CONFIG",
            0.94,
            "MediaTek DA Version Mismatch / DA Handshake Failure",
            "The loaded DA binary is incompatible with this chipset's architecture or partition layout.",
            [
                "Select 'Custom DA' option in tool and choose matching chipset DA.",
                "For newer Helio / Dimensity SoCs, use multi-DA v6.",
                "Verify scatter file corresponds to exact phone build number."
            ],
            ["DA Binary Compatibility Table"]
        ),
        (
            r"(cmd_write_data[_\s]*failed|status[_\s]*storage[_\s]*not[_\s]*ready|s_storage_emmc_read_only|status[_\s]*write[_\s]*fail)",
            "Hardware Fault",
            "Storage / eMMC Degraded",
            "CRITICAL_HARDWARE",
            0.96,
            "Flash Memory Write Rejection (eMMC/UFS Read-Only or Bad Blocks)",
            "The storage IC acknowledged commands but failed physical sector write verification. Typically indicates eMMC memory health reached 90% EOF life.",
            [
                "Check if flash mode is write-protected or encrypted.",
                "Test eMMC health via ISP Pinout using EasyJTAG or UFI Box.",
                "If SLC/MLC life is at 100% consumed, replace eMMC chip.",
                "Re-partition and format via scatter if bad blocks are logical only."
            ],
            ["ISP eMMC Pinout (CLK, CMD, DAT0, VCC, VCCQ)"]
        ),

        # ---------------------------------------------------------------------
        # 3. QUALCOMM SNAPDRAGON (EDL 9008) ERRORS
        # ---------------------------------------------------------------------
        (
            r"(sahara[_\s]*nak[_\s]*0x0000000e|sahara[_\s]*hello[_\s]*failed|command[_\s]*rejected[_\s]*by[_\s]*target)",
            "Configuration / Auth",
            "Qualcomm Sahara Protocol",
            "FIRMWARE_CONFIG",
            0.96,
            "Qualcomm Sahara Error: NAK 0x0000000E (Programmer Rejected)",
            "The Qualcomm Secondary Bootloader (PBL) rejected the selected prog_firehose_*.elf programmer. Reasons: Wrong HWID, OEM PK-Hash signature mismatch, or wrong DDR type (DDR4 vs DDR5).",
            [
                "Verify device SoC (e.g. SDM660, SM6115, SM7150) matches programmer ELF.",
                "For Xiaomi/Oppo devices, ensure programmer is authenticated (Signed ELF).",
                "Try alternate firehose loader from same CPU family.",
                "Unplug battery, reconnect test point, and re-insert USB cable."
            ],
            ["EDL Test Point", "USB D+ / D- QDLoader 9008 COM Port"]
        ),
        (
            r"(firehose[_\s]*nak|sector[_\s]*write[_\s]*error|write[_\s]*failed[_\s]*to[_\s]*sector|failed[_\s]*to[_\s]*configure[_\s]*ufs[_\s]*lun)",
            "Hardware Fault",
            "Qualcomm UFS / eMMC",
            "CRITICAL_HARDWARE",
            0.95,
            "Qualcomm Firehose Write Failure / UFS LUN Communication Error",
            "Firehose programmer successfully loaded into RAM, but storage drive write operation failed. Indicates damaged UFS LUN partitions or physical hardware defect.",
            [
                "Check rawprogram0.xml sector sizes and partition boundaries.",
                "Probe UFS power rails: VCC (2.5V - 3.3V) and VCCQ2 (1.2V).",
                "If sector write stalls at same offset every time, storage has bad NAND blocks."
            ],
            ["UFS_VCC (2.5V)", "UFS_VCCQ2 (1.2V)", "UFS_RESET_N"]
        ),
        (
            r"(failed[_\s]*to[_\s]*open[_\s]*com[_\s]*port|serial[_\s]*exception|access[_\s]*denied.*com|port[_\s]*disconnected)",
            "Connection / Driver",
            "USB Serial COM Interface",
            "DRIVER_CONNECTION",
            0.92,
            "COM Port Access Denied or Unexpected Disconnection",
            "The Windows COM port was abruptly closed by device watchdog or occupied by another background application (e.g., ModemManager, QFIL, MiFlash).",
            [
                "Close other flashing tools or ADB server instances in Task Manager.",
                "Check USB cable and USB port (connect directly to motherboard rear USB 2.0).",
                "Open '🔧 Drivers' in tool and verify Qualcomm QDLoader 9008 driver.",
                "Ensure phone battery has at least 3.7V charge."
            ],
            ["USB Cable", "Windows Device Manager COM Port"]
        ),

        # ---------------------------------------------------------------------
        # 4. SAMSUNG ODIN PROTOCOL ERRORS
        # ---------------------------------------------------------------------
        (
            r"(fail![\s\S]*\(auth\)|sw[_\s]*rev[_\s]*check[_\s]*fail|device[_\s]*[0-9]*[_\s]*binary[_\s]*[0-9]*|fused[_\s]*[0-9]*.*binary[_\s]*[0-9]*)",
            "Firmware / Security",
            "Samsung Knox / Binary Rollback",
            "FIRMWARE_CONFIG",
            0.98,
            "Samsung Odin Error: Binary Rollback Check Failed (SW REV CHECK FAIL)",
            "You are attempting to flash a firmware with a lower binary (bootloader rollback security) than what is currently fused in the CPU Knox OTP registers.",
            [
                "Read current binary version from phone Download Mode screen (e.g. 'B:4' or 'BIT:4').",
                "Download a Samsung official firmware with equal or higher binary level (e.g. U4, S4, or higher).",
                "Never attempt to downgrade binary on Samsung Knox devices."
            ],
            ["Samsung Download Mode Screen Status"]
        ),
        (
            r"(nand[_\s]*write[_\s]*start[\s\S]*failed!|complete\(write\)[_\s]*operation[_\s]*failed|hidden\.img[_\s]*fail)",
            "Firmware / Partition",
            "Samsung NAND Partitioning",
            "FIRMWARE_CONFIG",
            0.93,
            "Samsung Odin Error: NAND Write Operation Failed / Hidden.img Fail",
            "Partition size mismatch between active PIT table and firmware package. Common when flashing firmware from a different regional CSC carrier.",
            [
                "Load matching PIT file in Odin PIT slot and check 'Re-Partition'.",
                "If failure occurred on hidden.img, use HOME_CSC instead of CSC.",
                "Ensure USB 3.0 / USB-C connection is stable."
            ],
            ["PIT Partition Table Table (BL / CSC)"]
        ),

        # ---------------------------------------------------------------------
        # 5. UNISOC / SPREADTRUM (SPD) ERRORS
        # ---------------------------------------------------------------------
        (
            r"(fdl2[_\s]*timeout|check[_\s]*baudrate[_\s]*timeout|spreadtrum[_\s]*handshake[_\s]*fail|bsl[_\s]*not[_\s]*responding)",
            "Connection / Protocol",
            "Unisoc BSL / FDL Handshake",
            "DRIVER_CONNECTION",
            0.94,
            "Unisoc BSL Bootloader Handshake Timeout / FDL Transmission Failure",
            "The device did not answer boot rom sync packet (0x7E) within timeout window, or FDL2 loader timed out.",
            [
                "Verify phone is fully powered OFF before holding Volume Down + plugging USB.",
                "Install Unisoc SPRD COM Driver from '🔧 Drivers' menu.",
                "Ensure PAC firmware file matches target Tiger/SC chipset variant exactly."
            ],
            ["SPRD USB D+ / D- Boot Key (Vol- or Boot Pin)"]
        ),

        # ---------------------------------------------------------------------
        # 6. FASTBOOT & ADB ERRORS
        # ---------------------------------------------------------------------
        (
            r"(failed[_\s]*\(remote:[_\s]*partition[_\s]*table[_\s]*doesn't[_\s]*exist\)|failed[_\s]*\(remote:[_\s]*unknown[_\s]*partition\))",
            "Firmware / Dynamic Partition",
            "Fastboot Bootloader",
            "FIRMWARE_CONFIG",
            0.95,
            "Fastboot Error: Partition Not Found (FastbootD Required)",
            "Target partition (system, vendor, product) is a logical dynamic partition (Android 10+), which cannot be flashed in standard bootloader mode.",
            [
                "Switch to FastbootD mode by running command: fastboot reboot fastboot.",
                "Once in FastbootD screen, re-flash the partition.",
                "Check partition slot (_a or _b) using Slot Controller."
            ],
            ["FastbootD Dynamic Super Partition"]
        )
    ]

    def __init__(self, logger=None):
        self.logger = logger
        self.active_listener = None

    def analyze_log(self, raw_log: str, log_hint: str = "auto") -> DiagnosisReport:
        """
        Analyzes raw log text and returns a structured diagnostic report with actionable repair roadmap.
        """
        if not raw_log or not raw_log.strip():
            return DiagnosisReport(
                fault_type="No Data",
                subsystem="None",
                severity="HEALTHY",
                confidence=0.0,
                signature_matched="None",
                summary="Log text is empty. Please paste log content or capture from tool/UART.",
                technical_details="No lines were available for pattern evaluation.",
                repair_steps=["Paste or capture log text to initiate diagnosis."]
            )

        log_lower = raw_log.lower()

        # Step 1: Scan rule pattern matrix
        for pattern, fault_type, subsystem, severity, conf, summary, details, steps, tps in self.RULES:
            match = re.search(pattern, log_lower, re.IGNORECASE)
            if match:
                matched_str = match.group(0)
                return DiagnosisReport(
                    fault_type=fault_type,
                    subsystem=subsystem,
                    severity=severity,
                    confidence=conf,
                    signature_matched=matched_str,
                    summary=summary,
                    technical_details=details,
                    repair_steps=steps,
                    schematic_test_points=tps
                )

        # Step 2: Fallback heuristic analysis
        if "error" in log_lower or "failed" in log_lower or "fail" in log_lower:
            err_lines = [line.strip() for line in raw_log.splitlines() if any(k in line.lower() for k in ["error", "fail", "timeout", "exception"])]
            sample_err = err_lines[0] if err_lines else "Generic failure detected"

            return DiagnosisReport(
                fault_type="General Operation Error",
                subsystem="Unknown Protocol",
                severity="FIRMWARE_CONFIG",
                confidence=0.75,
                signature_matched=sample_err[:60],
                summary="Operation failed with generic error signature.",
                technical_details=f"Extracted error line: {sample_err}",
                repair_steps=[
                    "Check USB cable connection and COM port stability.",
                    "Verify firmware package compatibility with exact device model.",
                    "Restart phone in boot mode and re-attempt operation."
                ],
                schematic_test_points=["Battery Voltage (3.8V+)", "USB D+ / D- continuity"]
            )

        # Step 3: Log is healthy / normal
        return DiagnosisReport(
            fault_type="No Errors Detected",
            subsystem="System Normal",
            severity="HEALTHY",
            confidence=0.99,
            signature_matched="Success / Clean Log",
            summary="No error patterns or hardware faults detected in log.",
            technical_details="The log sequence appears normal without critical exceptions, crashes, or timeouts.",
            repair_steps=["No action required. Log indicates normal operation."]
        )


class UARTStreamListener:
    """Listens to hardware UART COM port in real-time and streams output."""

    def __init__(self, port: str, baudrate: int = 115200, on_line_cb: Optional[Callable[[str], None]] = None):
        self.port = port
        self.baudrate = baudrate
        self.on_line_cb = on_line_cb
        self._running = False
        self._thread = None
        self._ser = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass

    def _read_loop(self):
        try:
            import serial
            self._ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            while self._running:
                line = self._ser.readline()
                if line:
                    decoded = line.decode("ascii", errors="replace").strip()
                    if decoded and self.on_line_cb:
                        self.on_line_cb(decoded)
        except Exception as e:
            if self.on_line_cb:
                self.on_line_cb(f"[UART Error] {str(e)}")
        finally:
            self._running = False
