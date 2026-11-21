import os

p = r"C:\Windows\Resources"
for root, dirs, files in os.walk(p):
    for f in files:
        full = os.path.join(root, f)
        print(f"{os.path.relpath(full, p):40s} | {os.path.getsize(full):8d} bytes")
