"""Run five guest questions through the live chat endpoint and save full results."""
import json
from pathlib import Path
import re
import sys
import time

import httpx

QUESTIONS = [
    ("short_cbt", "brief", "CBT là gì?"),
    ("short_latency", "brief", "Trong báo cáo thực nghiệm Acamind, độ trễ trung bình được ghi là bao nhiêu?"),
    ("long_comparison", "deep", "Hãy đối chiếu hai tài liệu “IdeaAnchor: Teaching LLMs to Turn Literature into Research Ideas” và “Báo cáo thực nghiệm đối sánh & dữ liệu test hệ thống Acamind”. Với từng tài liệu, trình bày mục tiêu nghiên cứu, phương pháp, dữ liệu hoặc bộ đánh giá, kết quả chính và hạn chế. Sau đó chỉ ra điểm giống và khác trong cách đánh giá chất lượng ý tưởng hoặc câu trả lời. Mỗi nhận định cần có tên tài liệu và trang cụ thể. Nếu một tiêu chí không có bằng chứng trong tài liệu được truy xuất, hãy ghi rõ là chưa tìm thấy và không suy đoán."),
    ("therapy_exposure", "deep", "Theo tài liệu được truy xuất, người lo âu và né tránh khi thuyết trình có thể áp dụng những bước CBT nào để tập đối mặt dần một cách an toàn? Chỉ nêu bước có nguồn và trích dẫn trang."),
    ("therapy_insomnia", "deep", "Theo tài liệu được truy xuất, có giải pháp trị liệu nào cho người mất ngủ liên quan đến căng thẳng? Nêu cách áp dụng, giới hạn bằng chứng và trích dẫn trang; nếu không đủ nguồn, hãy từ chối phần chưa được hỗ trợ."),
]

output = Path(__file__).resolve().parents[1] / "outputs" / "ollama_five_questions_2026-10-24.json"
only_label = sys.argv[1] if len(sys.argv) > 1 else None
results = json.loads(output.read_text(encoding="utf-8")) if only_label and output.exists() else []
for label, mode, question in QUESTIONS:
    if only_label and label != only_label:
        continue
    prefix = ("[He thong: MODE=BRIEF. Hay tra loi trong khoang 2-4 cau, dung trong tam cau hoi va khong mo rong sang chu de khac.] "
              if mode == "brief" else
              "[He thong: MODE=DEEP. Hay tra loi chuyen sau. Voi cau hoi phuc tap, trinh bay co cau truc, trich dan so trang tai lieu va khong them noi dung lap day.] ")
    start = time.perf_counter()
    first_text_ms = None
    try:
        with httpx.Client(timeout=httpx.Timeout(600.0, connect=10.0), trust_env=False) as client:
            with client.stream("POST", "http://127.0.0.1:8000/api/v1/chat",
                               json={"query": prefix + question, "document_ids": [],
                                     "force_web_search": False}) as response:
                status = response.status_code
                no_context = response.headers.get("x-no-context")
                decision = response.headers.get("x-evidence-decision")
                parts = []
                for chunk in response.iter_text():
                    if chunk:
                        if first_text_ms is None:
                            first_text_ms = round((time.perf_counter() - start) * 1000)
                        parts.append(chunk)
                answer = "".join(parts)
        if status != 200:
            outcome = "error"
        elif decision == "partial" and re.search(r"\[[^\]]+\.pdf\s*-\s*(?:Trang|Page)\s*\d+\]", answer):
            outcome = "partial_answer"
        elif (decision == "refuse" or no_context == "true" or
              any(phrase in answer.lower() for phrase in (
                  "chưa cung cấp đủ bằng chứng", "chưa tìm thấy trong các đoạn",
                  "chưa tìm thấy đủ bằng chứng", "no sufficient evidence"))):
            outcome = "refused"
        elif answer.strip():
            outcome = "answered"
        else:
            outcome = "empty"
        result = {"label": label, "mode": mode, "question": question, "status": status,
                  "outcome": outcome, "decision": decision, "no_context": no_context,
                  "first_text_ms": first_text_ms,
                  "total_ms": round((time.perf_counter() - start) * 1000),
                  "citation_count": len(re.findall(r"\[[^\]]+\.pdf\s*-\s*(?:Trang|Page)\s*\d+\]", answer)),
                  "answer": answer}
    except Exception as exc:
        result = {"label": label, "mode": mode, "question": question,
                  "outcome": "error", "error": type(exc).__name__,
                  "total_ms": round((time.perf_counter() - start) * 1000)}
    results = [existing for existing in results if existing["label"] != label]
    results.append(result)
    print(json.dumps({key: value for key, value in result.items() if key != "answer"}, ensure_ascii=True), flush=True)

output.parent.mkdir(exist_ok=True)
results.sort(key=lambda result: next(i for i, item in enumerate(QUESTIONS) if item[0] == result["label"]))
for result in results:
    if result.get("decision") == "partial" and result.get("citation_count", 0) > 0:
        result["outcome"] = "partial_answer"
        continue
    if result["outcome"] == "answered" and any(phrase in result.get("answer", "").lower() for phrase in (
            "chưa tìm thấy trong các đoạn", "chưa tìm thấy đủ bằng chứng")):
        result["outcome"] = "refused"
output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"saved": str(output), "count": len(results)}, ensure_ascii=True), flush=True)
