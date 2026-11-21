with open(r'c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'LoadAutoHubSamplePartitions' in line:
            print(f'{i}: {line.strip()[:100]}')
