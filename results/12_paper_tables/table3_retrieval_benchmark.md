### Bảng 3 (Đã đo lại): Đánh giá Truy hồi Toàn diện và Các Baseline Mạnh (C1–C6) trên Toàn bộ Corpus 70,825 Chunks (N=45 câu hỏi In-Scope)

| Config | System Description | Recall@5 (95% CI) | Recall@10 (95% CI) | MRR@10 (95% CI) | NDCG@10 (95% CI) | Top-1 Doc Hit | Top-1 Page Hit | DCSR Skip Rate (45Q / 50Q) | Cold Latency P50 / Mean (ms) | Warm Latency P50 / Mean (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| C1 | C1: BM25 / GIN FTS Only | 0.5889 [0.4741, 0.7111] | 0.6704 [0.563, 0.7778] | 0.5710 [0.4536, 0.6904] | 0.5269 [0.4303, 0.6246] | 0.4444 | 0.4000 | N/A (No Reranker) | 925.2 / 904.6 | 910.7 / 902.5 |
| C2 | C2: Naive Dense (HNSW ef=100) | 0.6481 [0.5333, 0.763] | 0.6926 [0.5815, 0.8] | 0.7867 [0.6664, 0.8938] | 0.6826 [0.5692, 0.7872] | 0.7556 | 0.5111 | N/A (No Reranker) | 127.0 / 299.8 | 89.3 / 89.0 |
| C3 | C3: Hybrid RRF (k=60, No Rerank) | 0.9704 [0.9407, 0.9926] | 1.0000 [1.0, 1.0] | 0.9574 [0.9037, 1.0] | 0.9666 [0.9322, 0.9939] | 0.9333 | 0.9111 | N/A (No Reranker) | 986.8 / 1113.9 | 967.8 / 957.2 |
| C4 | C4: Hybrid RRF + Reranker (Full K=16) | 1.0000 [1.0, 1.0] | 1.0000 [1.0, 1.0] | 1.0000 [1.0, 1.0] | 1.0000 [1.0, 1.0] | 1.0000 | 0.8444 | 0.0% / 0.0% (Always Rerank) | 20801.4 / 21297.4 | 967.8 / 957.3 |
| C5 | C5: Hybrid RRF + DCSR (Frozen) | 0.9852 [0.963, 1.0] | 1.0000 [1.0, 1.0] | 0.9833 [0.95, 1.0] | 0.9828 [0.956, 1.0] | 0.9778 | 0.8667 | 31.1% (14/45) / 28.0% (14/50) | 19967.9 / 15581.8 | 967.8 / 957.3 |
| C6 | C6: Full ACAMIND (RRF + Frozen Gate + DCSR) | 0.9852 [0.963, 1.0] | 1.0000 [1.0, 1.0] | 0.9833 [0.95, 1.0] | 0.9828 [0.956, 1.0] | 0.9778 | 0.8667 | 31.1% (14/45) / 28.0% (14/50) | 19967.9 / 15581.8 | 967.8 / 957.3 |

> **Ghi chú:** Mọi hệ thống truy vấn trên toàn bộ 70,825 chunks (không dùng bộ lọc gian lận document_id). Cold Latency xóa toàn bộ bộ nhớ đệm (_query_embed_cache, _rerank_cache) trước mỗi truy vấn; Warm Latency đo khi bộ nhớ đệm đã nóng.
