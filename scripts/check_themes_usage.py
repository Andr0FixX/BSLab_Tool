import re

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

bg_colors = set(re.findall(r'Background="([^"]+)"', xaml))
print("Backgrounds used:", sorted(bg_colors))
dyn_resources = set(re.findall(r'\{DynamicResource\s+([^\}]+)\}', xaml))
print("DynamicResources used:", dyn_resources)
