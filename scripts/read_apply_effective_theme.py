import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    cs = f.read()

pos1 = cs.find('private void ApplyEffectiveTheme')
pos2 = cs.find('private void UpdateThemeSelectorUi')
print(cs[pos1:pos2])
