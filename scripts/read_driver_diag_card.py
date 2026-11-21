import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

pos = xaml.find('WINDOWS SYSTEM &amp; DRIVER DIAGNOSTICS')
if pos == -1:
    pos = xaml.find('WINDOWS SYSTEM & DRIVER DIAGNOSTICS')
print(xaml[pos-100:pos+1200])
