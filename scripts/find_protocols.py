path = r'c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'jasmine_prog' in line or 'PROTOCOLS' in line:
            print(f"Line {i+1}: {line.strip()}")
