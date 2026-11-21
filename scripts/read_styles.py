import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

for key in ['CyberBulletButton', 'CyberNavTab', 'ActiveNavTab']:
    pos = xaml.find(f'x:Key="{key}"')
    if pos != -1:
        end_pos = xaml.find('</Style>', pos)
        print(f"=== Style: {key} ===")
        print(xaml[pos-20:end_pos+8])
