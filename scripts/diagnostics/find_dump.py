with open(r"src\ui\BSLabTool.UI\MainWindow.xaml.cs", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if "ExecuteDumpSelectedPartitionsAsync" in line:
            print(f"Line {idx+1}: {line.strip()}", flush=True)
