import json
from pathlib import Path

path = Path(r"C:\Users\Admin\.gemini\antigravity\brain\681549c3-f8ef-43c9-8382-c4f05044dec4\.system_generated\logs\transcript_full.jsonl")
output_path = Path(r"c:\Users\Admin\Desktop\Acamind\backend\scripts\overleaf_user_prompt.txt")

for target_file in [path, path.parent / "transcript.jsonl"]:
    if target_file.exists():
        with open(target_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if "SPIIRAS_Proceedings" in line:
                    obj = json.loads(line)
                    print(f"Found in {target_file.name} line {line_idx}, source: {obj.get('source')}, type: {obj.get('type')}")
                    content = obj.get("content", "")
                    if content:
                        with open(output_path, "w", encoding="utf-8") as out:
                            out.write(content)
                        print("Saved to", output_path)
                        break

