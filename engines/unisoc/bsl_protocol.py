import time
import struct
import serial

class BSLProtocol:
    """
    Spreadtrum / Unisoc Boot-Serial-Link (BSL) HDLC Packet Protocol.
    Handles 0x7E frame delimitation, byte-stuffing, and command acknowledgments.
    """

    FRAME_DELIMITER = 0x7E
    ESCAPE_BYTE = 0x7D

    # Standard BSL Commands
    CMD_CONNECT = 0x00
    CMD_START_DATA = 0x01
    CMD_MID_DATA = 0x02
    CMD_END_DATA = 0x03
    CMD_EXEC_DATA = 0x04
    CMD_NORMAL_RESET = 0x05
    CMD_READ_FLASH = 0x06
    CMD_READ_CHIP_TYPE = 0x08
    CMD_ERASE_FLASH = 0x09
    CMD_SET_BAUDRATE = 0x0A
    CMD_READ_PARTITION = 0x15
    CMD_WRITE_PARTITION = 0x16
    CMD_ERASE_PARTITION = 0x17

    # Responses
    REP_ACK = 0x80
    REP_VER = 0x81

    @staticmethod
    def escape_payload(data: bytes) -> bytes:
        """Applies HDLC byte stuffing (0x7E -> 0x7D 0x5E, 0x7D -> 0x7D 0x5D)."""
        out = bytearray()
        for b in data:
            if b == BSLProtocol.FRAME_DELIMITER:
                out.append(BSLProtocol.ESCAPE_BYTE)
                out.append(0x5E)
            elif b == BSLProtocol.ESCAPE_BYTE:
                out.append(BSLProtocol.ESCAPE_BYTE)
                out.append(0x5D)
            else:
                out.append(b)
        return bytes(out)

    @staticmethod
    def unescape_payload(data: bytes) -> bytes:
        """Reverses HDLC byte stuffing."""
        out = bytearray()
        escaped = False
        for b in data:
            if escaped:
                if b == 0x5E:
                    out.append(BSLProtocol.FRAME_DELIMITER)
                elif b == 0x5D:
                    out.append(BSLProtocol.ESCAPE_BYTE)
                else:
                    out.append(b)
                escaped = False
            elif b == BSLProtocol.ESCAPE_BYTE:
                escaped = True
            else:
                out.append(b)
        return bytes(out)

    @staticmethod
    def frame_packet(cmd_type: int, payload: bytes = b'') -> bytes:
        """
        Builds a complete BSL packet:
        0x7E + Escape(type[2] + len[2] + payload) + 0x7E
        """
        header = struct.pack(">HH", cmd_type, len(payload))
        raw_body = header + payload
        escaped_body = BSLProtocol.escape_payload(raw_body)
        return bytes([BSLProtocol.FRAME_DELIMITER]) + escaped_body + bytes([BSLProtocol.FRAME_DELIMITER])

    @staticmethod
    def send_cmd(ser: serial.Serial, cmd_type: int, payload: bytes = b'', timeout: float = 3.0) -> (bool, int, bytes):
        """
        Sends framed BSL command to serial port and waits for Response.
        Returns: (success: bool, resp_type: int, resp_payload: bytes)
        """
        packet = BSLProtocol.frame_packet(cmd_type, payload)
        ser.reset_input_buffer()
        ser.write(packet)

        start_t = time.time()
        buf = bytearray()
        in_frame = False

        while time.time() - start_t < timeout:
            byte = ser.read(1)
            if not byte:
                continue

            b = byte[0]
            if b == BSLProtocol.FRAME_DELIMITER:
                if in_frame and len(buf) >= 4:
                    # End of frame received
                    unescaped = BSLProtocol.unescape_payload(buf)
                    if len(unescaped) >= 4:
                        resp_type, resp_len = struct.unpack(">HH", unescaped[:4])
                        resp_data = unescaped[4 : 4 + resp_len]
                        is_ack = (resp_type == BSLProtocol.REP_ACK)
                        return is_ack, resp_type, resp_data
                    buf.clear()
                else:
                    in_frame = True
                    buf.clear()
            elif in_frame:
                buf.append(b)

        return False, 0, b''

    @staticmethod
    def sync_device(ser: serial.Serial, attempts: int = 40) -> bool:
        """
        Streams 0x7E synchronization frames to trap the Unisoc Bootloader (BROM).
        Returns True when phone responds with 0x7E ACK packet.
        """
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for attempt in range(1, attempts + 1):
            ser.write(bytes([BSLProtocol.FRAME_DELIMITER]))
            time.sleep(0.04)

            # Check if phone responded
            available = ser.in_waiting
            if available > 0:
                raw = ser.read(available)
                if BSLProtocol.FRAME_DELIMITER in raw:
                    return True

        return False
