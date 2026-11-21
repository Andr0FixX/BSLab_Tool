with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    text = f.read()

opens = text.count('{')
closes = text.count('}')
print(f"Opens: {opens}, Closes: {closes}, Diff: {opens - closes}")

if opens > closes:
    diff = opens - closes
    text = text.rstrip() + ("\n}" * diff) + "\n"
    with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Appended {diff} closing braces.")
