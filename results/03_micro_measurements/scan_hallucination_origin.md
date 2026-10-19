# Stage 3f: Origin and Denominator Audit of "42.5% Scan Hallucination Rate"

## 1. Objective
Locate every occurrence of `42.5` (or `0.425`) across all scripts, logs, JSON outputs, and manuscripts in the repository to determine:
1. How many degraded/scanned PDFs ($|\mathcal{D}_{\text{scan}}|$) and how many queries ($\sum_{d \in \mathcal{D}_{\text{scan}}} |\mathcal{Q}_d|$) formed the denominator of Eq. 14 (`R_SH = 42.5%`).
2. Whether an empirical experiment disabling the Scan Circuit Breaker on scanned PDFs was ever executed.

---

## 2. Repository-Wide Search Results for `42.5` / `0.425`

| File Path | Line(s) | Exact Content / Context | Role |
| :--- | :--- | :--- | :--- |
| `backend/scripts/update_paper_docx.py` | L285 | `["(-) Loại bỏ Scan Circuit-Breaker", "245.0 ms", "1.38 s", "0.5820", "28.5%", "42.5%"]` | **Primary origin:** Hardcoded Python list literal used to overwrite Table VI in the Word manuscript. |
| `backend/scripts/apply_paper_updates.py` | L318 | `"...bịa đặt thông số điều trị (cỡ mẫu N, thang đo tâm lý, giá trị p) trên 42.5% số lượt truy vấn..."` | Hardcoded narrative string inserted into Section 4.6 to match Table VI. |
| `backend/scripts/generate_overleaf_tex.py` | L483, L498, L514 | `inducing a 42.5\% hallucination rate`, `& 245.0 ms & 1.38 s & 0.5820 & 28.5\% & 42.5\% \\`, `catastrophic 42.5\% hallucination rate` | Generator script that produced `Acamind_Overleaf_Hoan_Chinh.tex`. |
| `Acamind_Overleaf_Hoan_Chinh.tex` | L476, L491, L507 | Same LaTeX text and Table 7 row (b). | Target Overleaf manuscript. |
| `Bai_Bao_Khoa_Hoc_Acamind_Hoan_Chinh.md` | L289, L303 | Same Markdown text and Table VI row. | Exported Markdown manuscript. |

---

## 3. Audit Findings

1. **Zero Experimental Logs or Scripts:**
   - There is **no script, notebook, or JSON output** anywhere in `backend/scripts/`, `outputs/`, or `tests/` that ever ran an ablation disabling the Scan Circuit Breaker (`_MIN_CHAR_DENSITY = 0`) on scanned PDFs.
   - All six rows of Table 7 (`tab:ablation_study`) in `backend/scripts/update_paper_docx.py` (lines 282–290) were written as hardcoded string literals:
     - Row (a) copied `247.2 ms`, `1.38 s` (50-query P50) alongside `0.6875`, `47.8%` (8-query mean).
     - Row (b) hardcoded `245.0 ms`, `1.38 s`, `0.5820`, `28.5%`, `42.5%`.
     - Row (c) hardcoded `432.2 ms` (`= 247.2 + 185.0`), `1.56 s` (`= 1.38 + 0.18`), `0.6880`, `48.0%`, `0.0%`.
     - Row (f) hardcoded `298.5 ms`, `1.82 s`, `0.6210`, `31.0%`, `0.0%`.
2. **Audit of the 499 arXiv PDFs (`backend/data/raw_pdfs_500/`):**
   - Every single one of the 499 arXiv PDFs is a digital-born PDF with readable text layers (`0` documents have $C_{\text{density}}(D) < 50$ chars/page).
   - Therefore, $|\mathcal{D}_{\text{scan}}| = 0$ in the 499-paper corpus, making the denominator of Eq. 14 ($\sum_{d \in \mathcal{D}_{\text{scan}}} |\mathcal{Q}_d|$) equal to **zero** on the benchmark corpus.
3. **Conclusion:**
   - The `42.5%` scan hallucination rate had **no empirical denominator** in the existing codebase; it will be replaced in **Stage 10** by a real, controlled synthetic degraded/blank-PDF experiment with logged queries and verifiable outputs.
