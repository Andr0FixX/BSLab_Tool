import json

with open(r'C:\Users\AndroFixX\.gemini\antigravity\brain\a7b5fbb7-27a4-484b-88df-af3bcd9f6cd1\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            if d.get('step_index') == 14897:
                print("CommandLine:", d['tool_calls'][0]['args']['CommandLine'])
                break
        except:
            pass
