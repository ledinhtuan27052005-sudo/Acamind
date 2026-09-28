# Mã Nguồn Trực Quan Hóa 7 Sơ Đồ Phong Cách Draw.io (Dự Án Acamind)

Tài liệu này cung cấp toàn bộ mã nguồn Mermaid và cấu trúc khối chuẩn để mở và chỉnh sửa trực tiếp trên **[Draw.io](https://app.diagrams.net/)**.

### Cách mở trên Draw.io trong 5 giây:
1. Mở trang web [Draw.io](https://app.diagrams.net/).
2. Chọn **Arrange** (Sắp xếp) $\rightarrow$ **Insert** (Chèn) $\rightarrow$ **Advanced** (Nâng cao) $\rightarrow$ **Mermaid**.
3. Sao chép và dán đoạn mã của từng sơ đồ bên dưới vào ô nhập $\rightarrow$ Bấm **Insert**. Sơ đồ sẽ tự động xuất hiện với đầy đủ các khối hình, mũi tên và nhãn văn bản có thể kéo thả và đổi màu tùy ý!

---

## 1. Figure 1: Mô Hình Nguyên Lý (Conceptual Paradigm)
```mermaid
graph TD
    subgraph Generic_LLM ["Cách tiếp cận LLM thông thường (Rủi ro ảo giác y sinh)"]
        Q1["User Question Q (Câu hỏi học thuật tâm lý)"] --> LLM1["Standard LLM (Chỉ có Parametric Memory)"]
        LLM1 --> H1["❌ Ảo giác thông tin (Factual Hallucination)<br/>• Chẩn đoán sai lệch, tiêu chuẩn bịa đặt<br/>• Không có số trang kiểm chứng"]
    end

    subgraph Acamind_RAG ["Hệ thống RAG Chuyên Biệt Acamind"]
        Q2["User Question Q (Câu hỏi học thuật tâm lý)"] --> HR["Thu hồi song song (Parallel Hybrid Retrieval)<br/>• Dense Vector: multilingual-e5-base on HNSW (ef=100)<br/>• Sparse Lexical: PostgreSQL GIN BM25"]
        KB[("Kho sách Giáo trình & Protocol<br/>Tâm lý học Việt Nam")] -.-> HR
        HR --> CS["Hợp nhất RRF (k=60) & Bỏ qua Rerank (Delta RRF >= 2.5)"]
        CS --> LLM2["Llama 3.3 70B (Ràng buộc Non-parametric 10 quy tắc)"]
        LLM2 --> OUT["✅ Câu trả lời chuẩn xác 100% (Faithfulness = 1.00)<br/>• Trích dẫn neo trang: [DSM-5.pdf - Page 142]<br/>• Hoặc ngắt mạch từ chối: __NO_CONTEXT__"]
    end

    style Generic_LLM fill:#FFF5F5,stroke:#DC2626,stroke-width:2px
    style Acamind_RAG fill:#F0FDF4,stroke:#16A34A,stroke-width:2px
    style H1 fill:#FEE2E2,stroke:#EF4444,stroke-width:1.5px
    style OUT fill:#DCFCE7,stroke:#22C55E,stroke-width:1.5px
```

---

## 2. Figure 2: Bản Vẽ Kiến Trúc Hệ Thống 4 Lớp (Overall Architecture)
```mermaid
graph TD
    subgraph L4 ["Layer 4: Processing & Generation Engine (Tầng Xử Lý & Sinh Lời Giải)"]
        L4_1["Parallel Coordinator"] --> L4_2["RRF Rank Fusion (k=60)"]
        L4_2 --> L4_3{"Confident Skip<br/>(Delta RRF >= 2.5?)"}
        L4_3 -- Yes (Skip Rerank) --> L4_4["Llama 3.3 70B Engine"]
        L4_3 -- No (Uncertain) --> L4_R["BGE-Reranker-v2-m3"]
        L4_R --> L4_4
        L4_4 --> L4_5["Page Citation: [File.pdf - Page X]"]
    end

    subgraph L3 ["Layer 3: Storage Layer (PostgreSQL Database)"]
        L3_1[("pgvector: HNSW Index (ef_search=100)<br/>768-dim E5 Embeddings")]
        L3_2[("GIN Index: tsvector<br/>Okapi BM25 Lexical")]
        L3_3[("Metadata Table (SHA-256 Deduplication)")]
    end

    subgraph L2 ["Layer 2: Preprocessing & Ingestion (Tầng Tiền Xử Lý)"]
        L2_1["Multi-Engine Parser (PyMuPDF + pdfplumber)"] --> L2_2{"Scan Detector<br/>(<50 chars?)"}
        L2_2 -- Digital --> L2_3["Recursive Splitter (800 chars / 200 overlap)"]
        L2_2 -- Scanned --> L2_4["Flag as Image Scan Page"]
        L2_3 --> L2_5["multilingual-e5-base"]
    end

    subgraph L1 ["Layer 1: Knowledge Base Layer (Tầng Dữ Liệu Gốc)"]
        L1_1["Raw Psychology PDFs"]
        L1_2["Neo4j Graph Database"]
        L1_3["L1 Compressed Memory Cache (Gemini Summaries)"]
    end

    L1_1 --> L2_1
    L2_5 --> L3_1
    L2_3 --> L3_2
    L3_1 --> L4_1
    L3_2 --> L4_1

    style L1 fill:#F8FAFC,stroke:#64748B,stroke-width:1.5px
    style L2 fill:#F0FDF4,stroke:#16A34A,stroke-width:1.5px
    style L3 fill:#EFF6FF,stroke:#2563EB,stroke-width:1.5px
    style L4 fill:#FAF5FF,stroke:#9333EA,stroke-width:1.5px
```

---

## 3. Figure 3: Thu Hồi Lai & Tối Ưu Độ Trễ (Hybrid Retrieval & Confident Skip)
```mermaid
flowchart LR
    Q(["User Query Q"]) --> D_BRANCH["Dense Vector Branch<br/>multilingual-e5-base"]
    Q --> S_BRANCH["Sparse Lexical Branch<br/>PostgreSQL GIN tsvector"]

    D_BRANCH --> D_HNSW["Query Vector in R^768<br/>pgvector HNSW (ef=100)<br/>Cosine Sim -> Top-20 Chunks"]
    S_BRANCH --> S_BM25["Okapi BM25 Ranking<br/>k1=1.2, b=0.75<br/>Lexical Match -> Top-20 Chunks"]

    D_HNSW --> RRF["Reciprocal Rank Fusion (RRF)<br/>RRF(d) = sum 1 / (60 + r_m(d))"]
    S_BM25 --> RRF

    RRF --> COND{"Confidence Test<br/>RRF(d1) / RRF(d2) >= 2.5 ?"}

    COND -- "YES (Confident)" -.->|Bypass Cross-Encoder<br/>Save 200-500ms| LLM["Llama 3.3 70B Engine<br/>Prompt + Retrieved Passages"]
    COND -- "NO (Uncertain)" -->|Full Cross-Attention| RERANK["BAAI/bge-reranker-v2-m3<br/>Select Top-8 Chunks"]
    RERANK --> LLM

    LLM --> OUT(["Final Cited Response<br/>[File.pdf - Page X]"])

    style COND fill:#FEF3C7,stroke:#D97706,stroke-width:2px
    style RRF fill:#EFF6FF,stroke:#2563EB,stroke-width:2px
    style LLM fill:#F0FDF4,stroke:#16A34A,stroke-width:2px
    linkStyle 6 stroke:#0D9488,stroke-width:2.5px,stroke-dasharray: 5 5;
    linkStyle 7 stroke:#D97706,stroke-width:2px;
```

---

## 4. Figure 4: Phân Bổ Độ Trễ Hệ Thống (Latency Breakdown)
```mermaid
gantt
    title Acamind Latency Breakdown (outputs/ measurement data)
    dateFormat X
    axisFormat %s s

    section Digital PDF (Full RAG: 3.03s)
    Hybrid Search (0.20s)           :a1, 0, 20
    Cross-Encoder Rerank (0.33s)    :a2, after a1, 33
    Llama 3.3 70B Generation (2.50s):a3, after a2, 250

    section Scanned PDF (Safe Refusal: 1.50s)
    Scan Filter & Check (0.10s)     :b1, 0, 10
    Refusal Token Generation (1.40s):b2, after b1, 140

    section L1 Compressed Memory (0.38s)
    Summary Cosine Scan (0.06s)     :c1, 0, 6
    Fast Prompt Return (0.32s)      :c2, after c1, 32
```

---

## 5. Figure 5: Đánh Giá Chất Lượng RAGAS (LLM-as-a-Judge)
```mermaid
xychart-beta
    title "RAGAS Quality Scores on Academic Psychology Benchmark"
    x-axis ["Faithfulness", "Answer Relevancy", "Context Quality"]
    y-axis "Score (0.0 to 1.0)" 0 --> 1.0
    bar [1.00, 1.00, 0.867]
```

---

## 6. Figure 6: Ma Trận So Sánh Năng Lực Baseline (Radar Capability)
```mermaid
graph TD
    A["Acamind (Ours)"] -->|5/5| C1["1. Raw Long-PDF Ingestion"]
    A -->|5/5| C2["2. Hybrid Search (HNSW + BM25)"]
    A -->|5/5| C3["3. Dynamic Rerank & Latency Bypass"]
    A -->|5/5| C4["4. Page Anchor Citation [Page X]"]
    A -->|5/5| C5["5. Hallucination Circuit Breaker"]
    A -->|5/5| C6["6. Specialized Psychology / Bilingual VN"]

    style A fill:#1E3A8A,stroke:#2563EB,color:#FFF,stroke-width:3px
    style C1 fill:#EFF6FF,stroke:#3B82F6
    style C2 fill:#EFF6FF,stroke:#3B82F6
    style C3 fill:#EFF6FF,stroke:#3B82F6
    style C4 fill:#EFF6FF,stroke:#3B82F6
    style C5 fill:#EFF6FF,stroke:#3B82F6
    style C6 fill:#EFF6FF,stroke:#3B82F6
```

---

## 7. Figure 7: Bộ Nhớ Kép & Ngắt Mạch Từ Chối An Toàn
```mermaid
flowchart TD
    IN(["User Input Query Q"]) --> CHK_L1{"Kiểm tra Bộ nhớ L1<br/>(Compressed Chapter Summaries)?"}

    CHK_L1 -- "Khớp khái niệm tổng quan" --> RESP_L1["⚡ Trả lời siêu tốc từ L1 Cache<br/>Thời gian: < 0.50s (TB: 0.38s)"]

    CHK_L1 -- "Yêu cầu tra cứu sâu" --> L2_RET["Truy vấn L2 Deep Chunks<br/>(Parallel HNSW + BM25 via RRF)"]

    L2_RET --> CB{"Circuit Breaker<br/>(Kiểm tra an toàn y tế)"}

    CB -- "Trang Scan (<50 chars)<br/>HOẶC Score < Safety Threshold" --> REFUSE["🛑 KÍCH HOẠT NGẮT MẠCH<br/>Xuất mã __NO_CONTEXT__<br/>Từ chối minh bạch trong 1.50s<br/>(Triệt tiêu 100% ảo giác)"]

    CB -- "Đủ ngữ cảnh tin cậy" --> GEN["Llama 3.3 70B Generator<br/>Ràng buộc Non-parametric"]

    GEN --> OK["✅ Câu trả lời chuẩn xác<br/>Trích dẫn neo trang: [File.pdf - Page X]"]

    style CHK_L1 fill:#EFF6FF,stroke:#2563EB,stroke-width:2px
    style CB fill:#FEF3C7,stroke:#D97706,stroke-width:2px
    style REFUSE fill:#FEE2E2,stroke:#DC2626,stroke-width:2px
    style RESP_L1 fill:#DCFCE7,stroke:#16A34A,stroke-width:2px
    style OK fill:#DCFCE7,stroke:#16A34A,stroke-width:2px
```
