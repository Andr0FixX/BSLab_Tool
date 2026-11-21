with open('src/ui/BSLabTool.UI/MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's trace depth and print every time depth drops to 1
n = len(content)
line = 1
col = 1
stack = []
state = 0
i = 0
while i < n:
    c = content[i]
    if c == '\n':
        line += 1
        col = 1
    else:
        col += 1
        
    if state == 1: # LINE COMMENT
        if c == '\n':
            state = 0
        i += 1
        continue
    elif state == 2: # BLOCK COMMENT
        if c == '*' and i + 1 < n and content[i+1] == '/':
            state = 0
            i += 2
            col += 1
            continue
        i += 1
        continue
    elif state == 3: # STRING
        if c == '\\':
            i += 2
            col += 1
            continue
        if c == '"':
            state = 0
        i += 1
        continue
    elif state == 4: # VERBATIM STRING
        if c == '"':
            if i + 1 < n and content[i+1] == '"':
                i += 2
                col += 1
                continue
            state = 0
        i += 1
        continue
    elif state == 5: # CHAR
        if c == '\\':
            i += 2
            col += 1
            continue
        if c == "'":
            state = 0
        i += 1
        continue

    if c == '/' and i + 1 < n:
        if content[i+1] == '/':
            state = 1
            i += 2
            col += 1
            continue
        elif content[i+1] == '*':
            state = 2
            i += 2
            col += 1
            continue
            
    if c == '@' and i + 1 < n and content[i+1] == '"':
        state = 4
        i += 2
        col += 1
        continue
        
    if c == '"':
        state = 3
        i += 1
        continue
    if c == "'":
        state = 5
        i += 1
        continue
        
    if c == '{':
        stack.append((line, col))
    elif c == '}':
        if stack:
            opened_line, opened_col = stack.pop()
            if len(stack) == 1:
                # We are at depth 1 (inside namespace, outside class or class closed!)
                print(f"Depth became 1 at line {line}:{col} (opened at {opened_line}:{opened_col})")
            elif len(stack) == 0:
                print(f"Depth became 0 at line {line}:{col} (opened at {opened_line}:{opened_col})")
        else:
            print(f"EXTRA CLOSING BRACE at {line}:{col}")
    i += 1
