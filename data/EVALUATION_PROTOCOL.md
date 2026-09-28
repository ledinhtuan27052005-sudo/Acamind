# Protocol đánh giá tái lập Acamind

## Phạm vi bằng chứng

- `eval_questions.json` hiện có 10 câu hỏi độc lập, mỗi câu phải có đáp án chuẩn do người đánh giá lập và UUID tài liệu nguồn.
- `backend/scripts/run_operational_test.py --repeat 100` tạo 1.000 lượt chạy. Đây là **kiểm thử độ ổn định vận hành**, không phải 1.000 quan sát QA độc lập.
- File JSONL là evidence gốc: giữ lại câu hỏi, đáp án chuẩn, UUID tài liệu, phản hồi, số trích dẫn, độ trễ, lỗi HTTP và thời điểm chạy.

## Điều kiện trước khi chạy

1. Docker PostgreSQL/Neo4j, backend và Ollama đang hoạt động.
2. `backend/.env` có `GEMINI_API_KEY` hợp lệ; không đưa khóa vào bài báo hoặc kho mã nguồn.
3. Tất cả UUID trong `eval_questions.json` phải trỏ tới tài liệu đã xử lý thành công.
4. Ghi nhận phiên bản commit, model LLM, model embedding, OS, CPU/GPU/RAM và thời điểm chạy.

## Lệnh chạy

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\run_operational_test.py --repeat 100
.\.venv\Scripts\python.exe scripts\evaluation.py
```

Hoặc dùng trực tiếp tập đầu vào 1.000 lượt đã gán nhãn `operational_repeat`:

```powershell
.\.venv\Scripts\python.exe scripts\run_operational_test.py --input ..\data\operational_test_1000_input.json --repeat 1
```

## Báo cáo trong bài báo

- Nêu rõ số câu hỏi độc lập và số lần chạy lặp.
- Báo cáo mean, median, P95 latency; success, error, no-context; tỷ lệ câu trả lời có trích dẫn trang.
- Báo cáo Faithfulness, Answer Relevancy và Context Precision theo LLM-as-a-judge, gồm prompt, judge model và phiên bản.
- So sánh Dense-only, BM25-only, Hybrid RRF và Hybrid RRF + rerank trên **cùng** tập test.
- Với PDF scan, báo cáo true/false refusal; không coi điểm RAGAS bằng 0 là thước đo an toàn.
