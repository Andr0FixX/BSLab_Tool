with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'x:Name="View' in line:
            print(f"{i+1}: {line.strip()}")
