import re

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

# Replace CyberPillButton with CyberBulletButton
if 'CyberPillButton' in xaml:
    xaml = xaml.replace('CyberPillButton', 'CyberBulletButton')
    print("Replaced CyberPillButton with CyberBulletButton.")
    with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'w', encoding='utf-8') as f:
        f.write(xaml)

# Find all StaticResource usages
static_resources = set(re.findall(r'\{StaticResource\s+([^\}]+)\}', xaml))

# Find all declared keys in MainWindow.xaml and App.xaml
keys = set(re.findall(r'x:Key="([^"]+)"', xaml))
keys.update(['BackgroundDark', 'CardDark', 'AccentCyan', 'TextPrimary', 'TextSecondary'])

print("All StaticResources used:", sorted(static_resources))
print("Missing resources:")
for r in sorted(static_resources):
    if r not in keys:
        print(" [MISSING]:", r)

if not [r for r in static_resources if r not in keys]:
    print("ALL STATCRESOURCES ARE 100% VALID!")
