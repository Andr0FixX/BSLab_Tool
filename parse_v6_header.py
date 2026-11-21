import struct

with open("resources/loaders/mtk/MTK_DA_V6.bin", "rb") as f:
    f.seek(0x60)
    # Read count & magic
    sec_count, magic = struct.unpack("<II", f.read(8))
    print(f"Sec count: {sec_count}, Magic: {hex(magic)}")
    
    # Let's inspect bytes from 0x60 to 0x200
    f.seek(0x60)
    data = f.read(256)
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{0x60 + i:04x}: {hex_str:<48} | {ascii_str}")
