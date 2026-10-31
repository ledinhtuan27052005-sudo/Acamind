"""S8: đổi tên cột nhãn tự động trong bộ 300 câu hỏi và thêm cột cho rà soát thủ công.

- Gold_Candidate_Files  -> Auto_Candidate_Files   (gợi ý tự động, KHÔNG phải đáp án chuẩn)
- Gold_Candidate_Pages  -> Auto_Candidate_Pages
- Corpus_Answerability  -> Auto_Answerability
- Thêm: Human_Answerability, Review_Note, Locked
Tạo bản sao lưu *.bak trước khi ghi đè. Chạy lại nhiều lần vẫn an toàn (idempotent).
"""
import csv
import shutil
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "Query and result" / "300_cau_hoi_tam_ly_hoc"
RENAME = {
    "Gold_Candidate_Files": "Auto_Candidate_Files",
    "Gold_Candidate_Pages": "Auto_Candidate_Pages",
    "Corpus_Answerability": "Auto_Answerability",
}
NEW_COLS = ["Human_Answerability", "Review_Note", "Locked"]


def fix_header(header):
    header = [RENAME.get(h, h) for h in header]
    return header + [c for c in NEW_COLS if c not in header]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    csv_path, xlsx_path = BASE.with_suffix(".csv"), BASE.with_suffix(".xlsx")
    for p in (csv_path, xlsx_path):
        bak = p.with_suffix(p.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(p, bak)

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header = fix_header(rows[0])
    body = [r + [""] * (len(header) - len(r)) for r in rows[1:]]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows([header] + body)

    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.worksheets[0]
    old = [c.value for c in ws[1]]
    new = fix_header(old)
    for i, name in enumerate(new, 1):
        ws.cell(row=1, column=i, value=name)
    wb.save(xlsx_path)
    print("CSV cột:", len(header), "| XLSX cột:", len(new))
    print(header)


if __name__ == "__main__":
    main()
