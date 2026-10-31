"""
Module xử lý Đa Ngôn Ngữ & Dịch Truy Vấn Chéo (Cross-Lingual Information Retrieval & Generation)
cho hệ thống Acamind.
- Tự động nhận diện ngôn ngữ câu hỏi (Tiếng Việt / Tiếng Anh)
- Từ điển thuật ngữ Tâm lý học & Y sinh đối chiếu chuẩn DSM-5 / ICD-11 / APA
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


# ── Từ điển thuật ngữ Tâm lý học & Khoa học liên ngành đối chiếu song ngữ ──
# Tách riêng thuật ngữ CHỦ ĐỀ CỤ THỂ (Topic/Entity Terms) và từ khóa BỔ TRỢ CHUNG (Modifiers)
TOPIC_GLOSSARY_VI_TO_EN: dict[str, str] = {
    # Các chuyên ngành & Khái niệm Tâm lý học nền tảng
    "tâm lý học": "psychology psychological",
    "tâm lý học nhận thức": "cognitive psychology cognition",
    "nhận thức": "cognitive cognition",
    "tâm lý học lâm sàng": "clinical psychology",
    "tâm lý học xã hội": "social psychology",
    "tâm lý học phát triển": "developmental psychology",
    "tâm lý học thần kinh": "neuropsychology neuroscience",
    "khoa học nhận thức": "cognitive science",
    "tâm lý học hành vi": "behavioral psychology behaviorism",
    "tâm lý học nhân văn": "humanistic psychology",
    "tâm lý học tích cực": "positive psychology interventions wellbeing",
    "can thiệp tâm lý tích cực": "positive psychology interventions meta-analytical wellbeing",
    "tâm lý tích cực": "positive psychology interventions wellbeing",
    "hạnh phúc chủ quan": "subjective well-being wellbeing",
    "hạnh phúc tâm lý": "psychological well-being wellbeing",
    "phúc lợi tâm lý": "psychological well-being subjective well-being",
    "tâm lý học giáo dục": "educational psychology",
    "tâm lý học sức khỏe": "health psychology",

    # Rối loạn & Bệnh lý tâm thần
    "trầm cảm": "depression depressive MDD",
    "lo âu": "anxiety anxious GAD",
    "rối loạn lo âu": "anxiety disorder GAD",
    "rối loạn lo âu lan tỏa": "generalized anxiety GAD",
    "rối loạn ám ảnh cưỡng chế": "obsessive compulsive OCD",
    "ám ảnh cưỡng chế": "obsessive compulsive OCD",
    "rối loạn lưỡng cực": "bipolar mania manic",
    "lưỡng cực": "bipolar mania",
    "tâm thần phân liệt": "schizophrenia psychotic psychosis",
    "triệu chứng dương tính": "positive symptoms delusions hallucinations",
    "triệu chứng âm tính": "negative symptoms apathy avolition",
    "loạn thần": "psychosis psychotic",
    "rối loạn sau sang chấn": "posttraumatic PTSD trauma",
    "sang chấn tâm lý": "trauma PTSD traumatic",
    "sang chấn": "trauma PTSD traumatic",
    "ptsd": "PTSD posttraumatic trauma",
    "tự kỷ": "autism autistic ASD",
    "phổ tự kỷ": "autism autistic ASD",
    "tăng động giảm chú ý": "hyperactivity ADHD attention",
    "adhd": "ADHD hyperactivity attention",
    "rối loạn nhân cách": "personality disorder",
    "rối loạn nhân cách ranh giới": "borderline personality BPD",
    "rối loạn ăn uống": "eating disorder anorexia bulimia",
    "chán ăn tâm thần": "anorexia eating disorder",
    "ăn vô độ": "bulimia binge eating",
    "béo phì": "obesity overweight bariatric weight",
    "phẫu thuật giảm cân": "bariatric surgery weight loss",
    "phẫu thuật": "surgery surgical postoperative",
    "mất ngủ": "insomnia sleep disorder",
    "giấc ngủ": "sleep insomnia circadian",
    "mộng du": "sleepwalking somnambulism parasomnia",
    "ác mộng": "nightmare dream sleep",
    "rối loạn hoảng sợ": "panic disorder panic attack",
    "hoảng sợ": "panic disorder attack",
    "hoảng loạn": "panic disorder attack",
    "rối loạn dạng cơ thể": "somatic symptom disorder somatization",
    "ám ảnh sợ xã hội": "social anxiety phobia",
    "ám ảnh sợ": "phobia phobic",
    "nghiện": "addiction substance dependence",
    "lạm dụng chất": "substance abuse addiction",
    "rượu": "alcohol drinking alcoholism",
    "tự sát": "suicide suicidal self-harm",
    "tự tử": "suicide suicidal self-harm prevention",
    "tự làm hại": "self-harm suicidal NSSI",
    "tự hại": "self-harm nonsuicidal NSSI",
    "bốc đồng": "impulsivity impulsive behavior",
    "cưỡng chế": "compulsive compulsion ritual",
    "kiệt sức": "burnout exhaustion occupational",
    "căng thẳng công nghệ": "technostress digital technology stress",
    "technostress": "technostress digital technology stress",
    "áp lực học đường": "academic stress school pressure",
    "căng thẳng": "stress distress cortisol",
    "đau mãn tính": "chronic pain analgesia",
    "sa sút trí tuệ": "dementia Alzheimer cognitive decline",
    "alzheimer": "Alzheimer dementia neurodegeneration",

    # Liệu pháp & Phương pháp can thiệp
    "liệu pháp nhận thức hành vi qua máy tính": "computer therapy computerized CBT internet-administered iCBT",
    "cbt qua máy tính": "computer therapy computerized CBT internet-administered iCBT",
    "nhận thức hành vi": "CBT cognitive behavioral",
    "liệu pháp nhận thức hành vi": "CBT cognitive behavioral therapy",
    "cbt": "CBT cognitive behavioral",
    "liệu pháp hành vi biện chứng": "DBT dialectical behavior",
    "dbt": "DBT dialectical behavior",
    "liệu pháp chấp nhận và cam kết": "acceptance commitment therapy ACT",
    "phân tâm học": "psychoanalysis psychodynamic",
    "phân tâm": "psychoanalysis psychodynamic Freud",
    "tái cấu trúc nhận thức": "cognitive restructuring",
    "kích hoạt hành vi": "behavioral activation",
    "tiếp xúc thực tế": "exposure therapy vivo",
    "tiếp xúc và ngăn ngừa phản ứng": "exposure response prevention ERP",
    "ngăn ngừa phản ứng": "response prevention ERP exposure",
    "erp": "ERP exposure response prevention",
    "giải mẫn cảm": "desensitization exposure",
    "chánh niệm": "mindfulness MBSR MBCT",
    "thiền": "meditation mindfulness",
    "thôi miên": "hypnotherapy hypnosis",
    "liệu pháp thân chủ trọng tâm": "person-centered Rogerian",
    "liệu pháp gia đình": "family therapy systemic",
    "liệu pháp nhóm": "group therapy group CBT intervention",
    "liệu pháp cá nhân": "individual therapy psychotherapy counseling",
    "liệu pháp tâm lý": "psychotherapy psychological therapy counseling",
    "tâm lý trị liệu": "psychotherapy counseling therapy",
    "trị liệu trực tuyến": "online therapy teletherapy internet-administered iCBT",
    "trị liệu trực tiếp": "face-to-face therapy in-person psychotherapy",
    "trị liệu ngắn hạn": "brief therapy short-term psychotherapy",
    "trị liệu dài hạn": "long-term psychotherapy maintenance treatment",
    "dược lý": "pharmacotherapy medication antidepressant SSRI",
    "thuốc chống trầm cảm": "antidepressant SSRI SNRI pharmacotherapy medication",
    "giả dược": "placebo sham control",
    "chẩn đoán phân biệt": "differential diagnosis diagnostic criteria DSM",
    "chức năng sống": "daily functioning functional impairment quality of life",

    # Khái niệm lý thuyết, Nhận thức, Xã hội & Thần kinh
    "cơ chế tự vệ": "defense mechanisms ego",
    "cơ chế phòng vệ": "defense mechanisms ego coping",
    "vị thành niên": "adolescents adolescence youth",
    "lão niên": "older adults elderly aging",
    "tính cách": "character personality traits",
    "khí chất": "temperament biological reactivity",
    "lắng nghe chủ động": "active listening therapeutic alliance empathy",
    "vô thức": "unconscious subconscious",
    "tiềm thức": "subconscious unconscious",
    "ý thức": "conscious consciousness",
    "chuyển di": "transference",
    "phản chuyển di": "countertransference",
    "méo mó nhận thức": "cognitive distortions bias",
    "thiên kiến nhận thức": "cognitive bias heuristic",
    "suy nghĩ tự động": "automatic thoughts negative",
    "thuyết gắn bó": "attachment theory styles",
    "gắn bó": "attachment bonding",
    "lòng tự trọng": "self-esteem self-worth",
    "hiệu quả bản thân": "self-efficacy",
    "tự trắc ẩn": "self-compassion",
    "khả năng phục hồi": "resilience coping",
    "đối phó": "coping emotion regulation",
    "điều hòa cảm xúc": "emotion regulation affective",
    "cảm xúc": "emotion emotional affective",
    "trí tuệ cảm xúc": "emotional intelligence",
    "trí nhớ": "memory recall episodic",
    "trí nhớ làm việc": "working memory executive",
    "chức năng điều hành": "executive function cognitive control",
    "chú ý": "attention attentional",
    "nhân cách": "personality traits extraversion neuroticism",
    "động lực": "motivation intrinsic extrinsic",
    "cô đơn": "loneliness isolation",
    "mạng xã hội": "social media smartphone digital",
    "thanh thiếu niên": "adolescents youth adolescent",
    "trẻ em": "children pediatric childhood",
    "người cao tuổi": "older adults elderly aging",
    "sinh viên": "students college university academic",
    "học sinh": "students school adolescents academic",
    "thần kinh học": "neuroscience neural brain",
    "não bộ": "brain cerebral neural neuroimaging",
    "chất dẫn truyền thần kinh": "neurotransmitter serotonin dopamine",
    "vỏ não trước trán": "prefrontal cortex PFC",
    "hạch hạnh nhân": "amygdala limbic",
    "hồi hải mã": "hippocampus memory",

    # Trí tuệ nhân tạo, Mô hình ngôn ngữ & Can thiệp số trong Sức khỏe tâm thần
    "trí tuệ nhân tạo": "artificial intelligence machine learning",
    "mô hình ngôn ngữ lớn": "large language models LLM",
    "mô hình ngôn ngữ": "language models LLM NLP",
    "llm": "LLM language models",
    "sức khỏe tâm thần": "mental health psychiatric wellbeing",
    "can thiệp số": "digital intervention mHealth",
    "học máy": "machine learning deep learning",
    "xử lý ngôn ngữ tự nhiên": "natural language processing NLP",
    "phân tích cảm xúc": "sentiment analysis emotion recognition",
    "nhận diện cảm xúc": "emotion recognition affective",
    # Bổ sung từ điển chuyên sâu cho bộ 300 câu hỏi Tâm lý học (Lý thuyết, Đối chiếu, Trị liệu)
    "tâm lý học nghiên cứu": "psychology definition",
    "tâm lý học là gì": "psychology definition",
    "khái niệm tâm lý học": "psychology definition",
    "định nghĩa tâm lý học": "psychology definition",
    "big five": "Big Five personality traits OCEAN Costa McCrae",
    "5 yếu tố lớn": "Big Five personality traits OCEAN",
    "eysenck": "Eysenck PEN model extraversion neuroticism psychoticism",
    "piaget": "Piaget cognitive development stages sensorimotor preoperational",
    "vygotsky": "Vygotsky sociocultural zone proximal development ZPD",
    "maslow": "Maslow hierarchy needs self-actualization",
    "tháp nhu cầu": "Maslow hierarchy needs self-actualization",
    "skinner": "Skinner operant conditioning reinforcement punishment",
    "điều kiện hóa kết quả": "operant conditioning Skinner reinforcement",
    "điều kiện hóa cổ điển": "classical conditioning Pavlov",
    "pavlov": "Pavlov classical conditioning",
    "bandura": "Bandura social learning observational self-efficacy",
    "học tập xã hội": "social learning theory Bandura observational",
    "rogers": "Carl Rogers humanistic unconditional positive regard client-centered",
    "adler": "Alfred Adler individual psychology inferiority complex",
    "jung": "Carl Jung collective unconscious archetypes",
    "sternberg": "Sternberg triangular theory love intimacy passion commitment",
    "tam giác tình yêu": "Sternberg triangular theory love intimacy passion commitment",
    "gardner": "Gardner multiple intelligences",
    "đa trí tuệ": "multiple intelligences Gardner",
    "tâm lý học tiến hóa": "evolutionary psychology mate selection Buss",
    "chọn lọc bạn đời": "mate selection evolutionary psychology",
    "rorschach": "Rorschach inkblot projective test",
    "vết mực": "Rorschach inkblot projective",
    "trắc nghiệm phóng chiếu": "projective test Rorschach TAT",
    "phỏng vấn lâm sàng": "structured clinical interview SCID diagnostic",
    "bdi": "Beck Depression Inventory BDI",
    "phq-9": "PHQ-9 Patient Health Questionnaire depression",
    "gad-7": "GAD-7 Generalized Anxiety Disorder scale",
    "ngưỡng tuyệt đối": "absolute threshold psychophysics sensation",
    "ngưỡng sai biệt": "difference threshold Weber Fechner",
    "trì hoãn": "procrastination self-regulation temporal motivation",
    "thấu cảm": "empathy cognitive affective",
    "tội lỗi": "guilt shame moral emotion",
    "xấu hổ": "shame guilt self-conscious",
    "tức giận": "anger aggression hostility",
    "động lực nội tại": "intrinsic motivation self-determination",
    "động lực ngoại tại": "extrinsic motivation reward",
    "trí nhớ ngắn hạn": "short-term memory STM working memory",
    "trí nhớ dài hạn": "long-term memory LTM consolidation",
    "sự quên": "forgetting Ebbinghaus interference decay",
    "tư duy": "thinking divergent convergent problem solving",
    "nhân cách ái kỷ": "narcissistic personality NPD grandiosity",
    "ái kỷ": "narcissistic personality NPD",
    "chống đối xã hội": "antisocial personality ASPD psychopathy",
    "khép kín": "schizoid personality disorder",
    "rối loạn tic": "tic disorder Tourette habit reversal",
    "tourette": "Tourette tic disorder",
    "triệu chứng cơ thể": "somatic symptom disorder somatization",
    "lo âu chia ly": "separation anxiety disorder",
    "trầm cảm dai dẳng": "persistent depressive disorder dysthymia",
    "dysthymia": "dysthymia persistent depressive disorder",
    "khí sắc chu kỳ": "cyclothymia cyclothymic disorder",
    "emdr": "EMDR eye movement desensitization reprocessing",
    "giải mẫn cảm có hệ thống": "systematic desensitization Wolpe",
    "phơi nhiễm kéo dài": "prolonged exposure therapy Foa",
    "thực tế ảo": "virtual reality exposure therapy VRET",
    "eft": "emotionally focused therapy EFT couples",
    "gottman": "Gottman couples therapy relationship",
    "liệu pháp ánh sáng": "bright light therapy seasonal affective SAD",
    "liệu pháp nghệ thuật": "art therapy expressive",
    "liệu pháp âm nhạc": "music therapy",
    "liệu pháp trò chơi": "play therapy child-centered",
    "liệu pháp tự sự": "narrative therapy externalizing",
    "cbt-i": "CBT-I cognitive behavioral therapy insomnia",
    "aba": "applied behavior analysis ABA autism",
    "phản hồi sinh học": "biofeedback neurofeedback HRV",
    "quyết đoán": "assertiveness training social skills",
    "viết nhật ký": "expressive writing therapeutic journaling Pennebaker",
    "12 bước": "12-step facilitation Alcoholics Anonymous",
    "ssri": "SSRI selective serotonin reuptake inhibitor",
    "lithium": "lithium mood stabilizer bipolar",
    "benzodiazepine": "benzodiazepine GABA tolerance withdrawal",
    "ect": "electroconvulsive therapy ECT",
    "sốc điện": "electroconvulsive therapy ECT",
    "tự vận động": "autogenic training progressive muscle relaxation",
    "nơi an toàn": "safe place visualization guided imagery",
    "kế hoạch an toàn": "safety planning suicide prevention Stanley Brown",
    # Liệu pháp tiếp xúc (exposure-based therapies) và các khái niệm chuẩn liên quan
    "tiếp xúc kéo dài": "prolonged exposure therapy Foa",
    "liệu pháp tiếp xúc": "exposure therapy",
    "kỹ thuật tiếp xúc": "exposure technique therapy",
    "tiếp xúc từng bước": "graded exposure hierarchy",
    "tiếp xúc tăng dần": "graded exposure hierarchy",
    "tiếp xúc nội quan": "interoceptive exposure",
    "thang phân cấp nỗi sợ": "fear hierarchy graded exposure",
    "thang phân cấp": "hierarchy graded exposure",
    # Trị liệu cặp đôi / gia đình
    "trị liệu cặp đôi": "couples therapy",
    "liệu pháp cặp đôi": "couples therapy",
    "tập trung vào cảm xúc": "emotionally focused therapy EFT",
    # Stress như một khái niệm độc lập (trước đây chỉ có "căng thẳng")
    "stress": "stress",
}

# Từ bổ nghĩa thuộc tính (qualifier): đứng sau danh từ trong tiếng Việt nhưng đứng TRƯỚC trong tiếng Anh
# (vd. "gắn bó an toàn" -> "secure attachment", "stress mãn tính" -> "chronic stress").
# Chỉ được thêm khi đã khớp ít nhất 1 thuật ngữ chủ đề, và được xếp lên đầu để không bị cắt khi rút gọn truy vấn.
QUALIFIER_GLOSSARY_VI_TO_EN: dict[str, str] = {
    "an toàn": "secure",
    "né tránh": "avoidant avoidance",
    "mất tổ chức": "disorganized",
    "hỗn loạn": "disorganized",
    "ám ảnh": "preoccupied",
    "cấp tính": "acute",
    "mãn tính": "chronic",
    "kéo dài": "prolonged persistent",
    "khởi phát sớm": "early-onset",
    "nặng": "severe",
    "nhẹ": "mild",
}

MODIFIER_GLOSSARY_VI_TO_EN: dict[str, str] = {
    "chẩn đoán phân biệt": "differential diagnosis distinguish",
    "tiêu chí chẩn đoán": "diagnostic criteria DSM ICD",
    "chẩn đoán": "diagnosis diagnostic",
    "triệu chứng": "symptoms clinical manifestation",
    "điều trị": "treatment therapy intervention",
    "phát hiện sớm": "early detection screening",
    "can thiệp": "intervention treatment therapy",
    "tổng quan": "review scoping systematic",
    "đánh giá": "assessment evaluation scale",
    "sàng lọc": "screening detection",
    "phân tích gộp": "meta-analysis meta-analytical pooled effect",
    "tổng quan hệ thống": "systematic review literature search",
    "kích thước hiệu ứng": "effect size standardized mean difference",
    "cỡ mẫu": "sample size participants studies totaling",
    "người tham gia": "participants subjects sample",
    "theo dõi": "follow-up months sustainable",
    "hiệu quả": "effectiveness efficacy effect",
}

PSYCHOLOGY_GLOSSARY_VI_TO_EN: dict[str, str] = {
    **TOPIC_GLOSSARY_VI_TO_EN,
    **MODIFIER_GLOSSARY_VI_TO_EN,
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


def _match_whole_phrase(text: str, phrase: str) -> bool:
    """Kiểm tra cụm từ khớp nguyên từ (word boundary), tránh khớp chuỗi con sai lệch (như 'ai' trong 'tài liệu')."""
    if not text or not phrase:
        return False
    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def _extract_matched_concept_groups(query: str, lang: str) -> list[list[str]]:
    """Trích xuất các nhóm từ đồng nghĩa theo từng khái niệm khớp trong câu hỏi.
    - Ưu tiên khớp cụm từ dài trước (vd: 'liệu pháp nhận thức hành vi' trước 'nhận thức').
    - Chỉ mở rộng từ khóa bổ trợ chung (MODIFIER_GLOSSARY_VI_TO_EN như 'điều trị', 'triệu chứng')
      khi đã có ít nhất 1 thuật ngữ chủ đề cụ thể (TOPIC_GLOSSARY_VI_TO_EN) khớp, tránh việc câu hỏi
      ngoài miền (như 'điều trị bệnh gút') bị dịch thành 'treatment therapy' và kéo nhầm bài tâm lý.
    """
    clean_q = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]', '', query, flags=re.IGNORECASE).strip().lower()
    has_vi_accents = any(c in _VI_CHARS for c in clean_q)
    clean_q_no_accent = strip_accents(clean_q)

    groups: list[list[str]] = []
    consumed_text = clean_q
    consumed_no_accent = clean_q_no_accent

    if lang == "vi":
        _BROAD_DISCIPLINES = {
            "tâm lý học", "tâm lý học lâm sàng", "tâm lý học nhận thức",
            "tâm lý học xã hội", "tâm lý học phát triển", "tâm lý học giáo dục",
            "tâm lý học sức khỏe", "sức khỏe tâm thần", "nhận thức", "cảm xúc",
        }
        matched_topic_items: list[tuple[int, int, list[str]]] = []
        sorted_topics = sorted(TOPIC_GLOSSARY_VI_TO_EN.items(), key=lambda kv: len(kv[0]), reverse=True)
        for vi_term, en_expansion in sorted_topics:
            matched = False
            pos = 9999
            if _match_whole_phrase(consumed_text, vi_term):
                matched = True
                pos = clean_q.find(vi_term)
                consumed_text = re.sub(r"(?<!\w)" + re.escape(vi_term) + r"(?!\w)", " ", consumed_text)
            elif not has_vi_accents and len(vi_term) >= 4:
                vi_no_acc = strip_accents(vi_term)
                if _match_whole_phrase(consumed_no_accent, vi_no_acc):
                    matched = True
                    pos = clean_q_no_accent.find(vi_no_acc)
                    consumed_no_accent = re.sub(r"(?<!\w)" + re.escape(vi_no_acc) + r"(?!\w)", " ", consumed_no_accent)
            if matched:
                en_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', en_expansion)]
                if en_words:
                    is_broad = 1 if vi_term in _BROAD_DISCIPLINES else 0
                    matched_topic_items.append((is_broad, pos if pos >= 0 else 9999, en_words))

        matched_topic_items.sort(key=lambda item: (item[0], item[1]))
        groups = [item[2] for item in matched_topic_items]

        # Từ bổ nghĩa thuộc tính: chỉ khi đã có chủ đề khớp; đặt lên đầu danh sách nhóm
        if groups:
            qualifier_groups: list[list[str]] = []
            for vi_term, en_expansion in sorted(QUALIFIER_GLOSSARY_VI_TO_EN.items(), key=lambda kv: len(kv[0]), reverse=True):
                if _match_whole_phrase(consumed_text, vi_term) or (
                    not has_vi_accents and len(vi_term) >= 4 and _match_whole_phrase(consumed_no_accent, strip_accents(vi_term))
                ):
                    consumed_text = re.sub(r"(?<!\w)" + re.escape(vi_term) + r"(?!\w)", " ", consumed_text)
                    en_words = [w.lower() for w in re.findall(r'\b[a-zA-Z-]{3,}\b', en_expansion)]
                    if en_words:
                        qualifier_groups.append(en_words)
            groups = qualifier_groups + groups

        # Chỉ mở rộng từ khóa bổ trợ chung nếu đã có ít nhất 1 chủ đề cụ thể khớp
        if groups:
            sorted_mods = sorted(MODIFIER_GLOSSARY_VI_TO_EN.items(), key=lambda kv: len(kv[0]), reverse=True)
            for vi_term, en_expansion in sorted_mods:
                if _match_whole_phrase(consumed_text, vi_term) or (
                    not has_vi_accents and len(vi_term) >= 4 and _match_whole_phrase(consumed_no_accent, strip_accents(vi_term))
                ):
                    en_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', en_expansion)]
                    if en_words:
                        groups.append(en_words)
    else:
        sorted_en = sorted(PSYCHOLOGY_GLOSSARY_EN_TO_VI.items(), key=lambda kv: len(kv[0]), reverse=True)
        for en_term, vi_expansion in sorted_en:
            if _match_whole_phrase(consumed_text, en_term):
                consumed_text = re.sub(r"(?<!\w)" + re.escape(en_term) + r"(?!\w)", " ", consumed_text)
                vi_words = [w.lower() for w in re.findall(r'\b\w{2,}\b', vi_expansion)]
                if vi_words:
                    groups.append(vi_words)

    return groups


def translate_query(query: str, target_lang: str) -> str:
    """Dịch/mở rộng câu hỏi sang ngôn ngữ mục tiêu ('en' hoặc 'vi') tức thì (<1ms) bằng từ điển học thuật
    song ngữ kết hợp cache, tránh gọi đồng bộ LLM làm nghẽn hàng đợi Ollama khi đang chat.
    Giữ nguyên ngữ nghĩa câu hỏi gốc khi không có thuật ngữ chuyên ngành khớp để mô hình đa ngữ
    multilingual-e5-base không bị mất chủ đề.
    """
    clean_q = re.sub(r'^\[(?:he\s+thong|system):[^\]]+\]', '', query, flags=re.IGNORECASE).strip()
    cache_key = f"{target_lang}:{clean_q.lower()}"
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    source_lang = "vi" if target_lang == "en" else "en"
    expanded = expand_query_terms_for_fts(clean_q, source_lang)
    if expanded:
        translated = " ".join(expanded[:10])
        _TRANSLATION_CACHE[cache_key] = translated
        return translated

    _TRANSLATION_CACHE[cache_key] = clean_q
    return clean_q


def expand_query_terms_for_fts(query: str, lang: str) -> list[str]:
    """Trích xuất và mở rộng các từ khóa song ngữ cho Postgres Full-Text Search (FTS).
    Khi hỏi tiếng Việt -> sinh thêm từ khóa tiếng Anh tương ứng.
    Khi hỏi tiếng Anh -> sinh thêm từ khóa tiếng Việt tương ứng.
    """
    groups = _extract_matched_concept_groups(query, lang)
    seen = set()
    unique_terms = []
    _PHRASE_HEAD_MODIFIERS = {
        "working", "borderline", "obsessive", "cognitive", "positive", "negative",
        "emotional", "social", "executive", "behavioral", "dialectical", "generalized",
        "bariatric", "chronic", "prefrontal", "artificial", "large", "language",
        "natural", "sentiment", "subjective", "psychological", "developmental",
        "clinical", "differential", "exposure", "person", "family", "substance",
        "eating", "defense", "automatic", "attachment", "older", "mental",
        "digital", "machine", "early", "systematic", "effect", "sample", "response",
    }
    # Ưu tiên lấy cụm từ đại diện chính (1 từ nếu là danh từ đơn, 2 từ nếu là cụm danh từ) của mỗi nhóm khái niệm trước, sau đó mới đến các từ đồng nghĩa
    for pass_idx in range(2):
        for g_idx, g in enumerate(groups):
            if not g:
                continue
            limit_0 = 2 if g[0].lower() in _PHRASE_HEAD_MODIFIERS else 1
            candidates = g[:limit_0] if pass_idx == 0 else g[limit_0:]
            for t in candidates:
                tl = t.lower()
                if tl not in seen:
                    seen.add(tl)
                    unique_terms.append(tl)

    for acr in re.findall(r'\b[A-Z]{2,10}(?:-\d+)?\b', query):
        al = acr.lower()
        if al not in seen:
            seen.add(al)
            unique_terms.append(al)
    return unique_terms


def get_cross_lingual_query_bundle(query: str) -> dict:
    """Đóng gói toàn bộ thông tin truy vấn song ngữ phục vụ Retriever."""
    lang = detect_language(query)
    target_lang = "en" if lang == "vi" else "vi"

    concept_groups = _extract_matched_concept_groups(query, lang)
    fts_expanded = expand_query_terms_for_fts(query, lang)
    translated = translate_query(query, target_lang)

    return {
        "orig_query": query,
        "orig_lang": lang,
        "target_lang": target_lang,
        "translated_query": translated,
        "fts_expanded_terms": fts_expanded,
        "fts_concept_groups": concept_groups,
    }
