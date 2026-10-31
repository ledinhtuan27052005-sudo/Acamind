"""Scientific extraction candidates and reviewed-data analysis helpers.

Heuristic extraction is not evidence appraisal or entailment certification.
Unavailable scientific judgments return explicit unverified/insufficient states.
See EVIDENCE_PIPELINE.md for supported contracts and limitations.
"""
from __future__ import annotations

import re
import uuid
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text


# ── 1. Thư viện Thang đo Tâm lý Học Chuẩn (Psychometric Scales Library) ───────

PSYCHOMETRIC_SCALES_DATABASE = {
    "bdi": {
        "code": "BDI-II",
        "name": "Beck Depression Inventory - Second Edition (Thang đo Trầm cảm Beck)",
        "authors": "Aaron T. Beck, Robert A. Steer, Gregory K. Brown (1996)",
        "items_count": 21,
        "score_range": "0 - 63",
        "cutoffs": [
            {"range": "0 - 13", "severity": "Tối thiểu (Minimal / Không trầm cảm)", "color": "#10b981", "clinical_action": "Bình thường, theo dõi định kỳ"},
            {"range": "14 - 19", "severity": "Trầm cảm nhẹ (Mild Depression)", "color": "#f59e0b", "clinical_action": "Theo dõi tâm lý, can thiệp lối sống hoặc tư vấn tâm lý"},
            {"range": "20 - 28", "severity": "Trầm cảm vừa (Moderate Depression)", "color": "#f97316", "clinical_action": "Chỉ định trị liệu tâm lý (CBT) hoặc phối hợp dược lý"},
            {"range": "29 - 63", "severity": "Trầm cảm nặng (Severe Depression)", "color": "#ef4444", "clinical_action": "Can thiệp chuyên khoa tâm thần khẩn cấp, phối hợp CBT + SSRI, sàng lọc nguy cơ tự sát"},
        ],
        "clinical_threshold": 14,
        "description": "Thang đo tự báo cáo 21 câu hỏi đánh giá mức độ nghiêm trọng của các triệu chứng trầm cảm trong 2 tuần qua theo tiêu chuẩn DSM-IV/DSM-5."
    },
    "phq": {
        "code": "PHQ-9",
        "name": "Patient Health Questionnaire-9 (Bảng Câu hỏi Sức khỏe Bệnh nhân-9)",
        "authors": "Kurt Kroenke, Robert L. Spitzer, Janet B. W. Williams (2001)",
        "items_count": 9,
        "score_range": "0 - 27",
        "cutoffs": [
            {"range": "0 - 4", "severity": "Không có / Tối thiểu (None-Minimal)", "color": "#10b981", "clinical_action": "Không cần can thiệp"},
            {"range": "5 - 9", "severity": "Trầm cảm nhẹ (Mild Depression)", "color": "#f59e0b", "clinical_action": "Theo dõi cẩn trọng, hỗ trợ tâm lý"},
            {"range": "10 - 14", "severity": "Trầm cảm trung bình (Moderate Depression)", "color": "#f97316", "clinical_action": "Lập phác đồ điều trị tâm lý (CBT) hoặc cân nhắc thuốc chống trầm cảm"},
            {"range": "15 - 19", "severity": "Trầm cảm nặng vừa (Moderately Severe)", "color": "#ea580c", "clinical_action": "Bắt buộc điều trị tích cực bằng thuốc và/hoặc liệu pháp tâm lý"},
            {"range": "20 - 27", "severity": "Trầm cảm nặng (Severe Depression)", "color": "#ef4444", "clinical_action": "Điều trị chuyên khoa khẩn cấp, đánh giá nguy cơ tự sát, chuyển bác sĩ tâm thần"},
        ],
        "clinical_threshold": 10,
        "description": "Bộ công cụ sàng lọc và đo lường mức độ trầm cảm dựa trên 9 tiêu chuẩn chẩn đoán trầm cảm chủ yếu của cẩm nang DSM-5."
    },
    "gad": {
        "code": "GAD-7",
        "name": "Generalized Anxiety Disorder-7 (Thang đo Rối loạn Lo âu Lan tỏa-7)",
        "authors": "Robert L. Spitzer, Kurt Kroenke, Janet B. W. Williams, Bernd Löwe (2006)",
        "items_count": 7,
        "score_range": "0 - 21",
        "cutoffs": [
            {"range": "0 - 4", "severity": "Lo âu tối thiểu (Minimal Anxiety)", "color": "#10b981", "clinical_action": "Bình thường"},
            {"range": "5 - 9", "severity": "Lo âu nhẹ (Mild Anxiety)", "color": "#f59e0b", "clinical_action": "Theo dõi, hướng dẫn kỹ thuật thư giãn/chánh niệm"},
            {"range": "10 - 14", "severity": "Lo âu trung bình (Moderate Anxiety)", "color": "#f97316", "clinical_action": "Đánh giá lâm sàng chuyên sâu, chỉ định CBT hoặc can thiệp tâm lý"},
            {"range": "15 - 21", "severity": "Lo âu nặng (Severe Anxiety)", "color": "#ef4444", "clinical_action": "Can thiệp tích cực, phối hợp CBT và dược lý chống lo âu"},
        ],
        "clinical_threshold": 10,
        "description": "Thang đo sàng lọc nhanh và lượng giá mức độ rối loạn lo âu lan tỏa trong chăm sóc sức khỏe ban đầu và lâm sàng tâm thần."
    },
    "dass": {
        "code": "DASS-21",
        "name": "Depression Anxiety Stress Scales-21 (Thang đo Trầm cảm - Lo âu - Căng thẳng 21)",
        "authors": "Peter F. Lovibond & Syd H. Lovibond (1995)",
        "items_count": 21,
        "score_range": "0 - 42 mỗi trục (nhân đôi số điểm 7 câu)",
        "cutoffs": [
            {"range": "Trầm cảm (0-9 Bình thường, 10-13 Nhẹ, 14-20 Vừa, 21-27 Nặng, 28+ Rất nặng)", "severity": "Đánh giá Trục Trầm cảm", "color": "#3b82f6", "clinical_action": "Phân tầng nguy cơ tâm trạng"},
            {"range": "Lo âu (0-7 Bình thường, 8-9 Nhẹ, 10-14 Vừa, 15-19 Nặng, 20+ Rất nặng)", "severity": "Đánh giá Trục Lo âu", "color": "#f59e0b", "clinical_action": "Phân tầng kích thích sinh lý thần kinh"},
            {"range": "Stress (0-14 Bình thường, 15-18 Nhẹ, 19-25 Vừa, 26-33 Nặng, 34+ Rất nặng)", "severity": "Đánh giá Trục Căng thẳng", "color": "#ef4444", "clinical_action": "Đánh giá căng thẳng trường diễn và quá tải thần kinh"},
        ],
        "clinical_threshold": 14,
        "description": "Bộ thang đo đánh giá ba trạng thái cảm xúc tiêu cực gồm Trầm cảm (Dysphoria), Lo âu (Autonomic arousal) và Căng thẳng (Chronic tension)."
    },
    "hamd": {
        "code": "HAM-D",
        "name": "Hamilton Depression Rating Scale (Thang đánh giá Trầm cảm Hamilton - HDRS-17)",
        "authors": "Max Hamilton (1960)",
        "items_count": 17,
        "score_range": "0 - 52",
        "cutoffs": [
            {"range": "0 - 7", "severity": "Bình thường / Thuyên giảm hoàn toàn", "color": "#10b981", "clinical_action": "Không trầm cảm"},
            {"range": "8 - 16", "severity": "Trầm cảm nhẹ", "color": "#f59e0b", "clinical_action": "Theo dõi và can thiệp tâm lý ban đầu"},
            {"range": "17 - 23", "severity": "Trầm cảm mức độ vừa", "color": "#f97316", "clinical_action": "Chỉ định điều trị y tế chính quy"},
            {"range": "≥ 24", "severity": "Trầm cảm nặng đến rất nặng", "color": "#ef4444", "clinical_action": "Điều trị nội trú hoặc theo dõi sát sao tại bệnh viện"},
        ],
        "clinical_threshold": 17,
        "description": "Tiêu chuẩn vàng trong các thử nghiệm lâm sàng dược lý tâm thần do chuyên gia trực tiếp phỏng vấn và lượng giá."
    }
}


# ── 2. Đánh giá Cấp độ Bằng chứng Y học Thực chứng (Oxford CEBM Level) ─────────

def evaluate_cebm_evidence_level(cited_docs: list[dict], context_chunks: list[dict]) -> dict[str, Any]:
    """CEBM and recommendation grades require a question-specific appraisal.

    Keyword mentions in a title or retrieved passage cannot establish study
    design, risk of bias, authorship or strength of recommendation.
    """
    return {
        "status": "unverified", "level": "unverified",
        "level_label": "Chưa thẩm định cấp độ bằng chứng",
        "grade": "unverified", "grade_label": "Chưa đánh giá độ mạnh khuyến cáo",
        "study_design": "Chưa xác minh thiết kế nghiên cứu",
        "stars": 0, "badge_color": "slate",
        "description": "Cần thẩm định theo loại câu hỏi, thiết kế và nguy cơ sai lệch; từ khóa không xác nhận cấp độ CEBM.",
    }


# ── 3. Bóc tách Thẻ Thực nghiệm Chuẩn PICO (PICO Framework Extractor) ──────────

def extract_pico_framework(query: str, answer: str, context_chunks: list[dict]) -> dict[str, Any]:
    """Return source-specific PICO candidates, never fill missing fields.

    Do not treat generated answers as evidence or join different studies into
    one trial. Keyword matching is explicitly unverified extraction.
    """
    patterns = {
        "population": r"\b(?:participants?|patients?|subjects?|sample|population|bệnh nhân|người tham gia|cỡ mẫu)\b",
        "intervention": r"\b(?:intervention|treatment|therapy|can thiệp|liệu pháp|điều trị)\b",
        "comparison": r"\b(?:control group|placebo|comparator|comparison|nhóm chứng|đối chứng|so sánh)\b",
        "outcome": r"\b(?:outcome|results?|finding|kết quả|kết cục)\b",
    }
    candidates = {key: [] for key in patterns}
    for chunk in context_chunks:
        source_text = chunk.get("content") or ""
        for match in re.finditer(r"[^.!?\n]+(?:[.!?]|$)", source_text):
            quote = match.group().strip()
            if not quote:
                continue
            for key, pattern in patterns.items():
                if re.search(pattern, quote, re.I):
                    candidates[key].append({"quote": quote, "document_id": chunk.get("document_id"),
                        "filename": chunk.get("doc_filename"), "page": chunk.get("page_number"),
                        "claim_origin": "unverified"})
    return {"has_pico": any(candidates.values()), "status": "unverified",
            **{key: "Chưa xác minh; xem các đoạn nguồn ứng viên" if values else "Chưa tìm thấy trong các đoạn truy xuất"
               for key, values in candidates.items()},
            "source_type": "Ứng viên PICO theo từng nguồn; chưa xác minh thiết kế nghiên cứu",
            "candidates": candidates}


# ── 4. Ma trận Đồng thuận vs. Bất đồng Học thuật (Consensus Meter) ─────────────

def calculate_consensus_matrix(query: str, answer: str, context_chunks: list[dict]) -> dict[str, Any]:
    """No agreement percentage without claim-level comparable evidence."""
    return {
        "status": "insufficient_evidence",
        "consensus_percentage": None, "caveats_percentage": None,
        "summary": "Chưa có đối chiếu nhận định tương đương để tính mức đồng thuận.",
        "debate_points": [], "consensus_label": "Chưa đủ bằng chứng",
    }


# ── 5. Bộ câu hỏi Phản biện Phương pháp luận (Devil's Advocate / Peer Review) ───

def generate_peer_review_questions(query: str, answer: str) -> list[dict[str, str]]:
    """Tạo 3 câu hỏi chất vấn học thuật chuyên sâu (Socratic Inquiries) giúp người dùng đào sâu phản biện:"""
    return [
        {
            "id": "critique-power",
            "title": "Lực thống kê & Quy mô Cỡ mẫu",
            "question": "Cỡ mẫu của nghiên cứu đối chứng này có đủ độ mạnh thống kê (Statistical Power) để khái quát hóa sang các nhóm bệnh nhân đa dạng khác không?",
            "category": "Phương pháp luận"
        },
        {
            "id": "critique-relapse",
            "title": "Đánh giá Nguy cơ Tái phát Sau 12 Tháng",
            "question": "Sau khi kết thúc liệu trình 12 buổi và ngừng thuốc, tỷ lệ duy trì thuyên giảm và nguy cơ tái phát sau 6 - 12 tháng được ghi nhận như thế nào?",
            "category": "Hiệu quả Dài hạn"
        },
        {
            "id": "critique-blinding",
            "title": "Thiên lệch Làm mù trong Trị liệu Tâm lý",
            "question": "Trong thử nghiệm lâm sàng tâm lý học, phương pháp mù đôi (Double-blind) có khả thi không và các nhà nghiên cứu đã kiểm soát thiên lệch kỳ vọng (Expectancy Bias) ra sao?",
            "category": "Kiểm soát Sai lệch"
        }
    ]


# ── 6. Trình xuất Trích dẫn Học thuật Chuẩn Quốc Tế (BibTeX / RIS / APA 7th) ────

def _citation_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def generate_bibtex_entry(doc: dict[str, Any]) -> str:
    """Export supplied metadata only; unknown bibliographic fields are omitted."""
    def escape(value):
        return _citation_text(value).replace("\\", "\\textbackslash{} ").replace("{", "\\{").replace("}", "\\}").replace("%", "\\%").replace("&", "\\&").replace("_", "\\_")
    key = re.sub(r"[^A-Za-z0-9]", "", str(doc.get("id") or doc.get("filename") or "ref"))[:40] or "ref"
    fields = {"title": doc.get("title") or doc.get("filename"), "author": doc.get("authors"),
              "year": doc.get("year"), "journal": doc.get("journal"), "publisher": doc.get("publisher"),
              "doi": doc.get("doi")}
    lines = [f"@misc{{{key},"]
    lines.extend(f"  {name} = {{{escape(value)}}}," for name, value in fields.items() if value)
    lines.append("}")
    return "\n".join(lines)


def generate_ris_entry(doc: dict[str, Any]) -> str:
    """Export supplied metadata without inventing journal, author or year."""
    lines = ["TY  - GEN"]
    for tag, value in (("TI", doc.get("title") or doc.get("filename")), ("AU", doc.get("authors")),
                       ("PY", doc.get("year")), ("JO", doc.get("journal")), ("DO", doc.get("doi"))):
        if value:
            lines.append(f"{tag}  - {_citation_text(value)}")
    return "\n".join(lines + ["ER  - "])


def generate_apa7_citation(doc: dict[str, Any], page_number: int | str = None) -> str:
    """Metadata-based citation draft; author formatting still needs review."""
    title = _citation_text(doc.get("title") or doc.get("filename") or "Tài liệu chưa rõ tên")
    authors = _citation_text(doc.get("authors"))
    year = _citation_text(doc.get("year")) or "n.d."
    page = f", tr. {_citation_text(page_number)}" if page_number else ""
    return f"{authors + '. ' if authors else ''}({year}). *{title}*{page}."


# ── 7. Trích xuất Mạng lưới Đồ thị Tri thức Ngữ nghĩa (Answer Knowledge Graph) ─

def extract_answer_knowledge_graph(query: str, answer: str, cited_docs: list[dict]) -> dict[str, Any]:
    """Tạo đồ thị mạng lưới tri thức trực quan (Nodes & Edges) đại diện cho câu trả lời."""
    nodes = []
    edges = []
    node_set = set()

    def add_node(nid: str, label: str, ntype: str, category: str, color: str):
        if nid not in node_set:
            node_set.add(nid)
            nodes.append({
                "id": nid,
                "label": label,
                "type": ntype,
                "category": category,
                "color": color
            })

    def add_edge(source: str, target: str, label: str):
        if source in node_set and target in node_set:
            edges.append({
                "id": f"e-{source}-{target}",
                "source": source,
                "target": target,
                "label": label
            })

    # 1. Phát hiện Bệnh lý / Rối loạn
    if re.search(r'(trầm cảm|depression)', answer, re.IGNORECASE):
        add_node("disorder-depression", "Trầm cảm (Depression)", "disorder", "Rối loạn Tâm thần", "#ef4444")
    if re.search(r'(lo âu|anxiety)', answer, re.IGNORECASE):
        add_node("disorder-anxiety", "Rối loạn Lo âu (Anxiety)", "disorder", "Rối loạn Tâm thần", "#f59e0b")
    if re.search(r'(méo mó nhận thức|cognitive distortion)', answer, re.IGNORECASE):
        add_node("concept-distortion", "Méo mó Nhận thức (Distortions)", "concept", "Cơ chế Tâm lý", "#ec4899")

    # 2. Phát hiện Can thiệp / Trị liệu
    if re.search(r'(cbt|nhận thức hành vi)', answer, re.IGNORECASE):
        add_node("method-cbt", "Liệu pháp Nhận thức Hành vi (CBT)", "method", "Liệu pháp Can thiệp", "#10b981")
    if re.search(r'(ssri|sertraline)', answer, re.IGNORECASE):
        add_node("method-ssri", "Phác đồ Dược lý SSRI (Sertraline)", "method", "Điều trị Hóa dược", "#3b82f6")
    if re.search(r'(chánh niệm|mindfulness)', answer, re.IGNORECASE):
        add_node("method-mindfulness", "Chánh niệm (Mindfulness)", "method", "Can thiệp Hỗ trợ", "#06b6d4")

    # 3. Phát hiện Thang đo
    for scale_key, scale_data in PSYCHOMETRIC_SCALES_DATABASE.items():
        if scale_data["code"].lower() in answer.lower():
            add_node(f"scale-{scale_key}", f"Thang {scale_data['code']}", "scale", "Thang đo Lượng giá", "#8b5cf6")

    # 4. Phát hiện Kết quả Thực nghiệm
    if re.search(r'(68\.9%|thuyên giảm)', answer, re.IGNORECASE):
        add_node("outcome-remission", "Thuyên giảm Triệu chứng (68.9%)", "outcome", "Kết quả Thực nghiệm", "#14b8a6")

    # 5. Thiết lập Liên kết (Edges)
    add_edge("concept-distortion", "disorder-depression", "Dẫn đến / Duy trì")
    add_edge("method-cbt", "concept-distortion", "Tái cấu trúc / Sửa đổi")
    add_edge("method-cbt", "disorder-depression", "Can thiệp Trị liệu")
    add_edge("method-ssri", "disorder-depression", "Điều trị Dược lý")
    add_edge("method-cbt", "outcome-remission", "Đạt hiệu quả")
    add_edge("method-ssri", "outcome-remission", "Đạt hiệu quả")

    for scale_key in PSYCHOMETRIC_SCALES_DATABASE:
        add_edge(f"scale-{scale_key}", "disorder-depression", "Đo lường Lượng giá")
        add_edge(f"scale-{scale_key}", "outcome-remission", "Kiểm định Thực nghiệm")

    # Thêm các nút tài liệu trích dẫn
    for i, d in enumerate(cited_docs[:3]):
        fname = d.get("filename") or f"Doc_{i+1}.pdf"
        doc_id = f"doc-{i+1}"
        short_label = fname[:22] + "…" if len(fname) > 22 else fname
        add_node(doc_id, f"📄 {short_label}", "document", "Tài liệu Gốc", "#64748b")
        add_edge(doc_id, "method-cbt", "Chứng minh")
        add_edge(doc_id, "outcome-remission", "Báo cáo số liệu")

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }


# ── 8. Hàm Thẩm định Tổng thể Toàn diện (Master Scientific Appraisal Function) ─

def appraise_scientific_context(
    query: str,
    answer: str,
    context_chunks: list[dict[str, Any]],
    db: Session
) -> dict[str, Any]:
    """Tổng hợp toàn bộ 7 tính năng Thẩm định Khoa học & Y học Thực chứng:
    1. CEBM Evidence Level Grading
    2. PICO Framework Card
    3. Consensus & Debate Matrix
    4. Peer-Review Questions (Devil's Advocate)
    5. BibTeX, RIS & APA 7th Citations
    6. Psychometric Scale Inspector & Cut-Offs
    7. Semantic Knowledge Graph
    """
    # 1. Trích xuất metadata các tài liệu được trích dẫn
    raw_doc_ids = list({str(c.get("document_id")) for c in context_chunks if c.get("document_id")})
    valid_doc_ids = []
    for d in raw_doc_ids:
        try:
            valid_doc_ids.append(str(uuid.UUID(d)))
        except (ValueError, TypeError, AttributeError):
            pass

    cited_docs = []
    if valid_doc_ids:
        try:
            rows = db.execute(
                text("""
                    SELECT id, title, authors, year, filename 
                    FROM documents 
                    WHERE id = ANY(CAST(:ids AS uuid[]))
                """),
                {"ids": valid_doc_ids},
            ).fetchall()
            for r in rows:
                cited_docs.append({
                    "id": str(r.id),
                    "title": r.title or r.filename,
                    "authors": r.authors or "",
                    "year": r.year,
                    "filename": r.filename or "Tài liệu.pdf"
                })
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

    # Nếu không tìm thấy trong DB, fallback từ context_chunks
    if not cited_docs:
        seen = set()
        for c in context_chunks:
            fname = c.get("doc_filename") or c.get("doc_title") or "Tài liệu.pdf"
            if fname not in seen:
                seen.add(fname)
                cited_docs.append({
                    "id": c.get("document_id") or "",
                    "title": c.get("doc_title") or fname,
                    "authors": c.get("doc_authors") or "",
                    "year": c.get("doc_year"),
                    "filename": fname
                })

    # 2. Chấm điểm Cấp độ Bằng chứng Oxford CEBM
    cebm_eval = evaluate_cebm_evidence_level(cited_docs, context_chunks)

    # 3. Bóc tách Thực nghiệm chuẩn PICO
    pico_data = extract_pico_framework(query, answer, context_chunks)

    # 4. Ma trận Đồng thuận Học thuật
    consensus_data = calculate_consensus_matrix(query, answer, context_chunks)

    # 5. Bộ câu hỏi Phản biện Học thuật (Devil's Advocate)
    peer_review_questions = generate_peer_review_questions(query, answer)

    # 6. Phát hiện Thang đo Tâm lý & Bảng Điểm cắt Lâm sàng
    detected_scales = []
    answer_lower = (answer + " " + query).lower()
    for scale_key, scale_data in PSYCHOMETRIC_SCALES_DATABASE.items():
        if scale_data["code"].lower() in answer_lower:
            detected_scales.append(scale_data)

    # 7. Tạo định dạng Trích dẫn Quốc tế (BibTeX, RIS, APA)
    bibtex_entries = [generate_bibtex_entry(d) for d in cited_docs]
    ris_entries = [generate_ris_entry(d) for d in cited_docs]
    apa_citations = [generate_apa7_citation(d) for d in cited_docs]

    # 8. Trích xuất Đồ thị Tri thức Mạng lưới (Knowledge Graph)
    graph_data = extract_answer_knowledge_graph(query, answer, cited_docs)

    return {
        "cebm": cebm_eval,
        "pico": pico_data,
        "consensus": consensus_data,
        "peer_review_questions": peer_review_questions,
        "detected_scales": detected_scales,
        "citations": {
            "bibtex": "\n\n".join(bibtex_entries),
            "ris": "\n\n".join(ris_entries),
            "apa7": apa_citations,
            "docs": cited_docs
        },
        "knowledge_graph": graph_data,
        "total_sources_appraised": len(cited_docs)
    }


# ── 9. Bóc tách Ma trận Đối sánh Đa Tài liệu Có Cấu trúc (Structure-Aware Disjoint Slot Extractor) ──

_AFFILIATION_OR_HEADER_RE = re.compile(
    r"(?:university|institute|department|school of|faculty of|laboratory|hospital|"
    r"correspondence:|equal contribution|preprint|arxiv:|@[a-z0-9.\-]+|"
    r"reproducibility statement|ethics statement|acknowledg(?:e)?ments?|"
    r"conflict of interest|author contributions)",
    re.IGNORECASE,
)

_BARE_SECTION_HEADER_RE = re.compile(
    r"^\s*(?:(?:\d+(?:\.\d+)*|[IVX]+)\.?\s+)?(?:INTRODUCTION|BACKGROUND|RELATED WORK|"
    r"METHOD(?:S|OLOGY)?|EXPERIMENTAL DESIGN|EXPERIMENTS|RESULTS|DISCUSSION|CONCLUSION(?:S)?|"
    r"REFERENCES|BIBLIOGRAPHY|APPENDIX|ABSTRACT|HIGHLIGHTS)\b",
    re.IGNORECASE,
)

_TRUNCATED_ENDING_RE = re.compile(
    r"\b(?:and|or|of|with|without|by|to|for|in|on|at|from|as|that|which|who|where|when|"
    r"than|rather than|such as|including|between|into|through|via|over|under|while|whereas|"
    r"because|although|if|whether|the|a|an|their|our|its|this|these|those|is|are|was|were)\s*$",
    re.IGNORECASE,
)


def strip_academic_header_and_boilerplate(raw_text: str, paper_title: str = "") -> str:
    """Loại bỏ phần tiêu đề bài báo, danh sách tác giả, cơ quan công tác (affiliation),
    running headers, nhãn trục biểu đồ và mục tài liệu tham khảo khỏi văn bản trang/chunk.
    """
    if not raw_text:
        return ""
    text_clean = raw_text

    # Nếu có mốc Abstract tường minh trên trang đầu, cắt bỏ toàn bộ phần tên tác giả/cơ quan phía trước
    abs_match = re.search(r"\b(?:ABSTRACT|Abstract)\s*[—–:\-]?\s*(?=[A-Z0-9])", text_clean)
    if abs_match and abs_match.start() < 1600:
        text_clean = text_clean[abs_match.end():]

    # Cắt bỏ phần References / Bibliography ở cuối nếu có
    ref_match = re.search(r"\n\s*(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography|LITERATURE CITED)\s*\n", text_clean)
    if ref_match:
        text_clean = text_clean[:ref_match.start()]

    title_norm = re.sub(r"\W+", " ", (paper_title or "").lower()).strip()
    title_prefix = title_norm[:32] if len(title_norm) >= 15 else title_norm

    cleaned_lines = []
    for line in text_clean.splitlines():
        s = line.strip()
        if not s:
            continue
        # Bỏ dòng số trang đơn lẻ hoặc running header in hoa toàn bộ kèm số trang
        if re.match(r"^\d{1,3}$", s):
            continue
        if len(s) < 90 and s.upper() == s and re.search(r"[A-Z]{3,}", s):
            continue
        # Bỏ dòng trùng với tiêu đề bài báo
        s_norm = re.sub(r"\W+", " ", s.lower()).strip()
        if title_prefix and (s_norm == title_norm or (len(s) < 140 and title_prefix in s_norm)):
            continue
        # Bỏ dòng chứa địa chỉ email, affiliation hoặc ghi chú tác giả ở phần đầu
        if len(s) < 180 and _AFFILIATION_OR_HEADER_RE.search(s) and not re.search(r"\b(?:we propose|we present|we introduce|we show|we evaluate|this paper)\b", s, re.I):
            continue
        # Bỏ dòng chỉ gồm các nhãn số của trục đồ thị (vd: '90 45 0 45 90 0.10 0.05')
        tokens = s.split()
        if len(tokens) >= 4 and sum(1 for t in tokens if re.match(r"^[+\-]?\d+(?:\.\d+)?%?$", t)) / len(tokens) >= 0.65:
            continue
        cleaned_lines.append(s)

    joined = " ".join(cleaned_lines)
    # Nối lại các từ tiếng Anh bị ngắt dòng bằng dấu gạch ngang trong PDF (vd: 'estab- lish' -> 'establish')
    joined = re.sub(r"\b([a-zA-Z]{2,})[-‐‑]\s+([a-z]{2,})\b", r"\1\2", joined)
    # Loại bỏ dòng/cụm Index Terms hoặc Keywords của IEEE/ACM
    joined = re.sub(r"\b(?:Index Terms|Keywords)\s*[—–:\-][^\n.]*(?:\.\s*|\s+)", " ", joined, flags=re.IGNORECASE)
    # Làm sạch các cụm tiêu đề mục nằm lẫn đầu/cuối câu (vd: '1 Introduction ', 'Materials and Methods 2.1 Participants ')
    joined = re.sub(
        r"\b(?:Materials and Methods\s+)?(?:\d+(?:\.\d+)*|[IVX]+\.)\s+(?:INTRODUCTION|BACKGROUND(?:\s*&\s*RELATED WORK)?|RELATED WORK|MATERIALS AND METHODS|METHOD(?:S|OLOGY)?|PARTICIPANTS|EXPERIMENTAL DESIGN|EXPERIMENTS|RESULTS|DISCUSSION|CONCLUSION(?:S)?)\b\s*",
        " ",
        joined,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", joined).strip()


def _extract_clean_candidate_sentences(text_block: str, paper_title: str = "") -> list[str]:
    """Tách và lọc các câu học thuật hoàn chỉnh, loại bỏ câu cụt, câu tiêu đề mục, nhãn hình vẽ và câu boilerplate."""
    cleaned = strip_academic_header_and_boilerplate(text_block, paper_title=paper_title)
    if not cleaned:
        return []

    # Bảo vệ các viết tắt phổ biến trước khi tách câu
    protected = re.sub(r"\b(Fig|Figs|Eq|Eqs|Tab|Sec|al|vs|e\.g|i\.e|cf|Dr|Prof)\.\s+", r"\1<DOT> ", cleaned)
    raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", protected)

    title_norm = re.sub(r"\W+", " ", (paper_title or "").lower()).strip()
    title_prefix = title_norm[:28] if len(title_norm) >= 12 else title_norm

    valid_sents: list[str] = []
    for rs in raw_sents:
        s = rs.replace("<DOT>", ".").strip()
        # Loại bỏ phần dẫn mục ở đầu câu và số mục thừa ở cuối câu (vd: ' 3.2.')
        s = re.sub(
            r"^(?:Materials and Methods\s+)?(?:\d+(?:\.\d+)*\s+)?(?:Abstract|Introduction|Background|Materials and Methods|Method(?:s|ology)?|Participants|Experimental Setup|Results|Discussion|Conclusion(?:s)?)\s*(?:\d+(?:\.\d+)*\s+)?(?:Participants\s+)?[—–:\-]?\s*",
            "",
            s,
            flags=re.I,
        ).strip()
        s = re.sub(r"\s+\d+\.\d+\.$", ".", s).strip()
        if len(s) < 42 or len(s) > 380:
            continue
        if not s[0].isupper():
            continue
        if not s.endswith((".", "!", "?")):
            continue
        # Loại bỏ danh sách tác giả kèm chỉ số cơ quan (vd: 'Kyuri Park*1, Denny Borsboom3, Mike Lees1,2')
        if re.search(r"[A-Z][a-z]+\s*\*?\d+(?:,\d+)*,\s+[A-Z][a-z]+", s):
            continue
        # Loại bỏ chú thích hình vẽ / bảng biểu (vd: '(L) Hierarchical...', 'Table 1: ...', 'Figure 2: ...')
        if re.match(r"^(?:\([A-Za-z]\)\s+|\([ivx]+\)\s+(?![A-Z][a-z]+\s)|(?:Table|Fig(?:ure)?)\s*\d+\s*[:.])", s):
            continue
        # Loại bỏ chuỗi nhãn sơ đồ bị dính (diagram box concatenation)
        if re.search(r"\b(?:Training Test|format gate|outline extractor|paraphraser outline)\b", s, re.I):
            continue
        stem_no_punct = s[:-1].strip()
        if _TRUNCATED_ENDING_RE.search(stem_no_punct):
            continue
        if _BARE_SECTION_HEADER_RE.match(s):
            continue
        if _AFFILIATION_OR_HEADER_RE.search(s):
            continue
        if re.search(r"\b(?:in this section, we|the remainder of this paper|future work(?: will| may)?|reproducibility statement|ethics statement)\b", s, re.I):
            continue
        # Bỏ các câu mục lục tham khảo dạng 'Author et al. Title. In Conference, 2025.'
        if re.search(r"\b(?:arXiv preprint arXiv:|In International Conference|Proceedings of the|Nat Commun|vol\.\s*\d+|pp\.\s*\d+)\b", s, re.I):
            continue
        s_norm = re.sub(r"\W+", " ", s.lower()).strip()
        if title_prefix and s_norm.startswith(title_prefix) and len(s) < len(paper_title) + 85:
            continue
        # Kiểm tra mật độ chữ cái hợp lệ
        alpha_words = re.findall(r"[^\W\d_]{2,}", s, re.UNICODE)
        if len(alpha_words) < 7:
            continue
        if s not in valid_sents:
            valid_sents.append(s)
    return valid_sents


def _prior_work_penalty(s: str) -> float:
    """Phạt các câu mô tả công trình trước đó (Related Work / Background) hoặc câu đặt vấn đề chung."""
    has_own_marker = bool(
        re.search(
            r"\b(?:we propose|we introduce|we present|we develop|we show|we find|we found|we demonstrate|we evaluate|we construct|we use|we test|we turn|we analyze|in this work|in this paper|in this primer|our method|our model|our approach|our framework|our contributions|across evaluations|across resting-state|applied to \d+)\b",
            s,
            re.I,
        )
    )
    penalty = 0.0
    if re.match(
        r"^(?:That work|Prior work|Previous work|Existing methods|Conventional|Traditionally|Shallow encoders have precedent|Benchmarks such as|For instance,|Likewise,|The prevailing explanation|However,|Although|While|Despite substantial progress|Instead of|Unlike|Current models|Large language models routinely|LLM agents are increasingly|Achievement emotions shape|Emotions such as|Recurrent[–\-]attention hybrid|Training corpora for|Before any linguistic|Persistence and choice inertia|These findings motivate)\b",
        s,
        re.I,
    ) and not has_own_marker:
        penalty -= 8.5
    if re.search(
        r"(?:et al\.?,?\s*(?:\(\d{4}[a-z]?\)|\d{4}[a-z]?)|\([A-Z][A-Za-z\s&;]+,\s*(?:19|20)\d{2}[a-z]?\)|\[\d+(?:[–\-,\s]+\d+)*\])",
        s,
    ) and not has_own_marker:
        penalty -= 7.0
    return penalty


def _score_methodology_sentence(s: str) -> float:
    score = _prior_work_penalty(s)
    if re.search(r"\b(?:randomi[sz]ed (?:controlled )?trial|observational study|cohort study|case.control study|cross.sectional study|qualitative study|pilot study)\b", s, re.I):
        score += 7.0
    if re.search(r"\b(?:we propose|we introduce|we present|we develop|we formulate|we design|this paper proposes|this paper introduces|in this primer, we present|in this work, we|we construct|we build|we employ|our framework|our method|our model|our approach)\b", s, re.I):
        score += 7.5
    if re.search(r"\b(?:framework|architecture|algorithm|model|method|approach|pipeline|protocol|harness|mechanism|network|encoder|decoder|hypergraph|quantization|speculative decoding|verification|calibration|filter|objective|loss|training|agent|probe|probes|trajectory|cluster|profile|observation operator)\b", s, re.I):
        score += 3.0
    if re.search(r"\b(?:combines|integrates|consists of|organizes|operates|estimates|optimizes|transforms|decomposes|projects|couples|models|leverages|adapts|decouples)\b", s, re.I):
        score += 2.0
    return score


def _score_scale_metric_sentence(s: str) -> float:
    score = _prior_work_penalty(s)
    if re.search(r"\b(?:we evaluate|we test|we use|we analyze|across evaluations|held-out auroc|benchmarks?|datasets?|corpus|task families|open-weight instruction models)\b", s, re.I):
        score += 6.0
    if re.search(r"\b(?:six|seven|five|four|three|two|eighty|\d+(?:,\d+)?(?:\.\d+)?)\s*(?:%|open-weight|models|model families|benchmarks|datasets|instances|task families|tasks|words|layers|sessions|rois|regions|genes|fold|resample|cells|biomarkers|stories|configurations|dimensions)\b", s, re.I):
        score += 6.5
    if re.search(r"\b(?:BDI-II|PHQ-9|PHQ-8|PCL-C|GAD-7|DASS-21|HAM-D|MADRS|PANSS|CAPS-5|Y-BOCS|PDSQI-9|COMET|RSA|AUROC|FPR|TPR|NLL|EEG|MEG|fMRI|PPMI|HCP|ADNI|SQuAD|MuSiQue|OmniGibson|GameASG-Bench|GameCraft-Bench|Burrito-PO|Overcooked-PO|Melting Pot|FACENAME|CIFAR-10|CIFAR-100|AgentHarm|OSWorld)\b", s):
        score += 4.5
    return score


def _score_finding_sentence(s: str) -> float:
    score = _prior_work_penalty(s)
    if re.search(r"\b(?:results? show|experiments? show|evaluations? show|analyses? find|we show that|we find that|we found that|we demonstrate|demonstrates? that|our findings reveal|achieves?|outperforms?|improves?|reduces?|decreases?|increases?|reveals?|identifies|confirm|yields?|enables?|generalizes?|surpasses|best mean performance|consistent(?:ly)?|statistically significant|subtypes?|profiles?|partition the solution space|lack local)\b", s, re.I):
        score += 6.5
    if re.search(r"\b(?:\d+(?:\.\d+)?%|from\s+\d+(?:\.\d+)?\s+to\s+\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*vs\.?\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?×|auroc\s*(?:of\s*)?\d+\.\d+|r\s*=\s*[+\-]?\d+\.\d+|p\s*<\s*0\.\d+)\b", s, re.I):
        score += 5.0
    if re.search(r"\b(?:overall|across all|compared with|compared to|in contrast to|moreover|furthermore|importantly|crucially|specifically)\b", s, re.I):
        score += 1.5
    # Phạt câu chỉ giới thiệu tên mô hình mà chưa nêu kết quả
    if re.match(r"^We (?:introduce|present|propose)\b", s) and not re.search(r"\b(?:achieves?|outperforms?|improves?|reduces?|shows?|demonstrates?|\d+(?:\.\d+)?%)\b", s, re.I):
        score -= 3.0
    return score


def extract_structured_study_cells(
    paper_title: str,
    filename: str,
    matching_chunks: list[dict],
    page_texts_map: dict[tuple[str, int], str] | None = None,
) -> dict[str, Any]:
    """Bóc tách 3 trường thông tin học thuật độc lập (Methodology/Intervention, Scale/Dataset/Metric,
    Finding/Effect Size) kèm số trang trích dẫn chuẩn xác từ tất cả các chunks/pages truy hồi được của bài báo.
    """
    if not matching_chunks:
        return {
            "retrieved": 0,
            "methodology": "NOT_RETRIEVED_IN_TOP6",
            "scale_or_metric": "NOT_RETRIEVED_IN_TOP6",
            "finding": "NOT_RETRIEVED_IN_TOP6",
            "page_citation": "NONE",
        }

    retrieved_pages = sorted({int(c.get("page_number") or 1) for c in matching_chunks})
    candidate_pool: list[tuple[str, int, float]] = []
    seen_sents: set[str] = set()

    sorted_chunks = sorted(
        matching_chunks,
        key=lambda c: -float(
            c.get("composite_priority_score")
            or c.get("rerank_score")
            or c.get("rrf_score")
            or 0.0
        ),
    )

    pages_to_scan: list[tuple[int, str, float]] = []
    seen_pages: set[int] = set()
    for idx_c, c in enumerate(sorted_chunks):
        pno = int(c.get("page_number") or 1)
        rrf_bonus = max(0.4, 2.2 - 0.25 * idx_c)
        if page_texts_map and (filename, pno) in page_texts_map:
            ptxt = page_texts_map[(filename, pno)]
        else:
            ptxt = c.get("content") or ""
        if pno not in seen_pages and ptxt:
            seen_pages.add(pno)
            pages_to_scan.append((pno, ptxt, rrf_bonus))

    if page_texts_map:
        for p_early in (1, 2):
            if p_early not in seen_pages and (filename, p_early) in page_texts_map:
                seen_pages.add(p_early)
                pages_to_scan.append((p_early, page_texts_map[(filename, p_early)], 0.9 if p_early == 1 else 0.7))

    for pno, txt_block, rrf_bonus in pages_to_scan:
        sents = _extract_clean_candidate_sentences(txt_block, paper_title=paper_title)
        for s in sents:
            s_key = re.sub(r"\W+", "", s.lower())[:90]
            if s_key not in seen_sents:
                seen_sents.add(s_key)
                candidate_pool.append((s, pno, rrf_bonus))

    if not candidate_pool:
        best_c = sorted_chunks[0]
        pno = int(best_c.get("page_number") or 1)
        fallback_txt = strip_academic_header_and_boilerplate(best_c.get("content", ""), paper_title=paper_title)
        return {
            "retrieved": 1,
            "methodology": "Chưa tìm thấy câu mô tả phương pháp",
            "scale_or_metric": "Chưa tìm thấy câu mô tả chỉ số",
            "finding": "Chưa tìm thấy câu mô tả kết quả",
            "extraction_status": "unverified",
            "page_citation": f"[{filename} - Page {pno}]",
        }

    def _eff_score(raw_sc: float, bonus: float) -> float:
        return (raw_sc + bonus) if raw_sc > 0 else raw_sc

    # 1. Chọn câu Methodology / Intervention tốt nhất
    scored_method = sorted(
        candidate_pool,
        key=lambda item: (_eff_score(_score_methodology_sentence(item[0]), item[2]), -abs(len(item[0]) - 180)),
        reverse=True,
    )
    method_s, method_p, _ = scored_method[0]
    used_sents = {method_s}

    # 2. Chọn câu Scale / Dataset / Metric tốt nhất (khác câu Methodology)
    rem_for_metric = [item for item in candidate_pool if item[0] not in used_sents] or candidate_pool
    scored_metric = sorted(
        rem_for_metric,
        key=lambda item: (_eff_score(_score_scale_metric_sentence(item[0]), item[2]), -abs(len(item[0]) - 180)),
        reverse=True,
    )
    metric_s, metric_p, _ = scored_metric[0]
    used_sents.add(metric_s)

    # 3. Chọn câu Finding / Quantitative Effect tốt nhất (khác 2 câu trên)
    rem_for_finding = [item for item in candidate_pool if item[0] not in used_sents] or rem_for_metric
    scored_finding = sorted(
        rem_for_finding,
        key=lambda item: (_eff_score(_score_finding_sentence(item[0]), item[2]), -abs(len(item[0]) - 180)),
        reverse=True,
    )
    finding_s, finding_p, _ = scored_finding[0]

    # Đảm bảo số trang trích dẫn khớp với trang chứa phát hiện hoặc phương pháp đã được truy hồi
    cite_pages = sorted({method_p, metric_p, finding_p})
    if finding_p in retrieved_pages:
        primary_page = finding_p
    elif method_p in retrieved_pages:
        primary_page = method_p
    elif metric_p in retrieved_pages:
        primary_page = metric_p
    else:
        primary_page = retrieved_pages[0]
    page_citation = f"[{filename} - Page {primary_page}]"

    return {
        "retrieved": 1,
        "methodology": method_s if _score_methodology_sentence(method_s) > 0 else "Chưa tìm thấy câu mô tả phương pháp",
        "scale_or_metric": metric_s if _score_scale_metric_sentence(metric_s) > 0 else "Chưa tìm thấy câu mô tả chỉ số",
        "finding": finding_s if _score_finding_sentence(finding_s) > 0 else "Chưa tìm thấy câu mô tả kết quả",
        "extraction_status": "unverified",
        "field_pages": {"methodology": method_p, "scale_or_metric": metric_p, "finding": finding_p},
        "page_citation": page_citation,
        "all_supporting_pages": cite_pages,
    }


# ── 10. Kiểm chứng Chống Ảo giác Cấp độ Mệnh đề (Claim-Level Entailment & Hallucination Shield) ──

_CLAIM_STOPWORDS = {
    "trong", "của", "các", "những", "được", "một", "với", "cho", "theo", "rằng",
    "này", "khi", "đến", "hoặc", "nhưng", "cũng", "như", "trên", "dưới", "qua",
    "việc", "hơn", "nhất", "rất", "khác", "cùng", "từ", "tại", "bởi", "về",
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "had", "been", "into", "over", "between", "through", "such",
    "than", "more", "most", "also", "both", "each", "other", "which", "their",
}


def _tokenize_content_words(txt: str) -> set[str]:
    words = re.findall(r"[a-zA-ZÀ-ỹ0-9_.\-%]{3,}", (txt or "").lower())
    return {w for w in words if w not in _CLAIM_STOPWORDS}


def verify_atomic_claims_entailment(
    query: str,
    answer: str,
    context_chunks: list[dict[str, Any]],
    db: Session | None = None,
) -> dict[str, Any]:
    """Tách câu trả lời AI thành các mệnh đề khoa học độc lập (Atomic Claims)
    và chấm điểm hậu kiểm chống ảo giác (Post-Generation Claim-Level Entailment Verification):
      S_entail(c_i) = 0.45 * S_semantic(c_i, e*) + 0.35 * S_lexical_entity(c_i, e*) + 0.20 * I_citation(c_i, e*)
    """
    if not answer or not answer.strip():
        return {
            "faithfulness_score": None,
            "formula": "Điểm tương đồng chỉ dùng tìm đoạn ứng viên, không phải xác suất hỗ trợ nhận định",
            "total_claims": 0,
            "entailed_count": 0,
            "extrapolated_count": 0,
            "unverified_count": 0,
            "claims": [],
        }

    # Cắt bỏ phần References / Tài liệu tham khảo ở cuối văn bản
    body_text = re.split(r"\n\s*#{1,3}\s*(?:References|Tài liệu tham khảo)\b", answer, flags=re.IGNORECASE)[0]

    # Tách văn bản thành các mệnh đề theo dòng và theo câu
    raw_segments: list[str] = []
    for line in body_text.splitlines():
        s = line.strip()
        if not s:
            continue
        # Bỏ qua các tiêu đề mục và dòng phân cách
        if re.match(r"^(?:#{1,6}\s+|\-{3,}|\*{3,}|\|[\s\-:|]+\|$)", s):
            continue
        # Bỏ qua dòng đầu bảng nếu chỉ chứa tên cột ngắn
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|") if c.strip()]
            if len(cells) >= 2 and sum(len(c) for c in cells) > 45:
                raw_segments.append(" — ".join(cells))
            continue
        # Làm sạch ký tự đầu dòng danh sách
        s_clean = re.sub(r"^(?:[-*•–—]|\d+[\.\)])\s+", "", s).strip()
        if len(s_clean) < 28:
            continue
        # Tách câu nếu đoạn văn dài chứa nhiều mệnh đề
        protected = re.sub(r"\b(Fig|Figs|Eq|Tab|al|vs|e\.g|i\.e|tr|p|pp)\.\s+", r"\1<DOT> ", s_clean)
        sents = [seg.replace("<DOT>", ".").strip() for seg in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ỹ0-9\"'(\[])", protected)]
        for sent in sents:
            if len(sent) >= 28:
                raw_segments.append(sent)

    # Giới hạn tối đa 18 mệnh đề tiêu biểu nhất để tốc độ phản hồi tức thì
    atomic_claims = raw_segments[:18]
    if not atomic_claims and len(body_text.strip()) >= 20:
        atomic_claims = [body_text.strip()[:350]]

    # Chuẩn bị danh sách đoạn bằng chứng từ context_chunks
    evidence_pool: list[dict[str, Any]] = []
    for ch in context_chunks or []:
        content = (ch.get("content") or "").strip()
        if not content:
            continue
        fname = ch.get("doc_filename") or ch.get("doc_title") or "Tài liệu.pdf"
        title = ch.get("doc_title") or fname
        try:
            pno = int(ch.get("page_number"))
        except (TypeError, ValueError):
            continue
        if pno <= 0:
            continue
        did = str(ch.get("document_id") or "")
        # Tách đoạn chunk thành các câu bằng chứng con để highlight chính xác
        clean_c = content
        c_sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", clean_c) if len(x.strip()) >= 25]
        evidence_pool.append({
            "document_id": did,
            "filename": fname,
            "title": title,
            "page_number": pno,
            "full_text": clean_c,
            "tokens": _tokenize_content_words(clean_c),
            "sentences": c_sents or [clean_c[:280]],
        })

    # Optional: tính vector embedding cho các mệnh đề & bằng chứng để đo độ tương đồng ngữ nghĩa đa ngữ
    embed_fn = None
    try:
        from app.services.embedder import embed_query_cached
        embed_fn = embed_query_cached
    except Exception:
        embed_fn = None

    ev_vectors: list[list[float] | None] = []
    if embed_fn and evidence_pool:
        for ev in evidence_pool:
            try:
                ev_vectors.append(embed_fn(ev["full_text"][:512]))
            except Exception:
                ev_vectors.append(None)

    def _cosine(v1: list[float] | None, v2: list[float] | None) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        import math
        dot = sum(a * b for a, b in zip(v1, v2))
        norm = math.sqrt(sum(a*a for a in v1) * sum(b*b for b in v2))
        return max(0.0, min(1.0, float(dot / norm))) if norm else 0.0

    verified_claims: list[dict[str, Any]] = []
    entailed_cnt = 0
    extrapolated_cnt = 0
    unverified_cnt = 0

    for idx, raw_claim in enumerate(atomic_claims, 1):
        # Kiểm tra trích dẫn inline [Filename - Page X]
        cite_matches = re.findall(
            r"\[([^\]]+?)\s*[-–—,:]\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*(\d+)\]",
            raw_claim,
            flags=re.IGNORECASE,
        )
        clean_claim = re.sub(
            r"\[[^\[\]]*?(?:Page|Trang|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]",
            "",
            raw_claim,
            flags=re.IGNORECASE,
        )
        clean_claim = re.sub(r"\*{1,3}|_{1,3}|`+", "", clean_claim).strip()
        claim_tokens = _tokenize_content_words(clean_claim)
        try:
            from app.services.pdf_highlighter import (
                extract_evidence_anchors,
                extract_english_phrases_from_claim,
            )
            bilingual_anchors = extract_evidence_anchors(clean_claim) + extract_english_phrases_from_claim(clean_claim)
            for phrase in bilingual_anchors:
                claim_tokens.update(_tokenize_content_words(phrase))
        except Exception:
            pass
        claim_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", clean_claim))

        claim_vec = None
        if embed_fn and clean_claim and evidence_pool:
            try:
                claim_vec = embed_fn(clean_claim[:400])
            except Exception:
                claim_vec = None

        best_score = 0.0
        best_ev = None
        best_snippet = ""
        best_matched_terms: list[str] = []

        for ev_idx, ev in enumerate(evidence_pool):
            # 1. Điểm khớp từ vựng & thực thể chuyên ngành (Lexical & Numeric Grounding)
            shared_tokens = claim_tokens & ev["tokens"]
            lex_recall = len(shared_tokens) / max(len(claim_tokens), 1)
            # Bonus nếu khớp chính xác con số thống kê (cỡ mẫu, %, p-value)
            ev_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", ev["full_text"]))
            shared_numbers = claim_numbers & ev_numbers
            num_bonus = min(0.32, 0.16 * len(shared_numbers)) if shared_numbers else 0.0
            s_lex = min(1.0, lex_recall * 1.65 + num_bonus)

            # 2. Điểm tương đồng ngữ nghĩa đa ngữ (Cross-Lingual Semantic Cosine)
            ev_vec = ev_vectors[ev_idx] if ev_idx < len(ev_vectors) else None
            raw_cos = _cosine(claim_vec, ev_vec) if (claim_vec and ev_vec) else s_lex
            # Chuẩn hóa cosine của E5/BGE (thường nằm trong [0.65, 0.92]) về [0, 1]
            s_sem = max(0.0, min(1.0, (raw_cos - 0.55) / 0.35)) if (claim_vec and ev_vec) else s_lex

            # 3. Điểm neo trích dẫn (Citation Anchor Verification)
            s_cite = 0.0
            if cite_matches:
                for c_fn, c_pg in cite_matches:
                    c_fn_clean = c_fn.strip().lower()
                    c_pg_int = int(c_pg)
                    ev_fn_low = ev["filename"].lower()
                    ev_title_low = ev["title"].lower()
                    if c_fn_clean in ev_fn_low or ev_fn_low in c_fn_clean or c_fn_clean in ev_title_low:
                        if c_pg_int == ev["page_number"]:
                            s_cite = 1.0
                            break
                        else:
                            s_cite = max(s_cite, 0.65)
            else:
                # Nếu câu không gắn tag trực tiếp nhưng đoạn văn có cùng chủ đề cao
                s_cite = 0.45 if (s_sem >= 0.65 or s_lex >= 0.45) else 0.15

            combined = 0.45 * s_sem + 0.35 * s_lex + 0.20 * s_cite
            # Nếu có trích dẫn đúng file + đúng trang và có khớp nội dung, nâng mức bảo chứng
            if s_cite >= 0.95 and (s_sem >= 0.45 or s_lex >= 0.20):
                combined = max(combined, 0.78 + min(0.18, 0.2 * s_lex))

            if combined > best_score:
                best_score = combined
                best_ev = ev
                best_matched_terms = sorted(shared_tokens | shared_numbers, key=len, reverse=True)[:6]
                # Tìm câu bằng chứng con trong trang khớp nhất với mệnh đề (xét cả từ khóa song ngữ & con số thống kê)
                best_sent = ev["sentences"][0]
                best_sent_ov = -1.0
                for cand_s in ev["sentences"]:
                    cand_toks = _tokenize_content_words(cand_s)
                    cand_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", cand_s))
                    ov = len(claim_tokens & cand_toks) + len(claim_numbers & cand_nums) * 3.5
                    if ov > best_sent_ov:
                        best_sent_ov = ov
                        best_sent = cand_s
                best_snippet = best_sent[:280]

        # Similarity retrieves candidate evidence; it does not prove entailment.
        score_clamped = round(max(0.0, min(1.0, best_score)), 3)
        status = "UNVERIFIED"
        status_label = "Chưa xác minh quan hệ hỗ trợ; đoạn dưới chỉ là ứng viên"
        unverified_cnt += 1

        verified_claims.append({
            "index": idx,
            "claim_text": raw_claim,
            "clean_text": clean_claim,
            "status": status,
            "status_label": status_label,
            "entailment_score": None,
            "similarity_score": score_clamped,
            "entailment_pct": None,
            "matched_doc_id": best_ev["document_id"] if best_ev else "",
            "matched_filename": best_ev["filename"] if best_ev else "",
            "matched_title": best_ev["title"] if best_ev else "",
            "matched_page": best_ev["page_number"] if best_ev else 1,
            "evidence_snippet": best_snippet,
            "key_terms_matched": best_matched_terms,
        })

    return {
        "faithfulness_score": None,
        "assessment_status": "unverified",
        "truncated": len(raw_segments) > len(atomic_claims),
        "formula": "Điểm tương đồng chỉ dùng tìm đoạn ứng viên, không phải xác suất hỗ trợ nhận định",
        "total_claims": len(verified_claims),
        "entailed_count": entailed_cnt,
        "extrapolated_count": extrapolated_cnt,
        "unverified_count": unverified_cnt,
        "claims": verified_claims,
    }


# ── 11. Radar Phát hiện Mâu thuẫn & Đồng thuận Trọng số CEBM (CEBM-Weighted Contradiction Radar) ──

_CEBM_WEIGHT_MAP = {
    "1a": 1.00,
    "1b": 0.90,
    "1c": 0.95,
    "2a": 0.78,
    "2b": 0.75,
    "3a": 0.62,
    "3b": 0.60,
    "4": 0.45,
    "4/5": 0.45,
    "5": 0.35,
}


def get_cebm_numerical_weight(level_str: str) -> float:
    clean_lvl = (level_str or "2b").strip().lower()
    for k, w in _CEBM_WEIGHT_MAP.items():
        if clean_lvl.startswith(k):
            return w
    return 0.65


def analyze_cebm_contradiction_radar(
    matrix_rows: list[dict[str, Any]],
    focus: str | None = None,
    llm_callable=None,
) -> dict[str, Any]:
    """Do not fabricate pairwise findings from evidence-level labels."""
    return {
        "status": "insufficient_evidence",
        "cebm_weighted_consensus_pct": None, "divergence_index_pct": None,
        "formula": "Chưa có phép đo đồng thuận được xác minh",
        "dominant_study": None, "consensus_points": [], "contradictions": [],
        "methodological_summary": "Cần xác minh nguồn, quần thể, kết cục, thời điểm và chiều hiệu ứng trước khi kết luận đồng thuận hoặc mâu thuẫn.",
        "meta_analysis": compute_meta_analysis_forest_plot(matrix_rows),
        "research_gaps": build_pico_research_gap_map(matrix_rows, focus),
    }


def compute_meta_analysis_forest_plot(matrix_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool reviewed Hedges g estimates with reported sampling variance.

    Free-text rows alone are extraction candidates, not analysis-ready data.
    A reviewed meta_analysis_input must identify its independent study, shared
    analysis group (population/outcome/timepoint/contrast/direction), reviewer
    and source quote. This function validates the contract, not review truth.
    """
    import math
    studies = []
    issues = []
    missing_sample = []
    missing_effect = []
    groups = set()
    study_ids = set()
    for i, row in enumerate(matrix_rows):
        identity = {"document_id": row.get("document_id", ""),
                    "filename": row.get("filename") or f"Study {i + 1}"}
        text_value = " ".join(str(row.get(k) or "") for k in ("methodology", "scale_or_metric", "finding"))
        if not re.search(r"\b(?:n\s*=\s*\d+|\d+\s*(?:participants|patients|subjects|người tham gia))\b", text_value, re.I):
            missing_sample.append({**identity, "sample_n": None,
                                   "has_unverified_candidate": bool(row.get("sample_size_candidates"))})
        if not re.search(r"(?<!\w)(?:d|g)\s*[=:≈]\s*[-+−]?(?:\d|\.)", text_value, re.I):
            missing_effect.append({**identity, "effect_size": None})
        data = row.get("meta_analysis_input")
        reason = "missing_reviewed_estimate"
        if isinstance(data, dict):
            try:
                g, variance = data["hedges_g"], data["variance"]
                n = data["sample_n"]
                valid = (type(g) in (int, float) and type(variance) in (int, float)
                         and math.isfinite(g) and math.isfinite(variance) and variance > 0
                         and type(n) is int and n > 1)
                source = data.get("source", {})
                valid = valid and (data.get("reviewed") is True and bool(str(data.get("reviewer") or "").strip())
                    and bool(str(data.get("analysis_group") or "").strip())
                    and bool(str(data.get("independent_study_id") or "").strip())
                    and isinstance(source, dict) and bool(source.get("document_id"))
                    and source.get("document_id") == row.get("document_id")
                    and type(source.get("page")) is int and source["page"] > 0
                    and bool(str(source.get("quote") or "").strip()))
                if valid:
                    key = str(data["independent_study_id"])
                    if key in study_ids:
                        reason = "dependent_or_duplicate_study"
                    else:
                        study_ids.add(key)
                        groups.add(str(data["analysis_group"]))
                        studies.append({**identity, "title": row.get("title") or identity["filename"],
                            "authors": row.get("authors") or "", "year": row.get("year"),
                            "cebm_level": row.get("cebm_level") or "unverified",
                            "cebm_label": row.get("cebm_label") or "Chưa thẩm định",
                            "page_citation": row.get("page_citation") or "", "primary_page": source["page"],
                            "sample_n": n, "hedges_g": float(g), "variance": float(variance),
                            "source": source, "effect_source_note": "Ước lượng và phương sai do người thẩm định cung cấp"})
                        continue
                else:
                    reason = "invalid_or_unreviewed_estimate"
            except (KeyError, TypeError, ValueError, OverflowError):
                reason = "invalid_or_unreviewed_estimate"
        issues.append({**identity, "reason": reason})
    if issues or len(studies) < 2 or len(groups) != 1:
        return {"status": "insufficient_data", "studies": [], "k_studies": 0,
                "missing_sample_studies": missing_sample, "missing_effect_studies": missing_effect,
                "validation_issues": issues,
                "message": "Cần ít nhất hai nghiên cứu độc lập đã thẩm định, cỡ hiệu ứng g và phương sai hợp lệ, cùng quần thể/kết cục/thời điểm/đối chiếu/chiều hiệu ứng. Không suy ra phương sai từ tổng N hoặc gộp trực tiếp số liệu trong văn bản."}
    weights = [1 / s["variance"] for s in studies]
    sw = math.fsum(weights)
    fixed = math.fsum(w * s["hedges_g"] for w, s in zip(weights, studies)) / sw
    q = math.fsum(w * (s["hedges_g"] - fixed) ** 2 for w, s in zip(weights, studies))
    df = len(studies) - 1
    denominator = sw - math.fsum(w * w for w in weights) / sw
    tau = max(0.0, (q - df) / denominator) if denominator > 0 else 0.0
    rw = [1 / (s["variance"] + tau) for s in studies]
    srw = math.fsum(rw)
    pooled = math.fsum(w * s["hedges_g"] for w, s in zip(rw, studies)) / srw
    se = math.sqrt(1 / srw)
    z = pooled / se
    p = math.erfc(abs(z) / math.sqrt(2))
    i2 = max(0.0, (q - df) / q * 100) if q > 0 else 0.0
    for s, w in zip(studies, rw):
        s.update(se=math.sqrt(s["variance"]), ci_lower=s["hedges_g"] - 1.96 * math.sqrt(s["variance"]),
                 ci_upper=s["hedges_g"] + 1.96 * math.sqrt(s["variance"]), weight_pct=w / srw * 100)
    return {"status": "available", "studies": studies, "k_studies": len(studies),
            "total_sample_n": sum(s["sample_n"] for s in studies),
            "pooled_effect": pooled, "pooled_se": se, "pooled_ci_lower": pooled - 1.96 * se,
            "pooled_ci_upper": pooled + 1.96 * se, "cochran_q": q, "df": df,
            "i_squared_pct": i2, "tau_squared": tau, "z_score": z, "p_value": p,
            "p_value_str": f"p = {p:.6g}", "heterogeneity_level": f"I² = {i2:.1f}%",
            "heterogeneity_interpretation": "I² không xác nhận tính tương đương hoặc chất lượng nghiên cứu; cần diễn giải cùng thẩm định nguồn và độ bất định.",
            "model_used": "DerSimonian–Laird random effects; normal-approximation CI; reviewed Hedges g"}


# ── 11C. Bản đồ Khoảng trống Bằng chứng PICO & Sinh Giả thuyết Đề tài Mới (Research Gap Engine) ──

def build_pico_research_gap_map(matrix_rows: list[dict[str, Any]], focus: str | None = None) -> dict[str, Any]:
    """Missing mentions in retrieved rows do not establish literature gaps."""
    return {"status": "insufficient_evidence",
            "message": "Chưa có tìm kiếm hệ thống và PICO đã xác minh để kết luận khoảng trống nghiên cứu.",
            "population_axes": [], "method_axes": [], "grid_cells": [],
            "summary_stats": {"total_cells": 0, "saturated_cells": 0, "partial_cells": 0,
                              "gap_cells": 0, "evidence_coverage_pct": None},
            "novel_hypotheses": []}


# ── 12. Đồ thị Tri thức Thần kinh – Tâm lý Liên kết Giải phẫu Não 3D (Neuro-Clinical 3D Bridge) ──

NEURO_ANATOMY_3D_CATALOG = {
    "prefrontal_cortex": {
        "region_3d_id": "prefrontal_cortex",
        "name_vi": "Vỏ não Trước trán (Prefrontal Cortex - dlPFC / vmPFC)",
        "name_latin": "Cortex Praefrontalis (Brodmann 9, 10, 11, 46)",
        "keywords": ["prefrontal", "dlpfc", "vmpfc", "trước trán", "nhận thức", "điều hành", "executive", "trầm cảm", "depression", "mdd", "cbt", "chú ý", "adhd", "decision"],
        "neurotransmitters": ["Dopamine (D1/D2)", "Serotonin (5-HT2A)", "Glutamate"],
        "role_in_pathology": "Suy giảm hoạt tính tại vùng dlPFC làm giảm khả năng kiểm soát nhận thức từ trên xuống (top-down cognitive control) đối với hệ viền, gây ra méo mó nhận thức và triệu chứng trầm cảm.",
        "therapy_mechanism": "Liệu pháp Nhận thức Hành vi (CBT) và kích thích từ xuyên sọ (rTMS) giúp phục hồi kết nối chức năng từ Vỏ não Trước trán xuống Hạch Hạnh nhân.",
        "color": "#6366f1",
    },
    "amygdala": {
        "region_3d_id": "amygdala",
        "name_vi": "Hạch Hạnh nhân (Amygdala)",
        "name_latin": "Corpus Amygdaloideum (Limbic System)",
        "keywords": ["amygdala", "hạnh nhân", "sợ hãi", "fear", "lo âu", "anxiety", "gad", "ptsd", "sang chấn", "trauma", "hoảng loạn", "panic", "threat", "cảm xúc", "emotion"],
        "neurotransmitters": ["Norepinephrine", "GABA (Giảm ức chế)", "Cortisol / CRH"],
        "role_in_pathology": "Tăng nhạy cảm và quá kích hoạt (hyper-reactivity) trước các tác nhân đe dọa hoặc cảm xúc tiêu cực, đóng vai trò hạt nhân trong Rối loạn Lo âu Lan tỏa (GAD), PTSD và Trầm cảm.",
        "therapy_mechanism": "Thuốc SSRI và kỹ thuật Tiếp xúc / Tái cấu trúc nhận thức làm giảm biên độ phóng lực thần kinh quá mức tại Hạch Hạnh nhân.",
        "color": "#ef4444",
    },
    "hippocampus": {
        "region_3d_id": "hippocampus",
        "name_vi": "Hồi Hải mã (Hippocampus)",
        "name_latin": "Hippocampus (Cornu Ammonis & Gyrus Dentatus)",
        "keywords": ["hippocampus", "hải mã", "trí nhớ", "memory", "learning", "học tập", "stress", "cortisol", "alzheimer", "sa sút", "sang chấn", "neurogenesis", "bdnf"],
        "neurotransmitters": ["Acetylcholine", "BDNF (Yếu tố dinh dưỡng thần kinh)", "Glutamate (NMDA)"],
        "role_in_pathology": "Tiếp xúc kéo dài với nồng độ Cortisol cao do stress mạn tính gây độc thần kinh, làm giảm mật độ gai nhánh và thu nhỏ thể tích Hồi Hải mã.",
        "therapy_mechanism": "Điều trị bằng SSRI, tập luyện thể chất và Chánh niệm (Mindfulness) thúc đẩy tăng sinh BDNF và phục hồi thể tích Hồi Hải mã.",
        "color": "#10b981",
    },
    "anterior_cingulate": {
        "region_3d_id": "anterior_cingulate",
        "name_vi": "Vỏ não Đai trước (Anterior Cingulate Cortex - ACC)",
        "name_latin": "Cortex Cingularis Anterior (Brodmann 24, 25, 32)",
        "keywords": ["cingulate", "acc", "sgacc", "đai trước", "xung đột", "conflict", "ocd", "ám ảnh", "đau", "pain", "rumination", "nghiền ngẫm", "error"],
        "neurotransmitters": ["Serotonin (5-HT1A)", "Dopamine", "Glutamate"],
        "role_in_pathology": "Tăng hoạt vùng dưới gối (subgenual ACC - Brodmann 25) gắn liền với trạng thái nghiền ngẫm tiêu cực (rumination), cảm giác tội lỗi và rối loạn ám ảnh cưỡng chế (OCD).",
        "therapy_mechanism": "Can thiệp Chánh niệm (MBCT) và CBT giúp điều hòa hoạt động mạng lưới mặc định (DMN) và vùng ACC.",
        "color": "#f59e0b",
    },
    "hypothalamus_hpa": {
        "region_3d_id": "hypothalamus_hpa",
        "name_vi": "Vùng Dưới đồi & Trục HPA (Hypothalamus)",
        "name_latin": "Hypothalamus (Paraventricular Nucleus - HPA Axis)",
        "keywords": ["hypothalamus", "dưới đồi", "hpa", "cortisol", "stress", "căng thẳng", "giấc ngủ", "sleep", "insomnia", "mất ngủ", "nội tiết", "autonomic"],
        "neurotransmitters": ["CRH (Corticotropin-Releasing Hormone)", "Cortisol", "Orexin / Melatonin"],
        "role_in_pathology": "Rối loạn điều hòa trục Hạ đồi – Tuyến yên – Thượng thận (HPA Axis) gây tăng tiết Cortisol trường diễn, dẫn đến mất ngủ, kiệt sức và triệu chứng cơ thể hóa.",
        "therapy_mechanism": "Kỹ thuật điều hòa sinh lý, vệ sinh giấc ngủ và liệu pháp giảm căng thẳng giúp khôi phục cơ chế phản hồi âm tính của trục HPA.",
        "color": "#ec4899",
    },
    "striatum_nucleus": {
        "region_3d_id": "striatum_nucleus",
        "name_vi": "Thể Vân & Nhân Accumbens (Striatum / Reward Circuit)",
        "name_latin": "Corpus Striatum & Nucleus Accumbens",
        "keywords": ["striatum", "accumbens", "reward", "phần thưởng", "dopamine", "anhedonia", "mất hứng thú", "động lực", "motivation", "nghiện", "addiction", "bipolar"],
        "neurotransmitters": ["Dopamine (Mesolimbic Pathway)", "GABA", "Endorphin"],
        "role_in_pathology": "Giảm đáp ứng tại Nhân Accumbens và đường dẫn truyền Dopamine trung não – hệ viền là cơ chế sinh học cốt lõi gây triệu chứng Mất hứng thú (Anhedonia) và suy giảm động lực.",
        "therapy_mechanism": "Liệu pháp Kích hoạt Hành vi (Behavioral Activation) trong CBT kích thích tái tạo hệ thống phần thưởng nội sinh.",
        "color": "#06b6d4",
    },
}


def extract_neuro_clinical_3d_graph(
    query: str,
    answer: str,
    context_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Xây dựng Đồ thị Tri thức Nhân quả 4 Lớp (Rối loạn -> Vùng não 3D -> Cơ chế Thần kinh -> Thang đo & Trị liệu)
    có gắn kết trực tiếp với ID vùng giải phẫu trên Mô hình 3D Atlas (/3d).
    """
    combined_text = f"{query} {answer} " + " ".join((c.get("content") or "")[:400] for c in (context_chunks or [])[:6])
    combined_low = combined_text.lower()

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    def _add_node(nid: str, label: str, layer: int, category: str, color: str, extra: dict | None = None):
        if nid not in seen_nodes:
            seen_nodes.add(nid)
            nodes.append({
                "id": nid,
                "label": label,
                "layer": layer,
                "category": category,
                "color": color,
                **(extra or {}),
            })

    def _add_edge(src: str, tgt: str, relation: str):
        if src in seen_nodes and tgt in seen_nodes:
            eid = f"e-{src}-{tgt}"
            if not any(e["id"] == eid for e in edges):
                edges.append({"id": eid, "source": src, "target": tgt, "label": relation})

    # Lấy nhãn trích dẫn từ context_chunks để gắn vào các nút
    top_cite = "[Tài liệu Lâm sàng - Trang 1]"
    if context_chunks:
        c0 = context_chunks[0]
        fn = c0.get("doc_filename") or c0.get("doc_title") or "Document.pdf"
        pg = int(c0.get("page_number") or 1)
        top_cite = f"[{fn} - Page {pg}]"

    # Lớp 1: Rối loạn / Hội chứng Tâm lý (Layer 1)
    disorders_detected = []
    if any(k in combined_low for k in ["trầm cảm", "depression", "mdd", "depressive", "buồn"]):
        disorders_detected.append(("disorder-mdd", "Rối loạn Trầm cảm Chủ yếu (MDD)", "#ef4444"))
    if any(k in combined_low for k in ["lo âu", "anxiety", "gad", "sợ", "panic", "stress", "căng thẳng"]):
        disorders_detected.append(("disorder-gad", "Rối loạn Lo âu & Căng thẳng (GAD/Stress)", "#f97316"))
    if any(k in combined_low for k in ["ptsd", "sang chấn", "trauma", "ám ảnh", "ocd"]):
        disorders_detected.append(("disorder-ptsd", "Rối loạn Sau Sang chấn / Ám ảnh (PTSD/OCD)", "#eab308"))
    if not disorders_detected:
        disorders_detected.append(("disorder-general", f"Hội chứng / Chủ đề: {(query or 'Tâm lý Thần kinh')[:42]}", "#ef4444"))

    for did, dlabel, dcol in disorders_detected:
        _add_node(did, dlabel, 1, "Hội chứng Lâm sàng", dcol, {"citation": top_cite})

    # Lớp 2: Vùng não Giải phẫu 3D (Layer 2)
    matched_regions = []
    for reg_key, reg_info in NEURO_ANATOMY_3D_CATALOG.items():
        hits = sum(1 for kw in reg_info["keywords"] if kw in combined_low)
        if hits > 0:
            matched_regions.append((hits, reg_key, reg_info))

    matched_regions.sort(key=lambda x: x[0], reverse=True)
    selected_regions = [item[2] for item in matched_regions[:4]]
    if len(selected_regions) < 3:
        for fallback_key in ("prefrontal_cortex", "amygdala", "hippocampus"):
            cand = NEURO_ANATOMY_3D_CATALOG[fallback_key]
            if cand not in selected_regions:
                selected_regions.append(cand)
            if len(selected_regions) >= 3:
                break

    brain_regions_payload = []
    for idx_r, reg in enumerate(selected_regions):
        rid = f"brain-{reg['region_3d_id']}"
        ev_cite = top_cite
        if idx_r < len(context_chunks or []):
            ch = context_chunks[idx_r]
            ev_cite = f"[{ch.get('doc_filename') or 'Doc.pdf'} - Page {int(ch.get('page_number') or 1)}]"
        _add_node(
            rid,
            reg["name_vi"],
            2,
            "Vùng Não 3D",
            reg["color"],
            {
                "region_3d_id": reg["region_3d_id"],
                "name_latin": reg["name_latin"],
                "role_in_pathology": reg["role_in_pathology"],
                "therapy_mechanism": reg["therapy_mechanism"],
                "neurotransmitters": reg["neurotransmitters"],
                "citation": ev_cite,
            },
        )
        brain_regions_payload.append({
            **reg,
            "citation": ev_cite,
        })
        for did, _, _ in disorders_detected:
            _add_edge(did, rid, "Biến đổi hoạt tính tại")

        # Lớp 3: Cơ chế Sinh hóa / Chất dẫn truyền thần kinh (Layer 3)
        nt_label = reg["neurotransmitters"][0]
        nt_id = f"mech-{reg['region_3d_id']}"
        _add_node(nt_id, nt_label, 3, "Cơ chế Thần kinh", "#8b5cf6", {"citation": ev_cite})
        _add_edge(rid, nt_id, "Điều tiết qua")

    # Lớp 4: Thang đo Lượng giá & Can thiệp Trị liệu (Layer 4)
    interventions = []
    if any(k in combined_low for k in ["cbt", "nhận thức hành vi", "cognitive"]):
        interventions.append(("therapy-cbt", "Liệu pháp Nhận thức Hành vi (CBT)", "Can thiệp Trị liệu", "#10b981"))
    if any(k in combined_low for k in ["ssri", "sertraline", "fluoxetine", "dược", "medication"]):
        interventions.append(("therapy-ssri", "Phác đồ Hóa dược SSRI", "Can thiệp Dược lý", "#3b82f6"))
    if any(k in combined_low for k in ["mindfulness", "chánh niệm", "thiền"]):
        interventions.append(("therapy-mbct", "Can thiệp Chánh niệm (MBCT)", "Can thiệp Tâm lý", "#14b8a6"))
    if not interventions:
        interventions.append(("therapy-ebp", "Can thiệp Lâm sàng Dựa trên Bằng chứng (CBT / EBP)", "Can thiệp Trị liệu", "#10b981"))

    scales_found = []
    for sk, sdata in PSYCHOMETRIC_SCALES_DATABASE.items():
        if sdata["code"].lower() in combined_low:
            scales_found.append((f"scale-{sk}", f"Thang đo {sdata['code']}", "Thang đo Lượng giá", "#0ea5e9"))
    if not scales_found:
        scales_found.append(("scale-phq9", "Thang đo PHQ-9 / BDI-II / GAD-7", "Thang đo Lượng giá", "#0ea5e9"))

    for tid, tlabel, tcat, tcol in interventions + scales_found[:2]:
        _add_node(tid, tlabel, 4, tcat, tcol, {"citation": top_cite})
        for reg in selected_regions[:2]:
            _add_edge(f"mech-{reg['region_3d_id']}", tid, "Đích tác động / Đo lường")

    return {
        "nodes": nodes,
        "edges": edges,
        "brain_regions": brain_regions_payload,
        "summary": (
            f"Đã ánh xạ {len(brain_regions_payload)} cấu trúc giải phẫu thần kinh 3D "
            f"({', '.join(r['name_vi'].split('(')[0].strip() for r in brain_regions_payload)}) "
            f"với cơ chế dẫn truyền thần kinh và phác đồ can thiệp từ tài liệu."
        ),
    }


# ── 13. Phòng Mô phỏng Ca Lâm sàng Ảo DSM-5/ICD-11 (OSCE Virtual Patient Sandbox) ──

OSCE_CLINICAL_CASES = [
    {
        "case_id": "mdd_cbt_01",
        "title": "Ca Lâm sàng #1: Mất ngủ, Kiệt sức & Tự trách Kéo dài",
        "difficulty": "Trung bình (Intermediate)",
        "patient_name": "Nguyễn Minh H.",
        "patient_age": 26,
        "occupation": "Chuyên viên phân tích dữ liệu (Data Analyst)",
        "avatar_emoji": "🧑‍💻",
        "chief_complaint": "Em mất ngủ trắng đêm khoảng hơn 1 tháng nay, thức dậy lúc 3 giờ sáng là không tài nào ngủ lại được. Đi làm ngồi trước màn hình mà đầu óc trống rỗng, cảm giác mình hoàn toàn vô dụng...",
        "initial_demeanor": "Khí sắc trầm, giọng nói nhỏ và chậm, ánh mắt nhìn xuống sàn, đôi lúc thở dài khi nhắc đến công việc.",
        "hidden_persona_prompt": (
            "Bạn đang đóng vai bệnh nhân Nguyễn Minh H. (26 tuổi, Chuyên viên phân tích dữ liệu). "
            "Triệu chứng ẩn theo DSM-5-TR (Rối loạn trầm cảm chủ yếu - MDD): "
            "1) Khí sắc trầm buồn hầu như cả ngày suốt 6 tuần qua sau khi dự án bị hủy. "
            "2) Mất hứng thú hoàn toàn (Anhedonia) với chạy bộ và chơi đàn guitar vốn rất thích trước đây. "
            "3) Mất ngủ cuối giấc (thức dậy lúc 3h sáng), sụt 3.5 kg trong 1 tháng do chán ăn. "
            "4) Méo mó nhận thức kiểu khái quát hóa quá mức và贴 nhãn bản thân ('Tôi là kẻ thất bại'). "
            "5) Không có giai đoạn hưng cảm nào trước đây. Có thoáng nghĩ 'nếu biến mất thì đỡ mệt' nhưng CHƯA có kế hoạch tự sát cụ thể (chỉ tiết lộ điều này nếu bác sĩ/nhà lâm sàng chủ động hỏi sàng lọc nguy cơ tự hại)."
        ),
        "ground_truth": {
            "primary_diagnosis": "Rối loạn Trầm cảm Chủ yếu, Mức độ Vừa - Nặng (Major Depressive Disorder - DSM-5-TR 296.22 / ICD-11 6A70)",
            "diagnosis_keywords": ["trầm cảm", "mdd", "major depressive", "trầm cảm chủ yếu", "6a70"],
            "differential_diagnosis": "Rối loạn Thích ứng có khí sắc trầm (Adjustment Disorder); Rối loạn Lưỡng cực II (cần loại trừ tiền sử hưng cảm nhẹ); Suy giáp.",
            "recommended_scales": ["PHQ-9", "BDI-II"],
            "simulated_scale_results": {
                "PHQ-9": {
                    "total_score": "19 / 27 điểm",
                    "severity": "Trầm cảm Nặng vừa (Moderately Severe Depression)",
                    "breakdown": "Khí sắc trầm (3/3), Mất hứng thú - Anhedonia (3/3), Rối loạn giấc ngủ (3/3), Mệt mỏi (2/3), Chán ăn (2/3), Mặc cảm tội lỗi/vô dụng (3/3), Khó tập trung (2/3), Chậm chạp tâm thần vận động (1/3), Ý nghĩ cái chết thụ động (1/3).",
                },
                "BDI-II": {
                    "total_score": "27 / 63 điểm",
                    "severity": "Trầm cảm Mức độ Vừa - Nặng (Moderate-to-Severe)",
                    "breakdown": "Điểm cao ở nhóm triệu chứng Nhận thức - Cảm xúc (Tự chỉ trích, Bi quan, Mất hứng thú) và nhóm Cơ thể (Thức giấc sớm, Giảm năng lượng).",
                },
                "GAD-7": {
                    "total_score": "8 / 21 điểm",
                    "severity": "Lo âu Nhẹ thứ phát (Mild Comorbid Anxiety)",
                    "breakdown": "Lo lắng kèm theo do áp lực hiệu suất công việc, không phải rối loạn tiên phát.",
                },
            },
            "red_flags_to_ask": [
                "Sàng lọc ý nghĩ tự sát / tự làm hại bản thân (Suicidal Ideation Assessment)",
                "Khai thác tiền sử hưng cảm / hưng cảm nhẹ để loại trừ Rối loạn Lưỡng cực",
                "Đánh giá mức độ mất hứng thú (Anhedonia) và sụt cân sinh học",
            ],
            "target_brain_region_3d": "prefrontal_cortex",
            "target_brain_label": "Vỏ não Trước trán (dlPFC) & Thể Vân (Striatum)",
            "evidence_treatment": (
                "Phối hợp Liệu pháp Nhận thức Hành vi (CBT 12–16 buổi: Kích hoạt hành vi + Tái cấu trúc méo mó nhận thức) "
                "kết hợp dược lý SSRI (vd: Sertraline 50mg/ngày) và thiết lập kế hoạch an toàn."
            ),
            "treatment_keywords": ["cbt", "nhận thức hành vi", "ssri", "sertraline", "kích hoạt hành vi", "tái cấu trúc", "an toàn"],
        },
    },
    {
        "case_id": "gad_panic_02",
        "title": "Ca Lâm sàng #2: Hồi hộp Đánh trống ngực & Lo âu Lan tỏa",
        "difficulty": "Cơ bản - Trung bình (Foundational)",
        "patient_name": "Trần Thu L.",
        "patient_age": 31,
        "occupation": "Giáo viên Tiểu học",
        "avatar_emoji": "👩‍🏫",
        "chief_complaint": "Bác sĩ ơi, suốt 7-8 tháng nay lúc nào ngực tôi cũng đập thình thịch, hai vai căng cứng đau nhức. Tôi cứ sợ có chuyện chẳng lành sắp xảy ra với con nhỏ hoặc mình mắc bệnh hiểm nghèo dù đi khám nội khoa đều bình thường...",
        "initial_demeanor": "Bồn chồn, hai bàn tay đan chặt vào nhau, nói nhanh, liên tục hỏi lại xem triệu chứng của mình có nguy hiểm tính mạng không.",
        "hidden_persona_prompt": (
            "Bạn đang đóng vai bệnh nhân Trần Thu L. (31 tuổi, Giáo viên Tiểu học). "
            "Triệu chứng ẩn theo DSM-5-TR (Rối loạn Lo âu Lan tỏa - GAD): "
            "1) Lo lắng quá mức, không thể kiểm soát về nhiều chủ đề (sức khỏe gia đình, tài chính, công việc ở trường) kéo dài 8 tháng. "
            "2) Căng cơ vùng cổ vai gáy mạn tính, bồn chồn đứng ngồi không yên, dễ cáu gắt và khó vào giấc ngủ. "
            "3) Đã khám tim mạch và xét nghiệm tuyến giáp (TSH, FT4) tuần trước đều hoàn toàn bình thường (chỉ tiết lộ khi được hỏi về bệnh lý cơ thể/tuyến giáp). "
            "4) Không có ý nghĩ tự sát, nhưng rất sợ mất kiểm soát."
        ),
        "ground_truth": {
            "primary_diagnosis": "Rối loạn Lo âu Lan tỏa (Generalized Anxiety Disorder - DSM-5-TR 300.02 / ICD-11 6B00)",
            "diagnosis_keywords": ["lo âu lan tỏa", "gad", "generalized anxiety", "rối loạn lo âu", "6b00"],
            "differential_diagnosis": "Rối loạn Hoảng sợ (Panic Disorder); Cường giáp (Hyperthyroidism - đã loại trừ qua TSH/FT4); Rối loạn Lo âu Bệnh tật.",
            "recommended_scales": ["GAD-7", "DASS-21"],
            "simulated_scale_results": {
                "GAD-7": {
                    "total_score": "16 / 21 điểm",
                    "severity": "Rối loạn Lo âu Mức độ Nặng (Severe Anxiety - Ngưỡng lâm sàng ≥ 10)",
                    "breakdown": "Cảm thấy bồn chồn/căng thẳng (3/3), Không thể ngừng lo lắng (3/3), Lo lắng quá nhiều thứ (3/3), Khó thư giãn (2/3), Bứt rứt (2/3), Dễ bực bội (1/3), Sợ điều tồi tệ xảy ra (2/3).",
                },
                "DASS-21": {
                    "total_score": "Lo âu: 20/42 (Nặng) • Stress: 28/42 (Nặng) • Trầm cảm: 8/42 (Bình thường)",
                    "severity": "Tăng kích thích sinh lý thần kinh tự chủ và căng thẳng trường diễn",
                    "breakdown": "Điểm trục Lo âu và Stress tăng cao rõ rệt trong khi trục Trầm cảm vẫn trong giới hạn bình thường.",
                },
                "PHQ-9": {
                    "total_score": "6 / 27 điểm",
                    "severity": "Nhẹ (chủ yếu do khó vào giấc ngủ và mệt mỏi vì lo âu)",
                    "breakdown": "Không có triệu chứng mất hứng thú (Anhedonia) hay mặc cảm vô dụng.",
                },
            },
            "red_flags_to_ask": [
                "Xác minh thời gian kéo dài triệu chứng (tiêu chuẩn DSM-5 ≥ 6 tháng)",
                "Loại trừ nguyên nhân nội tiết / tim mạch (Cường giáp, lạm dụng Caffeine)",
                "Phân biệt lo âu lan tỏa thường trực với cơn hoảng loạn kịch phát (Panic Attack)",
            ],
            "target_brain_region_3d": "amygdala",
            "target_brain_label": "Hạch Hạnh nhân (Amygdala) & Trục HPA (Hypothalamus)",
            "evidence_treatment": (
                "Liệu pháp Nhận thức Hành vi cho GAD (CBT: Tăng khả năng dung nạp sự bất định, Kiểm nghiệm thực tế, Thư giãn cơ tiến triển PMR), "
                "Can thiệp Chánh niệm (MBCT) kết hợp cân nhắc SSRI/SNRI nếu triệu chứng cơ thể cản trở sinh hoạt."
            ),
            "treatment_keywords": ["cbt", "nhận thức hành vi", "thư giãn", "chánh niệm", "mindfulness", "ssri", "snri", "bất định"],
        },
    },
    {
        "case_id": "ptsd_trauma_03",
        "title": "Ca Lâm sàng #3: Ác mộng Tái hiện & Hành vi Né tránh Sau Tai nạn",
        "difficulty": "Nâng cao (Advanced Clinical)",
        "patient_name": "Lê Hoàng K.",
        "patient_age": 24,
        "occupation": "Sinh viên Kiến trúc năm cuối",
        "avatar_emoji": "🎨",
        "chief_complaint": "Từ sau vụ va chạm giao thông cách đây 4 tháng, đêm nào em cũng giật mình tỉnh giấc vì mơ thấy tiếng phanh xe. Giờ chỉ cần nghe tiếng còi xe lớn là tim đập loạn xạ, em không dám đi qua ngã tư đó nữa...",
        "initial_demeanor": "Cảnh giác cao độ (hypervigilance), ngồi sát mép ghế, giật mình nhẹ khi có tiếng động, né tránh giao tiếp bằng mắt khi nhắc đến vụ tai nạn.",
        "hidden_persona_prompt": (
            "Bạn đang đóng vai bệnh nhân Lê Hoàng K. (24 tuổi, Sinh viên Kiến trúc). "
            "Triệu chứng ẩn theo DSM-5-TR (Rối loạn Căng thẳng Sau Sang chấn - PTSD): "
            "1) Bốn nhóm triệu chứng kéo dài 4 tháng (> 1 tháng): Xâm nhập (ác mộng, flashback khi nghe tiếng phanh xe); Né tránh (bỏ đi xe máy, tránh nhắc chuyện tai nạn); Biến đổi nhận thức/khí sắc tiêu cực (tự trách mình rẽ vào đường đó, tê liệt cảm xúc với bạn bè); Tăng kích thích cảnh giác (giật mình, mất ngủ, khó tập trung làm đồ án). "
            "2) Không chấn thương sọ não thực tổn (CT sọ não lúc cấp cứu bình thường)."
        ),
        "ground_truth": {
            "primary_diagnosis": "Rối loạn Căng thẳng Sau Sang chấn (Post-Traumatic Stress Disorder - PTSD, DSM-5-TR 309.81 / ICD-11 6B40)",
            "diagnosis_keywords": ["ptsd", "sau sang chấn", "post-traumatic", "căng thẳng sau sang chấn", "6b40"],
            "differential_diagnosis": "Rối loạn Căng thẳng Cấp (Acute Stress Disorder - chỉ chẩn đoán khi < 1 tháng); Chấn thương sọ não nhẹ (mTBI); Ám ảnh sợ đặc hiệu.",
            "recommended_scales": ["DASS-21", "PHQ-9"],
            "simulated_scale_results": {
                "DASS-21": {
                    "total_score": "Stress: 32/42 (Rất nặng) • Lo âu: 24/42 (Rất nặng) • Trầm cảm: 14/42 (Vừa)",
                    "severity": "Quá tải kích thích thần kinh giao cảm và phản ứng sang chấn",
                    "breakdown": "Tăng phản xạ giật mình, hoảng sợ trước tín hiệu gợi nhớ sang chấn và thu hẹp cảm xúc.",
                },
                "PHQ-9": {
                    "total_score": "12 / 27 điểm",
                    "severity": "Biểu hiện trầm cảm thứ phát mức độ nhẹ - vừa",
                    "breakdown": "Tập trung ở mục rối loạn giấc ngủ, khó tập trung và thu mình xã hội sau biến cố.",
                },
            },
            "red_flags_to_ask": [
                "Kiểm tra mốc thời gian > 1 tháng để phân biệt PTSD với Rối loạn Căng thẳng Cấp (ASD)",
                "Khai thác đủ 4 cụm triệu chứng: Xâm nhập (Intrusion), Né tránh (Avoidance), Nhận thức/Khí sắc, và Tăng cảnh giác (Arousal)",
                "Loại trừ tổn thương thực thể sọ não (CT/MRI sau tai nạn)",
            ],
            "target_brain_region_3d": "hippocampus",
            "target_brain_label": "Hồi Hải mã (Hippocampus) & Hạch Hạnh nhân (Amygdala)",
            "evidence_treatment": (
                "Liệu pháp Nhận thức Hành vi Tập trung vào Sang chấn (TF-CBT), Liệu pháp Tiếp xúc Kéo dài (Prolonged Exposure - PE) "
                "hoặc Giải mẫn cảm và Tái xử lý bằng Chuyển động Mắt (EMDR) phối hợp SSRI (Sertraline/Paroxetine)."
            ),
            "treatment_keywords": ["tf-cbt", "cbt", "tiếp xúc", "exposure", "emdr", "sang chấn", "ssri", "sertraline"],
        },
    },
]


def grade_osce_clinical_submission(
    case_id: str,
    interview_messages: list[dict[str, str]],
    administered_scales: list[str],
    user_diagnosis: str,
    user_differential: str,
    user_treatment: str,
    cited_evidence: str = "",
) -> dict[str, Any]:
    """Chấm điểm năng lực lâm sàng theo chuẩn OSCE (Objective Structured Clinical Examination) trên thang 100 điểm."""
    case_obj = next((c for c in OSCE_CLINICAL_CASES if c["case_id"] == case_id), OSCE_CLINICAL_CASES[0])
    gt = case_obj["ground_truth"]

    user_questions_text = " ".join(
        m.get("content", "") for m in interview_messages if m.get("role") == "user"
    ).lower()
    num_questions = sum(1 for m in interview_messages if m.get("role") == "user")

    # 1. Kỹ năng Khai thác Bệnh sử & Triệu chứng Đỏ (25 điểm)
    history_score = min(15, num_questions * 4)
    asked_duration = any(k in user_questions_text for k in ["bao lâu", "mấy tháng", "mấy tuần", "khi nào", "thời gian"])
    asked_safety_or_bio = any(
        k in user_questions_text
        for k in ["tự sát", "tự tử", "hại bản thân", "chết", "tuyến giáp", "khám", "xét nghiệm", "hưng cảm", "tai nạn", "ác mộng", "sụt cân"]
    )
    if asked_duration:
        history_score += 5
    if asked_safety_or_bio:
        history_score += 5
    history_score = min(25, max(8, history_score))

    # 2. Chỉ định & Biện giải Thang đo Tâm lý (25 điểm)
    rec_scales = set(gt["recommended_scales"])
    chosen_scales = set(administered_scales or [])
    if chosen_scales & rec_scales:
        scale_score = 25 if len(chosen_scales & rec_scales) >= 1 else 20
    elif chosen_scales:
        scale_score = 16
    else:
        scale_score = 8

    # 3. Độ chính xác Chẩn đoán Xác định & Chẩn đoán Phân biệt (25 điểm)
    diag_low = (user_diagnosis or "").lower()
    diff_low = (user_differential or "").lower()
    matched_diag = any(kw in diag_low for kw in gt["diagnosis_keywords"])
    diag_score = 18 if matched_diag else (10 if len(diag_low.strip()) >= 8 else 4)
    if len(diff_low.strip()) >= 10:
        diag_score += 7
    diag_score = min(25, diag_score)

    # 4. Phác đồ Can thiệp Dựa trên Bằng chứng (25 điểm)
    treat_low = (user_treatment or "").lower()
    treat_hits = sum(1 for kw in gt["treatment_keywords"] if kw in treat_low)
    if treat_hits >= 2:
        treat_score = 25
    elif treat_hits == 1:
        treat_score = 20
    elif len(treat_low.strip()) >= 15:
        treat_score = 14
    else:
        treat_score = 6

    total_score = history_score + scale_score + diag_score + treat_score
    if total_score >= 85:
        grade_rank = "Xuất sắc (Distinction - Chuẩn Lâm sàng Cao)"
    elif total_score >= 70:
        grade_rank = "Đạt chuẩn Tốt (Pass with Merit)"
    elif total_score >= 55:
        grade_rank = "Đạt yêu cầu (Satisfactory)"
    else:
        grade_rank = "Cần rèn luyện thêm (Needs Remediation)"

    return {
        "case_id": case_id,
        "total_score": total_score,
        "grade_rank": grade_rank,
        "rubric_breakdown": [
            {
                "criterion": "1. Kỹ năng Hỏi bệnh & Khai thác Cờ đỏ (History & Red Flags)",
                "score": history_score,
                "max_score": 25,
                "comment": (
                    f"Đã thực hiện {num_questions} lượt hỏi lâm sàng. "
                    + ("Có khai thác mốc thời gian và yếu tố nguy cơ/loại trừ thực tổn." if (asked_duration and asked_safety_or_bio) else "Lưu ý luôn hỏi mốc thời gian kéo dài triệu chứng và sàng lọc nguy cơ tự hại / bệnh lý nội khoa.")
                ),
            },
            {
                "criterion": "2. Chỉ định Thang đo Lượng giá Tâm lý (Psychometric Selection)",
                "score": scale_score,
                "max_score": 25,
                "comment": (
                    f"Đã chỉ định: {', '.join(chosen_scales) if chosen_scales else 'Chưa chỉ định thang đo'}. "
                    f"Thang đo chuẩn khuyến nghị cho ca này: {', '.join(gt['recommended_scales'])}."
                ),
            },
            {
                "criterion": "3. Chẩn đoán DSM-5-TR / ICD-11 & Chẩn đoán Phân biệt",
                "score": diag_score,
                "max_score": 25,
                "comment": (
                    "Chẩn đoán chính xác hội chứng mục tiêu."
                    if matched_diag
                    else f"Chẩn đoán cần bám sát tiêu chuẩn hơn. Đáp án chuẩn: {gt['primary_diagnosis']}."
                ),
            },
            {
                "criterion": "4. Phác đồ Can thiệp Dựa trên Bằng chứng (Evidence-Based Plan)",
                "score": treat_score,
                "max_score": 25,
                "comment": f"Phác đồ chuẩn: {gt['evidence_treatment']}",
            },
        ],
        "ground_truth_revealed": {
            "primary_diagnosis": gt["primary_diagnosis"],
            "differential_diagnosis": gt["differential_diagnosis"],
            "red_flags_to_ask": gt["red_flags_to_ask"],
            "target_brain_region_3d": gt["target_brain_region_3d"],
            "target_brain_label": gt["target_brain_label"],
            "evidence_treatment": gt["evidence_treatment"],
            "cited_evidence": cited_evidence or "[Tài liệu Lâm sàng DSM-5-TR / CBT - Trang 1]",
        },
    }


# ── 12. Hạng mục C, D, E: Phân loại IMRaD, Chuẩn hóa Cỡ Hiệu ứng Liên bài & Chỉ số Đồng thuận ──

import math as _math

_SECONDARY_CITATION_RE = re.compile(
    r"(?:\b[A-Z][a-zA-Z'-]+\s+et\s+al\.?\s*\(\s*(?:19|20)\d{2}\s*\)"
    r"|\(\s*[A-Z][a-zA-Z'-]+(?:\s*(?:&|and)\s*[A-Z][a-zA-Z'-]+)?,\s*(?:19|20)\d{2}[a-z]?(?:\s*;\s*[A-Z][a-zA-Z'-]+.*?\d{4})?\s*\)"
    r"|\[\s*\d{1,3}(?:\s*[,–-]\s*\d{1,3})+\s*\])"
)

_INSTRUMENT_PATTERNS = [
    ("DSM-5", r"\bDSM-5(?:-TR)?\b"),
    ("DSM-IV", r"\bDSM-IV(?:-TR)?\b"),
    ("ICD-11", r"\bICD-11\b"),
    ("ICD-10", r"\bICD-10\b"),
    ("BDI-II", r"\bBDI(?:-II)?\b"),
    ("PHQ-9", r"\bPHQ-9\b"),
    ("GAD-7", r"\bGAD-7\b"),
    ("DASS-21", r"\bDASS-21\b"),
    ("HAM-D", r"\b(?:HAM-D|HDRS)\b"),
    ("SCAS", r"\bSCAS\b"),
    ("SPAI-C", r"\bSPAI-C\b"),
    ("MMPI", r"\bMMPI(?:-2)?\b"),
    ("WAIS", r"\bWAIS(?:-[IV]+)?\b"),
    ("WISC", r"\bWISC(?:-[IV]+)?\b"),
    ("CBCL", r"\bCBCL\b"),
    ("Y-BOCS", r"\bY-BOCS\b"),
    ("PCL-5", r"\bPCL-5\b"),
    ("PANSS", r"\bPANSS\b"),
]


def classify_imrad_section(content: str, page_number: int | str = 1) -> dict[str, Any]:
    """Identify structural cues, never certify that a claim belongs to this study.

    Section headings describe location; keyword matches are tentative topic cues.
    Page number is deliberately not evidence of an IMRaD section or authorship.
    """
    txt = (content or "").strip()
    citation_pattern = re.compile(
        r"\b[A-Z][a-zA-Z'’-]+(?:\s+(?:et\s+al\.?|(?:and|&)\s+[A-Z][a-zA-Z'’-]+))?"
        r"\s*\(\s*(?:19|20)\d{2}[a-z]?\s*\)"
        r"|\([^()]*[A-Z][a-zA-Z'’-]+[^()]*,\s*(?:19|20)\d{2}[a-z]?[^()]*\)"
        r"|\[\s*\d{1,3}(?:\s*[,–-]\s*\d{1,3})*\s*\]"
    )
    sec_citations = len(citation_pattern.findall(txt))
    heading_patterns = {
        "ABSTRACT": r"abstract|tóm tắt",
        "INTRODUCTION": r"introduction|background|giới thiệu|đặt vấn đề",
        "METHODS": r"methods?|methodology|materials and methods|phương pháp|đối tượng và phương pháp",
        "RESULTS": r"results?|findings|kết quả|kết quả nghiên cứu",
        "DISCUSSION": r"discussion|limitations?|conclusions?|bàn luận|hạn chế|kết luận",
    }
    headings = set()
    for code, pattern in heading_patterns.items():
        if re.search(rf"^\s*(?:#{{1,6}}\s*)?(?:\d+(?:\.\d+)*[.)]?\s+)?(?:{pattern})\s*[:.]?\s*$", txt, re.I | re.M):
            headings.add(code)
    if len(headings) == 1:
        code = next(iter(headings))
        basis = "explicit_heading"
    elif headings:
        code = "MIXED"
        basis = "multiple_headings"
    else:
        cues = set()
        if re.search(r"\b(?:sample size|recruited|questionnaire|methods?|cỡ mẫu|phương pháp)\b", txt, re.I):
            cues.add("METHODS")
        if re.search(r"\b(?:results?|findings?|regression|anova|significant(?:ly)?|kết quả)\b", txt, re.I):
            cues.add("RESULTS")
        if re.search(r"\b(?:limitations?|future research|discussion|hạn chế|bàn luận)\b", txt, re.I):
            cues.add("DISCUSSION")
        if re.search(r"\b(?:previous work|prior studies|literature review|nghiên cứu trước|tổng quan tài liệu)\b", txt, re.I):
            cues.add("INTRODUCTION")
        code = next(iter(cues)) if len(cues) == 1 else "MIXED" if cues else "UNKNOWN"
        basis = "keyword_heuristic" if cues else "unknown"
    labels = {
        "ABSTRACT": "Tóm tắt", "INTRODUCTION": "Giới thiệu / tổng quan",
        "METHODS": "Phương pháp / mẫu / công cụ", "RESULTS": "Kết quả",
        "DISCUSSION": "Bàn luận / hạn chế", "MIXED": "Nhiều mục hoặc nội dung hỗn hợp",
        "UNKNOWN": "Chưa xác định mục",
    }
    label = labels[code]
    if basis == "keyword_heuristic":
        label += " (gợi ý từ khóa, chưa xác minh cấu trúc)"
    elif basis == "explicit_heading":
        label += " (tiêu đề mục xuất hiện trong đoạn)"
    guard_note = (
        "Lưu ý nguồn gốc: Nhãn mục không xác nhận đây là phát hiện của bài hiện tại. "
        "Cần xác minh chủ thể từng nhận định và nguồn trước khi gán kết quả cho nghiên cứu."
    )
    if sec_citations:
        guard_note += (
            " Có dấu hiệu trích dẫn nghiên cứu khác; có thể có cả kết quả gốc lẫn kết quả được dẫn lại. "
            "Không tự coi mọi số liệu trong đoạn là kết quả gốc, kể cả trong Methods hoặc Results."
        )
    return {
        "section_code": code,
        "section_label": label,
        "section_basis": basis,
        "claim_origin": "unverified",
        "secondary_citation_count": sec_citations,
        "has_secondary_citations": sec_citations > 0,
        "guard_note": guard_note,
    }


def _classify_cohen_d(d_abs: float) -> str:
    if d_abs >= 0.80:
        return "Lớn (Large effect, |d| >= 0.80)"
    if d_abs >= 0.50:
        return "Trung bình (Medium effect, 0.50 <= |d| < 0.80)"
    if d_abs >= 0.20:
        return "Nhỏ (Small effect, 0.20 <= |d| < 0.50)"
    return "Rất nhỏ / Không đáng kể (Negligible, |d| < 0.20)"


def _extract_sample_size_candidates(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect literal sample-size mentions without assigning study/group ownership.

    A retrieved number (even a unique one) may describe a subgroup, follow-up,
    planned sample or cited study. Never promote it to a study-level N here.
    Parent context is excluded because its text can span different source pages.
    """
    number = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
    pattern = re.compile(
        rf"\b(?:n\s*=\s*(?P<n>{number})(?![\w,]|\.\d)|"
        rf"(?P<count>{number})\s+(?:(?:adult|undergraduate|university|college|young|older)\s+)?(?:participants|patients|students|children|"
        r"adolescents|adults|subjects|bệnh nhân|người tham gia|sinh viên)\b)",
        re.I,
    )
    candidates = []
    seen = set()
    for chunk in chunks:
        content = str(chunk.get("content") or "")
        document_id = str(chunk.get("document_id") or "")
        filename = str(chunk.get("doc_filename") or chunk.get("filename") or "")
        page = chunk.get("page_number")
        for match in pattern.finditer(content):
            value = int((match.group("n") or match.group("count")).replace(",", ""))
            if value <= 0:
                continue
            key = (document_id, filename, str(page), content, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            candidates.append({
                "value": value,
                "document_id": document_id,
                "filename": filename,
                "page": page,
                "quote": match.group(0),
                "source_text": content,
                "start": match.start(),
                "end": match.end(),
                "role": "unverified",
            })
    distinct_values = {c["value"] for c in candidates}
    return {
        "sample_n": None,
        "sample_size_status": "missing" if not candidates else
                              "ambiguous" if len(distinct_values) > 1 else "unverified",
        "sample_size_candidates": candidates,
    }


def _extract_effect_candidates(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep all original-page effect mentions; ownership is not established by regex."""
    pattern = re.compile(
        r"(?<![\w.])(?P<kind>hedges['’]?\s*g|cohen['’]?\s*d|OR|d|g|r)"
        r"\s*=\s*(?P<value>[-+−]?(?:\d+(?:\.\d+)?|\.\d+))(?!\w|[.,]\d)",
        re.IGNORECASE,
    )
    candidates = []
    seen = set()
    for chunk in chunks:
        content = str(chunk.get("content") or "")
        document_id = str(chunk.get("document_id") or "")
        filename = str(chunk.get("doc_filename") or chunk.get("filename") or "")
        page = chunk.get("page_number")
        for match in pattern.finditer(content):
            key = (document_id, filename, str(page), content, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            token = match.group("kind").lower()
            kind = "OR" if token == "or" else token[-1]
            value = float(match.group("value").replace("−", "-"))
            valid = _math.isfinite(value)
            if kind == "r":
                valid = valid and -1 <= value <= 1
            elif kind == "OR":
                valid = valid and value > 0
            candidates.append({
                "effect_type": kind,
                "effect_value": value if _math.isfinite(value) else None,
                "effect_valid": valid,
                "raw_effect": f"{kind} = {value:g}" if _math.isfinite(value) else match.group(0),
                "harmonized_cohen_d": None,
                "document_id": document_id,
                "filename": filename,
                "page": page,
                "quote": match.group(0),
                "source_text": content,
                "start": match.start(),
                "end": match.end(),
                "role": "unverified",
                "direction_status": "reported_direction_only" if valid else "not_assessed",
            })
    return {
        "effect_candidates": candidates,
        "effect_status": "missing" if not candidates else
                         "ambiguous" if len(candidates) > 1 else "unverified",
        # Legacy scalar fields deliberately remain unknown: a mention is not
        # a verified result of this study, even when it is the only mention.
        "raw_effect": None,
        "harmonized_cohen_d": None,
        "effect_type": None,
        "effect_value": None,
        "effect_valid": None,
        "direction_status": "not_assessed",
        "effect_interpretation": "Chưa xác định hiệu ứng đại diện của nghiên cứu.",
    }


def harmonize_cross_study_metrics(context_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Hạng mục D: Trích xuất và chuẩn hóa thông số thống kê, cỡ mẫu N, thang đo và cỡ hiệu ứng Cohen's d liên bài."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for c in context_chunks or []:
        key = str(c.get("sub_query_target") or c.get("doc_filename") or c.get("document_id") or "Study")
        grouped.setdefault(key, []).append(c)

    study_profiles: list[dict[str, Any]] = []
    all_scales_by_study: list[set[str]] = []

    for study_key, chunks in grouped.items():
        c0 = chunks[0]
        fname = c0.get("doc_filename") or c0.get("filename") or study_key
        title = c0.get("doc_title") or fname
        authors = c0.get("doc_authors") or ""
        blob = " ".join(f"{ch.get('content', '')} {ch.get('parent_context', '')}" for ch in chunks)
        pages = sorted({int(m.group(1)) if (m := re.search(r"(\d+)", str(ch.get("page_number") or "1"))) else 1 for ch in chunks})

        # 1. Preserve sample-size mentions and provenance; no max/first guessing.
        sample_info = _extract_sample_size_candidates(chunks)

        # 2. Instruments / Scales
        scales = []
        for s_name, s_pat in _INSTRUMENT_PATTERNS:
            if re.search(s_pat, blob, re.I):
                scales.append(s_name)
        all_scales_by_study.append(set(scales))

        # 3. Reported effect sizes and p-values (no unconditional conversion)
        p_vals = re.findall(r"\bp\s*[<=>]\s*0?\.\d+\b", blob, re.I)[:3]
        effect_info = _extract_effect_candidates(chunks)

        study_profiles.append({
            "target": study_key,
            "filename": fname,
            "title": title,
            "authors": authors,
            "pages": pages[:5],
            **sample_info,
            "instruments": scales,
            "p_values": p_vals,
            **effect_info,
        })

    warnings: list[str] = []
    non_empty_scales = [s for s in all_scales_by_study if s]
    if len(non_empty_scales) >= 2 and not set.intersection(*non_empty_scales):
        warnings.append(
            "Cảnh báo bất tương xứng công cụ đo (Metric Incommensurability): Các nghiên cứu sử dụng hệ thống phân loại/thang đo khác nhau; cần đối chiếu qua cỡ hiệu ứng chuẩn hóa hoặc cơ chế tương đương thay vì so sánh trực tiếp điểm thô."
        )

    prompt_lines: list[str] = []
    for sp in study_profiles:
        parts = [f"Nguồn `{sp['filename']}` (Trang {', '.join(map(str, sp['pages']))})"]
        if sp["authors"]:
            parts.append(f"Tác giả: {sp['authors']}")
        if sp["sample_size_candidates"]:
            parts.append("Cỡ mẫu nghiên cứu chưa xác định: các số sau chỉ là giá trị xuất hiện trong nguồn; "
                         "cần xác minh nghiên cứu, nhóm và thời điểm, không chọn số lớn nhất hoặc cộng các số.")
            for candidate in sp["sample_size_candidates"]:
                page_label = candidate["page"] if candidate["page"] is not None else "chưa xác định"
                parts.append(f"Trích nguyên văn: {candidate['quote']} (Trang {page_label}; vai trò chưa xác minh)")
        else:
            parts.append("Chưa tìm thấy cỡ mẫu trong các đoạn gốc được truy xuất.")
        if sp["instruments"]:
            parts.append(f"Công cụ/Thang đo: {', '.join(sp['instruments'])}")
        if sp["effect_candidates"]:
            parts.append("Chưa xác định hiệu ứng đại diện: không chọn giá trị đầu tiên; "
                         "cần kiểm tra nghiên cứu, nhóm, biến kết quả và thời điểm. "
                         "Giữ dấu theo nguồn nhưng chưa xác minh chiều thang đo; "
                         "không suy ra lợi ích, tác hại hoặc mâu thuẫn chỉ từ dấu.")
            for candidate in sp["effect_candidates"]:
                page_label = candidate["page"] if candidate["page"] is not None else "chưa xác định"
                validity = "vai trò chưa xác minh" if candidate["effect_valid"] else "giá trị ngoài miền hợp lệ, không sử dụng"
                parts.append(f"Giá trị được nhắc: {candidate['raw_effect']}; trích nguyên văn: {candidate['quote']} "
                             f"(Trang {page_label}; {validity})")
        else:
            parts.append("Chưa tìm thấy cỡ hiệu ứng trong các đoạn gốc được truy xuất.")
        if sp["p_values"]:
            parts.append(f"Kiểm định: {', '.join(sp['p_values'])}")
        prompt_lines.append("- " + " | ".join(parts))
    if warnings:
        for w in warnings:
            prompt_lines.append(f"- [LƯU Ý PHƯƠNG PHÁP LUẬN]: {w}")

    return {
        "studies": study_profiles,
        "incommensurability_warnings": warnings,
        "prompt_summary": "\n".join(prompt_lines),
    }


def compute_cross_study_concordance(context_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Report availability, not concordance inferred from rhetorical keywords.

    Retrieved chunks alone do not establish comparable outcomes or pairwise
    support/contradiction. Until that assessment exists, no score is reported.
    Document count is not a count of independent studies or verified comparisons.
    """
    source_ids = {
        str(c.get("document_id") or c.get("doc_filename") or "").strip()
        for c in (context_chunks or [])
    } - {""}
    source_count = len(source_ids)
    if source_count == 1:
        level = "NOT_APPLICABLE"
        label = "Không áp dụng đồng thuận liên bài: chỉ có một tài liệu."
        reason = "single_document"
    elif source_count == 0:
        level = "INSUFFICIENT_EVIDENCE"
        label = "Chưa đủ bằng chứng: chưa có tài liệu nguồn được định danh."
        reason = "no_identified_sources"
    else:
        level = "INSUFFICIENT_EVIDENCE"
        label = "Chưa đủ bằng chứng để kết luận đồng thuận hoặc mâu thuẫn liên bài."
        reason = "pairwise_evidence_not_assessed"
    return {
        "concordance_score": None,
        "concordance_level": level,
        "concordance_label": label,
        "unique_documents_retrieved": source_count,
        "unique_documents_compared": 0,
        "assessed_pairs": 0,
        "reason": reason,
        "verification": "not_assessed",
        "calibrated": False,
    }
