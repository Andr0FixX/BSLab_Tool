import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

pos1 = xaml.find('x:Name="ViewSettings"')
pos2 = xaml.find('<!-- ROW 3: BOTTOM STATUS BAR', pos1)
settings_xml = xaml[pos1:pos2]

for m in re.finditer(r'<TextBlock\s+Text="([^"]+)"\s+FontSize="9.5"[^>]*>', settings_xml):
    print(m.group(1))
