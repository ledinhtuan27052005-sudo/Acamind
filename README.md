# Acamind: An Intelligent Academic Question Answering System

> **A Specialized Retrieval-Augmented Generation (RAG) Architecture for Academic and Clinical Psychology Literature**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![PostgreSQL pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Neo4j 5](https://img.shields.io/badge/Neo4j-5-008CC1.svg)](https://neo4j.com/)

---

## 🌟 Giới thiệu tổng quan (Overview)

**Acamind** là hệ thống trợ lý học thuật thông minh ứng dụng kiến trúc **Retrieval-Augmented Generation (RAG)** chuyên sâu cho lĩnh vực tâm lý học (song ngữ Anh - Việt). Hệ thống giải quyết triệt để vấn đề ảo giác dữ kiện (factual hallucination) của các mô hình ngôn ngữ lớn (LLMs) thông qua:
1. **Parallel Hybrid Retrieval:** Kết hợp tìm kiếm vector ngữ nghĩa dày đặc (*Dense semantic search* via `multilingual-e5-base` trên chỉ mục đồ thị HNSW) và tìm kiếm từ khóa thưa thớt (*Lexical search* bằng PostgreSQL Full-Text Search, chấm điểm `ts_rank_cd` trên chỉ mục GIN; nhánh dự phòng dùng Okapi BM25 trong bộ nhớ), hợp nhất qua **Reciprocal Rank Fusion (RRF)**.
2. **Dynamic Confident Skip Reranking:** Thuật toán tự động nhận diện độ lệch tin cậy ($\Delta \text{RRF} \ge 2.5$) để bỏ qua mô hình Cross-Encoder đắt đỏ trên các truy vấn rõ ràng, giảm độ trễ rerank từ **467 ms** xuống còn **0.08 ms** (tiết kiệm 86.3% thời gian xử lý).
3. **Multi-Engine Ingestion & Auto-Healing Vision OCR:** Đường ống trích xuất PDF đa công cụ (`pdfplumber` + `PyMuPDF`) tích hợp cơ chế Scan Circuit-Breaker tự động nhận diện trang scan ($<50$ chars/trang) và kích hoạt **Gemini Multimodal Vision OCR** để số hóa hoàn chỉnh tài liệu (bảo toàn cấu trúc 2 cột, bảng biểu số liệu thống kê, và phân cấp đề mục Markdown); đồng thời kích hoạt **Safe Refusal** khi tài liệu hoàn toàn không có dữ liệu thực tế nhằm ngăn chặn 100% rủi ro sinh ảo giác.
4. **Dual-Memory Hierarchy:** Tầng bộ nhớ đệm L1 Compressed Cache (0.12s) kết hợp kho tri thức L2 pgvector/Neo4j.

---

## 📁 Cấu trúc thư mục (Repository Structure)

```text
Acamind/
├── ACAMIND_SPIIRAS_SUBMISSION/     # Bản thảo bài báo khoa học tiếng Anh (LaTeX chuẩn SPIIRAS/IEEE)
│   ├── main.tex                    # Master LaTeX file
│   ├── ref.bib                     # Danh mục tài liệu tham khảo BibTeX
│   └── figures/                    # Toàn bộ biểu đồ khoa học chất lượng cao
├── ACAMIND_VIETNAMESE_SUBMISSION/  # Bản dịch bài báo khoa học tiếng Việt (LaTeX master)
├── ACAMIND_Bai_Bao_Khoa_Hoc_Tieng_Viet.docx # Bản Word hoàn chỉnh bài báo tiếng Việt
├── backend/                        # Backend API (FastAPI, Python)
│   ├── app/
│   │   ├── api/                    # Endpoint routers (chat, upload, auth, doc)
│   │   ├── core/                   # Cấu hình hệ thống, settings
│   │   ├── db/                     # Kết nối PostgreSQL pgvector & Neo4j
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   └── services/               # Ingestion, embedder, retriever, reranker, LLM client
│   ├── scripts/                    # Scripts kiểm chuẩn thực nghiệm & ablation study
│   ├── requirements.txt            # Python dependencies
│   └── main.py                     # Entry point FastAPI server
├── frontend/                       # Giao diện người dùng Web (Next.js 14, React, TailwindCSS)
├── docker/                         # Docker compose & file khởi tạo cơ sở dữ liệu
│   ├── docker-compose.yml          # PostgreSQL pgvector (5433) + Neo4j (7687)
│   └── init_db.sql                 # Script khởi tạo bảng và chỉ mục HNSW/GIN
├── data/                           # Bộ ngữ liệu tài liệu tâm lý học & kết quả thực nghiệm
│   ├── raw_pdfs/                   # Các tài liệu PDF giáo trình tâm lý học
│   ├── ablation_study_results/     # Log kết quả thực nghiệm đo đạc (JSON/CSV)
│   └── pilot_experiment_results/   # Kết quả đánh giá LLM-as-a-judge (RAGAS)
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy sau khi Reset máy (Quick Start)

### 1. Yêu cầu môi trường (Prerequisites)
- **Hệ điều hành:** Windows 10/11, macOS, hoặc Linux
- **Python:** Phiên bản 3.11 hoặc 3.12+
- **Node.js:** Phiên bản 18+ hoặc 20+
- **Docker Desktop:** Để chạy PostgreSQL pgvector và Neo4j

### 2. Khởi chạy Database qua Docker
```bash
cd docker
docker compose up -d
```
*Dịch vụ sẽ mở tại:*
- PostgreSQL pgvector: `localhost:5433` (user: `admin`, pass: `secret`, db: `rag_db`)
- Neo4j: `localhost:7687` / Web UI: `localhost:7474` (user: `neo4j`, pass: `secretpassword`)

### 3. Cài đặt & Khởi chạy Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Kích hoạt venv (Windows PowerShell):
.venv\Scripts\Activate.ps1
# Cài đặt thư viện:
pip install -r requirements.txt

# Tạo file cấu hình môi trường .env (tham khảo .env.example):
cp .env.example .env
# Điền API Key của bạn (Gemini, Claude, hoặc Groq) vào .env

# Chạy server FastAPI:
uvicorn main:app --reload --port 8000
```
API Documentation có sẵn tại: `http://localhost:8000/docs`

### 4. Cài đặt & Khởi chạy Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev -- -p 3001
```
Giao diện ứng dụng truy cập tại: `http://localhost:3001`

---

## 📊 Kết quả Thực nghiệm Khoa học (Empirical Benchmarks)

Hệ thống đã trải qua kiểm chuẩn nghiêm ngặt và đạt các kết quả công bố:
- **Factual Faithfulness (RAGAS / Gemini 3.1 LLM Judge):** `1.00 / 1.00` (Không có ảo giác)
- **Answer Relevancy:** `1.00 / 1.00`
- **Context Quality:** `0.867`
- **Operational Stress Test ($N=1,000$ scenarios):** Pass rate `98.8%` (988/1000)
- **Average System Latency:** `2.395 giây` (và `1.50 giây` cho Safe Refusal)
- **Confident Skip Acceleration:** Giảm 86.3% thời gian rerank (từ 534.5ms xuống 73.5ms).

---

## 📜 Trích dẫn & Bài báo (Citation)

Nếu bạn sử dụng Acamind trong nghiên cứu học thuật, vui lòng trích dẫn:
```bibtex
@article{chi2026acamind,
  author    = {Dinh Thi Hue Chi and Le Dinh Tuan and Nguyen Cong Binh and Nguyen Viet Hung},
  title     = {Acamind: An Intelligent Academic Question Answering System Integrating Retrieval-Augmented Generation and Hybrid Search for the Psychology Domain},
  journal   = {SPIIRAS Proceedings},
  year      = {2026}
}
```

---
*© 2026 Acamind Research Initiative. All rights reserved.*


---

## 🏆 Bộ 9 Kỹ thuật Đột phá Phục vụ Thi Nghiên cứu Khoa học (NCKH Edition)

Toàn bộ tài liệu đặc tả toán học và hướng dẫn kiểm thử từng bước (Step-by-Step) đã được cập nhật đầy đủ tại:
- 📘 **[HUONG_DAN_HE_THONG_VA_KIEM_THU_NCKH.md](./HUONG_DAN_HE_THONG_VA_KIEM_THU_NCKH.md)**: Tài liệu đặc tả chi tiết 14 phân hệ & 8 kịch bản kiểm thử toàn diện phục vụ Hội đồng chấm thi NCKH.
- 📗 **[HƯỚNG_DẪN_STEP_BY_STEP.md](./HƯỚNG_DẪN_STEP_BY_STEP.md)**: Hướng dẫn từng bước & Checklist kiểm tra toàn bộ chức năng (Phần 5 cập nhật 9 kỹ thuật NCKH mới).
- 📙 **[HƯỚNG_DẪN_CHUYÊN_SÂU.md](./HƯỚNG_DẪN_CHUYÊN_SÂU.md)**: Phân tích kiến trúc & công thức toán học chuyên sâu bảo vệ NCKH.

| # | Kỹ thuật Khoa học Mới | Đường dẫn Giao diện | Điểm nhấn Học thuật |
| :-: | :--- | :--- | :--- |
| 1 | **Đối chiếu mệnh đề với đoạn nguồn ứng viên** | `/chat`, `/Literature`, `/RAG` | Điểm tương đồng chỉ dùng tìm đoạn; không chứng nhận entailment hoặc xác suất đúng |
| 2 | **Định lượng Độ Bất định Nhận thức & Entropy Bằng chứng (`Shannon Entropy H(q)`)** | `/chat` | Phân phối xác suất hậu nghiệm $P(c_k \mid q)$, Shannon Entropy (bits), $\mathcal{U}_{\text{epistemic}}$ & Gini-Simpson |
| 3 | **Trạng thái thẩm định liên bài** | `/Literature` | Chưa xác minh CEBM, đồng thuận và mâu thuẫn thì trả trạng thái thiếu bằng chứng, không sinh phần trăm |
| 4 | **Phân tích gộp dữ liệu đã thẩm định** | `/Literature` | Hàm tính DL yêu cầu g, phương sai, nguồn và xác nhận tính tương đương; luồng trích xuất văn bản hiện chưa cấp dữ liệu đã thẩm định |
| 5 | **Trạng thái khoảng trống PICO** | `/Literature` | Không suy ra khoảng trống toàn bộ lĩnh vực từ vài đoạn truy xuất; chưa có kết luận tự động |
| 6 | **Đồ thị Tri thức Thần kinh – Tâm lý 4 Tầng & Cầu nối Giải phẫu Não 3D X-Ray** | `/chat` $\leftrightarrow$ `/3d` | Liên kết Triệu chứng DSM-5/ICD-11 $\leftrightarrow$ 6 Vùng não 3D phát sáng X-Ray $\leftrightarrow$ Cơ chế trị liệu |
| 7 | **Phòng Mô phỏng Bệnh nhân Ảo Lâm sàng & Chấm điểm OSCE (Thang 100)** | `/Health` | 3 Ca bệnh nhân ảo chuẩn hóa, chỉ định `PHQ-9`/`GAD-7`/`BDI-II` & chấm điểm bệnh án Rubric 100đ |
| 8 | **Phòng Thí nghiệm Đối chứng Thuật toán Trực tiếp (`Single-Query A/B/C Ablation`)** | `/RAG` | Đối chiếu độ phủ từ khóa và thời gian truy xuất; các chỉ số độ đúng chưa đo |
| 9 | **Kiểm định thống kê** | `/RAG` | Chưa khả dụng khi thiếu nhãn độc lập và lượt chạy thực đo; đã bỏ số liệu giả lập |
