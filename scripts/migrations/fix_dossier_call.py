cs_path = r'src/ui/BSLabTool.UI/MainWindow.xaml.cs'
with open(cs_path, 'r', encoding='utf-8') as f:
    cs = f.read()

target = 'AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");\n        }'
replacement = 'AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");\n            PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);\n        }'

if target in cs:
    cs = cs.replace(target, replacement, 1)
    with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(cs)
    print("[+] Successfully inserted PrintProfessionalKnowledgeDossier into OnAiAskAndPlanClicked.")
else:
    print("[!] target not found, searching...")
    idx = cs.find('AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title} formulated')
    if idx != -1:
        print("Found at", idx)
        snippet = cs[idx:idx+200]
        print("Snippet:", repr(snippet))
        # let's replace after snippet
        end_brace = cs.find('}', idx)
        cs = cs[:end_brace] + '    PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);\n        ' + cs[end_brace:]
        with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(cs)
        print("[+] Replaced via index!")
