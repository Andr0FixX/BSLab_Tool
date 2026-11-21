import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(5580, min(len(lines), 5620)):
    print(f'{i+1}: {lines[i]}', end='')
