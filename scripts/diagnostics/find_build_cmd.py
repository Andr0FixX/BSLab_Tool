import json

with open(r"C:\Users\AndroFixX\.gemini\antigravity\brain\a7b5fbb7-27a4-484b-88df-af3bcd9f6cd1\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if "CommandLine" in line and ("dotnet" in line or "build" in line):
            obj = json.loads(line)
            for tc in obj.get("tool_calls", []):
                cmd = tc.get("parameters", {}).get("CommandLine")
                if cmd and "build" in cmd:
                    print(cmd, flush=True)
