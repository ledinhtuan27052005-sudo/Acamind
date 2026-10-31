# backend/eval — Thực nghiệm tái lập được cho bài báo

| File | Vai trò |
|---|---|
| `../app/services/ablation_config.py` | Cờ bật/tắt từng thành phần (`AblationFlags`), 7 cấu hình M1–M7, `clear_all_caches()` |
| `run_ablation.py` | Chạy `retrieve()` thật cho mỗi (câu hỏi × cấu hình), xóa cache trước mỗi lượt, xáo thứ tự cấu hình, ghi JSONL (chạy tiếp được) |
| `evaluate.py` | Tính chỉ số + kiểm định (Wilcoxon, McNemar exact, bootstrap CI, Holm) → Excel |
| `metrics.py` | Hit@k, Recall@k, MRR@10, nDCG@10 (nhãn 0/1/2), target coverage (nhãn người), facet coverage |
| `stats.py` | Kiểm định thống kê (scipy), không chặn sàn p-value |
| `migrate_question_columns.py` | Đổi tên cột nhãn tự động → `Auto_*`, thêm cột rà soát thủ công |

## Cấu hình (lũy tiến)

| Cấu hình | Thêm vào so với bậc trước |
|---|---|
| M1_Dense | Chỉ tìm kiếm vector với câu hỏi gốc |
| M2_Hybrid_RRF | + FTS/BM25 và hợp nhất RRF |
| M3_Rerank | + bộ chấm điểm lại |
| M4_Cross_Lingual | + dịch/mở rộng thuật ngữ Việt→Anh |
| M5_SubQuery | + phân rã câu so sánh |
| M6_Facet_Rerank | + chấm lại theo khía cạnh |
| M7_Acamind_Full | + ưu tiên mật độ từ khóa/số liệu, entity gating, đa dạng tài liệu và ngữ cảnh toàn trang (hệ thống KHÔNG chấm độ uy tín nguồn) |

> Bộ chấm điểm lại: trên máy không có GPU, mặc định `RERANK_FAST_CPU_SCORER=1` dùng bộ chấm điểm
> từ vựng heuristic (`scorer_model = lexical_heuristic_cpu` trong kết quả). Muốn dùng cross-encoder
> thật BAAI/bge-reranker-v2-m3 (đã có trong cache HuggingFace), đặt `RERANK_FAST_CPU_SCORER=0`
> trước khi chạy. Ghi rõ lựa chọn này trong bài báo.

## Lệnh

```powershell
# Chạy thử 10 câu
backend\.venv\Scripts\python.exe -X utf8 backend\eval\run_ablation.py --limit 10 --fresh
# Chạy đầy đủ 300 câu (tiếp tục nếu bị gián đoạn)
backend\.venv\Scripts\python.exe -X utf8 backend\eval\run_ablation.py
# Đánh giá bằng nhãn tự động (CHỈ để gỡ lỗi)
backend\.venv\Scripts\python.exe -X utf8 backend\eval\evaluate.py --split Test_Untouched
# Đánh giá bằng nhãn người (dùng cho bài báo)
backend\.venv\Scripts\python.exe -X utf8 backend\eval\evaluate.py --split Test_Untouched --qrels "Query and result\qrels_human.tsv"
# Kiểm thử
backend\.venv\Scripts\python.exe -m unittest tests.test_ablation_flags -v
```

> Nhãn tự động (`Auto_Candidate_Pages`) được sinh bởi chính từ điển + FTS của hệ thống,
> nên có thiên lệch vòng lặp. Chỉ dùng kết quả với `--qrels` (nhãn người) để báo cáo.
