import os

xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Navigation Button
target_nav = '<Button x:Name="TabBtnSettings" Content="⚙️ SETTINGS"'
backup_nav_btn = '<Button x:Name="TabBtnBackup" Content="🛡️ BACKUP" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>\n                    '

if 'x:Name="TabBtnBackup"' not in content:
    content = content.replace(target_nav, backup_nav_btn + target_nav)
    print("Added TabBtnBackup to Nav Strip.")

# 2. Add ViewBackup Grid
with open(r"C:\BSLab_Tool\src\ui\BSLabTool.UI\ViewBackup_block.xml", "r", encoding="utf-8") as bf:
    view_backup_xml = bf.read()

target_view = '<!-- ================================================================ -->\n            <!-- VIEW 6: ENTERPRISE SETTINGS'
if 'x:Name="ViewBackup"' not in content:
    content = content.replace(target_view, view_backup_xml + "\n\n            " + target_view)
    print("Added ViewBackup Grid to MainWindow.xaml.")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(content)

print("MainWindow.xaml updated successfully.")
