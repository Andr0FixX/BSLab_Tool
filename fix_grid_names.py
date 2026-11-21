xaml_path = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all <Grid x:Name="RootLayoutGrid"> back to <Grid>
content = content.replace('<Grid x:Name="RootLayoutGrid">', '<Grid>')

# Now replace only the one right after </Window.Resources>
target = '</Window.Resources>\n\n    <Grid>'
replacement = '</Window.Resources>\n\n    <Grid x:Name="RootLayoutGrid">'

if target in content:
    content = content.replace(target, replacement, 1)
    print("Successfully set unique RootLayoutGrid!")
else:
    # Try with \r\n
    target_rn = '</Window.Resources>\r\n\r\n    <Grid>'
    replacement_rn = '</Window.Resources>\r\n\r\n    <Grid x:Name="RootLayoutGrid">'
    if target_rn in content:
        content = content.replace(target_rn, replacement_rn, 1)
        print("Successfully set unique RootLayoutGrid with CRLF!")
    else:
        print("Target not found, searching index of </Window.Resources>")
        idx = content.find('</Window.Resources>')
        if idx != -1:
            grid_idx = content.find('<Grid>', idx)
            if grid_idx != -1:
                content = content[:grid_idx] + '<Grid x:Name="RootLayoutGrid">' + content[grid_idx+6:]
                print("Successfully replaced by index!")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(content)

count = content.count('x:Name="RootLayoutGrid"')
print(f"Final count of RootLayoutGrid: {count}")
