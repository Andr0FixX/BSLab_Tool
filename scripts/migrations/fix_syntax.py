cs_path = r'src/ui/BSLabTool.UI/MainWindow.xaml.cs'
with open(cs_path, 'r', encoding='utf-8') as f:
    cs = f.read()

bad = '''            AppendAutoHubLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");

            AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title    PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);
        } formulated. Awaiting technician authorization.");

        }'''

good = '''            AppendAutoHubLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");
            AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");
            PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);
        }'''

if bad in cs:
    cs = cs.replace(bad, good, 1)
    with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(cs)
    print("[+] Fixed successfully!")
else:
    print("[!] Bad block not matched, let's inspect...")
