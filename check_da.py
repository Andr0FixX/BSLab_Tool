import os, struct

def inspect_file(path):
    print("=== File:", path, "===")
    if not os.path.exists(path):
        print("Not found")
        return
    size = os.path.getsize(path)
    print("Size:", size)
    with open(path, "rb") as f:
        head = f.read(256)
        print("Header (hex):", head[:64].hex())
        print("Header (repr):", repr(head[:64]))
        
        # Check MTK DA container structure
        # Standard DA container has entries at specific offsets
        # Let's search for "MTK_DOWNLOAD_AGENT" or DA sections
        f.seek(0)
        data = f.read(min(size, 1024*1024))
        # Look for magic signatures
        for sig in [b"MTK_DOWNLOAD_AGENT", b"MTK_AllInOne_DA", b"DA_V6", b"\x99\x88\x66\x22"]:
            pos = data.find(sig)
            if pos != -1:
                print(f"Found signature {sig} at {hex(pos)}")

inspect_file("resources/loaders/mtk/MTK_DA_V6.bin")
inspect_file("resources/loaders/mtk/brand_da/OPPO.da")
