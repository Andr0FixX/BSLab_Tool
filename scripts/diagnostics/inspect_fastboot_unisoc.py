import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

idx_fb = xaml.find('x:Name="ViewFastboot"')
print('--- FASTBOOT & ADB ---')
print(xaml[idx_fb:idx_fb+2500])

idx_uni = xaml.find('x:Name="ViewUnisoc"')
print('--- UNISOC (SPD) ---')
print(xaml[idx_uni:idx_uni+2500])
