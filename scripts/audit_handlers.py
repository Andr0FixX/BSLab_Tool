import re

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml', 'r', encoding='utf-8') as f:
    xaml = f.read()

with open(r'C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    cs = f.read()

# Find all Button Click handlers
clicks = re.findall(r'Click="([^"]+)"', xaml)
print(f"Total Buttons with Click handlers in XAML: {len(clicks)}")
unique_clicks = sorted(list(set(clicks)))
print(f"Unique Click handlers: {len(unique_clicks)}")

# For each handler, find its implementation in cs
simulated = []
has_hardware = []
other = []

for c in unique_clicks:
    idx = cs.find(f" {c}(")
    if idx == -1:
        idx = cs.find(f" {c} (")
    if idx == -1:
        print(f"NOT FOUND: {c}")
        continue
    
    # Grab 2500 chars after method declaration
    chunk = cs[idx:idx+3500]
    
    # Check what calls exist
    hw_keywords = ['ExecuteCliAsync', 'SendSerialAtCommandAsync', 'BSLabBridge', 'Process.Start', 'OpenFileDialog', 'SaveFileDialog', 'Clipboard', 'GetActiveDevice', 'Close()', 'WindowState']
    has_hw = any(k in chunk for k in hw_keywords)
    
    if 'Task.Delay' in chunk and not any(k in chunk for k in ['ExecuteCliAsync', 'SendSerialAtCommandAsync', 'BSLabBridge']):
        simulated.append(c)
    elif has_hw:
        has_hardware.append(c)
    else:
        other.append(c)

print("\n=== DEFINITELY SIMULATED HANDLERS ===")
for s in sorted(simulated):
    print(f"  [SIMULATED] {s}")

print(f"\nTotal Simulated: {len(simulated)}")
print(f"Total Has Hardware: {len(has_hardware)}")
print(f"Total Other: {len(other)}")

print("\n=== OTHER HANDLERS (Needs Inspection) ===")
for o in sorted(other):
    print(f"  [OTHER] {o}")
