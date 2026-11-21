with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, l in enumerate(lines):
    if '<Grid x:Name="ViewAutoHub"' in l:
        start_idx = i
    if '<Grid x:Name="ViewMtk"' in l:
        end_idx = i
        break

print(f"ViewAutoHub starts at line {start_idx+1}, ends before line {end_idx+1}")
