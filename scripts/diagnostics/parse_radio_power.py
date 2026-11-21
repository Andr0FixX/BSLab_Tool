with open(r"C:\BSLab_Tool\scratch\logcat_radio.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "handleRadioPowerStateChange" in l or "setRadioPower" in l:
        print(f"--- Line {i} ---")
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(lines[j].strip())
