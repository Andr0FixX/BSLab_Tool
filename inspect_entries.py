import struct

with open("resources/loaders/mtk/MTK_DA_V6.bin", "rb") as f:
    f.seek(0x60)
    count, magic = struct.unpack("<II", f.read(8))
    print(f"Container count={count}, magic={hex(magic)}")
    
    # Let's inspect each entry
    # Let's see how entries are structured
    for i in range(count):
        pos = f.tell()
        data = f.read(200)
        # Find sub code / hw code
        print(f"\n--- Entry {i} at file offset {hex(pos)} ---")
        print("Hex:", data[:64].hex())
