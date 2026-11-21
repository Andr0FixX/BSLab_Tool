import tarfile

try:
    with tarfile.open("resources/loaders/mtk/brand_da/OPPO.da", "r") as t:
        print("TAR members in OPPO.da:")
        for m in t.getmembers():
            print(f"  {m.name} (size: {m.size})")
except Exception as e:
    print("Not a tar file:", e)
