import re
import io
import logging
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
    'does', 'did', 'as', 'that', 'this', 'these', 'those', 'it', 'its', 'from',
    'which', 'who', 'whom', 'whose', 'what', 'when', 'where', 'why', 'how', 'all',
    'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
    'just', 'should', 'now', 'could', 'would', 'also', 'about', 'between', 'into',
    # Vietnamese common stopwords
    'la', 'va', 'cua', 'trong', 'cac', 'nhung', 'co', 'duoc', 'cho', 'voi', 've',
    'nhu', 'khi', 'tu', 'tai', 'theo', 'de', 'nay', 'do', 'ra', 'vao', 'tren',
    'duoi', 'mot', 'hai', 'ba', 'bon', 'nam', 'qua', 'lai', 'da', 'dang', 'se'
}


def normalize_text(text: str) -> str:
    """Chuẩn hóa unicode NFC và khoảng trắng."""
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_tokens(text: str) -> set:
    """Tách tập hợp các từ có ý nghĩa (bỏ stop words)."""
    words = re.findall(r'\b[\w\-\.]{2,}\b', text.lower())
    return {w for w in words if w not in STOPWORDS and not w.isdigit()}


def extract_evidence_anchors(text: str) -> List[str]:
    """Trích xuất các mỏ neo chứng cứ gồm: số liệu %, p-value, thuật ngữ học thuật, từ viết tắt."""
    if not text:
        return []

    anchors = []

    # 1. Các tỷ lệ phần trăm (ví dụ: 68.9%, 82.5%, 10.0%, 5.0%)
    pcts = re.findall(r'\b\d+(?:\.\d+)?%', text)
    anchors.extend(pcts)

    # 2. Các chỉ số kiểm định thống kê và cỡ mẫu (ví dụ: p < 0.001, d = 0.95, N = 120, BDI-II, PHQ-9)
    stats = re.findall(r'(?:p\s*[<>=]\s*\d+(?:\.\d+)?|d\s*=\s*\d+(?:\.\d+)?|N\s*=\s*\d+)', text, re.IGNORECASE)
    anchors.extend(stats)

    # 3. Các thuật ngữ tiếng Anh gốc đặt trong dấu ngoặc đơn: (Cognitive psychology), (Behavioral psychology)
    parens = re.findall(r'\(([A-Za-z0-9\s\-]+)\)', text)
    for p in parens:
        p_clean = p.strip()
        if 3 <= len(p_clean) <= 45 and not p_clean.isdigit():
            anchors.append(p_clean)

    # 4. Các từ viết tắt chuyên ngành y khoa / tâm lý học (CBT, SSRI, MDD, DSM-5, BDI-II, PHQ-9, GAD-7, RCT, EBP)
    acronyms = re.findall(r'\b[A-Z][A-Za-z0-9\-]{1,10}(?:-[A-Za-z0-9]+)*\b', text)
    for a in acronyms:
        if a.isupper() and len(a) >= 2 and a not in ('AND', 'THE', 'FOR', 'WITH', 'NOT'):
            anchors.append(a)

    # Deduplicate giữ thứ tự xuất hiện
    seen = set()
    result = []
    for anc in anchors:
        k = anc.strip()
        k_lower = k.lower()
        if k and k_lower not in seen:
            seen.add(k_lower)
            result.append(k)
    return result


def extract_sentences_from_page(page: fitz.Page) -> List[str]:
    """Tách danh sách các câu hoàn chỉnh từ nội dung trang PDF, hỗ trợ cả bảng biểu, khối văn bản và đoạn văn."""
    blocks = page.get_text("blocks")
    if not blocks:
        return []

    sentences: List[str] = []
    for b in blocks:
        if len(b) > 6 and b[6] != 0:
            continue
        text = b[4].strip()
        if not text:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue

        # Nếu khối là bảng hoặc danh sách gồm nhiều dòng ngắn không kết thúc bằng dấu chấm
        if len(lines) > 1 and any(len(l) < 35 for l in lines) and not any(l.endswith('.') for l in lines[:-1]):
            row_str = ' '.join(lines)
            if len(row_str) >= 15:
                sentences.append(row_str)
        else:
            # Đoạn văn: nối các dòng bị ngắt và tách câu theo dấu kết thúc (. ! ?)
            para = ' '.join(lines)
            para = re.sub(r'\s+', ' ', para).strip()
            raw_sents = re.split(r'(?<=[.!?])\s+', para)
            for s in raw_sents:
                s_clean = s.strip()
                if len(s_clean) >= 20 and not s_clean.isdigit():
                    sentences.append(s_clean)
    return sentences


def ground_and_search_page_rects(
    page: fitz.Page,
    query: str
) -> Tuple[List[fitz.Rect], str, List[str]]:
    """Thuật toán Smart Evidence Grounding:
    Định vị chính xác câu văn / đoạn văn nguồn trong tài liệu PDF và trả về tọa độ highlight.
    
    Returns:
        rects: Danh sách bounding boxes trên trang cần bôi vàng.
        grounded_sentence: Câu nguyên văn trên trang PDF khớp nhất với luận điểm của AI.
        highlighted_terms: Danh sách các thuật ngữ, số liệu cốt lõi được bôi vàng.
    """
    rects: List[fitz.Rect] = []
    grounded_sentence = ""
    highlighted_terms: List[str] = []

    if not query:
        return rects, grounded_sentence, highlighted_terms

    clean_query = normalize_text(query.strip().strip('"\'*[]()'))
    if not clean_query:
        return rects, grounded_sentence, highlighted_terms

    # ── PASS 1: Thử tìm chính xác nguyên câu nếu có trong PDF ──
    if len(clean_query) <= 120:
        found = page.search_for(clean_query)
        if found:
            return found, clean_query, [clean_query[:50]]

    # ── PASS 2: Semantic Sentence Grounding (Định vị câu tương đồng nhất) ──
    page_sentences = extract_sentences_from_page(page)
    query_tokens = extract_tokens(clean_query)
    anchors = extract_evidence_anchors(clean_query)

    # Mở rộng song ngữ (Cross-lingual glossary expansion) nếu có thuật ngữ tâm lý học
    try:
        from app.services.cross_lingual import PSYCHOLOGY_GLOSSARY_VI_TO_EN, PSYCHOLOGY_GLOSSARY_EN_TO_VI
        q_lower = clean_query.lower()
        for vi_k, en_v in PSYCHOLOGY_GLOSSARY_VI_TO_EN.items():
            if vi_k in q_lower:
                for t in en_v.split():
                    if len(t) >= 4:
                        query_tokens.add(t.lower())
        for en_k, vi_v in PSYCHOLOGY_GLOSSARY_EN_TO_VI.items():
            if en_k in q_lower:
                for t in vi_v.split():
                    if len(t) >= 4:
                        query_tokens.add(t.lower())
    except Exception as e:
        logger.debug(f"Glossary expansion skip: {e}")

    best_sent = None
    best_score = 0.0

    for s in page_sentences:
        s_norm = normalize_text(s)
        s_tokens = extract_tokens(s_norm)
        overlap = query_tokens.intersection(s_tokens)

        # Thưởng điểm nếu câu trên trang chứa đúng số liệu % hoặc thuật ngữ mỏ neo
        bonus = 0.0
        for anc in anchors:
            if anc.lower() in s_norm.lower():
                bonus += 0.35

        score = (len(overlap) / (len(query_tokens) + 1e-6)) + bonus
        if score > best_score:
            best_score = score
            best_sent = s_norm

    # Nếu tìm thấy câu trên trang khớp ngữ cảnh (ngưỡng tin cậy >= 0.15)
    if best_sent and best_score >= 0.15:
        grounded_sentence = best_sent
        # Thử tìm kiếm nguyên câu
        sent_rects = page.search_for(best_sent)
        if sent_rects:
            rects.extend(sent_rects)
            highlighted_terms.append(best_sent[:60] + "...")
        else:
            # Nếu câu bị ngắt dòng hoặc ký tự lạ, chia thành các mệnh đề 6-10 từ
            words = best_sent.split()
            step = 8
            for i in range(0, len(words), step):
                chunk = " ".join(words[i:i + step])
                if len(chunk) >= 12:
                    c_rects = page.search_for(chunk)
                    if c_rects:
                        rects.extend(c_rects)
            if rects:
                highlighted_terms.append(best_sent[:60] + "...")

    # ── PASS 3: Highlight các mỏ neo số liệu định lượng (Percentages, stats, sample sizes) ──
    # Các số liệu định lượng cụ thể luôn được bôi vàng để nổi bật trong bảng hoặc đoạn văn
    for anc in anchors:
        is_numeric_stat = any(c.isdigit() for c in anc) or '<' in anc or '>' in anc or '=' in anc
        if is_numeric_stat:
            anc_rects = page.search_for(anc)
            if anc_rects:
                rects.extend(anc_rects)
                if anc not in highlighted_terms:
                    highlighted_terms.append(anc)

    # ── PASS 4: Fallback các từ viết tắt và mệnh đề con nếu chưa có rect nào ──
    if not rects:
        for anc in anchors:
            anc_rects = page.search_for(anc)
            if anc_rects:
                rects.extend(anc_rects)
                if anc not in highlighted_terms:
                    highlighted_terms.append(anc)

    if not rects:
        clauses = re.split(r'[,;.\n]', clean_query)
        for cl in clauses:
            cl_clean = cl.strip().strip('"\'*[]()')
            if 10 <= len(cl_clean) <= 60:
                c_rects = page.search_for(cl_clean)
                if c_rects:
                    rects.extend(c_rects)
                    highlighted_terms.append(cl_clean)

    # ── PASS 5: Deduplicate & merge rects ──
    unique_rects: List[fitz.Rect] = []
    for r in rects:
        is_dup = False
        for ur in unique_rects:
            if abs(r.x0 - ur.x0) < 3 and abs(r.y0 - ur.y0) < 3 and abs(r.x1 - ur.x1) < 3 and abs(r.y1 - ur.y1) < 3:
                is_dup = True
                break
        if not is_dup:
            unique_rects.append(r)

    return unique_rects, grounded_sentence, highlighted_terms


def search_page_rects(page: fitz.Page, query: str) -> List[fitz.Rect]:
    """Hàm tìm kiếm tọa độ bounding boxes trên trang (tương thích ngược)."""
    rects, _, _ = ground_and_search_page_rects(page, query)
    return rects


def generate_highlighted_pdf_stream(
    file_path: str,
    page_number: int,
    query: Optional[str] = None
) -> bytes:
    """Tạo tệp PDF mới với các highlight annotation màu vàng dạ quang được phủ trực tiếp lên trang được chỉ định.
    
    Args:
        file_path: Đường dẫn tệp PDF gốc.
        page_number: Trang cần highlight (1-indexed).
        query: Đoạn trích dẫn hoặc từ khóa cần tìm và bôi vàng.
        
    Returns:
        bytes của tệp PDF đã được nhúng highlight annotations.
    """
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        if not (1 <= page_number <= total_pages):
            return doc.tobytes()

        target_page_idx = page_number - 1
        page = doc[target_page_idx]

        if query and query.strip():
            rects, _, _ = ground_and_search_page_rects(page, query)
            for r in rects:
                try:
                    annot = page.add_highlight_annot(r)
                    # Màu vàng dạ quang chuẩn tài liệu học thuật (Amber/Gold: RGB 1.0, 0.88, 0.20)
                    annot.set_colors(stroke=(1.0, 0.88, 0.20))
                    annot.update()
                except Exception as e:
                    logger.debug(f"Could not add highlight annot: {e}")

        return doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()


def get_highlight_metadata(
    file_path: str,
    page_number: int,
    query: str
) -> Dict[str, Any]:
    """Lấy danh sách tọa độ bounding boxes và câu nguyên văn đối chứng từ trang PDF."""
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        if not (1 <= page_number <= total_pages):
            return {"page": page_number, "rects": [], "terms": [], "grounded_sentence": ""}

        page = doc[page_number - 1]
        rects, grounded_sentence, terms = ground_and_search_page_rects(page, query)
        
        return {
            "page": page_number,
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "rects": [[round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)] for r in rects],
            "terms": terms,
            "grounded_sentence": grounded_sentence,
        }
    finally:
        doc.close()
