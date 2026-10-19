# Quy tắc Tiền đăng ký Chọn Ngưỡng Cổng Từ chối CRAG (`results/04_gate/rule.md`)

## 1. Quy tắc chọn ngưỡng trên Tập DEV (Đặt trước khi xem kết quả TEST)
- **Mục tiêu:** Phân biệt truy vấn có thể trả lời từ kho tri thức (`y = 1`, $N_{\text{DEV, pos}} = 27$) với truy vấn không thể trả lời / ngoài miền / tiền đề sai (`y = 0`, $N_{\text{DEV, neg}} = 15$, gồm 3 câu OOD + 12 câu Hard In-Domain Unanswerable).
- **Hàm quyết định cổng tuyệt đối:**
  - Cổng đơn biến: Từ chối (`Refuse`) nếu tín hiệu $S(q) < \tau^*$.
  - Cổng kết hợp `OR` (`cos_top1_dense < tau_cos OR rerank_score_top1 < tau_rr`) hoặc 2 tầng (`S3_lexical_overlap < tau_lex OR S2_rerank_top1 < tau_rr`).
- **Tiêu chí chọn ngưỡng $\tau^*$ trên DEV:**
  1. Ưu tiên các điểm cắt giữ tỷ lệ từ chối nhầm câu hợp lệ trên DEV $\text{FPR}_{\text{valid}} = 1 - \text{TPR} \le 5\%$ (tối đa $1/27 = 3.7\%$ câu hợp lệ bị từ chối nhầm).
  2. Trong vùng $\text{FPR}_{\text{valid}} \le 5\%$, cực đại hóa chỉ số Youden $J(\tau) = \text{TPR}(\tau) + \text{TNR}(\tau) - 1$.
  3. Giải thích lựa chọn `S2_rerank_top1` làm cổng chính: Mặc dù `S1_cos_top1` đạt `AUROC = 1.0` trên tập DEV thuần tiếng Anh ($\tau^* = 0.853701$), điểm cosine của bi-encoder đơn ngữ bị dịch chuyển phân bố khi câu hỏi đặt bằng tiếng Việt đối chiếu với tài liệu tiếng Anh. Ngược lại, cross-encoder đa ngữ `BAAI/bge-reranker-v2-m3` (`S2_rerank_top1`, $\tau^* = 0.535542$, `AUROC = 0.9383`, `TPR = 96.3%`, `TNR = 93.3%`, $F_{1,\text{ref}} = 0.9333$) bất biến qua ngôn ngữ truy vấn.

## 2. Kết quả áp dụng quy tắc trên Tập DEV (42 queries)
| Tín hiệu cổng | AUROC (DEV) | AUPRC (DEV) | Ngưỡng đóng băng $\tau^*$ | TPR (Valid Pass) | FPR Valid (False Refusal) | TNR (True Refusal) | $F_{1,\text{ref}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline Eq. 8 ($\text{Conf}_{\text{RRF}} \ge 0.35$)** | 0.5000 | 0.6429 | `0.350000` | 100.0% (27/27) | 0.0% (0/27) | **0.0% (0/15)** | 0.0000 |
| **`S1`: Top-1 Dense Cosine** | 1.0000 | 1.0000 | `0.853701` | 100.0% (27/27) | 0.0% (0/27) | 100.0% (15/15) | 1.0000 |
| **`S2`: Top-1 Reranker Score (Primary)** | **0.9383** | **0.9337** | **`0.535542`** | **96.30% (26/27)** | **3.70% (1/27)** | **93.33% (14/15)** | **0.9333** |
| **`S3`: Lexical Overlap (Fast Pre-Gate)** | 0.8975 | 0.9303 | `0.283019` | 96.30% (26/27) | 3.70% (1/27) | 73.33% (11/15) | 0.8148 |
| **`S4_pre`: Logistic (`S1 + S3` LOOCV)** | 0.9951 | 0.9973 | `0.617348` | 100.0% (27/27) | 0.0% (0/27) | 93.33% (14/15) | 0.9655 |
| **`S4_full`: Logistic (`S1 + S2 + S3` LOOCV)** | 0.9852 | 0.9911 | `0.568666` | 100.0% (27/27) | 0.0% (0/27) | 93.33% (14/15) | 0.9655 |
