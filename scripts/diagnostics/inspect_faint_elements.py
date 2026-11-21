with open(r"src/ui/BSLabTool.UI/MainWindow.xaml", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

def print_section(title, start_pattern, num_lines=50):
    print(f"\n=================== {title} ===================")
    for i, l in enumerate(lines):
        if start_pattern in l:
            for j in range(i, min(len(lines), i + num_lines)):
                print(f"{j+1}: {lines[j].rstrip()}")
            break

print_section("EXTRACTION CONFIGURATION (Backup Tab)", "EXTRACTION CONFIGURATION")
print_section("HARDWARE DUMP PARAMETERS (Backup Tab)", "HARDWARE DUMP PARAMETERS")
print_section("HUAWEI DLOAD (Huawei Tab)", "HUAWEI DLOAD & SD-UPDATE FLASHER")
print_section("SETTINGS ANTI-BRICK (Settings Tab)", "ANTI-BRICK SAFETY GUARD ENGINE")
print_section("SETTINGS WORKSTATION PROFILE", "WORKSTATION PROFILE & LIFETIME LICENSE")
