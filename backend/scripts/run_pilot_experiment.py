"""Run a transparent, quota-conscious pilot RAG experiment against local Acamind.

This sends retrieved context from the selected local documents to the configured
Gemini service through the normal /evaluate/run endpoint. It records every
success and failure in JSON, so failures cannot be silently excluded.
"""

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "pilot_experiment_results"
API_URL = "http://127.0.0.1:8000/api/v1/evaluate/run"
INTERVAL_SECONDS = 10  # 6 evaluation calls/minute; conservative for Gemini quota.

CASES = [
    ("P01", "bf8bdb5e-1f00-47b9-bad3-1cce0c11732f", "Theo tài liệu, những yếu tố nào ảnh hưởng đến hứng thú học tập môn Tâm lý học đại cương của sinh viên?"),
    ("P02", "9ac376e0-c3a7-4181-91be-63618d144be1", "Theo nghiên cứu, nhu cầu tâm lý cơ bản, động lực học tập và trì hoãn học tập có mối liên hệ như thế nào?"),
    ("P03", "4bf3ba8d-20b1-4355-b958-ff8ba73bd503", "Tài liệu nêu những nhu cầu tư vấn tâm lý học đường nào của học sinh THPT?"),
    ("P04", "4852c4eb-81a7-460f-af7e-e7772a58d04f", "Mục tiêu và đóng góp chính của hướng dẫn về linear mixed-effects models là gì?"),
    ("P05", "fb28026c-84c7-4ee6-8548-8d13c0d9672b", "Theo tài liệu, biến độc lập và biến trung gian có vai trò gì trong thí nghiệm tâm lý xã hội?"),
    ("P06", "97110b8c-f3f9-413c-acda-56a286dfe36c", "Theo Orne, giả thuyết của nhà thí nghiệm có thể ảnh hưởng đến người tham gia như thế nào?"),
    ("P07", "ebda0a7b-c075-45f2-9141-31264cb3a626", "Tài liệu về social psychology experimental tập trung vào những vấn đề hoặc phương pháp nào?"),
    ("P08", "bcb74110-2a74-4228-afb3-68828092b3cb", "Các yếu tố nào liên quan đến việc làm của sinh viên chuyên ngành tâm lý học tham vấn được đề cập trong tài liệu?"),
    ("P09", "e17498d5-b10f-40aa-b8ae-adda98085b8e", "Tài liệu tâm lý học giáo dục trung học cơ sở đề cập những nội dung hoặc đối tượng giáo dục nào?"),
    ("P10", "537b9a4e-e3d4-4fa6-912a-a79ebb7f8124", "Hãy nêu mục tiêu nghiên cứu hoặc kết quả chính được trình bày trong tài liệu này."),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = []
    for index, (case_id, document_id, question) in enumerate(CASES, 1):
        started_at = datetime.now(timezone.utc).isoformat()
        timer = time.perf_counter()
        row = {"case_id": case_id, "document_id": document_id, "question": question, "started_at_utc": started_at}
        try:
            response = requests.post(API_URL, json={"question": question, "document_ids": [document_id]}, timeout=120)
            row["http_status"] = response.status_code
            response.raise_for_status()
            payload = response.json()
            row.update({
                "outcome": "success",
                "answer": payload.get("answer", ""),
                "sources": payload.get("sources", []),
                "faithfulness": payload.get("faithfulness"),
                "answer_relevancy": payload.get("answer_relevancy"),
                "context_quality": payload.get("context_quality"),
                "feedback": payload.get("feedback", ""),
            })
        except Exception as exc:
            row.update({"outcome": "error", "error": str(exc), "answer": "", "sources": []})
        row["latency_seconds"] = round(time.perf_counter() - timer, 3)
        rows.append(row)
        print(f"{case_id}: {row['outcome']} ({row['latency_seconds']:.2f}s)", flush=True)
        if index < len(CASES):
            time.sleep(INTERVAL_SECONDS)

    metric_keys = ("faithfulness", "answer_relevancy", "context_quality")
    successful = [r for r in rows if r["outcome"] == "success"]
    summary = {
        "experiment_type": "pilot: 10 independent document-grounded questions",
        "started_at_utc": rows[0]["started_at_utc"],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "gemini_rate_limit_interval_seconds": INTERVAL_SECONDS,
        "total_cases": len(rows),
        "successful_cases": len(successful),
        "failed_cases": len(rows) - len(successful),
        "mean_latency_seconds": round(statistics.mean([r["latency_seconds"] for r in rows]), 3),
        "metrics": {key: round(statistics.mean([r[key] for r in successful if isinstance(r.get(key), (int, float))]), 3) if any(isinstance(r.get(key), (int, float)) for r in successful) else None for key in metric_keys},
        "limitation": "Pilot evidence only. It does not include baseline/ablation or a held-out benchmark.",
    }
    result = {"summary": summary, "cases": rows}
    output_path = OUT_DIR / f"pilot_experiment_{stamp}.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output_path}", flush=True)


if __name__ == "__main__":
    main()
