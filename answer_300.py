import csv
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Desktop\Acamind")
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import settings
from app.services.llm_client import LLMClient

INPUT = ROOT / "Query and result" / "300_cau_hoi_tam_ly_hoc.csv"
CHECKPOINT = ROOT / "Query and result" / "answer_drafts_checkpoint.json"
rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig", newline="")))
client = LLMClient(settings.GEMINI_API_KEY, settings.GEMINI_BASE_URL, "gemini-3.5-flash-lite", "gemini")
done = json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else {}

system = """Bạn là biên tập viên kiến thức tâm lý học bằng tiếng Việt. Trả lời đúng trọng tâm từng câu hỏi. Câu ngắn: 1-2 câu. Câu dài: 3-5 câu bao quát mọi ý được hỏi. Chẩn đoán phải nói rõ thang sàng lọc không thay thế đánh giá lâm sàng. Điều trị thuốc chỉ mô tả nguyên tắc, không kê đơn cá nhân. Phân biệt rõ lý thuyết lịch sử với bằng chứng thực nghiệm. Không bịa số liệu, tiêu chuẩn hoặc khẳng định chắc chắn khi bằng chứng còn hạn chế. Trả về duy nhất JSON object với key là Question_ID và value là đáp án, không Markdown."""

def parse(raw, batch):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    data = json.loads(raw)
    ids = [r["Question_ID"] for r in batch]
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) and len(data[k].strip()) > 25 for k in ids):
        raise ValueError("invalid answer object")
    return [data[k].strip() for k in ids]

for start in range(0, len(rows), 8):
    batch = rows[start:start+8]
    if all(done.get(r["Question_ID"]) for r in batch):
        continue
    prompt = "Câu hỏi:\n" + "\n".join(f'{r["Question_ID"]}: {r["Câu hỏi"]}' for r in batch)
    for attempt in range(3):
        try:
            raw = client.complete([{"role": "user", "content": prompt}], system=system, max_tokens=3500, temperature=0.1)
            answers = parse(raw, batch)
            break
        except Exception as exc:
            if attempt == 0:
                (ROOT / "Query and result" / "answer_generation_error.txt").write_text(raw if 'raw' in locals() else str(exc), encoding="utf-8")
            if attempt == 2:
                print(f"FAILED {start+1}: {str(exc)[:100]}", flush=True)
                answers = [""] * len(batch)
            else:
                time.sleep(1)
    for r, answer in zip(batch, answers):
        done[r["Question_ID"]] = answer
    CHECKPOINT.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    if (start // 8 + 1) % 2 == 0:
        print(f"completed {min(start+8,len(rows))}/{len(rows)}", flush=True)

print("finished", len(done), flush=True)
