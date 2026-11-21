import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

idx = xaml.find('x:Key="CyberBulletButton"')
print('--- CyberBulletButton Style ---')
print(xaml[idx-30:idx+600])

idx_uni = xaml.find('x:Name="PanelUnisocBrom"')
print('--- PanelUnisocBrom Buttons ---')
print(xaml[idx_uni:idx_uni+1500])
