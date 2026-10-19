# Nhật ký Tái lập Thực nghiệm Toàn diện (Reproducibility Protocol — ACAMIND)

Tài liệu này ghi nhận đầy đủ môi trường phần cứng, phần mềm, cơ sở dữ liệu, hạt giống ngẫu nhiên (random seed), tham số chỉ mục và chuỗi lệnh thực thi tuần tự từ **Giai đoạn 0 đến Giai đoạn 12** để tái lập 100% các kết quả trong thư mục `results/`.

---

## 1. Cấu hình Hệ thống, Phần cứng & Phiên bản Phần mềm

| Thành phần | Thông số Thực tế Đã Xác minh (Truy nguyên: `results/00_recon/env_and_db_meta.json`, `results/01_embedding/stats.json`) |
| :--- | :--- |
| **Hệ điều hành** | Windows 11 (`10.0.26200`, AMD64) |
| **Vi xử lý (CPU)** | AMD Ryzen 5 8645HS w/ Radeon 760M Graphics (6 nhân vật lý / 12 luồng logic) |
| **Bộ nhớ RAM** | 15.31 GB |
| **Tăng tốc GPU** | Không sử dụng CUDA (`torch.cuda.is_available() == False`); toàn bộ embedding và cross-encoder reranking chạy trên CPU |
| **Git Commit Hash** | `f1a06934bc8374a6646bc7dcbe8d23bd328ca129` |
| **Python Runtime** | Python `3.11.9` (`backend/.venv/Scripts/python.exe`) |
| **Cơ sở dữ liệu** | PostgreSQL `16.15` (Docker container `insight-pgvector`, ánh xạ cổng `localhost:5433`, DB `rag_db`) |
| **Vector Extension** | `pgvector 0.8.7` |
| **Thư viện chính** | `torch 2.11.0+cpu`, `sentence-transformers 5.3.0`, `transformers 5.4.0`, `pymupdf 1.28.2`, `scipy 1.17.1`, `numpy 2.4.4`, `google-genai 1.69.0` |
| **Random Seed cố định** | `20261016` (cho mọi phép lấy mẫu, khởi tạo nhiễu PDF, và `B = 10,000` lần lấy mẫu lại Paired Bootstrap) |

---

## 2. Cấu hình Mô hình & Tham số Chỉ mục (Database & Models)

1. **Tập tài liệu (Corpus):**
   - `499` bài báo khoa học định dạng PDF có lớp văn bản số (digital text layer) thuộc tập arXiv trong `backend/data/raw_pdfs_500/` (`12,411` trang, `70,825` micro-chunks) + `1` tài liệu PDF scan thuần ảnh (`scan_2609.00557v1.pdf`, `3` trang, `0` ký tự trích xuất trực tiếp).
   - Tổng số bản ghi trong bảng `chunks` của PostgreSQL: `71,059` chunks (`70,825` chunks thuộc 499 bài arXiv + `234` chunks thuộc 5 tài liệu phụ trợ ngoài tập benchmark).
   - **Độ phủ vector nhúng:** `100.00%` (`70,825 / 70,825` arXiv chunks và `71,059 / 71,059` tổng chunks đều có vector 768 chiều hợp lệ, `0` giá trị `NULL`/`NaN`, chuẩn $L_2 = 1.0000$).
2. **Mô hình Bi-Encoder Embedding:**
   - Tên mô hình: `intfloat/multilingual-e5-base` ($d = 768$, chuẩn hóa $L_2$).
   - Tiền tố bắt buộc: `"passage: "` khi nhúng đoạn văn bản và `"query: "` khi nhúng câu hỏi truy vấn.
3. **Chỉ mục Vector HNSW (`pgvector 0.8.7`):**
   - Cấu hình xây dựng: `USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`.
   - Thời gian xây dựng lại toàn bộ chỉ mục trên 71,059 vectors: `52.21 giây` (dung lượng chỉ mục: `277 MB`).
   - Tham số truy vấn (`hnsw.ef_search`): `100` trong cấu hình chuẩn (`C2`–`C6`), và được khảo sát độ nhạy trên lưới $\{10, 20, 40, 80, 160, 320\}$ so với vét cạn chính xác (`SeqScan`) ở Giai đoạn 11.
4. **Chỉ mục Từ vựng GIN Full-Text Search (BM25-like):**
   - Bảng `chunks`: `CREATE INDEX idx_chunks_content_english_gin ON chunks USING gin (to_tsvector('english', content))` — thời gian xây dựng `10.77 giây`, dung lượng `28 MB`.
   - Bảng `page_texts`: `CREATE INDEX idx_page_texts_tsv_gin ON page_texts USING gin (tsv)` — thời gian xây dựng `3.89 giây`, dung lượng `24 MB`.
5. **Mô hình Cross-Encoder Reranker:**
   - Tên mô hình: `BAAI/bge-reranker-v2-m3` (`max_length = 512`, chạy trên CPU, chuẩn hóa điểm qua hàm sigmoid $\sigma(z) = 1 / (1 + e^{-z})$).
6. **Mô hình Ngôn ngữ Lớn (LLM Generation & Vision OCR):**
   - Tên mô hình: `gemini-2.5-flash-lite` (đọc khóa API từ biến môi trường `GEMINI_API_KEY`, nhiệt độ `temperature = 0.1`, giới hạn ngữ cảnh đầu vào `top_k = 5` chunks).

---

## 3. Khóa Ngưỡng Đóng băng Trước Khi Chạy Tập TEST (`frozen_thresholds.json`)

Mọi ngưỡng quyết định của cổng từ chối CRAG và cơ chế bỏ qua reranker (DCSR) đều được hiệu chỉnh **duy nhất trên tập DEV (`N = 42` câu hỏi: 27 câu có đáp án + 15 câu không có đáp án, hoàn toàn tách biệt tài liệu với tập TEST)** ở Giai đoạn 4 và Giai đoạn 5, sau đó lưu vào:
- `results/04_gate/frozen_thresholds.json` (và bản sao tại `results/frozen_thresholds.json`)
- **Mã băm SHA-256 đã khóa trước Giai đoạn 6:**
  `26d10139dd018675dff2aa15516ccbd92afeaf6f503431ae97854d8b324d8f51`

---

## 4. Trình tự Lệnh Thực thi Từng Giai đoạn (Stages 0 → 12)

Đảm bảo container PostgreSQL đang chạy tại cổng `5433` và biến môi trường `GEMINI_API_KEY` đã được thiết lập trong `.env`:

```powershell
# Kiểm tra trạng thái container PostgreSQL 16.15 + pgvector 0.8.7
docker ps --filter "name=insight-pgvector"

# Giai đoạn 1: Kiểm tra độ phủ 100% embedding (70,825 chunks) & đo thời gian xây dựng HNSW / GIN index
.\backend\.venv\Scripts\python.exe results/01_embedding/run_stage1_verify_and_index.py

# Giai đoạn 2: Xây dựng tập DEV tách biệt (42 câu) & kiểm tra rò rỉ dữ liệu so với TEST (50 câu)
.\backend\.venv\Scripts\python.exe results/02_split/build_dev_split.py

# Giai đoạn 3: Đo vi mô độ trễ Cross-Encoder CPU, độ trễ từng thành phần, vector chuỗi rỗng & phân phối Conf
.\backend\.venv\Scripts\python.exe results/03_micro_measurements/run_stage3_all.py

# Giai đoạn 4: Hiệu chỉnh cổng từ chối CRAG (S1..S4) trên tập DEV (N=42) & xuất ROC/PR curves
.\backend\.venv\Scripts\python.exe results/04_gate/run_stage4_gate_calibration.py

# Giai đoạn 5: Hiệu chỉnh ngưỡng DCSR trên tập DEV (N=27) & khóa file frozen_thresholds.json kèm SHA-256
.\backend\.venv\Scripts\python.exe results/05_dcsr/run_stage5_dcsr_calibration.py

# Giai đoạn 6: Đánh giá truy hồi (C1..C6) trên tập TEST (50 câu gốc + 10 câu Hard Unanswerable) với ngưỡng đóng băng
.\backend\.venv\Scripts\python.exe results/06_retrieval/run_stage6_retrieval_eval.py

# Giai đoạn 7: Đánh giá sinh câu trả lời End-to-End (BM25, Naive_Dense, ACAMIND) trên toàn bộ 50 câu hỏi TEST
.\backend\.venv\Scripts\python.exe results/07_generation/run_stage7_generation.py

# Giai đoạn 8: Xuất bảng chấm mù (150 dòng) cho 2 người chấm độc lập & script tính Cohen's kappa / Krippendorff's alpha
.\backend\.venv\Scripts\python.exe results/08_annotation/prepare_blind_eval.py

# Giai đoạn 9: Thực nghiệm cắt bỏ Scan Circuit Breaker (G0..G4) trên 300 PDF (1,200 trang, V0..V5) & Gemini Vision OCR
.\backend\.venv\Scripts\python.exe results/09_scan_breaker/run_stage9_scan_breaker.py

# Giai đoạn 10: Thực nghiệm cắt bỏ Cross-Article Synthesis (15 câu) & Dual-Memory L1/L2 (20 câu)
.\backend\.venv\Scripts\python.exe results/10_synthesis/run_stage10_synthesis_ablation.py

# Giai đoạn 11: Kiểm định thống kê bắt cặp (Wilcoxon, Paired Bootstrap B=10,000, Holm-Bonferroni, Fisher Exact) & HNSW ef_search
.\backend\.venv\Scripts\python.exe results/11_stats/run_stage11_stats.py

# Giai đoạn 12: Tổng hợp toàn bộ Bảng (CSV + Markdown) và Hình vẽ độ phân giải cao (PNG + PDF) cho bài báo
.\backend\.venv\Scripts\python.exe results/12_paper_tables/run_stage12_build_all.py
```

---

## 5. Quy trình Chạy Tiếp Sau Khi Người Chấm Hoàn thành Chấm Thủ Công (Stage 8 & Stage 10)

1. **Sau khi 2 người chấm điền xong file `results/08_annotation/blind_sheet.xlsx`** (hoặc `blind_eval_sheet.xlsx`):
   ```powershell
   .\backend\.venv\Scripts\python.exe results/08_annotation/compute_human_agreement.py
   ```
   Script sẽ tự động giải mã bằng `blind_key_DO_NOT_OPEN.json`, tính **Cohen's $\kappa$** và **Krippendorff's $\alpha$**, và cập nhật `results/08_annotation/human_eval_summary.json`.
2. **Sau khi người chấm điền xong 4 cột chấm điểm từng ô trong `results/10_synthesis/synthesis_matrix_cells_for_human_eval.xlsx`:**
   Chạy lại `run_stage12_build_all.py` để cập nhật cột Human Evaluation vào Bảng 4 và Bảng 6.
