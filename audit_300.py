import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Desktop\Acamind")
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import settings
from app.services.llm_client import LLMClient

path = ROOT / "Query and result" / "300_cau_tra_loi_tam_ly_hoc_tham_khao.csv"
out = ROOT / "Query and result" / "answer_audit.json"
rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
client = LLMClient(settings.GEMINI_API_KEY, settings.GEMINI_BASE_URL, "gemini-3.5-flash-lite", "gemini")
result = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
system = """Bạn là người phản biện kiến thức tâm lý học và sức khỏe tâm thần. Chỉ báo lỗi thực tế rõ ràng, khuyến nghị lâm sàng có thể gây hại, hoặc thiếu ý chính được hỏi. Đừng bắt lỗi văn phong. Đầu ra duy nhất JSON object, key Question_ID; value là câu trả lời đã sửa đầy đủ. Nếu đáp án đúng và đủ, bỏ qua key đó. Không phỏng đoán tiêu chuẩn hay số liệu; cẩn trọng với chứng cứ yếu."""

for start in range(0, len(rows), 10):
    batch = rows[start:start+10]
    if str(start) in result:
        continue
    prompt = "Rà soát các cặp câu hỏi/đáp án sau:\n" + "\n".join(f'{r["Question_ID"]} HỎI: {r["Câu hỏi"]}\nĐÁP: {r["Cau_tra_loi_tham_khao"]}' for r in batch)
    try:
        raw = client.complete([{"role": "user", "content": prompt}], system=system, max_tokens=3500, temperature=0.1)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        issues = json.loads(raw)
        if not isinstance(issues, dict):
            raise ValueError("expected object")
        result[str(start)] = issues
    except Exception as exc:
        result[str(start)] = {"ERROR": str(exc)[:120]}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if start % 50 == 0:
        print("audited", start+len(batch), flush=True)
print("done", len(result))
