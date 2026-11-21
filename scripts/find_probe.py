import os

for root, dirs, files in os.walk(r'c:\BSLab_Tool\src\ui\BSLabTool.UI'):
    for f in files:
        if f.endswith('.cs'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                for idx, line in enumerate(fl):
                    if 'PerformQuickHardwareProbe' in line:
                        print(f"{f}:{idx+1}: {line.strip()}")
