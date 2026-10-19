### Bảng 5 (Đã đo lại): Phân tích Chi tiết Hiệu năng ACAMIND theo 4 Nhóm Kịch bản trên N=50 Câu hỏi Thực tế

| Scenario Category | N | Cold Ret P50 / Mean (ms) | Warm Ret P50 / Mean (ms) | LLM P50 / Mean (ms) | Cold E2E P50 / Mean (ms) | Warm E2E P50 / Mean (ms) | Syntactic Cite Validity (Macro) | GT-Doc Cite Precision (Macro) | Refusal Rate (Gate + LLM) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Factual Q&A | 20 | 19280.0 / 16401.7 | 902.7 / 961.6 | 3721.7 / 3894.0 | 22578.1 / 20295.6 | 4758.0 / 4855.6 | 100.00% | 100.00% | 0.0% |
| Cross-Article Comparison | 15 | 20002.2 / 12288.8 | 1125.4 / 1143.4 | 5034.0 / 4949.9 | 23970.3 / 17238.8 | 6191.1 / 6093.4 | 99.63% | 99.63% | 0.0% |
| Literature Synthesis | 10 | 20926.4 / 15323.6 | 920.8 / 927.7 | 4609.4 / 4380.6 | 25662.7 / 19704.2 | 5610.0 / 5308.3 | 90.00% | 90.00% | 10.0% |
| Safe Refusal (Edge) | 5 | 21730.2 / 22697.1 | 504.2 / 440.5 | 0.0 / 0.0 | 21730.2 / 22697.1 | 504.2 / 440.5 | 0.00% | 0.00% | 100.0% |
| All Queries (Overall / Weighted) | 50 | 19967.9 / 15581.8 | 967.8 / 957.3 | 4130.0 / 3918.7 | 22884.2 / 19500.4 | 5129.9 / 4875.9 | 97.65% (N=45) | 97.65% (N=45) | OOD: 100% (5/5 Gate) | In-Scope: 2.2% (23/45) |

> **Ghi chú:** Giải quyết triệt để mâu thuẫn P0-4 trong Bảng 5 cũ (nơi E2E P50 < LLM Mean do trộn lẫn P50 với Mean). Ở đây cả P50 và Mean đều được báo cáo minh bạch, và Ret_Mean + LLM_Mean == E2E_Mean tuyệt đối trên mọi nhóm.
