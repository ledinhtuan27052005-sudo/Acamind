### Bảng Mới 1 (Giai đoạn 4 & 6): Hiệu chỉnh Cổng Từ chối CRAG trên Tập DEV (N=42) và Đánh giá Đóng băng trên Tập TEST (N=45 In-Scope + 5 OOD + 10 Hard Unanswerable)

| Gate Signal | Frozen Threshold (Calibrated on DEV N=42) | DEV AUROC (95% CI) & AUPRC | DEV TPR (Ans Pass) / TNR (Unans Refused) | TEST In-Scope Pass Rate (N=45) | TEST False Refusal Rate (N=45) | TEST OOD True Refusal (N=5) | TEST Hard Unseen In-Domain Refusal (N=10) | TEST Combined True Refusal (N=15) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Original Eq. 8 (Conf_RRF < 0.35) | tau_min = 0.35 (Unreachable: min Conf >= 0.4932) | N/A at tau=0.35 (0/42 refused) | 100.0% / 0.0% | 45/45 (100.0%) | 0.0% | 0/5 (0.0%) | 0/10 (0.0%) | 0/15 (0.0%) |
| S0: Recalibrated Conf_Eq8 (Tuned on DEV) | 0.810568 | 0.9691 [0.911111, 1.0] | AUPRC=0.9861 | 96.3% / 93.3% | 33/45 (73.3%) | 26.7% | 5/5 (100.0%) | 9/10 (90.0%) | 14/15 (93.3%) |
| S1: Top-1 Dense Cosine (Pre-Rerank) | 0.853701 | 1.0000 [1.0, 1.0] | AUPRC=1.0000 | 100.0% / 100.0% | 35/45 (77.8%) | 22.2% | 5/5 (100.0%) | 10/10 (100.0%) | 15/15 (100.0%) |
| S2: Top-1 Cross-Encoder Reranker Score (Primary Gate) | 0.535542 | 0.9383 [0.817284, 1.0] | AUPRC=0.9337 | 96.3% / 93.3% | 45/45 (100.0%) | 0.0% | 5/5 (100.0%) | 10/10 (100.0%) | 15/15 (100.0%) |
| S3: Query-Chunk Lexical Overlap (Fast Pre-Rerank Gate) | 0.283019 | 0.8975 [0.77037, 0.98642] | AUPRC=0.9303 | 96.3% / 73.3% | 45/45 (100.0%) | 0.0% | 5/5 (100.0%) | 8/10 (80.0%) | 13/15 (86.7%) |
| S4_pre: Logistic Regression (S1 + S3, LOOCV) | 0.617348 | 0.9951 [0.977778, 1.0] | AUPRC=0.9973 | 100.0% / 93.3% | 41/45 (91.1%) | 8.9% | 5/5 (100.0%) | 10/10 (100.0%) | 15/15 (100.0%) |
| S4_full: Logistic Regression (S1 + S2 + S3, LOOCV) | 0.568666 | 0.9852 [0.940741, 1.0] | AUPRC=0.9911 | 100.0% / 93.3% | 44/45 (97.8%) | 2.2% | 5/5 (100.0%) | 10/10 (100.0%) | 15/15 (100.0%) |

> **Ghi chú:** Ngưỡng được khóa trong frozen_thresholds.json (SHA-256: 26d10139dd018675dff2aa15516ccbd92afeaf6f503431ae97854d8b324d8f51) trước khi chạy trên tập TEST.
