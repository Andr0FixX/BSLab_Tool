with open('src/ui/BSLabTool.UI/MainWindow.xaml.cs', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'ExecuteDumpSelectedPartitionsAsync' in line:
            print(f"{idx}: {line.strip()}")
