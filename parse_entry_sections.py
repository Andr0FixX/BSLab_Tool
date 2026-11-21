import struct

with open("resources/loaders/mtk/MTK_DA_V6.bin", "rb") as f:
    f.seek(0x68)
    e = f.read(200)
    
    # Let's inspect fields of entry 0
    # 0x00: uint32
    # 0x04: uint16 magic (0xdada)
    # 0x06: uint16 hw_code
    # 0x08: uint16 hw_sub_code
    # 0x0a: uint16 hw_ver
    # 0x0c: uint32 sw_ver
    # 0x10: uint32 reserved
    # 0x14: uint16 pagesize
    # 0x16: uint16 sec_count
    u32_0, magic, hw_code, sub_code, hw_ver, sw_ver, res, pagesize, sec_count = struct.unpack("<IHhhhhIIHH", e[:24])
    print(f"magic: {hex(magic)}, hw_code: {hex(hw_code)}, sub_code: {hex(sub_code)}, hw_ver: {hex(hw_ver)}, sec_count: {sec_count}")
    
    # Sections start at offset 24
    # Each section: uint32 offset, uint32 length, uint32 load_addr, uint32 sig_len, uint32 sig_offset?
    # Let's see: 0x80 in file was offset 24 in entry (0x68 + 24 = 0x80)
    # At 0x80: 6c 37 00 00 (offset=0x376c), c8 9f 08 00 (len=0x89fc8), 00 00 00 01 (load_addr?), c8 9e 08 00, 00 01 00 00 ...
    sec_data = e[24:]
    for s in range(sec_count):
        s_chunk = sec_data[s*20 : (s+1)*20]
        s_off, s_len, s_addr, s_siglen, s_attr = struct.unpack("<IIIII", s_chunk)
        print(f"  Sec {s}: file_offset=0x{s_off:08x}, length=0x{s_len:08x} ({s_len} bytes), addr=0x{s_addr:08x}, siglen=0x{s_siglen:08x}, attr=0x{s_attr:08x}")
