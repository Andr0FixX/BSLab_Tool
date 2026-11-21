import re

cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

# Locate AI Hardware & System Co-Pilot section
marker = "// 🤖 AI HARDWARE & SYSTEM CO-PILOT (AUTONOMOUS TELEMETRY & REPAIR)"
pos = cs.find(marker)
end_marker = "// ===================================================================="
pos2 = cs.find(end_marker, pos + len(marker) + 100)

if pos != -1 and pos2 != -1:
    ai_section = cs[pos:pos2]
    # In ai_section, whenever AppendAutoHubLog is called, also call AppendAiAnalyseLog
    # Let's replace: AppendAutoHubLog(...) with AppendAutoHubLog(...);\n            AppendAiAnalyseLog(...)
    def repl(m):
        call = m.group(0)
        arg = m.group(1)
        return f"AppendAutoHubLog({arg});\n            AppendAiAnalyseLog({arg})"
    
    new_ai_section = re.sub(r'AppendAutoHubLog\((.*?)\)', repl, ai_section)
    cs = cs[:pos] + new_ai_section + cs[pos2:]
    print("Enhanced AI section with dual logging to AppendAiAnalyseLog.")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("Saved MainWindow.xaml.cs.")
