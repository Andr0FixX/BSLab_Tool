import os

path = r'c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'MTK_DA_' in line or 'INFINIX_TECNO.da' in line:
            print(f"Line {i+1}: {line.strip()}")
