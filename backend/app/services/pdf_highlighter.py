import re
import io
import logging
import unicodedata
import math
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
    'duoi', 'mot', 'hai', 'ba', 'bon', 'nam', 'qua', 'lai', 'da', 'dang', 'se',
    'tai', 'lieu', 'trang', 'bai', 'bao', 'nghien', 'cuu', 'cho', 'thay', 'rang',
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


def extract_english_phrases_from_claim(claim_text: str) -> List[str]:
    """Trích xuất các cụm từ tiếng Anh hoặc trích dẫn nguyên văn trong ngoặc đơn (...) / ngoặc kép "..."
    từ câu trả lời tiếng Việt của AI để định vị chính xác 100% câu gốc trên trang PDF."""
    if not claim_text:
        return []
    candidates: List[str] = []

    # 1. Cụm nằm trong ngoặc kép
    for m in re.finditer(r'["“«]([^"”»\n]{5,240})["”»]', claim_text):
        phrase = m.group(1).strip()
        if len(phrase.split()) >= 2:
            candidates.append(phrase)

    # 2. Cụm tiếng Anh nằm trong ngoặc đơn (...)
    for m in re.finditer(r'\(([^\(\)\[\]\n]{4,200})\)', claim_text):
        inner = m.group(1).strip()
        # Bỏ qua nhãn trích dẫn kiểu (Park et al., 2024) hoặc (Trang 1)
        if re.search(r'\bet\s+al\b|\b(?:Trang|Page)\s+\d+\b', inner, re.I):
            continue
        # Kiểm tra xem cụm trong ngoặc có chứa từ tiếng Anh (ASCII) hoặc số liệu không
        ascii_words = re.findall(r'\b[A-Za-z]{3,}\b', inner)
        if len(ascii_words) >= 1:
            # Nếu có dạng "English Term - ACRONYM", lấy cả cụm lẫn phần trước dấu gạch
            if " - " in inner:
                parts = [p.strip() for p in inner.split(" - ") if len(p.strip()) >= 3]
                candidates.extend(parts)
            candidates.append(inner)

    # Sắp xếp ưu tiên cụm dài hơn (nhiều từ hơn) để khớp đặc trưng nhất trước
    seen = set()
    uniq: List[str] = []
    for c in sorted(candidates, key=lambda x: len(x.split()), reverse=True):
        k = c.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    return uniq


def extract_evidence_anchors(text: str) -> List[str]:
    """Trích xuất các mỏ neo chứng cứ gồm: số liệu %, số thập phân, cỡ mẫu, p-value, thuật ngữ tiếng Anh, từ viết tắt.
    Tuyệt đối KHÔNG lấy năm xuất bản (1991, 2024) hoặc trích dẫn (Author et al., 2024) làm mỏ neo để tránh hút vào mục References.
    """
    if not text:
        return []

    anchors = []

    # 1. Các tỷ lệ phần trăm (ví dụ: 68.9%, 82.5%, 10.0%, 5.0%)
    pcts = re.findall(r'\b\d+(?:[.,]\d+)?%', text)
    anchors.extend(pcts)

    # 2. Các số liệu định lượng cụ thể (số thập phân 0.34, 0.20, 0.23, cỡ mẫu có dấu phẩy 6,139, hoặc số lượng 39, 40)
    # Loại trừ các số năm 1900..2035 và số trang nhỏ 1..3
    for num_m in re.finditer(r'\b\d{1,3}(?:,\d{3})+\b|\b\d+[.,]\d+\b|\b\d{2,4}\b', text):
        num_str = num_m.group(0)
        if re.match(r'^(?:19|20)\d{2}$', num_str):
            continue
        anchors.append(num_str)
        # Thêm biến thể đổi dấu phẩy <-> dấu chấm cho số thập phân
        if ',' in num_str and len(num_str.split(',')[1]) <= 2:
            anchors.append(num_str.replace(',', '.'))
        elif '.' in num_str:
            anchors.append(num_str.replace('.', ','))

    # 3. Các thuật ngữ tiếng Anh gốc đặt trong dấu ngoặc đơn (bỏ qua trích dẫn tác giả-năm kiểu '(Park et al., 2024)')
    parens = re.findall(r'\(([A-Za-z0-9\s\-,.;:]+)\)', text)
    for p in parens:
        p_clean = p.strip()
        if 3 <= len(p_clean) <= 80 and not p_clean.isdigit():
            if re.search(r'\bet\s+al\b|\b(?:19|20)\d{2}\b', p_clean, re.I):
                continue
            anchors.append(p_clean)
            for w in re.findall(r'\b[A-Za-z]{4,}\b', p_clean):
                if w.lower() not in STOPWORDS:
                    anchors.append(w)

    # 4. Các từ viết tắt chuyên ngành y khoa / tâm lý học (CBT, SSRI, MDD, DSM-5, BDI-II, PHQ-9, GAD-7, RCT, PPI, WHO)
    acronyms = re.findall(r'\b[A-Z][A-Za-z0-9\-]{1,10}(?:-[A-Za-z0-9]+)*\b', text)
    for a in acronyms:
        if a.isupper() and len(a) >= 2 and a not in ('AND', 'THE', 'FOR', 'WITH', 'NOT', 'DOI', 'URL', 'PDF', 'VOL'):
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


def _dehyphenate_words_text(words_slice: List[tuple]) -> Tuple[str, set]:
    """Ghép nối các từ bị ngắt dòng bằng dấu gạch ngang (ví dụ: 'in-' + 'trinsically' -> 'intrinsically')
    để so khớp câu hoàn chỉnh không bị đứt đoạn giữa câu."""
    if not words_slice:
        return "", set()
    raw_parts = [cw[4] for cw in words_slice]
    stext = " ".join(raw_parts).strip()
    stext_dehyph = re.sub(r'([A-Za-z]{2,})[-‐‑‒–\xad]\s+([a-z]{2,})\b', r'\1\2', stext)
    toks = {clean_tok(cw[4]) for cw in words_slice if clean_tok(cw[4]) and clean_tok(cw[4]) not in STOPWORDS}
    for t in stext_dehyph.split():
        ct = clean_tok(t)
        if ct and ct not in STOPWORDS:
            toks.add(ct)
    return stext_dehyph, toks


def segment_page_into_sentences(words: List[tuple]) -> List[Tuple[int, int, str, set]]:
    """Phân đoạn các từ trên trang thành các đơn vị câu/mục logic hoàn chỉnh với chỉ số từ đầu và cuối.
    Hỗ trợ tự động nối từ bị gạch nối xuống dòng (de-hyphenation) và loại bỏ mảnh từ bị cắt cụt ở đầu trang/cột.
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

        # Kết thúc câu chuẩn bằng . ! ? (ngoại trừ từ viết tắt e.g., i.e., Dr., vs., al., fig., tab., tên viết tắt 1 chữ cái 'A.')
        if (
            re.search(r'[.!?]["”\'\)]?$', word_str)
            and not re.search(r'\b(?:e\.g|i\.e|dr|mr|mrs|prof|vs|al|fig|tab|eq|no|vol|pp|cf)\.$', word_str, re.I)
            and not re.match(r'^[A-Z]\.$', word_str)
        ):
            is_terminal = True
        # Tiêu đề ngắn kết thúc bằng dấu hai chấm (ví dụ: 'Materials and Methods:', 'Table 1:', 'Background:')
        elif word_str.endswith(':') and len(current) <= 4:
            is_terminal = True
        # Ranh giới block văn bản trong PDF khi có khoảng cách dọc lớn (khác đoạn văn)
        elif idx + 1 < len(words) and words[idx + 1][5] != w[5]:
            vertical_gap = abs(float(words[idx + 1][1]) - float(w[3]))
            col_shift = abs(float(words[idx + 1][0]) - float(w[0]))
            if vertical_gap > 8.0 or col_shift > 120.0:
                is_terminal = True

        if is_terminal:
            # Nếu câu chỉ là 1 mảnh từ bị ngắt từ trang/cột trước (ví dụ: 'tion.' hoặc 'ments.'), bỏ qua
            if len(current) <= 2 and current[0][4][:1].islower():
                current = []
                continue
            stext, toks = _dehyphenate_words_text(current)
            if len(stext) >= 12:
                sentences.append((start_idx, idx, stext, toks))
            current = []

    if current:
        if not (len(current) <= 2 and current[0][4][:1].islower()):
            stext, toks = _dehyphenate_words_text(current)
            if len(stext) >= 12:
                sentences.append((start_idx, len(words) - 1, stext, toks))

    return sentences


def span_to_line_rects(words: List[tuple], start_idx: int, end_idx: int) -> List[fitz.Rect]:
    """Chuyển đổi một dải từ (start_idx..end_idx) trên trang thành danh sách các hình chữ nhật bao quanh từng dòng."""
    lines = defaultdict(list)
    for idx in range(start_idx, end_idx + 1):
        w = words[idx]
        lines[(w[5], w[6])].append(w)

    rects = []
    for key, lwords in sorted(lines.items(), key=lambda item: (min(w[1] for w in item[1]), min(w[0] for w in item[1]))):
        x0 = min(w[0] for w in lwords)
        y0 = min(w[1] for w in lwords)
        x1 = max(w[2] for w in lwords)
        y1 = max(w[3] for w in lwords)
        rects.append(fitz.Rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5))

    return rects


def _build_dehyphenated_page_tokens(words: List[tuple]) -> Tuple[List[str], List[Tuple[int, int]]]:
    """Xây dựng chuỗi token của trang PDF đã ghép nối các từ bị gạch nối cuối dòng,
    đồng thời lưu ánh xạ từng token về chỉ số từ gốc (word_start_idx, word_end_idx) trong `words`."""
    toks: List[str] = []
    spans: List[Tuple[int, int]] = []
    n = len(words)
    i = 0
    while i < n:
        w_str = words[i][4]
        if (
            i + 1 < n
            and re.search(r'[A-Za-z][-‐‑‒–\xad]$', w_str)
            and words[i + 1][6] != words[i][6]
            and re.match(r'^[a-z]{2,}', words[i + 1][4])
        ):
            merged = clean_tok(w_str[:-1] + words[i + 1][4])
            if merged:
                toks.append(merged)
                spans.append((i, i + 1))
                i += 2
                continue
        ct = clean_tok(w_str)
        if ct:
            toks.append(ct)
            spans.append((i, i))
        i += 1
    return toks, spans


def find_word_sequence_span(words: List[tuple], query_text: str) -> Optional[Tuple[int, int, str]]:
    """Tìm dải từ khớp chính xác hoặc mờ liên tục với truy vấn trích dẫn (hỗ trợ tự động nối từ bị gạch nối xuống dòng)."""
    dehyph_query = re.sub(r'([A-Za-z]{2,})[-‐‑‒–\xad]\s+([a-z]{2,})\b', r'\1\2', query_text or "")
    q_toks = [clean_tok(t) for t in dehyph_query.split() if clean_tok(t)]
    if not q_toks:
        return None

    page_toks, tok_spans = _build_dehyphenated_page_tokens(words)
    if not page_toks:
        return None
    m = len(q_toks)

    # 1. Khớp chính xác toàn bộ chuỗi token liên tục
    for i in range(len(page_toks) - m + 1):
        if page_toks[i : i + m] == q_toks:
            w_start = tok_spans[i][0]
            w_end = tok_spans[i + m - 1][1]
            stext, _ = _dehyphenate_words_text(words[w_start : w_end + 1])
            return (w_start, w_end, stext)

    # 2. Fuzzy SequenceMatcher qua difflib để lấy trọn vẹn cả đầu và cuối câu (kể cả khi có 1-2 từ sai khác nhỏ)
    matcher = difflib.SequenceMatcher(None, page_toks, q_toks)
    blocks = [b for b in matcher.get_matching_blocks() if b.size >= 2]
    if blocks:
        total_matched = sum(b.size for b in blocks)
        if total_matched >= 4 and (total_matched / m) >= 0.52:
            t_start = blocks[0].a
            t_end = blocks[-1].a + blocks[-1].size - 1
            if (t_end - t_start + 1) <= m * 1.50 + 4:
                w_start = tok_spans[t_start][0]
                w_end = tok_spans[t_end][1]
                stext, _ = _dehyphenate_words_text(words[w_start : w_end + 1])
                return (w_start, w_end, stext)

    # 3. Khớp chuỗi con dài nhất (Longest common sub-sequence contiguous match) nếu truy vấn dài
    if m >= 5:
        best_sub = None
        best_len = 0
        min_sub_len = max(4, int(m * 0.50))
        for sub_len in range(m, min_sub_len - 1, -1):
            for start_q in range(m - sub_len + 1):
                sub_q = q_toks[start_q : start_q + sub_len]
                for i in range(len(page_toks) - sub_len + 1):
                    if page_toks[i : i + sub_len] == sub_q:
                        if sub_len > best_len:
                            best_len = sub_len
                            best_sub = (tok_spans[i][0], tok_spans[i + sub_len - 1][1])
                            break
                if best_sub:
                    break
            if best_sub:
                break
        if best_sub and best_len >= 4 and (best_len / m) >= 0.50:
            stext, _ = _dehyphenate_words_text(words[best_sub[0] : best_sub[1] + 1])
            return (best_sub[0], best_sub[1], stext)

    return None


_ACADEMIC_VI_EN_MAP = {
    "tâm lý học tích cực": "positive psychology psychological interventions well-being",
    "can thiệp tâm lý tích cực": "positive psychology interventions psychological",
    "chiến lược bổ trợ": "complementary strategy",
    "quần thể chung": "general public population",
    "công chúng": "general public",
    "tâm lý xã hội": "psychosocial problems",
    "tiêu chí đưa vào": "inclusion criteria met",
    "tiêu chí lựa chọn": "inclusion criteria",
    "tự lực": "self-help",
    "cá nhân": "individual individuals",
    "theo nhóm": "group",
    "chất lượng": "quality moderators",
    "tâm lý học": "psychology psychological",
    "tâm lý": "psychology mental",
    "sức khỏe tâm thần": "mental health promotion well-being illness",
    "hạnh phúc chủ quan": "subjective well-being wellbeing",
    "hạnh phúc tâm lý": "psychological well-being wellbeing",
    "nhận thức": "cognitive cognition",
    "hành vi": "behavior behavioral",
    "nghiên cứu": "study studies research paper meta-analysis",
    "phân tích gộp": "meta-analysis meta-analytical systematic review pooled effect",
    "tổng quan hệ thống": "systematic literature search review",
    "kết quả": "results findings show standardized mean difference effect",
    "phương pháp": "methods methodology systematic literature search",
    "mô hình": "model framework architecture",
    "khái niệm": "concept concepts category definition",
    "định nghĩa": "definition defined state expressed",
    "phân loại": "categorization classification",
    "trí nhớ": "memory recall working",
    "chú ý": "attention visual",
    "cảm xúc": "emotion affective mood",
    "não bộ": "brain neural cortex",
    "thần kinh": "neural neuroscience neuron",
    "thị giác": "visual vision cortex",
    "thực nghiệm": "experiment empirical evaluation trial",
    "dữ liệu": "data dataset sample",
    "cỡ mẫu": "sample size participants studies totaling",
    "người tham gia": "participants subjects individuals sample",
    "hiệu quả": "effective effectiveness efficacy effect size",
    "kích thước hiệu ứng": "effect size sizes standardized mean difference",
    "theo dõi": "follow-up months sustainable",
    "điều trị": "treatment therapy intervention self-help group",
    "rối loạn": "disorder disorders syndrome clinical problems",
    "trầm cảm": "depression depressive mdd",
    "lo âu": "anxiety anxious gad",
    "tác giả": "author authors et al",
    "mục tiêu": "objective goal aim background",
    "kết luận": "conclusion conclusions discussion summary",
    "học máy": "machine learning deep",
    "con người": "human people subjects",
}


def _expand_bilingual_tokens(q_clean: str, base_tokens: set) -> set:
    """Mở rộng tập token truy vấn song ngữ Việt <-> Anh cho việc định vị câu nguồn trên PDF."""
    expanded = set(base_tokens)
    q_lower = q_clean.lower()
    for vi_phrase, en_words in _ACADEMIC_VI_EN_MAP.items():
        if vi_phrase in q_lower:
            for w in en_words.split():
                c = clean_tok(w)
                if len(c) >= 3 and c not in STOPWORDS:
                    expanded.add(c)
    try:
        from app.services.cross_lingual import (
            PSYCHOLOGY_GLOSSARY_VI_TO_EN,
            PSYCHOLOGY_GLOSSARY_EN_TO_VI,
            expand_query_terms_for_fts,
        )
        for vi_k, en_v in PSYCHOLOGY_GLOSSARY_VI_TO_EN.items():
            if len(vi_k) >= 4 and vi_k in q_lower:
                for t in en_v.split():
                    c = clean_tok(t)
                    if len(c) >= 3 and c not in STOPWORDS:
                        expanded.add(c)
        for en_k, vi_v in PSYCHOLOGY_GLOSSARY_EN_TO_VI.items():
            if len(en_k) >= 4 and en_k in q_lower:
                for t in vi_v.split():
                    c = clean_tok(t)
                    if len(c) >= 3 and c not in STOPWORDS:
                        expanded.add(c)
        for extra in expand_query_terms_for_fts(q_clean):
            for t in extra.split():
                c = clean_tok(t)
                if len(c) >= 3 and c not in STOPWORDS:
                    expanded.add(c)
    except Exception as e:
        logger.debug(f"Glossary expansion skip: {e}")
    return expanded


def _is_chart_or_table_line(ltext: str) -> bool:
    """Nhận diện dòng thuộc biểu đồ Forest Plot, trục tọa độ, hoặc ô số liệu bảng thống kê
    để ngăn chặn tuyệt đối việc vẽ hàng chục ô vàng rời rạc trên biểu đồ/bảng số."""
    if not ltext:
        return True
    s = ltext.strip()
    s_low = s.lower()

    # 1. Các nhãn đặc trưng của biểu đồ Forest Plot / Meta-Analysis / Trục đồ thị
    if any(p in s_low for p in (
        "statistics for each study",
        "std diff",
        "in means",
        "upper limit",
        "lower limit",
        "favours control",
        "favours ppi",
        "favours intervention",
        "favours treatment",
        "z-value",
        "p-value",
        "study name",
        "meta analysis",
        "random, 95% ci",
        "fixed, 95% ci",
        "test for overall effect",
        "sd standard deviation",
        "nr not reported",
        "table 1. continued",
        "table 2. continued",
        "table 3. continued",
    )):
        return True
    if re.match(r'^\s*(?:table|bảng|figure|fig\.?)\s+\d+\s*(?:\.\s*)?(?:continued|cont\.?)\b', s_low):
        return True
    if len(re.findall(r'\b[A-Z]{2,6}\s+[a-z]{3,}\s+[a-z]{3,}', s)) >= 3 and not re.search(r'\b(?:was|were|is|are|showed|found|examined|aimed|reported|conducted|demonstrated)\b', s_low):
        return True
    if s_low in ("upper", "lower", "limit", "limit limit", "total", "subtotal"):
        return True

    tokens = s.split()
    if not tokens:
        return True

    # Nếu dòng có động từ/giới từ câu văn xuôi chuẩn và kết thúc bằng dấu câu thì KHÔNG phải dòng trục đồ thị
    has_prose_structure = bool(
        re.search(r'\b(?:was|were|is|are|can|may|showed|found|examined|aimed|delivered|used|ranged|removed|suggests)\b', s_low)
    )
    if has_prose_structure:
        return False

    # 2. Dòng chứa toàn số thập phân / tọa độ trục (ví dụ: '-1,00 -0,50 0,00 0,50 1,00' hoặc '0,11 0,65 -0,43')
    num_tokens = sum(1 for t in tokens if re.match(r'^[+\-–—]?\d+(?:[.,]\d+)?%?$', t.strip('()[]')))
    if num_tokens >= 3 and (num_tokens / len(tokens)) >= 0.45:
        return True
    if len(tokens) <= 2 and num_tokens >= 1 and not s.endswith('.'):
        return True

    # 3. Dòng dữ liệu từng nghiên cứu trong Forest Plot (ví dụ: 'Abbott 2009 -0,06 0,48...' hoặc 'Abbott 2009 Cheavens 2006')
    author_year_hits = len(re.findall(r'\b[A-Z][a-zA-Z\'-]{1,20}\s+(?:19|20)\d{2}\b', s))
    if author_year_hits >= 1 and num_tokens >= 2:
        return True
    if author_year_hits >= 2 and not re.search(r'\b(?:is|are|was|were|showed|found|reported|conducted|included)\b', s_low):
        return True

    return False


def _is_boilerplate_sentence(stext: str) -> bool:
    """Kiểm tra xem câu có phải là Tiêu đề bài báo, Tác giả/Đơn vị công tác (Affiliation),
    Bảng số liệu / Forest Plot, hoặc mục Tài liệu tham khảo (References/Bibliography) không được phép trích dẫn."""
    if not stext:
        return True
    s_strip = stext.strip()
    words_list = s_strip.split()
    if len(words_list) < 6:
        return True
    s_low = s_strip.lower()

    # 0. Kiểm tra tỷ lệ chữ cái và mật độ số liệu để loại bỏ hoàn toàn dòng bảng biểu / Forest Plot
    non_space = re.sub(r'\s+', '', s_strip)
    if not non_space:
        return True
    alpha_chars = sum(1 for c in non_space if c.isalpha())
    if (alpha_chars / len(non_space)) < 0.45:
        return True
    if _is_chart_or_table_line(s_strip):
        return True

    # 1. Email, DOI, URL, bản quyền, nhãn loại bài báo, Disclosures ở đầu/cuối trang
    if any(m in s_low for m in (
        "email:", "e-mail", "@", "arxiv:", "doi:", "doi.org", "http://", "https://",
        "all rights reserved", "macmillan publishers", "springer nature", "biomed central",
        "licensee biomed", "creative commons attribution", "full list of author information",
        "original paper", "research article", "review article", "short communication",
        "case report", "published:", "received:", "accepted:", "available online",
        "corresponding author", "contributed equally", "conflict of interest",
        "competing interests", "ethics approval", "funding:", "acknowledgements",
        "nothing to disclose", "personal fees", "open access", "creative commons",
        "author contributions", "compliance with ethical standards",
    )):
        return True

    # 2. Đơn vị công tác (Affiliations) ở mọi trang
    if re.search(
        r'\b(?:department\s+of|division\s+of|faculty\s+of|school\s+of|institute\s+of|key\s+laboratory|'
        r'general\s+surgery\s+department|surgery\s+department|medicine\s+department|'
        r'university\s+of|university\s+college|university\s+hospital|universit[aäàeéio]\w*|'
        r'medical\s+center|medical\s+centre|medical\s+university|general\s+hospital|'
        r'nhs\s+foundation|centre\s+(?:for|of)|center\s+(?:for|of)|ministry\s+of\s+health)\b',
        s_low,
    ) and len(words_list) < 55:
        return True
    if re.match(r'^\s*\d{1,2}\s+[A-Z]', s_strip) and re.search(
        r'\b(?:department|division|unit|hospital|university|universit\w*|institute|faculty|school|clinic|center|centre|laboratory)\b',
        s_low,
    ):
        return True

    # 3. Nhận diện câu thuộc danh mục Tài liệu tham khảo (References / Bibliography)
    if re.match(r'^\s*(?:\[\d{1,3}\]|\d{1,3}\.)\s+[A-Z][a-zA-Z\'-]+', s_strip):
        return True
    if re.match(r'^\s*[A-Z][a-zA-Z\'-]+,\s+(?:[A-Z]\.\s*)+', s_strip) and re.search(r'\b(?:19|20)\d{2}[a-z]?\b', s_strip):
        return True
    if re.match(
        r'^\s*[A-Z][a-z]{1,15}\s+(?:[A-Z][a-zA-Z.]*\s+)?[A-Z][a-zA-Z\u00C0-\u017F\'-]{1,20}(?:,\s+(?:and\s+)?|\s+and\s+)[A-Z][a-z]{1,15}\s+',
        s_strip,
    ):
        return True
    if re.search(r'\b(?:in\s+proceedings\s+of|arxiv\s+preprint|pages\s+\d+[–\-]\d+)\b', s_low):
        return True
    if re.search(r'\b\d{1,4}\s*\(\s*\d{1,3}\s*\)\s*[,:]\s*\d+(?:[–\-]\d+)?\b|\bpp\.\s*\d+(?:[–\-]\d+)?\b', s_strip, re.I):
        return True
    try:
        from app.services.reference_filter import is_reference_content
        if is_reference_content(s_strip):
            return True
    except Exception:
        pass

    return False


def _is_reference_or_meta_in_context(
    sentences: List[Tuple[int, int, str, set]],
    idx: int,
) -> bool:
    """Kiểm tra câu thứ `idx` cùng cửa sổ câu lân cận.
    Ngăn chặn triệt để việc bôi vàng câu tiêu đề bài báo nằm kẹp giữa tên tác giả và tên tạp chí/DOI
    bên trong danh mục References hoặc danh sách Affiliations."""
    if idx < 0 or idx >= len(sentences):
        return True
    stext = sentences[idx][2]
    if _is_boilerplate_sentence(stext):
        return True
    try:
        from app.services.reference_filter import is_reference_content
        lo = max(0, idx - 2)
        hi = min(len(sentences), idx + 3)
        window_text = "\n".join(sentences[k][2] for k in range(lo, hi))
        if is_reference_content(window_text):
            return True
    except Exception:
        pass
    return False


def _snap_and_expand_evidence_span(
    words: List[tuple],
    sentences: List[Tuple[int, int, str, set]],
    raw_span: Optional[Tuple[int, int, str]],
    excerpt_hint: str = "",
    claim_query: str = "",
) -> Optional[Tuple[int, int, str]]:
    """Làm tròn dải từ khớp về trọn vẹn biên giới 1–2 câu bằng chứng cụ thể (không cắt cụt đầu/cuối câu,
    và không bôi lan sang cả đoạn dài không liên quan)."""
    if not raw_span or not words:
        return None
    raw_s, raw_e, _ = raw_span
    if not sentences:
        text_joined, _ = _dehyphenate_words_text(words[raw_s : raw_e + 1])
        if _is_boilerplate_sentence(text_joined):
            return None
        return (raw_s, raw_e, text_joined)

    # Tìm tất cả các câu giao cắt với raw_span
    overlapping_indices = [
        i
        for i, (s_idx, e_idx, _, _) in enumerate(sentences)
        if not (e_idx < raw_s or s_idx > raw_e)
    ]
    if not overlapping_indices:
        return None

    # Loại bỏ các câu thuộc References / Affiliations / Boilerplate / Bảng số
    valid_indices = [
        i for i in overlapping_indices if not _is_reference_or_meta_in_context(sentences, i)
    ]
    if not valid_indices:
        return None

    q_clean = normalize_text(claim_query or "")
    q_toks = _expand_bilingual_tokens(
        q_clean,
        {clean_tok(t) for t in q_clean.split() if clean_tok(t) and clean_tok(t) not in STOPWORDS},
    ) if q_clean else set()
    anchors = [clean_tok(a) for a in extract_evidence_anchors(q_clean) if clean_tok(a)]

    # Nếu raw_span quá rộng (ví dụ khớp cả đoạn > 2 câu), chọn 1-2 câu có điểm khớp cao nhất với claim_query
    if len(valid_indices) > 1 and q_toks:
        scored_valid = []
        for i in valid_indices:
            _, _, _, s_toks = sentences[i]
            ov = len(s_toks.intersection(q_toks))
            anc_h = sum(1 for a in anchors if any(a in tok for tok in s_toks))
            scored_valid.append((ov + 3.5 * anc_h, i))
        scored_valid.sort(key=lambda x: x[0], reverse=True)
        best_i = scored_valid[0][1]
        valid_indices = [best_i]

    first_i = min(valid_indices)
    last_i = max(valid_indices)

    # Chỉ mở rộng thêm tối đa 1 câu liền sau nếu câu hiện tại ngắn (< 24 từ), cùng đoạn văn,
    # và câu kế tiếp cũng khớp trực tiếp với claim_query (tổng độ dài <= 68 từ)
    cur_s = sentences[first_i][0]
    cur_e = sentences[last_i][1]
    cur_len = cur_e - cur_s + 1
    if cur_len < 10 and (last_i + 1) < len(sentences) and q_toks:
        next_i = last_i + 1
        if not _is_reference_or_meta_in_context(sentences, next_i):
            next_s, next_e, _, next_toks = sentences[next_i]
            same_block = (words[next_s][5] == words[cur_e][5])
            if same_block and (next_e - cur_s + 1) <= 68 and len(next_toks.intersection(q_toks)) >= 2:
                last_i = next_i

    final_s = sentences[first_i][0]
    final_e = sentences[last_i][1]
    final_text, _ = _dehyphenate_words_text(words[final_s : final_e + 1])
    return (final_s, final_e, final_text)


def _filter_body_words_on_page(page: fitz.Page, words: List[tuple]) -> List[tuple]:
    """Loại bỏ triệt để:
    1. Phần Tiêu đề bài báo (Title), Tên tác giả (Authors), Đơn vị công tác (Affiliations) ở đầu Trang 1.
    2. Toàn bộ mục Tài liệu tham khảo (References / Bibliography / Acknowledgements / Affiliations) từ tiêu đề mục trở xuống.
    3. Các dòng biểu đồ Forest Plot, bảng số liệu thống kê rời rạc và running header / footer.
    """
    if not words:
        return words

    page_h = float(page.rect.height or 800.0)
    is_first_page = (page.number == 0)

    # Nhóm từ theo từng dòng (block_no, line_no)
    line_groups = defaultdict(list)
    for w in words:
        line_groups[(w[5], w[6])].append(w)

    body_y_start = page_h * 0.045
    ref_y_cutoff = page_h * 0.945

    # Xác định vùng Title font lớn ở đầu Trang 1 thông qua page.get_text("dict")
    title_blocks_y1 = 0.0
    if is_first_page:
        try:
            pdict = page.get_text("dict")
            for blk in pdict.get("blocks", []):
                if blk.get("type") != 0:
                    continue
                bbox = blk.get("bbox", (0, 0, 0, 0))
                if bbox[1] > page_h * 0.42:
                    continue
                max_sz = 0.0
                blk_text = []
                for ln in blk.get("lines", []):
                    for sp in ln.get("spans", []):
                        max_sz = max(max_sz, float(sp.get("size", 0.0)))
                        blk_text.append(sp.get("text", ""))
                joined_blk = " ".join(blk_text).strip()
                if max_sz >= 13.5 and len(joined_blk.split()) <= 35:
                    title_blocks_y1 = max(title_blocks_y1, float(bbox[3]))
        except Exception:
            pass

    abstract_y1 = 0.0
    excluded_line_keys = set()

    for lkey, lwords in sorted(line_groups.items(), key=lambda item: min(w[1] for w in item[1])):
        lx0 = min(w[0] for w in lwords)
        lx1 = max(w[2] for w in lwords)
        ly0 = min(w[1] for w in lwords)
        ly1 = max(w[3] for w in lwords)
        ltext = " ".join(w[4] for w in lwords).strip()
        lclean = re.sub(r'^[\d.\s#]+', '', ltext).strip().lower().rstrip(':.')

        # Loại bỏ các dòng chữ xoay dọc 90 độ (bảng xoay ngang landscape hoặc lề dọc arXiv)
        if (ly1 - ly0) > 26.0 and (lx1 - lx0) < (ly1 - ly0) * 0.85:
            excluded_line_keys.add(lkey)
            continue

        # Loại bỏ các dòng thuộc biểu đồ Forest Plot / trục số / bảng số liệu
        if _is_chart_or_table_line(ltext):
            excluded_line_keys.add(lkey)

        # Trên Trang 1: Tìm tiêu đề Abstract / Tóm tắt để bỏ toàn bộ Title + Author + Affiliation phía trên
        if is_first_page and ly0 < page_h * 0.65 and abstract_y1 == 0.0:
            if lclean in ("abstract", "tóm tắt", "summary") or re.match(r'^abstract\b', ltext.strip(), re.I):
                if len(lwords) <= 3:
                    abstract_y1 = ly1
                else:
                    abstract_y1 = ly0 - 1.0

        # Trên mọi trang: Tìm tiêu đề References / Affiliations / Acknowledgements / Disclosures để cắt bỏ từ đó trở xuống
        if lclean in (
            "references", "reference", "bibliography", "tài liệu tham khảo",
            "literature cited", "works cited", "acknowledgements", "acknowledgments",
            "affiliations", "affiliation", "author information", "author contributions",
            "compliance with ethical standards", "competing interests", "conflict of interest",
            "conflicts of interest", "declarations", "disclosures",
        ) and len(lwords) <= 5 and ly0 > page_h * 0.08:
            ref_y_cutoff = min(ref_y_cutoff, ly0 - 1.0)

        # Cắt bỏ phần footnote bản quyền / author info ở cuối Trang 1
        if is_first_page and ly0 > page_h * 0.78:
            if any(m in ltext.lower() for m in (
                "full list of author information",
                "licensee biomed central",
                "creative commons attribution",
                "correspondence:",
                "corresponding author",
            )):
                ref_y_cutoff = min(ref_y_cutoff, ly0 - 1.0)

    if is_first_page:
        if abstract_y1 > 0.0:
            body_y_start = max(body_y_start, abstract_y1)
        elif title_blocks_y1 > 0.0:
            body_y_start = max(body_y_start, title_blocks_y1 + 2.0)

    filtered_words = [
        w for w in words
        if w[1] >= body_y_start
        and w[3] <= ref_y_cutoff
        and (w[5], w[6]) not in excluded_line_keys
        and not ((w[3] - w[1]) > 22.0 and (w[3] - w[1]) > (w[2] - w[0]) * 1.5)
    ]
    if ref_y_cutoff < page_h * 0.90:
        return filtered_words

    if not is_first_page and filtered_words:
        try:
            from app.services.reference_filter import is_reference_content
            page_txt = page.get_text("text") or ""
            half = len(page_txt) // 2
            if is_reference_content(page_txt) and (half < 150 or is_reference_content(page_txt[:half])):
                return []
        except Exception:
            pass
    if len(filtered_words) >= 8:
        return filtered_words
    if is_first_page and title_blocks_y1 > 0.0:
        fallback_words = [
            w for w in words
            if w[1] > title_blocks_y1 + 1.0 and w[3] <= ref_y_cutoff and (w[5], w[6]) not in excluded_line_keys
        ]
        if len(fallback_words) >= 8:
            return fallback_words
    return filtered_words


_NUM_WORD_TO_DIGIT = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "twenty": "20", "thirty": "30",
    "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
    "eighty": "80", "ninety": "90",
}
_DIGIT_TO_NUM_WORD = {v: k for k, v in _NUM_WORD_TO_DIGIT.items()}


def _expand_numeric_and_token_variants(tokens: set) -> set:
    expanded = set(tokens)
    for t in list(tokens):
        if t in _NUM_WORD_TO_DIGIT:
            expanded.add(_NUM_WORD_TO_DIGIT[t])
        if t in _DIGIT_TO_NUM_WORD:
            expanded.add(_DIGIT_TO_NUM_WORD[t])
        if re.match(r'^\d{1,3}[.,]\d{3}$', t):
            expanded.add(t.replace('.', ','))
            expanded.add(t.replace(',', '.'))
            expanded.add(re.sub(r'[.,]', '', t))
        elif re.match(r'^\d+[.,]\d{1,2}%?$', t):
            expanded.add(t.replace(',', '.'))
            expanded.add(t.replace('.', ','))
    return expanded


def ground_sentence_semantically(
    words: List[tuple],
    sentences: List[Tuple[int, int, str, set]],
    query_text: str,
    hint_sentence_indices: Optional[set] = None,
) -> Optional[Tuple[int, int, str]]:
    """Định vị câu nguồn chuẩn xác nhất trên trang PDF bằng IDF nội trang, đối chiếu số liệu song ngữ và mỏ neo chứng cứ."""
    q_clean = normalize_text(query_text)
    q_raw_tokens = [clean_tok(t) for t in q_clean.split() if clean_tok(t) and clean_tok(t) not in STOPWORDS]
    if not q_raw_tokens:
        return None
    q_tokens = _expand_numeric_and_token_variants(_expand_bilingual_tokens(q_clean, set(q_raw_tokens)))

    # 1. Tách riêng mỏ neo số liệu thực nghiệm (Hard Numeric Anchors) và mỏ neo thuật ngữ
    num_anchor_groups: List[set] = []
    for num_m in re.finditer(r'\b\d+(?:[.,]\d+)?%|\b\d{1,3}[.,]\d{3}\b|\b\d+[.,]\d{1,2}\b|\b\d{1,4}\b', q_clean):
        ns = clean_tok(num_m.group(0))
        if not ns or re.match(r'^(?:19|20)\d{2}$', ns):
            continue
        grp = _expand_numeric_and_token_variants({ns})
        num_anchor_groups.append(grp)

    en_phrases = [p.lower() for p in extract_english_phrases_from_claim(q_clean) if len(p.split()) >= 2]
    anchors = [clean_tok(a) for a in extract_evidence_anchors(q_clean) if clean_tok(a)]

    # 2. Tính Page-level IDF cho từng token trên trang để từ khóa đặc trưng thắng từ khóa lặp lại toàn trang
    n_sents = max(1, len(sentences))
    norm_sent_toks: List[set] = [_expand_numeric_and_token_variants(s_toks) for _, _, _, s_toks in sentences]
    df_map: Dict[str, int] = defaultdict(int)
    for st_set in norm_sent_toks:
        for tok in st_set:
            df_map[tok] += 1

    best_idx = -1
    best_score = 0.0
    denom = max(4.0, float(min(len(q_tokens), 16)))

    for idx, (s_idx, e_idx, stext, s_toks) in enumerate(sentences):
        if not s_toks or _is_reference_or_meta_in_context(sentences, idx):
            continue
        st_norm = norm_sent_toks[idx]
        overlap = q_tokens.intersection(st_norm)
        idf_overlap_score = sum(
            1.0 + math.log((n_sents + 1.0) / (df_map.get(tok, 1) + 0.5))
            for tok in overlap
        )
        num_hits = sum(1 for grp in num_anchor_groups if grp.intersection(st_norm))
        lex_anchor_hits = sum(
            1 for a in anchors
            if not any( c.isdigit() for c in a )
            and any(a == tok or (len(a) >= 5 and a in tok) for tok in st_norm)
            and df_map.get(a, 1) <= max(2, n_sents // 3)
        )
        stext_low = stext.lower()
        phrase_bonus = 0.0
        for ph in en_phrases:
            if ph in stext_low:
                ph_df = sum(1 for _, _, other_s, _ in sentences if ph in other_s.lower())
                phrase_bonus += (3.0 * min(5, len(ph.split()))) / (1.0 + 0.8 * max(0, ph_df - 1))

        hint_bonus = 0.20 if (hint_sentence_indices and idx in hint_sentence_indices) else 0.0

        if not overlap and num_hits == 0 and phrase_bonus == 0.0:
            continue

        score = (idf_overlap_score + 7.5 * num_hits + 2.0 * lex_anchor_hits + phrase_bonus + hint_bonus) / denom
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx >= 0 and best_score >= 0.12:
        s_idx, e_idx, stext, _ = sentences[best_idx]
        # Chỉ mở rộng sang câu kế tiếp nếu câu hiện tại quá ngắn (< 10 từ, ví dụ tiêu đề mục 'Results:')
        if (e_idx - s_idx + 1) < 10 and best_idx + 1 < len(sentences):
            ns_idx, ne_idx, ntext, ns_toks = sentences[best_idx + 1]
            same_block = (words[ns_idx][5] == words[e_idx][5])
            if (
                same_block
                and (ne_idx - s_idx + 1) <= 55
                and not _is_reference_or_meta_in_context(sentences, best_idx + 1)
            ):
                e_idx = ne_idx
                stext = f"{stext} {ntext}".strip()
        return (s_idx, e_idx, stext)
    return None


def ground_and_search_page_rects(
    page: fitz.Page,
    query: str,
    page_chunks: Optional[List[str]] = None,
) -> Tuple[List[fitz.Rect], str, List[str]]:
    """Thuật toán Smart Evidence Grounding chuẩn xác cao:
    Định vị chính xác 1–2 câu văn nguồn trên trang PDF khớp với nhận định được trích dẫn (claim_query).
    
    Quy tắc cốt lõi:
    - Tuyệt đối KHÔNG bôi vàng Tiêu đề bài báo, Tên tác giả/Đơn vị công tác, Biểu đồ Forest Plot/Bảng số, hoặc mục Tài liệu tham khảo.
    - Ưu tiên đối chiếu mệnh đề cụ thể (claim_query) mà người dùng vừa bấm trích dẫn để chỉ bôi vàng đúng 1–2 câu chứa bằng chứng đó (không bôi tràn cả đoạn chunk 900 ký tự).
    """
    rects: List[fitz.Rect] = []
    grounded_sentence = ""
    highlighted_terms: List[str] = []

    raw_words = page.get_text("words")
    if not raw_words:
        return rects, grounded_sentence, highlighted_terms

    # Lọc bỏ vùng Title/Author ở đầu Trang 1, các dòng biểu đồ/bảng số, và vùng References/Affiliations
    words = _filter_body_words_on_page(page, raw_words)
    if not words:
        return rects, grounded_sentence, highlighted_terms
    sentences = segment_page_into_sentences(words)
    if not sentences:
        return rects, grounded_sentence, highlighted_terms

    raw_query = re.sub(r'^\[(?:Trang|Page)\s+\d+\]\s*', '', normalize_text(query or ""), flags=re.I).strip()
    excerpt_hint = ""
    claim_query = raw_query
    if " || " in raw_query:
        parts = raw_query.split(" || ", 1)
        excerpt_hint = parts[0].strip()
        claim_query = parts[1].strip() or ""
    elif len(raw_query) > 320:
        excerpt_hint = raw_query
        claim_query = ""

    # Nếu câu trả lời là câu từ chối / không có thông tin -> tuyệt đối không bôi vàng
    if claim_query and re.search(
        r'(?i)(?:không đề cập trực tiếp|dựa vào kiến thức chung|không có thông tin|không tìm thấy thông tin|chưa tìm thấy đủ bằng chứng|no sufficient evidence)',
        claim_query,
    ):
        return rects, grounded_sentence, highlighted_terms

    try:
        from app.services.reference_filter import clean_front_matter_header, clean_reference_boundary, is_reference_content
        if excerpt_hint:
            excerpt_hint = clean_reference_boundary(clean_front_matter_header(excerpt_hint))
            if is_reference_content(excerpt_hint):
                excerpt_hint = ""
    except Exception:
        pass

    # Xác định tập các câu trên trang thuộc về excerpt_hint (đoạn chunk được truy xuất)
    hint_sentence_indices: set = set()
    if excerpt_hint:
        hint_toks = {clean_tok(t) for t in excerpt_hint.split() if clean_tok(t) and clean_tok(t) not in STOPWORDS}
        if hint_toks:
            for idx, (_, _, _, s_toks) in enumerate(sentences):
                if s_toks and not _is_reference_or_meta_in_context(sentences, idx):
                    overlap_ratio = len(s_toks.intersection(hint_toks)) / max(1, len(s_toks))
                    if overlap_ratio >= 0.45 and len(s_toks.intersection(hint_toks)) >= 3:
                        hint_sentence_indices.add(idx)

    span: Optional[Tuple[int, int, str]] = None

    # ── BƯỚC 1: Chỉ khớp chuỗi nguyên văn trực tiếp khi có trích dẫn dài đặc trưng (>= 5 từ, xuất hiện duy nhất 1 lần) ──
    if claim_query:
        en_phrases = [p for p in extract_english_phrases_from_claim(claim_query) if len(p.split()) >= 5]
        for phrase in en_phrases:
            ph_hits = sum(1 for _, _, st_other, _ in sentences if phrase.lower() in st_other.lower())
            if ph_hits <= 1:
                cand = find_word_sequence_span(words, phrase)
                if cand and (cand[1] - cand[0] + 1) <= 55:
                    span = _snap_and_expand_evidence_span(words, sentences, cand, excerpt_hint, claim_query)
                    if span:
                        break
        if not span and re.search(r'["“\'«][^"”\'»\n]{20,350}["”\'»]', claim_query):
            core_quote = extract_quote_candidate(claim_query)
            if core_quote and core_quote != claim_query and len(core_quote.split()) >= 5:
                cand_q = find_word_sequence_span(words, core_quote)
                if cand_q and (cand_q[1] - cand_q[0] + 1) <= 55:
                    span = _snap_and_expand_evidence_span(words, sentences, cand_q, excerpt_hint, claim_query)

    # ── BƯỚC 2: Định vị chính xác câu bằng chứng theo claim_query (mệnh đề người dùng vừa bấm trích dẫn) ──
    if not span and claim_query:
        cand_sem = ground_sentence_semantically(
            words, sentences, claim_query, hint_sentence_indices=hint_sentence_indices
        )
        if cand_sem:
            span = _snap_and_expand_evidence_span(words, sentences, cand_sem, excerpt_hint, claim_query)

    # ── BƯỚC 3: Nếu chưa tìm thấy, chọn câu hoàn chỉnh giàu thông tin nhất bên trong excerpt_hint ──
    if not span and excerpt_hint:
        # Tách excerpt_hint thành từng câu đơn lẻ (không bao giờ bôi tràn cả chunk 900 ký tự)
        raw_hint_sents = [
            s.strip()
            for s in re.split(r'(?<=[.!?])\s+|\n+', excerpt_hint)
            if len(s.strip().split()) >= 7 and not _is_boilerplate_sentence(s.strip())
        ]
        # Loại bỏ câu đầu nếu bị cắt cụt từ ở ranh giới chunk (bắt đầu bằng chữ thường)
        hint_sents = [s for s in raw_hint_sents if not s[0].islower()] or raw_hint_sents
        if hint_sents:
            q_toks = _expand_bilingual_tokens(
                claim_query or excerpt_hint,
                {clean_tok(t) for t in (claim_query or excerpt_hint).split() if clean_tok(t) and clean_tok(t) not in STOPWORDS},
            )
            anchors = [clean_tok(a) for a in extract_evidence_anchors(claim_query or excerpt_hint) if clean_tok(a)]

            def _score_hint_sent(s: str) -> float:
                st = {clean_tok(t) for t in s.split() if clean_tok(t) and clean_tok(t) not in STOPWORDS}
                ov = len(q_toks.intersection(st)) if claim_query else 0
                anc_h = sum(1 for a in anchors if any(a == tok or (len(a) >= 4 and a in tok) for tok in st))
                return ov * 2.0 + anc_h * 3.5 + min(len(st), 18) * 0.25

            best_hint_sent = max(hint_sents, key=_score_hint_sent)
            cand_hs = find_word_sequence_span(words, best_hint_sent)
            if not cand_hs:
                cand_hs = ground_sentence_semantically(words, sentences, best_hint_sent, hint_sentence_indices)
            if cand_hs:
                span = _snap_and_expand_evidence_span(words, sentences, cand_hs, excerpt_hint, claim_query or best_hint_sent)

    # ── BƯỚC 4: Đối chiếu qua các đoạn Chunk đã lập chỉ mục của trang từ Database ──
    if not span and page_chunks:
        clean_q = claim_query or excerpt_hint
        q_toks = _expand_bilingual_tokens(
            clean_q,
            {clean_tok(t) for t in clean_q.split() if clean_tok(t) and clean_tok(t) not in STOPWORDS},
        ) if clean_q else set()

        valid_chunks = []
        for ch in page_chunks:
            ch_clean = re.sub(r'^\[(?:Trang|Page)\s+\d+\]\s*', '', ch, flags=re.I).strip()
            try:
                from app.services.reference_filter import clean_front_matter_header, clean_reference_boundary, is_reference_content
                ch_clean = clean_reference_boundary(clean_front_matter_header(ch_clean))
                if not ch_clean or is_reference_content(ch_clean):
                    continue
            except Exception:
                pass
            if ch_clean and not _is_chart_or_table_line(ch_clean[:120]):
                valid_chunks.append(ch_clean)

        if valid_chunks:
            best_chunk = max(
                valid_chunks,
                key=lambda c: len(q_toks.intersection({clean_tok(t) for t in c.split() if clean_tok(t)})),
            )
            chunk_sents = [
                s.strip()
                for s in re.split(r'(?<=[.!?])\s+|\n{2,}', best_chunk)
                if len(s.strip().split()) >= 7 and not _is_boilerplate_sentence(s.strip()) and not s.strip()[0].islower()
            ]
            if chunk_sents:
                target_excerpt = max(
                    chunk_sents,
                    key=lambda s: len(q_toks.intersection({clean_tok(t) for t in s.split() if clean_tok(t)})),
                ) if q_toks else chunk_sents[0]
                cand_ch = find_word_sequence_span(words, target_excerpt)
                if not cand_ch:
                    cand_ch = ground_sentence_semantically(words, sentences, target_excerpt)
                if cand_ch:
                    span = _snap_and_expand_evidence_span(words, sentences, cand_ch, best_chunk, clean_q)

    # ── BƯỚC 5: Fallback bảo toàn bằng chứng trang (chỉ chọn 1 câu văn xuôi khoa học chuẩn, KHÔNG chọn Title/Ref/Bảng) ──
    if not span and sentences:
        body_candidates = [
            (s_idx, e_idx, stext)
            for idx, (s_idx, e_idx, stext, _) in enumerate(sentences)
            if 10 <= (e_idx - s_idx + 1) <= 55
            and not stext[0].islower()
            and not _is_reference_or_meta_in_context(sentences, idx)
        ]
        if body_candidates:
            span = _snap_and_expand_evidence_span(words, sentences, body_candidates[0], excerpt_hint, claim_query)

    # ── BƯỚC 6: Tạo hình chữ nhật bao quanh dải từ đã định vị ──
    if span:
        s_idx, e_idx, text_matched = span
        grounded_sentence = text_matched
        rects = span_to_line_rects(words, s_idx, e_idx)
        highlighted_terms.append(text_matched[:80] + ("..." if len(text_matched) > 80 else ""))

    return rects, grounded_sentence, highlighted_terms


def search_page_rects(page: fitz.Page, query: str) -> List[fitz.Rect]:
    """Hàm tìm kiếm tọa độ bounding boxes trên trang (tương thích ngược)."""
    rects, _, _ = ground_and_search_page_rects(page, query)
    return rects


def generate_highlighted_pdf_stream(
    file_path: str,
    page_number: int,
    query: Optional[str] = None,
    page_chunks: Optional[List[str]] = None,
) -> bytes:
    """Tạo tệp PDF mới với các highlight màu vàng dạ quang được phủ trực tiếp lên trang được chỉ định."""
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        if not (1 <= page_number <= total_pages):
            return doc.tobytes()

        target_page_idx = page_number - 1
        page = doc[target_page_idx]

        rects, _, _ = ground_and_search_page_rects(page, query or "", page_chunks=page_chunks)
        rects = [r for r in rects if (r.y1 - r.y0) <= 26.0 and (r.x1 - r.x0) >= (r.y1 - r.y0)]
        if rects:
            # Vẽ lớp phủ highlight hình chữ nhật màu vàng dạ quang sắc nét trực tiếp lên content stream
            for r in rects:
                try:
                    page.draw_rect(
                        r,
                        color=(0.95, 0.65, 0.05),
                        width=0.4,
                        fill=(1.0, 0.92, 0.18),
                        fill_opacity=0.38,
                        overlay=True,
                    )
                except Exception:
                    pass

        return doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()


def get_highlight_metadata(
    file_path: str,
    page_number: int,
    query: str,
    page_chunks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Lấy danh sách tọa độ bounding boxes và câu nguyên văn đối chứng từ trang PDF."""
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        if not (1 <= page_number <= total_pages):
            return {"page": page_number, "rects": [], "terms": [], "grounded_sentence": ""}

        page = doc[page_number - 1]
        rects, grounded_sentence, terms = ground_and_search_page_rects(page, query, page_chunks=page_chunks)

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
