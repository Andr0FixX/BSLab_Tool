import re

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

keys = re.findall(r'x:Key="([^"]+)"', xaml[:8000])
print('Resource keys in MainWindow.xaml:')
for k in keys:
    print(' -', k)
