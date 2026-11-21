import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

idx_uni = xaml.find('x:Name="PanelUnisocBrom"')
print(xaml[idx_uni+1000:idx_uni+2200])
