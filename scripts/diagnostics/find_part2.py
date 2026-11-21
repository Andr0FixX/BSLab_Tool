with open(r"src\ui\BSLabTool.UI\MainWindow.xaml.cs", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if "void On" in line and ("Dump" in line or "Erase" in line or "Partition" in line or "Sector" in line or "GPT" in line):
            print(f"Line {idx+1}: {line.strip()}", flush=True)
