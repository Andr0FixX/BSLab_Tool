with open(r"src\ui\BSLabTool.UI\MainWindow.xaml", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if any(k in line for k in ["TxtDiag", "OnDiag", "Write Dual IMEI", "DIAG 900E"]):
            print(f"Line {idx+1}: {line.strip()}", flush=True)
