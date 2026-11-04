import time
import serial
from core.logger import UILogger
from mtk.chipset_db import MtkChipsetDatabase

class MtkBromEngine:
    """Core MediaTek BootROM (BROM) Protocol Engine."""

    CMD_GET_HW_CODE = 0xFD
    CMD_GET_HW_SUB_CODE = 0xFE
    CMD_GET_HW_VER = 0xFF
    CMD_GET_SW_VER = 0xFC
    CMD_GET_TARGET_CONFIG = 0xD8

    def __init__(self, logger: UILogger):
        self.logger = logger
        self.serial_port = None

    def _open_port(self, port_name: str, baudrate: int = 115200, timeout: float = 1.0):
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                write_timeout=timeout
            )
            # Toggle DTR/RTS to wake up USB UART transceiver
            self.serial_port.dtr = True
            self.serial_port.rts = True
            time.sleep(0.05)
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            return True
        except Exception as e:
            self.logger.error(f"Failed to open {port_name}: {str(e)}")
            return False

    def _close_port(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None

    def _handshake(self) -> bool:
        """Executes the standard 4-Phase MTK BROM Synchronization."""
        self.logger.brom("Initiating MTK BROM Handshake Sequence...")
        
        # Phase 1: 0xA0 -> 0x5F (Loop up to 30 attempts)
        synced = False
        for attempt in range(1, 31):
            try:
                self.serial_port.write(bytes([0xA0]))
                resp = self.serial_port.read(1)
                if resp and resp[0] == 0x5F:
                    self.logger.brom(f"[SYNC 1/4] Sent 0xA0 -> Got 0x5F ACK (Attempt #{attempt})")
                    synced = True
                    break
                time.sleep(0.05)
            except Exception:
                pass

        if not synced:
            self.logger.error("Failed to sync Phase 1 (0xA0 -> 0x5F). Ensure phone is connected in BROM mode (Vol+ & Vol-).")
            return False

        # Phase 2: 0x0A -> 0xF5
        self.serial_port.write(bytes([0x0A]))
        resp2 = self.serial_port.read(1)
        if not resp2 or resp2[0] != 0xF5:
            self.logger.error(f"Phase 2 Sync Mismatch: Expected 0xF5, Got {resp2.hex() if resp2 else 'None'}")
            return False

        # Phase 3: 0x50 -> 0xAF
        self.serial_port.write(bytes([0x50]))
        resp3 = self.serial_port.read(1)
        if not resp3 or resp3[0] != 0xAF:
            self.logger.error(f"Phase 3 Sync Mismatch: Expected 0xAF, Got {resp3.hex() if resp3 else 'None'}")
            return False

        # Phase 4: 0x05 -> 0xFA
        self.serial_port.write(bytes([0x05]))
        resp4 = self.serial_port.read(1)
        if not resp4 or resp4[0] != 0xFA:
            self.logger.error(f"Phase 4 Sync Mismatch: Expected 0xFA, Got {resp4.hex() if resp4 else 'None'}")
            return False

        self.logger.success("MTK BROM Handshake Synchronized Successfully (All 4 Phases Verified)!")
        return True

    def _read_short_cmd(self, cmd: int):
        """Sends command and reads status (2 bytes) + 16-bit value (2 bytes)."""
        self.serial_port.write(bytes([cmd]))
        resp = self.serial_port.read(4)
        if len(resp) >= 4:
            status = (resp[0] << 8) | resp[1]
            val = (resp[2] << 8) | resp[3]
            return val
        return None

    def read_device_info(self, port_name: str) -> dict:
        """Reads complete hardware info from the connected MediaTek device."""
        self.logger.info(f"Connecting to {port_name}...")
        if not self._open_port(port_name):
            return None

        try:
            if not self._handshake():
                return None

            self.logger.info("Reading Hardware Architecture Registers...")
            
            # Read HW Code (0xFD)
            hw_code = self._read_short_cmd(self.CMD_GET_HW_CODE)
            if hw_code is None:
                self.logger.error("Failed to read Hardware Code (CMD 0xFD).")
                return None

            # Read HW Subcode (0xFE)
            hw_sub = self._read_short_cmd(self.CMD_GET_HW_SUB_CODE) or 0
            
            # Read HW Ver (0xFF)
            hw_ver = self._read_short_cmd(self.CMD_GET_HW_VER) or 0
            
            # Read SW Ver (0xFC)
            sw_ver = self._read_short_cmd(self.CMD_GET_SW_VER) or 0

            # Target Config (0xD8)
            self.serial_port.write(bytes([self.CMD_GET_TARGET_CONFIG]))
            cfg_resp = self.serial_port.read(8)
            sla_enabled = False
            daa_enabled = False
            sbc_enabled = False
            if len(cfg_resp) >= 4:
                cfg_val = (cfg_resp[2] << 8) | cfg_resp[3]
                sbc_enabled = bool(cfg_val & 0x01)
                sla_enabled = bool(cfg_val & 0x02)
                daa_enabled = bool(cfg_val & 0x04)

            # Query database
            db_info = MtkChipsetDatabase.lookup(hw_code)

            info = {
                "hw_code": f"0x{hw_code:04X}",
                "hw_code_int": hw_code,
                "soc": db_info["soc"],
                "name": db_info["name"],
                "family": db_info["family"],
                "hw_sub": f"0x{hw_sub:04X}",
                "hw_ver": f"0x{hw_ver:04X}",
                "sw_ver": f"0x{sw_ver:04X}",
                "sbc": sbc_enabled,
                "sla": sla_enabled,
                "daa": daa_enabled,
            }

            self.logger.success(f"Chipset Identified: {info['soc']} ({info['name']})")
            self.logger.info(f"HW Code: {info['hw_code']} | Sub: {info['hw_sub']} | Ver: {info['hw_ver']}")
            self.logger.info(f"Security: SBC={sbc_enabled} | SLA={sla_enabled} | DAA={daa_enabled}")
            return info

        except Exception as e:
            self.logger.error(f"Error during Read Info: {str(e)}")
            return None
        finally:
            self._close_port()

