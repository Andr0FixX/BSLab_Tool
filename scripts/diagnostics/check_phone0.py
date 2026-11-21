with open(r"C:\BSLab_Tool\scratch\logcat_radio.txt", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "setPowerStateToDesired" in line or ("RADIO_POWER" in line and "[PHONE0]" in line):
            print(f"{i}: {line.strip()}")
