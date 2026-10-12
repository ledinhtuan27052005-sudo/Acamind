"""
Module xử lý Đa Ngôn Ngữ & Dịch Truy Vấn Chéo (Cross-Lingual Information Retrieval & Generation)
cho hệ thống Acamind.
- Tự động nhận diện ngôn ngữ câu hỏi (Tiếng Việt / Tiếng Anh)
- Từ điển thuật ngữ Tâm lý học đối chiếu chuẩn DSM-5 / ICD-11 / APA
- Dịch và mở rộng truy vấn (Cross-Lingual Query Expansion) phục vụ song song Vector Search và Postgres FTS
"""
import re
import logging
import unicodedata
from app.services.llm_client import get_default_client

logger = logging.getLogger(__name__)
llm_client = get_default_client()

# Cache dịch câu hỏi trong bộ nhớ để tái sử dụng tức thì
_TRANSLATION_CACHE: dict[str, str] = {}

# Ký tự có dấu đặc trưng của tiếng Việt
_VI_CHARS = set("áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
                "ÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ")

# Từ vựng tiếng Việt phổ biến (kể cả khi không dấu)
_VI_STOPWORDS_NO_ACCENT = {
    "la", "gi", "nhu", "the", "nao", "cua", "trong", "va", "cac", "nhung",
    "nguoi", "dieu", "tri", "tai", "lieu", "tam", "ly", "hoc", "benh",
    "chuan", "doan", "trieu", "chung", "phuong", "phap", "suy", "nghi",
    "cam", "xuc", "hanh", "vi", "lo", "au", "tram", "roi", "loan", "nang",
    "kho", "khan", "bac", "si", "chuyen", "gia", "phac", "do", "y", "khoa"
}

# Từ vựng tiếng Anh phổ biến
_EN_WORDS = {
    "what", "is", "how", "to", "the", "in", "of", "and", "a", "an", "for",
    "depression", "anxiety", "cbt", "ocd", "bipolar", "stress", "hello", "hi",
    "who", "why", "where", "affect", "people", "psychology", "disorder",
    "mental", "health", "treatment", "therapy", "symptoms", "diagnosis",
    "criteria", "cognitive", "behavioral", "patients", "clinical", "study"
}

def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt chuẩn NFKD."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).replace('đ', 'd').replace('Đ', 'D')


# ── Từ điển thuật ngữ Tâm lý học đối chiếu song ngữ (Bilingual Psychology Glossary) ──
# Dùng để mở rộng từ khóa truy vấn FTS / BM25 ngay tức thì (~0ms)
PSYCHOLOGY_GLOSSARY_VI_TO_EN: dict[str, str] = {
    # Các chuyên ngành & Khái niệm Tâm lý học nền tảng
    "tâm lý học": "psychology psychological science",
    "tâm lý học nhận thức": "cognitive psychology cognition",
    "nhận thức": "cognitive cognition",
    "tâm lý học lâm sàng": "clinical psychology",
    "tâm lý học xã hội": "social psychology",
    "tâm lý học phát triển": "developmental psychology",
    "tâm lý học thần kinh": "neuropsychology cognitive neuroscience",
    "khoa học nhận thức": "cognitive science",
    "tâm lý học hành vi": "behavioral psychology behaviorism",
    "tâm lý học nhân văn": "humanistic psychology",
    "tâm lý học tích cực": "positive psychology",

    # Rối loạn & Bệnh lý tâm thần
    "trầm cảm": "depression major depressive disorder MDD",
    "lo âu": "anxiety generalized anxiety disorder GAD",
    "rối loạn lo âu": "anxiety disorder generalized anxiety GAD",
    "rối loạn lo âu lan tỏa": "generalized anxiety disorder GAD",
    "rối loạn ám ảnh cưỡng chế": "obsessive compulsive disorder OCD",
    "ám ảnh cưỡng chế": "obsessive compulsive disorder OCD",
    "rối loạn lưỡng cực": "bipolar disorder mania manic depressive",
    "lưỡng cực": "bipolar disorder",
    "tâm thần phân liệt": "schizophrenia psychotic psychosis",
    "rối loạn sau sang chấn": "post traumatic stress disorder PTSD",
    "sang chấn tâm lý": "trauma psychological trauma PTSD",
    "sang chấn": "trauma PTSD",
    "ptsd": "post traumatic stress disorder PTSD",
    "tự kỷ": "autism spectrum disorder ASD",
    "tăng động giảm chú ý": "attention deficit hyperactivity disorder ADHD",
    "adhd": "attention deficit hyperactivity disorder ADHD",
    "rối loạn nhân cách": "personality disorder",
    "rối loạn nhân cách ranh giới": "borderline personality disorder BPD",
    "rối loạn ăn uống": "eating disorder anorexia bulimia",
    "mất ngủ": "insomnia sleep disorder",
    "hoảng loạn": "panic disorder panic attack",
    "ám ảnh sợ xã hội": "social anxiety disorder social phobia",
    "ám ảnh sợ": "phobia specific phobia",
    
    # Liệu pháp & Phương pháp can thiệp
    "nhận thức hành vi": "cognitive behavioral therapy CBT",
    "liệu pháp nhận thức hành vi": "cognitive behavioral therapy CBT",
    "cbt": "cognitive behavioral therapy CBT",
    "liệu pháp hành vi biện chứng": "dialectical behavior therapy DBT",
    "dbt": "dialectical behavior therapy DBT",
    "liệu pháp chấp nhận và cam kết": "acceptance and commitment therapy ACT",
    "act": "acceptance and commitment therapy ACT",
    "phân tâm học": "psychoanalysis psychodynamic",
    "phân tâm": "psychoanalysis psychodynamic Freud",
    "tái cấu trúc nhận thức": "cognitive restructuring",
    "kích hoạt hành vi": "behavioral activation",
    "tiếp xúc thực tế": "exposure therapy in vivo exposure",
    "giải mẫn cảm": "systematic desensitization",
    "chánh niệm": "mindfulness mindfulness based",
    "thôi miên": "hypnotherapy hypnosis",
    "liệu pháp thân chủ trọng tâm": "person centered therapy Rogerian",
    "liệu pháp gia đình": "family therapy systemic therapy",

    # Khái niệm lý thuyết & Triệu chứng
    "tiêu chí chẩn đoán": "diagnostic criteria DSM ICD",
    "chẩn đoán": "diagnosis diagnostic criteria",
    "triệu chứng": "symptoms clinical features manifestation",
    "điều trị": "treatment therapy intervention management",
    "cơ chế tự vệ": "defense mechanisms ego defense",
    "vô thức": "unconscious subconscious",
    "tiềm thức": "subconscious unconscious",
    "ý thức": "conscious consciousness",
    "chuyển di": "transference",
    "phản chuyển di": "countertransference",
    "méo mó nhận thức": "cognitive distortions cognitive bias",
    "suy nghĩ tự động": "automatic thoughts negative automatic thoughts",
    "thuyết gắn bó": "attachment theory attachment styles",
    "gắn bó": "attachment theory",
    "lòng tự trọng": "self esteem self worth",
    "tự trắc ẩn": "self compassion",
    "khả năng phục hồi": "resilience psychological resilience",
    "thần kinh học": "neuroscience neural brain neurobiology",
    "chất dẫn truyền thần kinh": "neurotransmitter serotonin dopamine GABA",
    "vỏ não trước trán": "prefrontal cortex PFC",
    "hạch hạnh nhân": "amygdala",
    "hồi hải mã": "hippocampus",

    # Trí tuệ nhân tạo, Mô hình ngôn ngữ & Can thiệp số trong Sức khỏe tâm thần
    "trí tuệ nhân tạo": "artificial intelligence AI",
    "mô hình ngôn ngữ lớn": "large language models LLM LLMs",
    "mô hình ngôn ngữ": "language models LLM",
    "llm": "large language models LLM LLMs",
    "ai": "artificial intelligence AI",
    "sức khỏe tâm thần": "mental health psychiatric psychological wellbeing",
    "phát hiện sớm": "early detection screening identifying",
    "can thiệp": "intervention digital intervention treatment therapy",
    "can thiệp số": "digital intervention digital mental health",
    "học máy": "machine learning ML",
    "xử lý ngôn ngữ tự nhiên": "natural language processing NLP",
    "phân tích cảm xúc": "sentiment analysis emotion recognition",
    "nhận diện cảm xúc": "emotion recognition affective computing",
    "tổng quan": "scoping review review survey",
    "đánh giá": "assessment screening evaluation",
    "sàng lọc": "screening detection triage",
}

# Tạo chiều ngược lại EN -> VI
PSYCHOLOGY_GLOSSARY_EN_TO_VI: dict[str, str] = {
    "psychology": "tâm lý học",
    "cognitive psychology": "tâm lý học nhận thức",
    "cognition": "nhận thức",
    "clinical psychology": "tâm lý học lâm sàng",
    "social psychology": "tâm lý học xã hội",
    "developmental psychology": "tâm lý học phát triển",
    "neuropsychology": "tâm lý học thần kinh",
    "cognitive science": "khoa học nhận thức",
    "behaviorism": "chủ nghĩa hành vi tâm lý học hành vi",
    "depression": "trầm cảm rối loạn trầm cảm",
    "anxiety": "lo âu rối loạn lo âu",
    "cbt": "liệu pháp nhận thức hành vi",
    "cognitive behavioral": "nhận thức hành vi",
    "ocd": "ám ảnh cưỡng chế",
    "bipolar": "rối loạn lưỡng cực",
    "schizophrenia": "tâm thần phân liệt",
    "ptsd": "rối loạn sau sang chấn",
    "trauma": "sang chấn tổn thương tâm lý",
    "adhd": "tăng động giảm chú ý",
    "autism": "tự kỷ phổ tự kỷ",
    "dbt": "liệu pháp hành vi biện chứng",
    "act": "liệu pháp chấp nhận và cam kết",
    "psychoanalysis": "phân tâm học",
    "transference": "chuyển di",
    "countertransference": "phản chuyển di",
    "defense mechanism": "cơ chế tự vệ",
    "cognitive restructuring": "tái cấu trúc nhận thức",
    "mindfulness": "chánh niệm",
    "diagnosis": "chẩn đoán",
    "symptoms": "triệu chứng",
    "treatment": "điều trị",
    # AI & Modern Digital Health
    "artificial intelligence": "trí tuệ nhân tạo AI",
    "large language models": "mô hình ngôn ngữ lớn LLM",
    "llm": "mô hình ngôn ngữ lớn LLM",
    "mental health": "sức khỏe tâm thần",
    "early detection": "phát hiện sớm sàng lọc",
    "intervention": "can thiệp điều trị",
    "digital intervention": "can thiệp kỹ thuật số",
    "machine learning": "học máy",
    "natural language processing": "xử lý ngôn ngữ tự nhiên",
    "sentiment analysis": "phân tích cảm xúc",
    "scoping review": "nghiên cứu tổng quan",
}


def detect_language(query: str) -> str:
    """Nhận diện chính xác ngôn ngữ câu hỏi: 'vi' (Tiếng Việt) hoặc 'en' (Tiếng Anh).
    Hỗ trợ cả tiếng Việt có dấu và không dấu.
    """
    if not query:
        return "vi"

    clean_q = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]', '', query, flags=re.IGNORECASE).strip()

    # 1. Nếu có ký tự dấu tiếng Việt -> 100% Tiếng Việt
    if any(c in _VI_CHARS for c in clean_q):
        return "vi"

    # 2. Xử lý câu hỏi không dấu
    q_norm = strip_accents(clean_q).lower()
    words = re.findall(r'\b[a-z0-9]+\b', q_norm)
    if not words:
        return "vi"

    vi_word_count = sum(1 for w in words if w in _VI_STOPWORDS_NO_ACCENT)
    en_word_count = sum(1 for w in words if w in _EN_WORDS)

    if vi_word_count > en_word_count:
        return "vi"
    if en_word_count > 0 and en_word_count >= vi_word_count:
        return "en"

    return "vi"


def translate_query(query: str, target_lang: str) -> str:
    """Dịch câu hỏi sang ngôn ngữ mục tiêu ('en' hoặc 'vi') để phục vụ truy xuất chéo ngôn ngữ.
    Sử dụng bộ nhớ đệm (cache) và tra cứu nhanh trước khi gọi LLM.
    """
    clean_q = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]', '', query, flags=re.IGNORECASE).strip()
    cache_key = f"{target_lang}:{clean_q.lower()}"
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    target_name = "English" if target_lang == "en" else "Vietnamese"
    try:
        translated = llm_client.complete(
            messages=[{
                "role": "user",
                "content": f"Translate this psychology academic query into {target_name}. "
                           f"Return ONLY the direct translation, concise, with academic keywords, without quotes or explanation.\nQuery: {clean_q}"
            }],
            system="You are a specialized psychology and medical translator. Output only the translated search query in plain text.",
            max_tokens=60,
            temperature=0.0
        ).strip().strip('"').strip("'")
        if translated:
            _TRANSLATION_CACHE[cache_key] = translated
            return translated
    except Exception as e:
        logger.warning("Query translation via LLM failed: %s", e)

    return clean_q


def expand_query_terms_for_fts(query: str, lang: str) -> list[str]:
    """Trích xuất và mở rộng các từ khóa song ngữ cho Postgres Full-Text Search (FTS).
    Khi hỏi tiếng Việt -> sinh thêm từ khóa tiếng Anh tương ứng.
    Khi hỏi tiếng Anh -> sinh thêm từ khóa tiếng Việt tương ứng.
    Hỗ trợ cả trường hợp người dùng gõ tiếng Việt không dấu.
    """
    clean_q = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]', '', query, flags=re.IGNORECASE).strip().lower()
    clean_q_no_accent = strip_accents(clean_q)
    expanded_terms: list[str] = []

    if lang == "vi":
        # Tra cứu từ điển tiếng Việt -> tiếng Anh (khớp cả có dấu và không dấu)
        for vi_term, en_expansion in PSYCHOLOGY_GLOSSARY_VI_TO_EN.items():
            vi_term_no_accent = strip_accents(vi_term)
            if vi_term in clean_q or vi_term_no_accent in clean_q_no_accent:
                en_words = re.findall(r'\b[a-zA-Z]{3,}\b', en_expansion)
                expanded_terms.extend(en_words)
    else:
        # Tra cứu từ điển tiếng Anh -> tiếng Việt
        for en_term, vi_expansion in PSYCHOLOGY_GLOSSARY_EN_TO_VI.items():
            if en_term in clean_q:
                vi_words = re.findall(r'\b\w{2,}\b', vi_expansion)
                expanded_terms.extend(vi_words)

    seen = set()
    unique_terms = []
    for t in expanded_terms:
        tl = t.lower()
        if tl not in seen:
            seen.add(tl)
            unique_terms.append(tl)

    return unique_terms


def get_cross_lingual_query_bundle(query: str) -> dict:
    """Đóng gói toàn bộ thông tin truy vấn song ngữ phục vụ Retriever."""
    lang = detect_language(query)
    target_lang = "en" if lang == "vi" else "vi"

    # Mở rộng từ khóa FTS bằng glossary
    fts_expanded = expand_query_terms_for_fts(query, lang)

    # Dịch câu hỏi sang ngôn ngữ đối chiếu để tìm vector
    translated = translate_query(query, target_lang)

    # Tự động trích xuất các từ khóa học thuật quan trọng từ translated_query bổ sung vào fts_expanded
    # Đảm bảo ngay cả khi thuật ngữ chưa có trong từ điển tĩnh thì FTS vẫn tìm được tài liệu đối chiếu!
    if translated and translated.strip().lower() != query.strip().lower():
        if lang == "vi":
            en_stopwords = {
                "what", "is", "are", "how", "why", "when", "where", "who", "which",
                "the", "and", "for", "with", "that", "this", "from", "about", "does",
                "define", "definition", "overview", "explain", "describe"
            }
            trans_tokens = re.findall(r'\b[a-zA-Z]{3,}\b', translated.lower())
            for tok in trans_tokens:
                if tok not in en_stopwords and tok not in fts_expanded:
                    fts_expanded.append(tok)
        else:
            vi_stopwords = {"la", "gi", "nhu", "the", "nao", "cua", "trong", "va", "cac", "nhung"}
            trans_tokens = re.findall(r'\b\w{2,}\b', translated.lower())
            for tok in trans_tokens:
                if tok not in vi_stopwords and tok not in fts_expanded:
                    fts_expanded.append(tok)

    return {
        "orig_query": query,
        "orig_lang": lang,
        "target_lang": target_lang,
        "translated_query": translated,
        "fts_expanded_terms": fts_expanded
    }
