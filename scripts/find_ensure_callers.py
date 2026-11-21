import os

path = r'c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'EnsureValidHardwarePortAsync' in line:
            print(f"Line {i+1}: {line.strip()}")
