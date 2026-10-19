### Bảng 4 (Đã đo lại): So sánh Toàn diện End-to-End giữa 3 Kiến trúc trên Toàn bộ N=50 Câu hỏi Thực tế (Cùng LLM gemini-2.5-flash-lite, temperature=0.1, top-5 chunks)

| System Architecture | Cold Ret Mean (ms, N=50) | Warm Ret Mean (ms, N=50) | LLM Mean (ms, N=50) | Cold E2E P50 / Mean (ms, N=50) | Warm E2E P50 / Mean (ms, N=50) | Syntactic Cite Validity Micro / Macro (N=45) | GT-Doc Cite Precision All-45 / Answered-Only | Factual Q&A GT-Doc Cite Precision (N=20) | OOD Safe Refusal (N=5, Gate / LLM) | Human Faithfulness / Page Support (N=50) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| BM25 | 904.6 | 902.5 | 2120.1 | 2506.7 / 3024.7 | 2520.2 / 3022.6 | 99.19% / 32.89% | 32.89% / 98.67% (15/45 ans) | 74.00% | 5/5 (0 Gate + 5 LLM) | Ans-Faith=83.3% | Ans-PageSup=96.7% | F20-PageSup=72.5% |
| Naive_Dense | 299.8 | 89.0 | 2080.6 | 1628.5 / 2380.4 | 1592.1 / 2169.6 | 88.31% / 33.38% | 33.38% / 88.36% (17/45 ans) | 65.42% | 5/5 (0 Gate + 5 LLM) | Ans-Faith=94.4% | Ans-PageSup=94.4% | F20-PageSup=75.0% |
| ACAMIND | 15581.8 | 957.3 | 3918.7 | 22884.2 / 19500.4 | 5129.9 / 4875.9 | 99.84% / 97.65% | 97.65% / 99.87% (44/45 ans) | 100.00% | 5/5 (5 Gate + 0 LLM) | Ans-Faith=98.9% | Ans-PageSup=90.9% | F20-PageSup=90.0% |

> **Ghi chú:** Thay thế hoàn toàn Bảng 4 cũ (vốn chỉ chạy trên N=8 câu chọn lọc và dùng công thức heuristic làm tròn). Kiểm tra cộng tính: Cold_Ret_Mean + LLM_Mean == Cold_E2E_Mean (sai số 0.0 ms).
