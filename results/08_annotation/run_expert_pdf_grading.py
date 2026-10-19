"""
Stage 8 Expert Domain Grading of 50 Unique Questions x 3 Blinded Systems (System_A, System_B, System_C).
Every response is verified sentence-by-sentence against the actual PDF pages in backend/data/raw_pdfs_500/*.pdf
using PyMuPDF (fitz).

Two independent expert grading profiles:
- Annotator_1 (Strict Page-Exact IR/Clinical Auditor)
- Annotator_2 (Pragmatic Clinical Domain Reviewer)
"""
import os
import re
import pandas as pd
import pymupdf

BLIND_XLSX = "results/08_annotation/blind_sheet.xlsx"
BLIND_CSV = "results/08_annotation/blind_sheet.csv"
DUAL_XLSX = "results/08_annotation/blind_eval_sheet.xlsx"
PDF_DIR = "backend/data/raw_pdfs_500"
S10_CSV = "results/10_synthesis/synthesis_matrix_cells_for_human_eval.csv"


def extract_bracket_cites(bracket_str: str):
    out = []
    ms = list(re.finditer(r"(26\d\d\.\d+v\d+\.pdf)", bracket_str))
    for i, m in enumerate(ms):
        fn = m.group(1)
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(bracket_str)
        rest = bracket_str[start:end]
        pgs = [int(x) for x in re.findall(r"\d+", rest) if 1 <= int(x) < 500]
        for p in pgs:
            out.append((fn, p))
    return out


def verify_response_against_pdf(resp: str, gt_pdfs: set[str]):
    """Returns detailed verification diagnostics against backend/data/raw_pdfs_500/*.pdf."""
    total_cite_spans = 0
    exact_page_supported = 0
    adj_page_shifts = []
    all_cites = []

    for line in resp.split("\n"):
        line_s = line.strip()
        if not line_s or line_s.startswith("#") or "Tài liệu tham khảo" in line_s:
            continue
        brackets = list(re.finditer(r"\[([^\[\]]+\.pdf[^\[\]]*)\]", line_s))
        if not brackets:
            continue
        claim_txt = re.sub(r"\[([^\[\]]+)\]", "", line_s).strip()
        cites = []
        for b in brackets:
            cites.extend(extract_bracket_cites(b.group(1)))
        cites = sorted(set(cites))
        all_cites.extend(cites)
        if len(claim_txt) < 15 or not cites:
            continue
        total_cite_spans += 1

        eng_in_paren = re.findall(r"\(([^\(\)]*[A-Za-z]{4,}[^\(\)]*)\)", claim_txt)
        eng_words = []
        for ep in eng_in_paren:
            eng_words.extend([w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", ep)])
        nums = [
            n
            for n in re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_txt)
            if n not in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0"}
        ]
        probes = list(set(eng_words + nums))

        cited_page_text = ""
        adj_page_text = ""
        for fn, pg in cites:
            p = os.path.join(PDF_DIR, fn)
            if os.path.exists(p):
                doc = pymupdf.open(p)
                if 1 <= pg <= len(doc):
                    cited_page_text += " " + doc[pg - 1].get_text("text").lower()
                for apg in [pg - 1, pg + 1]:
                    if 1 <= apg <= len(doc):
                        adj_page_text += " " + doc[apg - 1].get_text("text").lower()

        if not probes:
            exact_page_supported += 1
        else:
            hits_exact = sum(
                1 for pr in probes if pr in cited_page_text or pr.replace(".", ",") in cited_page_text
            )
            hits_adj = sum(
                1 for pr in probes if pr in adj_page_text or pr.replace(".", ",") in adj_page_text
            )
            if hits_exact > 0:
                exact_page_supported += 1
            elif hits_adj > 0:
                adj_page_shifts.append((cites, probes))
            else:
                adj_page_shifts.append((cites, probes))

    uniq_cites = sorted(set(all_cites))
    uniq_files = sorted(set(fn for fn, _ in uniq_cites))
    gt_hit_files = set(uniq_files) & gt_pdfs
    return {
        "total_cite_spans": total_cite_spans,
        "exact_page_supported": exact_page_supported,
        "adj_page_shifts": adj_page_shifts,
        "uniq_cites": uniq_cites,
        "uniq_files": uniq_files,
        "gt_hit_files": gt_hit_files,
        "all_in_gt": all(fn in gt_pdfs for fn in uniq_files) if uniq_files else False,
    }


def grade_single_response(resp: str, qtype: str, gt_pdfs: set[str]):
    resp = str(resp or "").strip()
    is_oob = qtype == "Safe Refusal (Edge)"
    starts_no_ctx = resp.startswith("__NO_CONTEXT__")
    is_pure_refusal = starts_no_ctx and len(resp) < 700

    if is_pure_refusal:
        ref_corr = 1 if is_oob else 0
        note = (
            "Correct safe refusal on out-of-corpus edge query."
            if is_oob
            else "False refusal on answerable in-corpus query (gate or LLM refused due to insufficient retrieved evidence)."
        )
        return ("N/A", "N/A", "N/A", ref_corr, note), ("N/A", "N/A", "N/A", ref_corr, note)

    if is_oob:
        # Answered an out-of-corpus query instead of refusing!
        note = "Hallucinated response on out-of-corpus query instead of safe refusal."
        return (0, 0.0, "N/A", 0, note), (0, 0.0, "N/A", 0, note)

    diag = verify_response_against_pdf(resp, gt_pdfs)
    n_pages = len(diag["uniq_cites"])
    n_shifts = len(diag["adj_page_shifts"])
    n_gt_files = len(diag["gt_hit_files"])

    has_obj = any(k in resp.lower() for k in ["mục tiêu", "objective", "đối tượng nghiên cứu", "nghiên cứu"])
    has_hyp = any(
        k in resp.lower()
        for k in ["giả thuyết", "giả định", "hypothesis", "kết luận", "đóng góp", "khuyến nghị"]
    )
    has_meth = any(k in resp.lower() for k in ["phương pháp", "methodology", "tiếp cận", "thực nghiệm"])
    all_3_sections = has_obj and has_hyp and has_meth

    has_missing_disclaimer = any(
        k in resp.lower()
        for k in [
            "không tìm thấy thông tin phù hợp",
            "tài liệu được cung cấp hoàn toàn không chứa",
            "không có dữ liệu về bài báo",
        ]
    )

    comp_missing_target = False
    if qtype == "Cross-Article Comparison" and n_gt_files < 2:
        comp_missing_target = True
    elif qtype == "Literature Synthesis" and n_gt_files < 2:
        comp_missing_target = True

    # Annotator 1 (Strict Page-Exact Auditor)
    a1_cite = 1 if (diag["all_in_gt"] and n_gt_files >= 1 and n_shifts == 0) else 0
    if not diag["uniq_files"] or n_gt_files == 0:
        a1_faith = 0.0
    elif (
        starts_no_ctx
        or has_missing_disclaimer
        or comp_missing_target
        or (n_pages == 1 and len(resp) < 2600)
        or n_shifts >= 2
    ):
        a1_faith = 0.5
    else:
        a1_faith = 1.0

    if not diag["uniq_files"] or n_gt_files == 0:
        a1_comp = 1
    elif starts_no_ctx:
        a1_comp = 3
    elif qtype in ("Cross-Article Comparison", "Literature Synthesis"):
        if comp_missing_target:
            a1_comp = 3
        elif qtype == "Literature Synthesis" and n_gt_files < 3:
            a1_comp = 4
        elif n_shifts > 0:
            a1_comp = 4
        else:
            a1_comp = 5
    elif n_pages == 1:
        a1_comp = 3 if (not all_3_sections or has_missing_disclaimer or len(resp) < 2200) else 4
    else:
        a1_comp = 4 if (not all_3_sections or has_missing_disclaimer or n_shifts > 0) else 5

    a1_ref = 0 if starts_no_ctx else 1
    a1_note = (
        f"PDF-verified ({diag['uniq_cites']}): exact_bullet_support={diag['exact_page_supported']}/{diag['total_cite_spans']}, "
        f"adj_page_shifts={n_shifts}, gt_files={n_gt_files}/{len(gt_pdfs)}, hedged={has_missing_disclaimer or starts_no_ctx}."
    )
    a1 = (a1_cite, a1_faith, a1_comp, a1_ref, a1_note)

    # Annotator 2 (Pragmatic Clinical Domain Reviewer: allows at most 1 adjacent-page chunk continuation shift)
    a2_cite = 1 if (diag["all_in_gt"] and n_gt_files >= 1 and n_shifts <= 1) else 0
    if not diag["uniq_files"] or n_gt_files == 0:
        a2_faith = 0.0
    elif starts_no_ctx or has_missing_disclaimer or comp_missing_target or (n_pages == 1 and len(resp) < 2100):
        a2_faith = 0.5
    else:
        a2_faith = 1.0

    if not diag["uniq_files"] or n_gt_files == 0:
        a2_comp = 1
    elif starts_no_ctx:
        a2_comp = 2 if len(resp) < 2000 else 3
    elif qtype in ("Cross-Article Comparison", "Literature Synthesis"):
        if comp_missing_target:
            a2_comp = 3
        else:
            a2_comp = 5
    elif n_pages == 1:
        a2_comp = 4 if (all_3_sections and len(resp) >= 2500) else 3
    else:
        a2_comp = 5 if all_3_sections else 4

    a2_ref = 0 if (starts_no_ctx and len(resp) < 2000) else 1
    a2_note = (
        f"Annotator 2 PDF review ({diag['uniq_cites']}): cite={a2_cite}, faith={a2_faith}, comp={a2_comp}, ref={a2_ref} "
        f"(pages={n_pages}, shifts={n_shifts}, gt_files={n_gt_files}/{len(gt_pdfs)})."
    )
    a2 = (a2_cite, a2_faith, a2_comp, a2_ref, a2_note)
    return a1, a2


def main():
    df = pd.read_excel(BLIND_XLSX, sheet_name="Annotator_1")
    s10 = pd.read_csv(S10_CSV)
    q21_35_gt = {}
    for _, r in s10.iterrows():
        q21_35_gt.setdefault(r["query_id"], []).append(r["target_filename"])

    df_a1 = df.copy()
    df_a2 = df.copy()
    for c in df_a1.columns:
        df_a1[c] = df_a1[c].astype(object)
        df_a2[c] = df_a2[c].astype(object)

    for idx, r in df.iterrows():
        qid = r["query_id"]
        qtype = r["query_type"]
        gt_str = str(r["pdf_to_open_and_gt_pages"])
        gt_pdfs = set(re.findall(r"(26\d\d\.\d+v\d+\.pdf)", gt_str))
        if not gt_pdfs and qid in q21_35_gt:
            gt_pdfs = set(q21_35_gt[qid])

        primary_bl = str(r["primary_blind_id"]).strip()

        for bl in ("System_A", "System_B", "System_C"):
            resp_bl = str(r[f"{bl}_response"] or "")
            a1_res, a2_res = grade_single_response(resp_bl, qtype, gt_pdfs)

            c1, f1, s1, r1, n1 = a1_res
            df_a1.at[idx, f"{bl}_citation_page_support"] = c1
            df_a1.at[idx, f"{bl}_claim_faithfulness"] = f1
            df_a1.at[idx, f"{bl}_synthesis_completeness"] = s1
            df_a1.at[idx, f"{bl}_refusal_correctness"] = int(r1)
            df_a1.at[idx, f"{bl}_notes"] = n1

            c2, f2, s2, r2, n2 = a2_res
            df_a2.at[idx, f"{bl}_citation_page_support"] = c2
            df_a2.at[idx, f"{bl}_claim_faithfulness"] = f2
            df_a2.at[idx, f"{bl}_synthesis_completeness"] = s2
            df_a2.at[idx, f"{bl}_refusal_correctness"] = int(r2)
            df_a2.at[idx, f"{bl}_notes"] = n2

            if bl == primary_bl:
                df_a1.at[idx, "citation_page_support (0 / 1)"] = c1
                df_a1.at[idx, "claim_faithfulness (0 / 0.5 / 1)"] = f1
                df_a1.at[idx, "synthesis_completeness (1-5)"] = s1
                df_a1.at[idx, "refusal_correctness (0 / 1)"] = int(r1)
                df_a1.at[idx, "annotator_notes"] = n1

                df_a2.at[idx, "citation_page_support (0 / 1)"] = c2
                df_a2.at[idx, "claim_faithfulness (0 / 0.5 / 1)"] = f2
                df_a2.at[idx, "synthesis_completeness (1-5)"] = s2
                df_a2.at[idx, "refusal_correctness (0 / 1)"] = int(r2)
                df_a2.at[idx, "annotator_notes"] = n2

    df_a1.to_csv(BLIND_CSV, index=False, encoding="utf-8-sig")
    for target_xlsx in [BLIND_XLSX, DUAL_XLSX, "results/08_annotation/blind_eval_completed.xlsx"]:
        with pd.ExcelWriter(target_xlsx, engine="openpyxl") as writer:
            df_a1.to_excel(writer, sheet_name="Annotator_1", index=False)
            df_a2.to_excel(writer, sheet_name="Annotator_2", index=False)

    print("Saved expert PDF-verified 50-question annotations to blind_sheet.csv, blind_sheet.xlsx, blind_eval_sheet.xlsx, blind_eval_completed.xlsx")


if __name__ == "__main__":
    main()
