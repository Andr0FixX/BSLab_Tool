import serial
import time
import struct

def make_crc_table():
    table = []
    for i in range(256):
        curr = i
        for _ in range(8):
            if curr & 1:
                curr = (curr >> 1) ^ 0x8408
            else:
                curr >>= 1
        table.append(curr)
    return table

CRC_TABLE = make_crc_table()

def calc_crc(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc = ((crc >> 8) & 0xFF) ^ CRC_TABLE[(crc ^ b) & 0xFF]
    return (~crc) & 0xFFFF

def hdlc_encode(payload: bytes) -> bytes:
    crc = calc_crc(payload)
    raw = payload + struct.pack('<H', crc)
    out = bytearray()
    for b in raw:
        if b == 0x7E:
            out.extend([0x7D, 0x5E])
        elif b == 0x7D:
            out.extend([0x7D, 0x5D])
        else:
            out.append(b)
    return bytes([0x7E]) + bytes(out) + bytes([0x7E])

try:
    ser = serial.Serial('COM35', 115200, timeout=1.0)
    ser.dtr = True
    ser.rts = True
    time.sleep(0.1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print("Sending Cmd 0x00 (Version Request)...", flush=True)
    enc = hdlc_encode(b'\x00')
    ser.write(enc)
    time.sleep(0.2)

    data = ser.read(ser.in_waiting or 100)
    print("Received raw:", data.hex() if data else "Nothing", flush=True)

    ser.close()
except Exception as e:
    print("Exception:", e, flush=True)
