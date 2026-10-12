import sys
import os
import json
import urllib.request
import urllib.parse
import fitz

sys.path.insert(0, os.path.abspath('backend'))

from app.services.pdf_highlighter import (
    ground_and_search_page_rects,
    extract_evidence_anchors,
    get_highlight_metadata,
    generate_highlighted_pdf_stream,
)

print("=" * 70)
print("ACAMIND SMART EVIDENCE GROUNDING & HIGHLIGHT ACCURACY TEST SUITE")
print("=" * 70)

test_results = []

def run_test(name, fn):
    try:
        ok, detail = fn()
        status = "PASS" if ok else "FAIL"
        test_results.append((name, status, detail))
        print(f"[{status}] {name}")
        if detail:
            for d in detail:
                print(f"       -> {d}")
    except Exception as e:
        import traceback
        test_results.append((name, "ERROR", [str(e)]))
        print(f"[ERROR] {name}: {e}")
        traceback.print_exc()

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 1: English Academic Paper (2609.13304v1.pdf)
# ─────────────────────────────────────────────────────────────────────────────
pdf1_path = 'backend/data/raw_pdfs_500/2609.13304v1.pdf'

def test_1a_exact_sentence():
    doc = fitz.open(pdf1_path)
    page = doc[0]
    q = "Cognitive psychology was developed during the second half of the 20th century as a result of behavioral psychology’s limitations in explaining cognitive processes"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 3 and "cognitive psychology" in sent.lower()
    return ok, [
        f"Bounding boxes found: {len(rects)}",
        f"Grounded text: '{sent[:80]}...'",
        f"Terms: {terms}"
    ]

def test_1b_user_paraphrased_sentence():
    doc = fitz.open(pdf1_path)
    page = doc[0]
    # Exactly what user experienced in screenshot
    q = "Psychology is the scientific study of human behavior and cognitive processes, developed historically as an approach to understand how the mind processes information"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 4 and "cognitive psychology was developed" in sent.lower()
    return ok, [
        f"Bounding boxes found: {len(rects)} (multi-line cohesive highlight)",
        f"Grounded evidence in PDF: '{sent[:90]}...'",
        f"Terms highlighted: {terms}"
    ]

def test_1c_cross_lingual_vi_to_en():
    doc = fitz.open(pdf1_path)
    page = doc[0]
    q = "Tâm lý học nhận thức (Cognitive psychology) được phát triển vào nửa sau của thế kỷ 20 như một kết quả từ những hạn chế của tâm lý học hành vi (Behavioral psychology)"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 3 and "cognitive psychology was developed" in sent.lower()
    return ok, [
        f"Cross-lingual Bounding boxes: {len(rects)}",
        f"Grounded English sentence: '{sent[:90]}...'",
        f"Highlighted terms: {terms}"
    ]

def test_1d_abstract_grounding():
    doc = fitz.open(pdf1_path)
    page = doc[0]
    q = "The primary goal of this work is to reproduce the behavior of a human trader detailing psychological processes"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 2 and "reproduce the behavior of a human trader" in sent.lower()
    return ok, [
        f"Bounding boxes: {len(rects)}",
        f"Grounded sentence: '{sent[:85]}...'"
    ]

run_test("Suite 1.1: Exact Sentence Match on Paper 2609.13304v1.pdf", test_1a_exact_sentence)
run_test("Suite 1.2: Paraphrased Grounding (User's Reported Case)", test_1b_user_paraphrased_sentence)
run_test("Suite 1.3: Cross-Lingual VI -> EN Grounding on Paper 2609.13304v1.pdf", test_1c_cross_lingual_vi_to_en)
run_test("Suite 1.4: Abstract Section Grounding on Paper 2609.13304v1.pdf", test_1d_abstract_grounding)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 2: Clinical Scan Document (Tai_Lieu_Scan_Thu_Nghiem_CBT_Tam_Ly_Hoc.pdf)
# ─────────────────────────────────────────────────────────────────────────────
import glob
cbt_files = glob.glob('data/raw_pdfs/*Tai_Lieu_Scan*.pdf')
cbt_path = [f for f in cbt_files if 'bfc5899b' in f][0]

def test_2a_remission_percentage():
    doc = fitz.open(cbt_path)
    page = doc[1] # Page 2
    q = "Nhóm phối hợp CBT và SSRI đạt mức độ suy giảm triệu chứng trầm cảm vượt trội 68.9% so với hai nhóm đơn trị liệu"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 2 and any('68.9%' in t for t in terms)
    return ok, [
        f"Bounding boxes: {len(rects)}",
        f"Key numbers highlighted: {terms}"
    ]

def test_2b_table2_remission_82_5_pct():
    doc = fitz.open(cbt_path)
    page = doc[1] # Page 2
    q = "Tỷ lệ thuyên giảm lâm sàng đạt 82.5% và cỡ hiệu ứng d = 0.95 ở nhóm phối hợp"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 1 and any('82.5%' in t for t in terms)
    return ok, [
        f"Bounding boxes: {len(rects)}",
        f"Key metrics highlighted: {terms}"
    ]

def test_2c_sample_size_and_scales_p1():
    doc = fitz.open(cbt_path)
    page = doc[0] # Page 1
    q = "Cỡ mẫu nghiên cứu gồm N = 120 bệnh nhân được chẩn đoán theo DSM-5 và theo dõi thang đo BDI-II, PHQ-9"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 2 and any(k in terms for k in ['N = 120', 'DSM-5', 'BDI-II', 'PHQ-9'])
    return ok, [
        f"Bounding boxes: {len(rects)}",
        f"Anchor items highlighted: {terms}"
    ]

def test_2d_recommendations_p3():
    doc = fitz.open(cbt_path)
    page = doc[2] # Page 3
    q = "Đối với trầm cảm mức độ trung bình ưu tiên chỉ định CBT đơn thuần 12-16 tuần"
    rects, sent, terms = ground_and_search_page_rects(page, q)
    doc.close()
    ok = len(rects) >= 1
    return ok, [
        f"Bounding boxes: {len(rects)}",
        f"Grounded sentence: '{sent[:80]}...'",
        f"Terms: {terms}"
    ]

run_test("Suite 2.1: Quantitative Metric 68.9% on CBT Doc P.2", test_2a_remission_percentage)
run_test("Suite 2.2: Remission 82.5% & Effect Size on CBT Doc P.2", test_2b_table2_remission_82_5_pct)
run_test("Suite 2.3: Sample Size N=120 & Scales on CBT Doc P.1", test_2c_sample_size_and_scales_p1)
run_test("Suite 2.4: Clinical Recommendation on CBT Doc P.3", test_2d_recommendations_p3)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 3: Paper 2610.08585v1.pdf (Clinical reasoning in LLMs)
# ─────────────────────────────────────────────────────────────────────────────
paper_2610_files = glob.glob('backend/data/raw_pdfs_500/*2610.08585*.pdf')
if paper_2610_files:
    def test_3a_paper_2610():
        doc = fitz.open(paper_2610_files[0])
        page = doc[0]
        q = "Incidental information contaminates patient notes and disrupts clinical reasoning in large language models"
        rects, sent, terms = ground_and_search_page_rects(page, q)
        doc.close()
        ok = len(rects) >= 1
        return ok, [
            f"Bounding boxes: {len(rects)}",
            f"Grounded title / passage: '{sent[:80]}...'"
        ]
    run_test("Suite 3.1: Academic Title Grounding on Paper 2610.08585v1.pdf", test_3a_paper_2610)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 4: Live HTTP API Endpoints (/highlight-meta & /highlighted-file)
# ─────────────────────────────────────────────────────────────────────────────
def test_4a_live_api_meta():
    doc_id = "6870b4fd-d0a2-49ba-b7cf-4013eefcc433"
    q = "Psychology is the scientific study of human behavior and cognitive processes"
    url = f"http://localhost:8000/api/v1/document/{doc_id}/highlight-meta?page=1&query={urllib.parse.quote(q)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ok = resp.status == 200 and len(data.get('rects', [])) >= 4 and bool(data.get('grounded_sentence'))
        return ok, [
            f"HTTP Status: {resp.status}",
            f"Rects returned: {len(data['rects'])}",
            f"Grounded sentence in response: '{data['grounded_sentence'][:70]}...'",
            f"Terms: {data['terms']}"
        ]

def test_4b_live_api_pdf_stream():
    doc_id = "6870b4fd-d0a2-49ba-b7cf-4013eefcc433"
    q = "Cognitive psychology was developed during the second half of the 20th century"
    url = f"http://localhost:8000/api/v1/document/{doc_id}/highlighted-file?page=1&highlight={urllib.parse.quote(q)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        content_type = resp.headers.get('Content-Type')
        data = resp.read()
        # Verify it is a valid PDF with annotations
        doc = fitz.open(stream=data, filetype="pdf")
        annots = list(doc[0].annots())
        annot_count = len(annots)
        doc.close()
        ok = resp.status == 200 and content_type == 'application/pdf' and annot_count >= 1
        return ok, [
            f"HTTP Status: {resp.status}",
            f"Content-Type: {content_type}",
            f"PDF stream size: {len(data):,} bytes",
            f"Embedded Highlight Annotations on Page 1: {annot_count}"
        ]

def test_4c_live_cbt_scan_api():
    doc_id = "bfc5899b-cc61-453a-a6a6-163234b0ce85"
    q = "Nhóm phối hợp CBT và SSRI đạt tỷ lệ suy giảm triệu chứng 68.9%"
    url = f"http://localhost:8000/api/v1/document/{doc_id}/highlight-meta?page=2&query={urllib.parse.quote(q)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ok = resp.status == 200 and len(data.get('rects', [])) >= 2
        return ok, [
            f"HTTP Status: {resp.status}",
            f"Rects returned: {len(data['rects'])}",
            f"Terms highlighted: {data['terms']}"
        ]

run_test("Suite 4.1: Live API GET /highlight-meta (Schema & Grounded Evidence)", test_4a_live_api_meta)
run_test("Suite 4.2: Live API GET /highlighted-file (Embedded PDF Annotations)", test_4b_live_api_pdf_stream)
run_test("Suite 4.3: Live API CBT Document Page 2 with 68.9% Anchor", test_4c_live_cbt_scan_api)

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY & SCORE
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
total = len(test_results)
passed = sum(1 for _, status, _ in test_results if status == "PASS")
score = (passed / total) * 100
print(f"TOTAL TESTS: {total} | PASSED: {passed} | FAILED: {total - passed}")
print(f"GROUNDING & HIGHLIGHT ACCURACY SCORE: {score:.1f}%")
print("=" * 70)
