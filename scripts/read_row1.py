import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

pos1 = xaml.find('ROW 1:')
pos2 = xaml.find('<!-- VIEW 0:')

print(xaml[pos1:pos2])
