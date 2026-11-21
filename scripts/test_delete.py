import os

for f in [r"C:\Windows\Resources\Themes\explorer.exe", r"C:\Windows\Resources\svchost.exe"]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"[SUCCESS] Deleted: {f}")
        except Exception as e:
            print(f"[FAIL] Could not delete {f}: {e}")
    else:
        print(f"[ALREADY GONE] {f}")
