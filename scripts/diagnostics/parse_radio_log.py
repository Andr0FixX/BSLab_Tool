with open(r"C:\BSLab_Tool\scratch\logcat_radio.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Total lines:", len(lines))
for line in lines:
    l = line.lower()
    if any(k in l for k in ["setradiopower", "radiopower", "get_sim_status", "imei", "card_state", "modem_reset", "crash", "assert", "panic", "error 54"]):
        print(line.strip())
