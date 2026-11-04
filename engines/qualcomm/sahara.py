import time
import struct
import os
import serial

class SaharaEngine:
    """Qualcomm Sahara Protocol Handshake & Firehose Programmer Loader."""

    CMD_HELLO_REQ = 0x01
    CMD_HELLO_RSP = 0x02
    CMD_READ_DATA = 0x03
    CMD_END_IMAGE_TX = 0x04
    CMD_DONE_REQ = 0x05
    CMD_DONE_RSP = 0x06
    CMD_RESET_REQ = 0x07
    CMD_RESET_RSP = 0x08
    CMD_READ_DATA_64 = 0x12

    def __init__(self, serial_port: serial.Serial, logger=None):
        self.ser = serial_port
        self.logger = logger
        self.aborted = False

    def log(self, msg, level="info"):
        if self.logger:
            if level == "success":
                self.logger.success(msg)
            elif level == "error":
                self.logger.error(msg)
            elif level == "warn":
                self.logger.warn(msg)
            else:
                self.logger.brom(msg)
        else:
            print(f"[SAHARA] {msg}")

    def execute_handshake(self, programmer_path: str) -> bool:
        """
        Executes Sahara Handshake and streams programmer (prog_firehose_*.elf/mbn) to target.
        Returns True if device successfully enters Firehose mode.
        """
        if not os.path.exists(programmer_path):
            self.log(f"Programmer file not found: {programmer_path}", "error")
            return False

        prog_size = os.path.getsize(programmer_path)
        self.log(f"Initiating Sahara Handshake with Programmer: {os.path.basename(programmer_path)} ({prog_size} bytes)...")

        try:
            with open(programmer_path, "rb") as pf:
                prog_data = pf.read()

            # 1. Read Hello Packet from device
            # Device sends 0x01 0x00 0x00 0x00 ... (48 bytes)
            hello_raw = b""
            start_t = time.time()
            while time.time() - start_t < 6.0:
                available = self.ser.in_waiting
                if available > 0:
                    hello_raw += self.ser.read(available)
                    idx = hello_raw.find(b"\x01\x00\x00\x00")
                    if idx != -1 and len(hello_raw[idx:]) >= 48:
                        hello_raw = hello_raw[idx : idx + 48]
                        break
                time.sleep(0.05)

            if not hello_raw or len(hello_raw) < 8:
                # Try gentle single-byte wake-up to prompt BootROM buffer
                self.ser.write(b"\x00")
                time.sleep(0.2)
                if self.ser.in_waiting >= 8:
                    extra = self.ser.read(self.ser.in_waiting)
                    idx = extra.find(b"\x01\x00\x00\x00")
                    if idx != -1 and len(extra[idx:]) >= 48:
                        hello_raw = extra[idx : idx + 48]

            if not hello_raw or len(hello_raw) < 8:
                # Check if device is already in Firehose mode (sending XML)
                self.ser.write(b"<?xml version=\"1.0\" ?><data><nop /></data>\n")
                time.sleep(0.15)
                probe = self.ser.read_all()
                if probe and (b"response" in probe or b"xml" in probe or b"ACK" in probe):
                    self.log("Device is already in Firehose XML mode (Programmer already active)!", "success")
                    return True
                self.log("No response to Sahara Hello from device. Port is open, but device BootROM is not handshaking.", "error")
                self.log("[!] NOTE: Phone ko aik martaba USB se disconnect karein, aur dobara EDL 9008 mode mein connect karein taake Qualcomm BootROM fresh reset ho sake.", "warn")
                return False

            cmd, length = struct.unpack("<II", hello_raw[:8])
            if cmd != self.CMD_HELLO_REQ:
                self.log(f"Unexpected Sahara Command received: 0x{cmd:02X} (Expected 0x01 Hello)", "warn")
                return False

            version, min_ver, max_pkt_sz, mode = struct.unpack("<IIII", hello_raw[8:24])
            self.log(f"[SYNC] Sahara Hello received: Version={version}, Mode={mode}, MaxPacket={max_pkt_sz}")

            # 2. Send Hello Response (0x02)
            # cmd=0x02, len=0x30, ver=0x02, status=0, mode=0, reserved[7]
            hello_resp = struct.pack("<IIIIIIIIIIII", self.CMD_HELLO_RSP, 0x30, version, 0, mode, 0, 0, 0, 0, 0, 0, 0)
            self.ser.write(hello_resp)
            self.log("[SYNC] Sahara Hello Response Sent. Awaiting Data Request...")

            # 3. Handle Read Data loop
            bytes_transferred = 0
            while not self.aborted:
                req_hdr = self.ser.read(8)
                if not req_hdr or len(req_hdr) < 8:
                    continue

                cmd_id, pkt_len = struct.unpack("<II", req_hdr)

                # Case A: 32-bit Read Data (0x03)
                if cmd_id == self.CMD_READ_DATA:
                    rest = self.ser.read(pkt_len - 8)
                    image_id, data_offset, data_len = struct.unpack("<III", rest[:12])
                    chunk = prog_data[data_offset : data_offset + data_len]
                    self.ser.write(chunk)
                    bytes_transferred += len(chunk)

                # Case B: 64-bit Read Data (0x12)
                elif cmd_id == self.CMD_READ_DATA_64:
                    rest = self.ser.read(pkt_len - 8)
                    image_id, data_offset, data_len = struct.unpack("<IQQ", rest[:20])
                    chunk = prog_data[data_offset : data_offset + data_len]
                    self.ser.write(chunk)
                    bytes_transferred += len(chunk)

                # Case C: End of Image Transfer (0x04)
                elif cmd_id == self.CMD_END_IMAGE_TX:
                    rest = self.ser.read(pkt_len - 8)
                    img_id, status = struct.unpack("<II", rest[:8])
                    if status == 0:
                        self.log(f"Programmer Transfer Complete ({bytes_transferred} bytes verified)!", "success")
                        # Send Done Request (0x05)
                        done_req = struct.pack("<II", self.CMD_DONE_REQ, 8)
                        self.ser.write(done_req)
                    else:
                        self.log(f"Sahara End Image Tx reported failure status: 0x{status:02X}", "error")
                        return False

                # Case D: Done Response (0x06) -> SUCCESS!
                elif cmd_id == self.CMD_DONE_RSP:
                    rest = self.ser.read(pkt_len - 8)
                    self.log("Sahara Handshake Finalized! Device switching to Firehose XML...", "success")
                    time.sleep(0.5)
                    return True

                # Case E: Reset Response / Error
                elif cmd_id == self.CMD_RESET_RSP:
                    self.log("Sahara Target Reset received.", "warn")
                    return False
                else:
                    # Ignore non-blocking padding or unhandled debug
                    pass

            return False
        except Exception as e:
            self.log(f"Sahara Handshake Exception: {str(e)}", "error")
            return False
