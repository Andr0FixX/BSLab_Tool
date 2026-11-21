import os

f = r"C:\Windows\Resources\Themes\tjcm.cmn"
if os.path.exists(f):
    stat = os.stat(f)
    print(f"Size: {stat.st_size} bytes")
    with open(f, "rb") as fp:
        data = fp.read(256)
        print("First 256 bytes:", data[:64])
        # Check if it has MZ header or ASCII text
        if data.startswith(b"MZ"):
            print("WARNING: This is a Windows PE Executable/DLL renamed to .cmn!")
        else:
            print("Header bytes (hex):", data[:16].hex())
else:
    print("Does not exist")
