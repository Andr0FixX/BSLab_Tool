with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(379, 915):
    l = lines[i]
    if '<!--' in l or 'x:Name' in l:
        clean = l.strip().encode('ascii', 'replace').decode('ascii')
        print(f"{i+1}: {clean[:100]}")
