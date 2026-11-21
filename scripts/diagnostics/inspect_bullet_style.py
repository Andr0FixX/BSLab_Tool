import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

idx = xaml.find('x:Key="CyberBulletButton"')
idx2 = xaml.find('</Style>', idx)
print(xaml[idx:idx2+8])
