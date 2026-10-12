import sys
import json

sys.stdout.reconfigure(encoding="utf-8")
with open("scripts/results_50_scenarios.json", encoding="utf-8") as f:
    data = json.load(f)

for r in data["results"]:
    if not r["passed"]:
        print(f"ID {r['id']} [{r['category']}]: {r['title']}")
        print(f"  Notes: {r['notes']}")
        print(f"  Answer snippet: {r['answer_snippet'][:250]}")
        print()
