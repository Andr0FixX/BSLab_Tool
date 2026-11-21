with open(r"src\ui\BSLabTool.UI\MainWindow.xaml.cs", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "OnPartitionDoctor" in line or "OnQcomDumpSelected" in line or "OnQcomEraseSelected" in line:
        print(f"Line {idx+1}: {line.strip()}", flush=True)
