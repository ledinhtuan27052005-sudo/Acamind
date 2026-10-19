import re
import io
import logging
import unicodedata
import difflib
from collections import defaultdict
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


def clean_tok(token: str) -> str:
    """Chuẩn hóa token: lowercase, NFC, loại bỏ ký tự bao bọc ngoài cùng nhưng giữ nguyên số liệu, % và dấu nối."""
    if not token:
        return ""
    s = unicodedata.normalize('NFC', token.lower())
    s = re.sub(r'^[^\w%]+|[^\w%]+$', '', s)
    return s


def extract_quote_candidate(query: str) -> str:
    """Trích xuất đoạn trích dẫn cốt lõi nếu truy vấn chứa dấu ngoặc kép hoặc blockquote."""
    if not query:
        return ""
    q = query.strip()
    # 1. Tìm chuỗi nằm trong ngoặc kép "..." hoặc “...” hoặc '...'
    m = re.search(r'["“\'«]([^"”\'»\n]{6,350})["”\'»]', q)
    if m:
        return m.group(1).strip()
    # 2. Tìm dòng trích dẫn markdown blockquote > ...
    m_bq = re.search(r'^\s*>\s*(.+)$', q, re.MULTILINE)
    if m_bq:
        cleaned = re.sub(r'^["“\'\s]+|["”\'\s]+$', '', m_bq.group(1)).strip()
        if len(cleaned) >= 6:
            return cleaned
    return q


def extract_evidence_anchors(text: str) -> List[str]:
    """Trích xuất các mỏ neo chứng cứ gồm: số liệu %, p-value, thuật ngữ học thuật, từ viết tắt."""
    if not text:
        return []

    anchors = []

    # 1. Các tỷ lệ phần trăm (ví dụ: 68.9%, 82.5%, 10.0%, 5.0%)
    pcts = re.findall(r'\b\d+(?:\.\d+)?%', text)
    anchors.extend(pcts)

    # 2. Các chỉ số kiểm định thống kê và cỡ mẫu (ví dụ: p < 0.001, d = 0.95, N = 120, BDI-II, PHQ-9)
    stats = re.findall(r'(?:p\s*[<>=]\s*\d+(?:\.\d+)?|d\s*=\s*\d+(?:\.\d+)?|N\s*=\s*\d+|\b\d{4}\b)', text, re.IGNORECASE)
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
        k = clean_tok(anc)
        if k and k not in seen:
            seen.add(k)
            result.append(anc.strip())
    return result


def segment_page_into_sentences(words: List[tuple]) -> List[Tuple[int, int, str, set]]:
    """Phân đoạn các từ trên trang thành các đơn vị câu/mục logic hoàn chỉnh với chỉ số từ đầu và cuối.
    
    Returns:
        List of tuples: (start_word_idx, end_word_idx, sentence_text, set_of_normalized_tokens)
    """
    sentences = []
    current = []
    start_idx = 0

    for idx, w in enumerate(words):
        if not current:
            start_idx = idx
        current.append(w)
        word_str = w[4]
        is_terminal = False

        # Kết thúc câu chuẩn bằng . ! ? (ngoại trừ từ viết tắt e.g., i.e., Dr., vs., al., fig., tab.)
        if re.search(r'[.!?]$', word_str) and not re.search(r'\b(?:e\.g|i\.e|dr|mr|mrs|vs|al|fig|tab)\.$', word_str, re.I):
            is_terminal = True
        # Tiêu đề ngắn kết thúc bằng dấu hai chấm (ví dụ: 'Materials and Methods:', 'Table 1:')
        elif word_str.endswith(':') and len(current) <= 6:
            is_terminal = True
        # Ranh giới block văn bản trong PDF
        elif idx + 1 < len(words) and words[idx + 1][5] != w[5]:
            is_terminal = True

        if is_terminal:
            stext = ' '.join(cw[4] for cw in current).strip()
            if len(stext) >= 8:
                toks = {clean_tok(cw[4]) for cw in current if clean_tok(cw[4]) and clean_tok(cw[4]) not in STOPWORDS}
                sentences.append((start_idx, idx, stext, toks))
            current = []

    if current:
        stext = ' '.join(cw[4] for cw in current).strip()
        if len(stext) >= 8:
            toks = {clean_tok(cw[4]) for cw in current if clean_tok(cw[4]) and clean_tok(cw[4]) not in STOPWORDS}
            sentences.append((start_idx, len(words) - 1, stext, toks))

    return sentences


def span_to_line_rects(words: List[tuple], start_idx: int, end_idx: int) -> List[fitz.Rect]:
    """Chuyển đổi một dải từ (start_idx..end_idx) trên trang thành danh sách các hình chữ nhật bao quanh từng dòng.
    Đảm bảo:
    - Bắt đầu chính xác ở từ đầu tiên của dòng đầu.
    - Kết thúc chính xác ở từ cuối cùng của dòng cuối.
    - Không bị thừa ra ngoài phạm vi văn bản, không thiếu dòng do ngắt dòng hay gạch nối.
    """
    lines = defaultdict(list)
    for idx in range(start_idx, end_idx + 1):
        w = words[idx]
        lines[(w[5], w[6])].append(w)

    rects = []
    # Sắp xếp các dòng theo thứ tự đọc từ trên xuống dưới, từ trái sang phải
    for key, lwords in sorted(lines.items(), key=lambda item: (min(w[1] for w in item[1]), min(w[0] for w in item[1]))):
        x0 = min(w[0] for w in lwords)
        y0 = min(w[1] for w in lwords)
        x1 = max(w[2] for w in lwords)
        y1 = max(w[3] for w in lwords)
        # Thêm một chút padding vi mô (0.5pt) để phủ màu đẹp mắt mà không chạm sang dòng khác
        rects.append(fitz.Rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5))

    return rects


def find_word_sequence_span(words: List[tuple], query_text: str) -> Optional[Tuple[int, int, str]]:
    """Tìm dải từ khớp chính xác hoặc mờ liên tục với truy vấn trích dẫn."""
    q_toks = [clean_tok(t) for t in query_text.split() if clean_tok(t)]
    if not q_toks:
        return None

    page_toks = [clean_tok(w[4]) for w in words]
    m = len(q_toks)

    # 1. Khớp chính xác toàn bộ chuỗi token liên tục
    for i in range(len(page_toks) - m + 1):
        if page_toks[i : i + m] == q_toks:
            stext = ' '.join(words[k][4] for k in range(i, i + m))
            return (i, i + m - 1, stext)

    # 2. Khớp chuỗi con dài nhất (Longest common sub-sequence contiguous match) nếu truy vấn dài
    if m >= 5:
        best_sub = None
        best_len = 0
        min_sub_len = max(4, int(m * 0.45))
        for sub_len in range(m, min_sub_len - 1, -1):
            for start_q in range(m - sub_len + 1):
                sub_q = q_toks[start_q : start_q + sub_len]
                for i in range(len(page_toks) - sub_len + 1):
                    if page_toks[i : i + sub_len] == sub_q:
                        if sub_len > best_len:
                            best_len = sub_len
                            best_sub = (i, i + sub_len - 1)
                            break
                if best_sub:
                    break
            if best_sub:
                break
        if best_sub and best_len >= 4 and (best_len / m) >= 0.45:
            stext = ' '.join(words[k][4] for k in range(best_sub[0], best_sub[1] + 1))
            return (best_sub[0], best_sub[1], stext)

    # 3. Fuzzy SequenceMatcher qua difflib nếu có từ bị thiếu dấu hoặc sai lệch nhẹ
    matcher = difflib.SequenceMatcher(None, page_toks, q_toks)
    blocks = [b for b in matcher.get_matching_blocks() if b.size > 0]
    if blocks:
        total_matched = sum(b.size for b in blocks)
        if total_matched >= 4 and (total_matched / m) >= 0.50:
            start = blocks[0].a
            end = blocks[-1].a + blocks[-1].size - 1
            # Đảm bảo phạm vi dải từ không bị trải quá rộng sang các đoạn văn khác
            if (end - start + 1) <= m * 1.6 + 5:
                stext = ' '.join(words[k][4] for k in range(start, end + 1))
                return (start, end, stext)

    return None


def ground_sentence_semantically(
    words: List[tuple],
    sentences: List[Tuple[int, int, str, set]],
    query_text: str
) -> Optional[Tuple[int, int, str]]:
    """Định vị câu nguồn tốt nhất trên trang PDF bằng thuật toán phân tích ngữ nghĩa và mỏ neo chứng cứ."""
    q_clean = normalize_text(query_text)
    q_raw_tokens = [clean_tok(t) for t in q_clean.split() if clean_tok(t) and clean_tok(t) not in STOPWORDS]
    if not q_raw_tokens:
        return None
    q_tokens = set(q_raw_tokens)

    # Trích xuất anchors (số liệu %, p-value, năm, mã số, thuật ngữ viết tắt)
    anchors = [clean_tok(a) for a in extract_evidence_anchors(q_clean) if clean_tok(a)]

    # Mở rộng thuật ngữ song ngữ Anh - Việt
    try:
        from app.services.cross_lingual import PSYCHOLOGY_GLOSSARY_VI_TO_EN, PSYCHOLOGY_GLOSSARY_EN_TO_VI
        q_lower = q_clean.lower()
        for vi_k, en_v in PSYCHOLOGY_GLOSSARY_VI_TO_EN.items():
            if vi_k in q_lower:
                for t in en_v.split():
                    c = clean_tok(t)
                    if len(c) >= 3 and c not in STOPWORDS:
                        q_tokens.add(c)
        for en_k, vi_v in PSYCHOLOGY_GLOSSARY_EN_TO_VI.items():
            if en_k in q_lower:
                for t in vi_v.split():
                    c = clean_tok(t)
                    if len(c) >= 3 and c not in STOPWORDS:
                        q_tokens.add(c)
    except Exception as e:
        logger.debug(f"Glossary expansion skip: {e}")

    best_sent = None
    best_score = 0.0

    for s_idx, e_idx, stext, s_toks in sentences:
        overlap = q_tokens.intersection(s_toks)
        anchor_hits = sum(1 for a in anchors if any(a in tok for tok in s_toks))
        
        # Điểm tương đồng được tính dựa trên tỷ lệ bao phủ token ngữ nghĩa và thưởng điểm mỏ neo số liệu
        score = (len(overlap) + 2.5 * anchor_hits) / (len(q_tokens) + 1e-6)
        if score > best_score:
            best_score = score
            best_sent = (s_idx, e_idx, stext)

    if best_sent and best_score >= 0.15:
        return best_sent
    return None


def ground_and_search_page_rects(
    page: fitz.Page,
    query: str
) -> Tuple[List[fitz.Rect], str, List[str]]:
    """Thuật toán Smart Evidence Grounding chuẩn xác cao:
    Định vị chính xác câu văn hoặc đoạn văn nguồn trong tài liệu PDF và trả về tọa độ highlight hoàn chỉnh.
    
    Quy tắc cốt lõi:
    - Đúng chính xác đoạn trích dẫn (không thừa ra các đoạn/số liệu khác trên trang).
    - Phủ trọn vẹn toàn bộ các từ trong đoạn (không thiếu dòng hoặc cụm từ do ngắt dòng).
    
    Returns:
        rects: Danh sách bounding boxes trên trang cần bôi vàng.
        grounded_sentence: Đoạn nguyên văn trên trang PDF khớp nhất với luận điểm của AI.
        highlighted_terms: Danh sách các thuật ngữ, trích đoạn cốt lõi được bôi vàng.
    """
    rects: List[fitz.Rect] = []
    grounded_sentence = ""
    highlighted_terms: List[str] = []

    if not query or not query.strip():
        return rects, grounded_sentence, highlighted_terms

    clean_query = normalize_text(query)
    core_quote = extract_quote_candidate(clean_query)

    words = page.get_text("words")
    if not words:
        # Fallback cho trang PDF dạng ảnh thuần (chưa có text layer)
        return rects, grounded_sentence, highlighted_terms

    # ── BƯỚC 1: Tìm dải từ khớp trực tiếp từ trích dẫn cốt lõi ──
    span = find_word_sequence_span(words, core_quote)
    if not span and core_quote != clean_query:
        span = find_word_sequence_span(words, clean_query)

    # ── BƯỚC 2: Định vị ngữ nghĩa theo cấu trúc câu hoàn chỉnh trên trang ──
    sentences = segment_page_into_sentences(words)
    if not span and sentences:
        span = ground_sentence_semantically(words, sentences, core_quote)
        if not span and core_quote != clean_query:
            span = ground_sentence_semantically(words, sentences, clean_query)

    # ── BƯỚC 3: Tạo hình chữ nhật bao quanh dải từ đã định vị ──
    if span:
        s_idx, e_idx, text_matched = span
        grounded_sentence = text_matched
        rects = span_to_line_rects(words, s_idx, e_idx)
        highlighted_terms.append(text_matched[:80] + ("..." if len(text_matched) > 80 else ""))
        return rects, grounded_sentence, highlighted_terms

    # ── BƯỚC 4: Fallback mỏ neo đơn lẻ (nếu chỉ có 1 số liệu hoặc từ viết tắt đặc trưng) ──
    anchors = extract_evidence_anchors(core_quote or clean_query)
    for anc in anchors:
        anc_clean = clean_tok(anc)
        if not anc_clean:
            continue
        # Tìm vị trí xuất hiện của anchor trong danh sách từ
        for idx, w in enumerate(words):
            if anc_clean in clean_tok(w[4]):
                # Xác định câu chứa anchor này thay vì bôi vàng đơn lẻ khắp trang
                target_sent = None
                for s_idx, e_idx, stext, s_toks in sentences:
                    if s_idx <= idx <= e_idx:
                        target_sent = (s_idx, e_idx, stext)
                        break
                if target_sent:
                    s_idx, e_idx, stext = target_sent
                    grounded_sentence = stext
                    rects = span_to_line_rects(words, s_idx, e_idx)
                    highlighted_terms.append(stext[:80] + ("..." if len(stext) > 80 else ""))
                    return rects, grounded_sentence, highlighted_terms
                else:
                    # Bôi vàng từ đó
                    r = fitz.Rect(w[0] - 0.5, w[1] - 0.5, w[2] + 0.5, w[3] + 0.5)
                    rects.append(r)
                    grounded_sentence = w[4]
                    highlighted_terms.append(w[4])
                    return rects, grounded_sentence, highlighted_terms

    return rects, grounded_sentence, highlighted_terms


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
            if rects:
                try:
                    annot = page.add_highlight_annot(rects)
                    # Màu vàng dạ quang chuẩn tài liệu học thuật (Amber/Gold: RGB 1.0, 0.88, 0.20)
                    annot.set_colors(stroke=(1.0, 0.88, 0.20))
                    annot.update()
                except Exception as e:
                    # Fallback bôi từng rect nếu add_highlight_annot theo list gặp lỗi trên phiên bản PyMuPDF cũ
                    for r in rects:
                        try:
                            annot = page.add_highlight_annot(r)
                            annot.set_colors(stroke=(1.0, 0.88, 0.20))
                            annot.update()
                        except Exception:
                            pass

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
