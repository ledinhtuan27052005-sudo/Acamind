# -*- coding: utf-8 -*-
"""
Stage 8: Export Blind Human Annotation Sheet (50 Unique Questions, Side-by-Side System_A/B/C)
  - Writes BOTH:
      * results/08_annotation/blind_sheet.xlsx
      * results/08_annotation/blind_eval_sheet.xlsx
  - Contains two independent annotator sheets: "Annotator_1" and "Annotator_2", plus "Grading_Instructions".
  - 50 unique question rows (REAL_Q_01..50) with randomized System_A, System_B, System_C mapping (seed=20261016).
"""
import csv
import json
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
GEN_DIR = ROOT_DIR / "results" / "07_generation"
RAW_OUT_DIR = GEN_DIR / "raw_outputs"
SPLIT_DIR = ROOT_DIR / "results" / "02_split"
ANN_DIR = ROOT_DIR / "results" / "08_annotation"
S10_CSV = ROOT_DIR / "results" / "10_synthesis" / "synthesis_matrix_cells_for_human_eval.csv"
ANN_DIR.mkdir(parents=True, exist_ok=True)

SYSTEMS = ["BM25", "Naive_Dense", "ACAMIND"]


def clean_excel_str(s: str) -> str:
    if not isinstance(s, str):
        return s
    return ILLEGAL_CHARACTERS_RE.sub("", s)


def populate_annotator_sheet(ws, rows_for_excel: list[dict], headers: list[str]):
    ws.append(headers)
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    for r_idx, r_data in enumerate(rows_for_excel, start=2):
        ws.append([r_data[h] for h in headers])
        for c_idx in range(1, len(headers) + 1):
            ws.cell(row=r_idx, column=c_idx).alignment = Alignment(wrap_text=True, vertical="top")


def main():
    test_50 = json.loads((SPLIT_DIR / "test_50.json").read_text(encoding="utf-8"))
    gt_by_qid = {(q.get("query_id") or q.get("id")): q for q in test_50["queries"]}

    q21_35_gt = {}
    if S10_CSV.exists():
        with open(S10_CSV, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                q21_35_gt.setdefault(r["query_id"], []).append(r["target_filename"])

    rng = random.Random(20261016)
    blind_key = {}
    rows_for_excel = []

    for q_idx in range(1, 51):
        qid = f"REAL_Q_{q_idx:02d}"
        q_gt = gt_by_qid.get(qid, {})
        gt_targets = q_gt.get("ground_truth_docs") or q_gt.get("ground_truth_targets") or []
        pdf_open_hints = []
        for t in gt_targets:
            fn = t.get("filename", "")
            pgs = t.get("candidate_gt_pages") or t.get("gt_pages") or [1, 2, 3]
            pdf_open_hints.append(f"backend/data/raw_pdfs_500/{fn} (GT Pages: {pgs})")
        if not pdf_open_hints and qid in q21_35_gt:
            for fn in q21_35_gt[qid]:
                pdf_open_hints.append(f"backend/data/raw_pdfs_500/{fn} (GT Pages: [1, 2, 3])")
        pdf_hint_str = "\n".join(pdf_open_hints) if pdf_open_hints else "Out-of-Domain (No target PDF in corpus)"

        perm = list(SYSTEMS)
        rng.shuffle(perm)
        labels = ["System_A", "System_B", "System_C"]
        q_map = {}
        recs_by_label = {}

        for blabel, sys_name in zip(labels, perm):
            q_map[blabel] = sys_name
            f_path = RAW_OUT_DIR / sys_name / f"{qid}.json"
            if not f_path.exists():
                raise RuntimeError(f"Missing generated output {f_path}! Complete Stage 7 first.")
            recs_by_label[blabel] = json.loads(f_path.read_text(encoding="utf-8"))

        blind_key[qid] = q_map

        # Use randomized System_A as primary_blind_id for the primary columns, while keeping all 3 side-by-side
        primary_blabel = "System_A"
        rec_p = recs_by_label[primary_blabel]

        chunks_str_parts = []
        for idx_c, c in enumerate(rec_p.get("provided_chunks", []), 1):
            snippet = clean_excel_str((c.get("content") or "").replace("\n", " ")[:450])
            chunks_str_parts.append(f"[Chunk {idx_c}: {c.get('filename')} | Page {c.get('page_number')}] {snippet}")
        chunks_display = "\n\n".join(chunks_str_parts) if chunks_str_parts else "(No chunks passed to LLM - Gate Refused or 0 Hits)"

        row_dict = {
            "row_id": qid,
            "query_id": qid,
            "query_type": clean_excel_str(rec_p["type"]),
            "query_text": clean_excel_str(rec_p["query"]),
            "pdf_to_open_and_gt_pages": clean_excel_str(pdf_hint_str),
            "primary_blind_id": primary_blabel,
            "retrieved_top5_chunks": clean_excel_str(chunks_display),
            "system_response": clean_excel_str(rec_p["answer"]),
            "citation_page_support (0 / 1)": "",
            "claim_faithfulness (0 / 0.5 / 1)": "",
            "synthesis_completeness (1-5)": "" if not rec_p["is_ooc"] else "N/A",
            "refusal_correctness (0 / 1)": "",
            "annotator_notes": "",
        }
        for blabel in labels:
            r_b = recs_by_label[blabel]
            row_dict[f"{blabel}_response"] = clean_excel_str(r_b["answer"])
            row_dict[f"{blabel}_citation_page_support"] = ""
            row_dict[f"{blabel}_claim_faithfulness"] = ""
            row_dict[f"{blabel}_synthesis_completeness"] = "" if not r_b["is_ooc"] else "N/A"
            row_dict[f"{blabel}_refusal_correctness"] = ""
            row_dict[f"{blabel}_notes"] = ""

        rows_for_excel.append(row_dict)

    key_path = ANN_DIR / "blind_key_DO_NOT_OPEN.json"
    key_path.write_text(json.dumps(blind_key, indent=2, ensure_ascii=False), encoding="utf-8")

    wb = Workbook()
    headers = list(rows_for_excel[0].keys())

    ws1 = wb.active
    ws1.title = "Annotator_1"
    populate_annotator_sheet(ws1, rows_for_excel, headers)

    ws2 = wb.create_sheet(title="Annotator_2")
    populate_annotator_sheet(ws2, rows_for_excel, headers)

    ws_inst = wb.create_sheet(title="Grading_Instructions")
    instructions = [
        ["Column", "Scale", "Rubric / Definition"],
        ["citation_page_support (0 / 1)", "0, 1", "1 = Every cited [filename.pdf - Page X] in system_response genuinely contains the supporting evidence on that physical PDF page; 0 = Missing citation when answering, fabricated page, or page does not support the claim."],
        ["claim_faithfulness (0 / 0.5 / 1)", "0, 0.5, 1", "1 = All empirical statements (N, effect size d, clinical scale scores, findings) are supported by retrieved chunks/source PDF; 0.5 = Partially supported or hedged; 0 = Hallucinated/unsupported claims."],
        ["synthesis_completeness (1-5)", "1 to 5 (or N/A)", "1 = Fails to synthesize; 3 = Covers partial study without contrast; 5 = Complete multi-paper comparison / full answer."],
        ["refusal_correctness (0 / 1)", "0, 1", "For Safe Refusal queries (REAL_Q_46..50): 1 = System properly refuses out-of-domain query (__NO_CONTEXT__); For answerable queries: 1 = System answers without false refusal."],
    ]
    for row in instructions:
        ws_inst.append(row)

    path_main = ANN_DIR / "blind_sheet.xlsx"
    path_alias = ANN_DIR / "blind_eval_sheet.xlsx"
    wb.save(path_main)
    wb.save(path_alias)
    print(f"Saved 50-question blind sheet to {path_main} and {path_alias}", flush=True)


if __name__ == "__main__":
    main()
