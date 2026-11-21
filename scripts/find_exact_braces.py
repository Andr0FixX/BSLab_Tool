import re

with open('src/ui/BSLabTool.UI/MainWindow.xaml.cs', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's tokenize or parse C# braces properly
# We can use a proper state machine
idx = 0
n = len(content)
line = 1
col = 1

depth = 0
# Stack of (line, col, type)
stack = []

STATE_NORMAL = 0
STATE_LINE_COMMENT = 1
STATE_BLOCK_COMMENT = 2
STATE_STRING = 3
STATE_VERBATIM_STRING = 4
STATE_CHAR = 5

state = STATE_NORMAL
interp_brace_stack = [] # for interpolated strings

i = 0
while i < n:
    c = content[i]
    if c == '\n':
        line += 1
        col = 1
    else:
        col += 1
        
    if state == STATE_LINE_COMMENT:
        if c == '\n':
            state = STATE_NORMAL
        i += 1
        continue
    elif state == STATE_BLOCK_COMMENT:
        if c == '*' and i + 1 < n and content[i+1] == '/':
            state = STATE_NORMAL
            i += 2
            col += 1
            continue
        i += 1
        continue
    elif state == STATE_STRING:
        if c == '\\':
            i += 2
            col += 1
            continue
        if c == '"':
            state = STATE_NORMAL
        i += 1
        continue
    elif state == STATE_VERBATIM_STRING:
        if c == '"':
            if i + 1 < n and content[i+1] == '"':
                i += 2
                col += 1
                continue
            state = STATE_NORMAL
        i += 1
        continue
    elif state == STATE_CHAR:
        if c == '\\':
            i += 2
            col += 1
            continue
        if c == "'":
            state = STATE_NORMAL
        i += 1
        continue
        
    # STATE_NORMAL
    if c == '/' and i + 1 < n:
        if content[i+1] == '/':
            state = STATE_LINE_COMMENT
            i += 2
            col += 1
            continue
        elif content[i+1] == '*':
            state = STATE_BLOCK_COMMENT
            i += 2
            col += 1
            continue
            
    if c == '@' and i + 1 < n and content[i+1] == '"':
        state = STATE_VERBATIM_STRING
        i += 2
        col += 1
        continue
        
    if c == '$':
        # could be $" or $@ " or @$"
        if i + 1 < n and content[i+1] == '"':
            # interpolated string
            # for now, let's look ahead
            pass
        elif i + 2 < n and content[i+1] == '@' and content[i+2] == '"':
            pass
            
    if c == '"':
        state = STATE_STRING
        i += 1
        continue
    if c == "'":
        state = STATE_CHAR
        i += 1
        continue
        
    if c == '{':
        stack.append((line, col))
    elif c == '}':
        if not stack:
            print(f"EXTRA CLOSING BRACE at line {line}:{col}!")
        else:
            opened_line, opened_col = stack.pop()
            if len(stack) == 0:
                print(f"Stack reached 0 at line {line}:{col} (matched opening at {opened_line}:{opened_col})")
            elif len(stack) == 1:
                # Class level or namespace level
                pass
    i += 1

print(f"Remaining unmatched opening braces in stack: {len(stack)}")
for item in stack:
    print(f"  Unmatched opening brace at line {item[0]}:{item[1]}")
