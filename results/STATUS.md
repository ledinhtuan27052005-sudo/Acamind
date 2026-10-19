# Trạng thái Tiến độ Thực nghiệm (Experimental Protocol Status — ACAMIND)

**Cập nhật lần cuối:** `2026-10-16T13:48:00+07:00`  
**Trạng thái tổng thể:** **HOÀN TẤT TOÀN BỘ 12 GIAI ĐOẠN THỰC NGHIỆM MÁY TÍNH (STAGES 0 → 12)**

| Giai đoạn | Thư mục Kết quả | Trạng thái | Tệp Đầu ra Chính |
| :--- | :--- | :---: | :--- |
| **Stage 0: Khảo sát & Kiểm toán** | `results/00_recon/` | ✅ Hoàn tất | `recon.md`, `issues.md`, `assumptions.md`, `env_and_db_meta.json` |
| **Stage 1: Embedding 100% & Index** | `results/01_embedding/` | ✅ Hoàn tất | `stats.json`, `index_params.sql` (`70,825/70,825` chunks 100% embedded) |
| **Stage 2: Chia tập DEV / TEST** | `results/02_split/` | ✅ Hoàn tất | `test_50.json` (read-only), `dev_30.json` (42 câu DEV), `overlap_check.json` |
| **Stage 3: Đo Vi mô (Micro-Benchmarks)** | `results/03_micro_measurements/` | ✅ Hoàn tất | `reranker_cpu_latency.csv`, `component_latency_summary.json`, `empty_string_vector_test.json`, `conf_distribution_50.csv` |
| **Stage 4: Hiệu chỉnh Cổng CRAG** | `results/04_gate/` | ✅ Hoàn tất | `dev_gate_scores.csv`, `roc_pr_curves.json`, `frozen_thresholds.json` + `.sha256` |
| **Stage 5: Hiệu chỉnh DCSR** | `results/05_dcsr/` | ✅ Hoàn tất | `grid_search_dev.csv`, `pareto_skip_vs_ndcg.json` |
| **Stage 6: Đánh giá Truy hồi TEST** | `results/06_retrieval/` | ✅ Hoàn tất | `test_raw_retrieval.json`, `per_query_metrics.csv`, `summary_table.csv`, `significance_tests.json` |
| **Stage 7: Đánh giá Sinh End-to-End** | `results/07_generation/` | ✅ Hoàn tất | `raw_outputs/{BM25,Naive_Dense,ACAMIND}/REAL_Q_01..50.json`, `auto_metrics.csv`, `generation_summary.json` |
| **Stage 8: Giao thức Chấm Mù (150 dòng)** | `results/08_annotation/` | ✅ Hoàn tất | `blind_sheet.xlsx`, `blind_key_DO_NOT_OPEN.json`, `compute_human_agreement.py`, `human_eval_summary.json` |
| **Stage 9: Scan Circuit Breaker Ablation** | `results/09_scan_breaker/` | ✅ Hoàn tất | `scan_breaker_ablation.csv`, `hallucination_audit_20q.csv`, `scan_breaker_summary.json` |
| **Stage 10: Cross-Article & L1/L2 Ablation** | `results/10_synthesis/` | ✅ Hoàn tất | `cross_article_ablation_summary.csv`, `synthesis_ablation_summary.json`, `synthesis_matrix_cells_for_human_eval.xlsx` (30 dòng / 120 ô đã chấm) |
| **Stage 11: Kiểm định Thống kê & HNSW** | `results/11_stats/` | ✅ Hoàn tất | `paired_hypothesis_tests_retrieval.csv`, `paired_hypothesis_tests_generation.csv`, `hnsw_ef_search_tradeoff.csv`, `stats_summary.json` |
| **Stage 12: Bảng & Hình Bài báo** | `results/12_paper_tables/` | ✅ Hoàn tất | `table2`..`table6.{csv,md}`, `table_new_*.{csv,md}`, `figures/*.{png,pdf}`, `SUMMARY.md`, `REPRODUCE.md` |
