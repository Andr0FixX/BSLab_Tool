import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

pos0 = xaml.find('<!-- ROW 0: CUSTOM TITLE BAR')
if pos0 == -1: pos0 = xaml.find('ROW 0:')
pos1 = xaml.find('<!-- VIEW 0:')

print(xaml[pos0:pos0+2000])
