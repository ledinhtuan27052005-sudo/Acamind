### Bảng 6 (Đã đo lại): Nghiên cứu Cắt bỏ Thành phần (Ablation Study) Toàn diện cho Truy hồi, DCSR, Tổng hợp Đa tài liệu và Bộ nhớ Kép L1/L2

| Ablation Family | Configuration Variant | Eval Scope (N) | Primary Quality Metric | Secondary Quality Metric | Latency P50 / Mean (ms) | Key Empirical Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| A. Retrieval & DCSR (Stage 6) | C1: BM25 / GIN FTS Only | N=45 In-Scope | MRR@10 = 0.5710 | NDCG@10 = 0.5269 | R@10 = 0.6704 | Cold: 925.2 / 904.6 | Top-1 Page Hit = 40.0% |
| A. Retrieval & DCSR (Stage 6) | C2: Naive Dense (HNSW ef=100) | N=45 In-Scope | MRR@10 = 0.7867 | NDCG@10 = 0.6826 | R@10 = 0.6926 | Cold: 127.0 / 299.8 | Top-1 Page Hit = 51.1% |
| A. Retrieval & DCSR (Stage 6) | C3: Hybrid RRF (k=60, No Rerank) | N=45 In-Scope | MRR@10 = 0.9574 | NDCG@10 = 0.9666 | R@10 = 1.0000 | Cold: 986.8 / 1113.9 | Top-1 Page Hit = 91.1% |
| A. Retrieval & DCSR (Stage 6) | C4: Hybrid RRF + Reranker (Full K=16) | N=45 In-Scope | MRR@10 = 1.0000 | NDCG@10 = 1.0000 | R@10 = 1.0000 | Cold: 20801.4 / 21297.4 | Top-1 Page Hit = 84.4% |
| A. Retrieval & DCSR (Stage 6) | C5: Hybrid RRF + DCSR (Frozen) | N=45 In-Scope | MRR@10 = 0.9833 | NDCG@10 = 0.9828 | R@10 = 1.0000 | Cold: 19967.9 / 15581.8 | Top-1 Page Hit = 86.7% |
| A. Retrieval & DCSR (Stage 6) | C6: Full ACAMIND (RRF + Frozen Gate + DCSR) | N=45 In-Scope | MRR@10 = 0.9833 | NDCG@10 = 0.9828 | R@10 = 1.0000 | Cold: 19967.9 / 15581.8 | Top-1 Page Hit = 86.7% |
| B. Cross-Article Synthesis (Stage 10) | Full_Synthesis_Decomp_Dedup085 | N=15 Cross-Article | Doc Recall@6 = 1.0000 | Both Papers Hit@6 = 100.0% (15/15) | 570.2 / 663.5 | Dedup removed = 0.00 chunks/query |
| B. Cross-Article Synthesis (Stage 10) | Ablation_i_No_Query_Decomposition | N=15 Cross-Article | Doc Recall@6 = 0.8000 | Both Papers Hit@6 = 60.0% (9/15) | 289.3 / 326.2 | Dedup removed = 0.00 chunks/query |
| B. Cross-Article Synthesis (Stage 10) | Ablation_ii_No_Dedup_tau100 | N=15 Cross-Article | Doc Recall@6 = 1.0000 | Both Papers Hit@6 = 100.0% (15/15) | 438.9 / 479.7 | Dedup removed = 0.00 chunks/query |
| B. Cross-Article Synthesis (Stage 10) | Ablation_ii_Strict_Dedup_tau075 | N=15 Cross-Article | Doc Recall@6 = 1.0000 | Both Papers Hit@6 = 100.0% (15/15) | 442.4 / 492.1 | Dedup removed = 0.00 chunks/query |
| B. Cross-Article Synthesis (Stage 10) | Ablation_ii_Relaxed_Dedup_tau095 | N=15 Cross-Article | Doc Recall@6 = 1.0000 | Both Papers Hit@6 = 100.0% (15/15) | 447.7 / 498.4 | Dedup removed = 0.00 chunks/query |
| B. Cross-Article Synthesis (Stage 10) | Ablation_iii_No_Matrix_Schema | N=15 Cross-Article | Doc Recall@6 = 1.0000 | Both Papers Hit@6 = 100.0% (15/15) | 437.4 / 490.4 | Dedup removed = 0.00 chunks/query |
| C. Dual-Memory L1/L2 (Stage 10) | L1 Fast Memory Only (Eq. 3 Lexical Abstract Match) | N=20 Factual Q&A | Doc Recall@5 = 1.0000 | Corpus Scope = 499 docs | 1.3 / 1.4 | L1 scores 499 doc abstracts in ~3 ms; L2 provides granular page grounding |
| C. Dual-Memory L1/L2 (Stage 10) | L2 Deep Micro-Chunk Only (Hybrid RRF 70,825 chunks) | N=20 Factual Q&A | Doc Recall@5 = 1.0000 | Corpus Scope = 499 docs | 271.9 / 287.4 | L1 scores 499 doc abstracts in ~3 ms; L2 provides granular page grounding |
| C. Dual-Memory L1/L2 (Stage 10) | L1 + L2 Dual-Memory Combined | N=20 Factual Q&A | Doc Recall@5 = 1.0000 | Corpus Scope = 499 docs | 273.2 / 288.8 | L1 scores 499 doc abstracts in ~3 ms; L2 provides granular page grounding |

> **Ghi chú:** Mọi cấu hình được chạy thật trên cùng cơ sở dữ liệu PostgreSQL 70,825 chunks, không dùng hằng số giả lập.
