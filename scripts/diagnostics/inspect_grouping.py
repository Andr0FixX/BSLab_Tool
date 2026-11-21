import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

idx_fb = xaml.find('x:Name="PanelAdbActions"')
print('--- PanelAdbActions ---')
print(xaml[idx_fb:idx_fb+1000])

idx_uni = xaml.find('x:Name="PanelUnisocBrom"')
print('--- PanelUnisocBrom ---')
print(xaml[idx_uni:idx_uni+1500])
