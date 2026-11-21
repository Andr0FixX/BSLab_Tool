with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'rb') as f:
    data = f.read()

# Append \r\n}\r\n
if not data.endswith(b'\n}\r\n') and not data.endswith(b'\n}\n'):
    data = data.rstrip() + b'\r\n}\r\n'
    with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'wb') as f:
        f.write(data)
    print("Appended closing brace.")
else:
    print("Already ends with closing brace.")
