with open('src/ui/BSLabTool.UI/MainWindow.xaml.cs', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'OnEraseSelectedClicked' in line or 'OnDumpSelectedClicked' in line:
        start = max(0, i - 5)
        end = min(len(lines), i + 45)
        print(f"=== FOUND AT LINE {i+1} ===")
        for j in range(start, end):
            print(f"{j+1}: {lines[j]}", end='')
