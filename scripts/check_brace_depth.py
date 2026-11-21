with open('src/ui/BSLabTool.UI/MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
in_str = False
in_char = False
in_block_comment = False

for i, line in enumerate(lines, 1):
    j = 0
    while j < len(line):
        c = line[j]
        if in_block_comment:
            if c == '*' and j + 1 < len(line) and line[j+1] == '/':
                in_block_comment = False
                j += 2
                continue
            j += 1
            continue
        if in_str:
            if c == '\\':
                j += 2
                continue
            if c == '"':
                in_str = False
            j += 1
            continue
        if in_char:
            if c == '\\':
                j += 2
                continue
            if c == "'":
                in_char = False
            j += 1
            continue
        if c == '/' and j + 1 < len(line):
            if line[j+1] == '/':
                break
            if line[j+1] == '*':
                in_block_comment = True
                j += 2
                continue
        if c == '"':
            in_str = True
            j += 1
            continue
        if c == "'":
            in_char = True
            j += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                print(f"Depth reached 0 at line {i}: {line.strip()}")
            elif depth < 0:
                print(f"NEGATIVE depth at line {i}: {line.strip()}")
        j += 1
print(f"Final depth: {depth}")
