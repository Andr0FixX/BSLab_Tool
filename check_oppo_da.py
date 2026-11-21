import os, struct

with open("resources/loaders/mtk/brand_da/OPPO.da", "rb") as f:
    data = f.read(1024)
    # Check if there are filenames or sections
    print("OPPO.da first 256 bytes:")
    print(data[:128])
    # Search for MTK / DA strings or magic
    f.seek(0)
    full = f.read()
    for sig in [b"MTK_DOWNLOAD_AGENT", b"\x99\x88\x66\x22", b"\x7fELF", b"MMM"]:
        p = full.find(sig)
        if p != -1:
            print(f"OPPO.da has {sig} at {hex(p)}")
