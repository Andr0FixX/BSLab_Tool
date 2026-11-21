import glob

for fpath in glob.glob('src/ui/BSLabTool.UI/*.cs'):
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if 'ExecuteDumpSelectedPartitionsAsync' in line:
                print(f"{fpath}:{idx}: {line.strip()}")
