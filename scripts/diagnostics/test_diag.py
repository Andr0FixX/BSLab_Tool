import serial
import time
import struct

# Table for CRC-16-CCITT (reversed / Qualcomm Diag)
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

def hdlc_decode(frame: bytes) -> bytes:
    if frame.startswith(b'\x7e'):
        frame = frame[1:]
    if frame.endswith(b'\x7e'):
        frame = frame[:-1]
    res = bytearray()
    i = 0
    while i < len(frame):
        if frame[i] == 0x7D and i + 1 < len(frame):
            res.append(frame[i+1] ^ 0x20)
            i += 2
        else:
            res.append(frame[i])
            i += 1
    if len(res) < 2:
        return bytes(res)
    payload = res[:-2]
    # verify crc
    expected_crc = calc_crc(payload)
    actual_crc = struct.unpack('<H', res[-2:])[0]
    return bytes(payload)

def send_recv(ser, payload, timeout=1.0):
    enc = hdlc_encode(payload)
    ser.write(enc)
    time.sleep(0.05)
    t0 = time.time()
    buf = bytearray()
    while time.time() - t0 < timeout:
        if ser.in_waiting:
            c = ser.read(ser.in_waiting)
            buf.extend(c)
            if b'\x7e' in buf[1:]:
                # found end of frame
                break
        time.sleep(0.02)
    if not buf:
        return None
    # split by 0x7e
    frames = [f for f in buf.split(b'\x7e') if len(f) > 2]
    if frames:
        return hdlc_decode(frames[0])
    return None

try:
    ser = serial.Serial('COM35', 115200, timeout=1)
    print("COM35 opened successfully!", flush=True)

    # 1. Version request (cmd 0x00)
    resp = send_recv(ser, b'\x00')
    print("Cmd 0x00 (Version) response:", resp.hex() if resp else "None", flush=True)

    # 2. Unlock SPC (cmd 0x41 with '000000' or cmd 0x29)
    # DIAG_SPC_F = 0x41
    spc_payload = b'\x41' + b'000000'
    resp = send_recv(ser, spc_payload)
    print("Cmd 0x41 (Unlock SPC 000000) response:", resp.hex() if resp else "None", flush=True)

    # 3. Read NV Item 550 (NV_UE_IMEI_I = 550 = 0x0226)
    # DIAG_NV_READ_F = 0x26
    # payload: cmd(1) + item_id(2 LE) + 128 bytes dummy/zero + status(2 LE)
    nv_read_payload = struct.pack('<BH', 0x26, 550) + (b'\x00' * 130)
    resp = send_recv(ser, nv_read_payload)
    if resp:
        print(f"NV 550 Read Response length: {len(resp)}", flush=True)
        print("NV 550 Response hex:", resp.hex(), flush=True)
        if len(resp) >= 3:
            cmd = resp[0]
            item = struct.unpack('<H', resp[1:3])[0]
            status = struct.unpack('<H', resp[-2:])[0]
            print(f"Cmd: 0x{cmd:02X}, Item: {item}, Status: {status} (0=OK)", flush=True)
            data = resp[3:-2]
            print("Data (hex):", data[:16].hex(), flush=True)
    else:
        print("NV 550 Read returned None!", flush=True)

    ser.close()
except Exception as e:
    print(f"Exception: {e}", flush=True)
