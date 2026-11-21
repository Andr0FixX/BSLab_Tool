cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    content = f.read().rstrip()

content += "\n}\n"

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Added namespace closing brace.")
