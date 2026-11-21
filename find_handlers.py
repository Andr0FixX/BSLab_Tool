import re

with open('src/ui/BSLabTool.UI/MainWindow.xaml.cs', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'OnDumpSelectedClicked' in line or 'OnEraseSelectedClicked' in line:
            print(f"{idx}: {line.strip()}")
