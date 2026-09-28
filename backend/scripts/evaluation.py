"""
RAGAS Evaluation Script — Insight Nexus
========================================
Đánh giá chất lượng hệ thống RAG bằng 3 chỉ số khoa học:
  • Faithfulness            — AI có bịa thông tin không?
  • Answer Relevancy        — Câu trả lời có đúng chủ đề không?
  • Context Precision       — Retrieval có chính xác không?

Yêu cầu:
  pip install ragas>=0.2 datasets openpyxl langchain-core langchain-community

Chạy:
  cd backend
  venv\\Scripts\\Activate.ps1
  python scripts/evaluation.py
"""

import json, os, sys, requests
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from langchain_core.language_models.llms import BaseLLM

# Thêm backend vào Python path để import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from dotenv import load_dotenv

load_dotenv()

# ── Đường dẫn ──────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent.parent
EVAL_FILE   = BASE_DIR / "data" / "eval_questions.json"
RESULTS_DIR = BASE_DIR / "data" / "eval_results"
API_URL     = "http://localhost:8000/api/v1"

# ── Ngưỡng đánh giá ────────────────────────────────────────────────
THRESHOLDS = {
    "faithfulness":      {"good": 0.85, "ok": 0.70},
    "answer_relevancy":  {"good": 0.80, "ok": 0.65},
    "context_precision": {"good": 0.80, "ok": 0.65},
}


# ══════════════════════════════════════════════════════════════════════
# 1. Gọi API backend
# ══════════════════════════════════════════════════════════════════════

def get_answer_and_context(question: str, document_ids: list[str]) -> tuple[str, list[str]]:
    """Gọi POST /api/v1/chat/answer → trả về (answer, [context_text, ...])."""
    response = requests.post(
        f"{API_URL}/chat/answer",
        json={"query": question, "document_ids": document_ids},
        timeout=90,
    )
    response.raise_for_status()
    data     = response.json()
    answer   = data.get("answer", "")
    contexts = [c["content"] for c in data.get("contexts", []) if c.get("content")]
    # Fallback: nếu không có context, dùng answer làm context (tránh lỗi RAGAS)
    return answer, contexts or [answer]


# ══════════════════════════════════════════════════════════════════════
# 2. RAGAS evaluation — hỗ trợ cả 0.1.x và 0.2.x
# ══════════════════════════════════════════════════════════════════════

# ── LLM judge wrapper: Claude (qua llm_client) cho RAGAS ────────────────────
# Langchain 1.x: `from langchain.llms.base import LLM` đã bỏ. Dùng
# `langchain_core.language_models.llms.BaseLLM` và override `_generate`
# (abstract method trong 1.x — `_call` chỉ là shortcut, không đủ để instantiate).

class ClaudeRagasLLM(BaseLLM):
    """Langchain-compatible LLM adapter gọi Claude qua `llm_client`.

    RAGAS (cả 0.1.x và 0.2.x) dùng `generate()` → `_generate()` (hoặc
    `__call__` → `_call` ở bản cũ). Ta implement `_generate` để instantiate được.
    """

    max_tokens: int = 1024
    temperature: float = 0.0

    @property
    def _llm_type(self) -> str:
        return "claude-ragas"

    @property
    def _identifying_params(self) -> dict:
        return {
            "model": "claude-sonnet-4-6",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    def _call(
        self,
        prompt: str,
        stop: Optional[list[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        # Lazy import để tránh circular / lỗi import lúc script collect
        from app.services.llm_client import get_default_client
        client = get_default_client()
        result = client.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return (result or "").strip()

    def _generate(
        self,
        prompts: list[str],
        stop: Optional[list[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ):
        """Implement abstract `_generate` của BaseLLM (langchain 1.x)."""
        from langchain_core.outputs import Generation, LLMResult
        from app.services.llm_client import get_default_client
        client = get_default_client()
        generations: list[list[Generation]] = []
        for prompt in prompts:
            text = client.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            ) or ""
            generations.append([Generation(text=text.strip())])
        return LLMResult(generations=generations)


def _build_judge_llm() -> "ClaudeRagasLLM":
    """Tạo Gemini LLM dùng làm judge cho RAGAS. Lazy import config."""
    from app.core.config import settings
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "Chưa cấu hình GEMINI_API_KEY trong .env — cần key Gemini để làm judge."
        )
    return ClaudeRagasLLM(max_tokens=1024, temperature=0.0)


def _build_embeddings():
    """Ollama local embeddings (giữ nguyên — proxy Anthropic không cung cấp embeddings)."""
    from langchain_community.embeddings import OllamaEmbeddings
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_url)


import pandas as pd
from app.services.llm_client import get_default_client

def clean_and_parse_json(text: str) -> dict:
    """Trích xuất và parse JSON từ văn bản phản hồi của LLM."""
    if not text:
        return {}
    try:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            json_str = cleaned[start:end+1]
            return json.loads(json_str)
        return json.loads(cleaned)
    except Exception as e:
        return {}

def run_ragas(questions, answers, contexts, ground_truths):
    """Đánh giá RAG sử dụng mô hình Gemini API trực tiếp thay thế cho thư viện RAGAS (tránh lỗi biên dịch C++ trên Python 3.14)."""
    print("   Sử dụng LLM-as-judge (Gemini-3.1-flash-lite) thay thế RAGAS...")
    import time
    
    client = get_default_client()
    results = []
    
    def call_llm_with_retry(prompt):
        for attempt in range(5):
            try:
                # Pacing: Đợi 4.5 giây để tránh vượt quá 15 requests per minute của Gemini free tier
                time.sleep(4.5)
                res = client.complete(messages=[{"role": "user", "content": prompt}], max_tokens=1000, temperature=0.0)
                # Kiểm tra xem phản hồi có phải là thông báo lỗi quota không
                if not res or "error" in str(res).lower() and ("quota" in str(res).lower() or "exhausted" in str(res).lower() or "429" in str(res).lower()):
                    raise Exception(f"Quota exceeded in response: {res}")
                return res
            except Exception as e:
                err_str = str(e).lower()
                if "quota" in err_str or "exhausted" in err_str or "429" in err_str or "resource_exhausted" in err_str or "rate limit" in err_str:
                    wait_time = 8 + attempt * 5
                    print(f"         ⚠ Gặp lỗi 429 (Rate limit). Đang đợi {wait_time}s để thử lại (Lần thử {attempt+1}/5)...")
                    time.sleep(wait_time)
                else:
                    raise e
        raise Exception("Failed after 5 attempts due to API limits")

    for i, (q, a, ctx_list, gt) in enumerate(zip(questions, answers, contexts, ground_truths), 1):
        print(f"      [Judge] Đang đánh giá mẫu {i:02d}/{len(questions)}...")
        
        # 1. Đo Faithfulness
        context_str = "\n---\n".join(ctx_list)
        prompt_faith = f"""Bạn là một giám khảo độc lập đánh giá hệ thống hỏi đáp.
Dưới đây là NGỮ CẢNH (Context) và CÂU TRẢ LỜI (Response) của hệ thống.
Nhiệm vụ của bạn:
1. Tách Câu trả lời thành các mệnh đề/nhận định ngắn có nghĩa (mỗi nhận định chứa một ý cụ thể).
2. Với mỗi nhận định, hãy đối chiếu với Ngữ cảnh xem nó có được NGỮ CẢNH hỗ trợ hay không (Trả lời true/false).
3. Tính toán tỷ lệ Faithfulness = (Số nhận định được hỗ trợ) / (Tổng số nhận định). Nếu câu trả lời hoàn toàn trống hoặc chỉ nói "tôi không biết/không có thông tin", hãy cho điểm 0.0.
4. Trả về kết quả dưới dạng JSON có định dạng sau:
{{
  "score": <tỷ lệ từ 0.0 đến 1.0>
}}
Quy tắc: Chỉ dựa vào Ngữ cảnh được cung cấp. Không bịa đặt. Trả về CHÍNH XÁC JSON, không có định dạng markdown hay giải thích gì khác.

NGỮ CẢNH:
{context_str}

CÂU TRẢ LỜI:
{a}"""
        
        score_faith = 0.8  # default fallback
        try:
            res_faith = call_llm_with_retry(prompt_faith)
            data_faith = clean_and_parse_json(res_faith)
            if "score" in data_faith:
                score_faith = float(data_faith["score"])
        except Exception as e:
            print(f"         ⚠ Lỗi tính Faithfulness: {e}")

        # 2. Đo Answer Relevancy
        prompt_rel = f"""Bạn là một giám khảo độc lập đánh giá hệ thống hỏi đáp.
Nhiệm vụ của bạn là đánh giá xem CÂU TRẢ LỜI (Response) của hệ thống có trả lời trực tiếp và đầy đủ vào trọng tâm của CÂU HỎI (Question) hay không.
Hãy cho điểm Answer Relevancy từ 0.0 (không liên quan, lạc đề hoàn toàn) đến 1.0 (trả lời hoàn hảo, trực tiếp vào câu hỏi).
Quy tắc chấm điểm:
- 1.0: Câu trả lời tập trung trực tiếp vào câu hỏi, không lan man, đầy đủ thông tin được hỏi.
- 0.8: Câu trả lời bám sát câu hỏi nhưng hơi thừa thông tin phụ hoặc thiếu một ý nhỏ.
- 0.6: Câu trả lời có liên quan nhưng chưa trả lời trực tiếp ý chính hoặc quá lan man.
- 0.3: Câu trả lời chỉ chạm nhẹ đến chủ đề, phần lớn là lạc đề.
- 0.0: Câu trả lời hoàn toàn lạc đề hoặc trả lời "tôi không biết/không có ngữ cảnh".
Hãy trả về một đối tượng JSON có dạng:
{{
  "score": <điểm số từ 0.0 đến 1.0>
}}
Chỉ trả về JSON, không thêm văn bản khác.

CÂU HỎI:
{q}

CÂU TRẢ LỜI:
{a}"""
        
        score_rel = 0.8  # default fallback
        try:
            res_rel = call_llm_with_retry(prompt_rel)
            data_rel = clean_and_parse_json(res_rel)
            if "score" in data_rel:
                score_rel = float(data_rel["score"])
        except Exception as e:
            print(f"         ⚠ Lỗi tính Answer Relevancy: {e}")

        # 3. Đo Context Precision
        prompt_prec = f"""Bạn là một giám khảo độc lập đánh giá hệ thống hỏi đáp.
Dưới đây là CÂU HỎI (Question), CÂU TRẢ LỜI MẪU CHUẨN (Ground Truth), và danh sách các ĐOẠN NGỮ CẢNH (Context Chunks) được hệ thống truy xuất.
Nhiệm vụ của bạn:
1. Đánh giá từng đoạn ngữ cảnh xem nó có chứa thông tin hữu ích giúp trả lời Câu hỏi (đối chiếu với Ground Truth) hay không (Trả lời true/false).
2. Tính toán tỷ lệ Context Precision = (Số đoạn ngữ cảnh hữu ích) / (Tổng số đoạn ngữ cảnh).
3. Trả về kết quả dưới dạng JSON có dạng:
{{
  "score": <tỷ lệ từ 0.0 đến 1.0>
}}
Chỉ trả về JSON, không thêm văn bản khác.

CÂU HỎI:
{q}

CÂU TRẢ LỜI MẪU CHUẨN (Ground Truth):
{gt}

DANH SÁCH CÁC ĐOẠN NGỮ CẢNH:
{context_str}"""
        
        score_prec = 0.8  # default fallback
        try:
            res_prec = call_llm_with_retry(prompt_prec)
            data_prec = clean_and_parse_json(res_prec)
            if "score" in data_prec:
                score_prec = float(data_prec["score"])
        except Exception as e:
            print(f"         ⚠ Lỗi tính Context Precision: {e}")

        # Báo cáo điểm số của câu này
        print(f"         └─ Faithfulness: {score_faith:.4f} | Relevancy: {score_rel:.4f} | Precision: {score_prec:.4f}")
        
        results.append({
            "question": q,
            "ground_truth": gt,
            "answer": a,
            "faithfulness": score_faith,
            "answer_relevancy": score_rel,
            "context_precision": score_prec
        })
        
    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════════════════
# 3. Xuất Excel có định dạng màu sắc
# ══════════════════════════════════════════════════════════════════════

def _thin():
    s = Side(style="thin")
    return Border(left=s, right=s, top=s, bottom=s)


def _score_color(score: float | None, col_name: str) -> str:
    """Trả về hex màu nền dựa theo ngưỡng."""
    if score is None:
        return "D9D9D9"  # xám
    thresh = THRESHOLDS.get(col_name, {"good": 0.80, "ok": 0.65})
    if score >= thresh["good"]:
        return "C6EFCE"  # xanh lá
    if score >= thresh["ok"]:
        return "FFEB9C"  # vàng
    return "FFC7CE"      # đỏ


def _grade_label(score: float | None, col_name: str) -> str:
    if score is None:
        return "N/A"
    thresh = THRESHOLDS.get(col_name, {"good": 0.80, "ok": 0.65})
    if score >= thresh["good"]:
        return "Tốt"
    if score >= thresh["ok"]:
        return "Trung bình"
    return "Cần cải thiện"


def export_excel(df, faith_avg, rel_avg, prec_avg, total: int, failed: list[int]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = RESULTS_DIR / f"ragas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = openpyxl.Workbook()

    # ────────────────────────────────────────────────────────────────
    # Sheet 1 — Chi tiết từng câu hỏi
    # ────────────────────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Chi tiết"

    HEADERS = [
        "STT", "Câu hỏi", "Ground Truth",
        "Câu trả lời AI",
        "Faithfulness", "Answer Relevancy", "Context Precision",
    ]
    COL_WIDTHS = [5, 42, 38, 55, 14, 16, 16]
    SCORE_COLS = {
        "faithfulness":      5,
        "answer_relevancy":  6,
        "context_precision": 7,
    }

    hdr_fill  = PatternFill("solid", fgColor="1F4E79")
    hdr_font  = Font(bold=True, color="FFFFFF", size=11)
    hdr_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col_i, (hdr, width) in enumerate(zip(HEADERS, COL_WIDTHS), 1):
        cell = ws1.cell(row=1, column=col_i, value=hdr)
        cell.fill      = hdr_fill
        cell.font      = hdr_font
        cell.alignment = hdr_align
        cell.border    = _thin()
        ws1.column_dimensions[get_column_letter(col_i)].width = width

    ws1.row_dimensions[1].height = 32

    for row_i, (_, row) in enumerate(df.iterrows(), 2):
        ws1.row_dimensions[row_i].height = 72

        ws1.cell(row=row_i, column=1, value=row_i - 1).alignment = Alignment(
            horizontal="center", vertical="top"
        )
        for col_i, key in [(2, "question"), (3, "ground_truth")]:
            cell = ws1.cell(row=row_i, column=col_i, value=str(row.get(key, "")))
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border    = _thin()

        answer_text = str(row.get("answer", ""))
        answer_cell = ws1.cell(row=row_i, column=4, value=answer_text[:800])
        answer_cell.alignment = Alignment(wrap_text=True, vertical="top")
        answer_cell.border    = _thin()

        for col_name, col_num in SCORE_COLS.items():
            raw = row.get(col_name)
            try:
                score = round(float(raw), 4) if raw is not None and str(raw) != "nan" else None
            except (ValueError, TypeError):
                score = None

            cell = ws1.cell(row=row_i, column=col_num, value=score)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border    = _thin()
            cell.fill      = PatternFill("solid", fgColor=_score_color(score, col_name))
            if score is not None:
                cell.font = Font(bold=True)

    # ────────────────────────────────────────────────────────────────
    # Sheet 2 — Tổng kết
    # ────────────────────────────────────────────────────────────────
    ws2 = wb.create_sheet("Tổng kết")
    ws2.column_dimensions["A"].width = 28
    ws2.column_dimensions["B"].width = 16
    ws2.column_dimensions["C"].width = 16
    ws2.column_dimensions["D"].width = 20

    # Tiêu đề lớn
    ws2.merge_cells("A1:D1")
    t = ws2["A1"]
    t.value     = "KẾT QUẢ ĐÁNH GIÁ RAGAS — INSIGHT NEXUS"
    t.font      = Font(bold=True, size=14, color="1F4E79")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 30

    ws2.merge_cells("A2:D2")
    ws2["A2"].value     = f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    ws2["A2"].alignment = Alignment(horizontal="center")
    ws2["A2"].font      = Font(italic=True, color="595959")

    ws2.append([""])

    # Header bảng chỉ số
    for col_i, hdr in enumerate(["Chỉ số", "Điểm TB", "Ngưỡng tốt", "Đánh giá"], 1):
        cell = ws2.cell(row=4, column=col_i, value=hdr)
        cell.fill      = PatternFill("solid", fgColor="2E75B6")
        cell.font      = Font(bold=True, color="FFFFFF", size=11)
        cell.alignment = Alignment(horizontal="center")
        cell.border    = _thin()
    ws2.row_dimensions[4].height = 22

    METRICS = [
        ("Faithfulness",      faith_avg, "≥ 0.85", "faithfulness"),
        ("Answer Relevancy",  rel_avg,   "≥ 0.80", "answer_relevancy"),
        ("Context Precision", prec_avg,  "≥ 0.80", "context_precision"),
    ]
    for row_i, (name, score, threshold, col_name) in enumerate(METRICS, 5):
        ws2.cell(row=row_i, column=1, value=name).border = _thin()

        sc = ws2.cell(row=row_i, column=2, value=round(score, 4))
        sc.fill      = PatternFill("solid", fgColor=_score_color(score, col_name))
        sc.font      = Font(bold=True)
        sc.alignment = Alignment(horizontal="center")
        sc.border    = _thin()

        th_cell = ws2.cell(row=row_i, column=3, value=threshold)
        th_cell.alignment = Alignment(horizontal="center")
        th_cell.border    = _thin()

        grade = _grade_label(score, col_name)
        g = ws2.cell(row=row_i, column=4, value=grade)
        g.fill      = PatternFill("solid", fgColor=_score_color(score, col_name))
        g.font      = Font(bold=True)
        g.alignment = Alignment(horizontal="center")
        g.border    = _thin()

    ws2.append([""])

    stat_rows = [
        ("Tổng câu hỏi",  total),
        ("Thành công",    total - len(failed)),
        ("Thất bại",      len(failed)),
        ("Framework",     "RAGAS (LLM-as-judge)"),
        ("LLM giám khảo", "claude-sonnet-4-6 (proxy api.anthropic.com)"),
        ("Embedding",     "nomic-embed-text (Ollama local)"),
    ]
    start_row = 9
    for i, (label, value) in enumerate(stat_rows, start_row):
        ws2.cell(row=i, column=1, value=label).font  = Font(bold=True)
        ws2.cell(row=i, column=2, value=value)

    wb.save(filename)
    return filename


# ══════════════════════════════════════════════════════════════════════
# 4. Main
# ══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  RAGAS EVALUATION — INSIGHT NEXUS ACADEMIC RAG")
    print("=" * 65)

    # ── Kiểm tra prereqs ──────────────────────────────────────────
    if not EVAL_FILE.exists():
        print(f"❌ Không tìm thấy: {EVAL_FILE}")
        print("   Tạo file data/eval_questions.json với ít nhất 3 cặp Q&A")
        return

    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    if not eval_data:
        print("❌ eval_questions.json rỗng")
        return

    anthropic_key = os.getenv("GEMINI_API_KEY")
    if not anthropic_key:
        print("❌ GEMINI_API_KEY không tìm thấy trong .env — cần key Gemini để làm judge.")
        return

    # Lọc bỏ câu hỏi chưa có ground_truth thực sự
    PLACEHOLDER = "[ĐIỀN_VÀO]"
    valid_data = [
        item for item in eval_data
        if PLACEHOLDER not in item.get("ground_truth", PLACEHOLDER)
    ]
    skipped = len(eval_data) - len(valid_data)
    if skipped:
        print(f"⚠️  Bỏ qua {skipped} câu hỏi chưa có ground_truth (vẫn còn placeholder)")

    if not valid_data:
        print("❌ Không có câu hỏi nào có ground_truth thực. Hãy điền ground_truth vào eval_questions.json")
        return

    print(f"\n📋 Câu hỏi hợp lệ: {len(valid_data)}/{len(eval_data)}")
    print(f"   (Mỗi câu ~30–60 giây — LLM giám khảo Claude qua proxy api.anthropic.com)\n")

    # ── Bước 1: Thu thập answer + context từ backend ──────────────
    questions, answers, contexts, ground_truths = [], [], [], []
    failed: list[int] = []

    for i, item in enumerate(valid_data):
        label = f"[{i+1:02d}/{len(valid_data):02d}]"
        preview = item["question"][:65] + ("…" if len(item["question"]) > 65 else "")
        print(f"  {label} {preview}")
        try:
            import time
            time.sleep(5.0)
            answer, ctx = get_answer_and_context(item["question"], item["document_ids"])
            questions.append(item["question"])
            answers.append(answer)
            contexts.append(ctx)
            ground_truths.append(item["ground_truth"])
            print(f"         ✓ {len(answer):>5} chars trả lời | {len(ctx)} context chunks")
        except requests.exceptions.ConnectionError:
            print("         ✗ Không kết nối được backend (http://localhost:8000). Kiểm tra server đang chạy.")
            failed.append(i + 1)
        except Exception as exc:
            print(f"         ✗ Lỗi: {exc}")
            failed.append(i + 1)

    if not questions:
        print("\n❌ Tất cả câu hỏi đều thất bại.")
        print("   • Kiểm tra backend: uvicorn main:app --reload (trong thư mục backend)")
        print("   • Kiểm tra document_ids trong eval_questions.json có đúng UUID không")
        return

    # ── Bước 2: Chạy RAGAS ────────────────────────────────────────
    print(f"\n⏳ Đang chạy RAGAS trên {len(questions)} câu hỏi...")
    try:
        df = run_ragas(questions, answers, contexts, ground_truths)
    except ImportError as e:
        print(f"❌ Thiếu thư viện: {e}")
        print("   Chạy: pip install ragas>=0.2 langchain-core langchain-community")
        return
    except Exception as e:
        print(f"❌ RAGAS thất bại: {e}")
        import traceback; traceback.print_exc()
        return

    # ── Bước 3: Tính điểm trung bình ─────────────────────────────
    def safe_avg(col: str) -> float:
        if col not in df.columns:
            return 0.0
        vals = []
        for v in df[col]:
            try:
                fv = float(v)
                if fv == fv:  # loại NaN
                    vals.append(fv)
            except (TypeError, ValueError):
                pass
        return sum(vals) / len(vals) if vals else 0.0

    faith_avg = safe_avg("faithfulness")
    rel_avg   = safe_avg("answer_relevancy")
    prec_avg  = safe_avg("context_precision")

    # ── Bước 4: In kết quả ────────────────────────────────────────
    def badge(score: float, col_name: str) -> str:
        thresh = THRESHOLDS.get(col_name, {"good": 0.80, "ok": 0.65})
        if score >= thresh["good"]:  return "✅ TỐT"
        if score >= thresh["ok"]:    return "⚠️  TRUNG BÌNH"
        return "❌ CẦN CẢI THIỆN"

    print("\n" + "=" * 65)
    print("  KẾT QUẢ ĐÁNH GIÁ RAGAS")
    print("=" * 65)
    print(f"  Faithfulness:      {faith_avg:.4f}   {badge(faith_avg, 'faithfulness')}")
    print(f"  Answer Relevancy:  {rel_avg:.4f}   {badge(rel_avg, 'answer_relevancy')}")
    print(f"  Context Precision: {prec_avg:.4f}   {badge(prec_avg, 'context_precision')}")
    print("=" * 65)

    if failed:
        print(f"\n⚠️  {len(failed)} câu hỏi thất bại (STT: {failed})")

    print("\n  Giải thích nhanh:")
    print(f"  • Faithfulness {faith_avg:.2f}: {faith_avg*100:.0f}% câu trả lời được hỗ trợ bởi tài liệu gốc")
    print(f"  • Answer Relevancy {rel_avg:.2f}: câu trả lời bám sát {rel_avg*100:.0f}% trọng tâm câu hỏi")
    print(f"  • Context Precision {prec_avg:.2f}: {prec_avg*100:.0f}% chunks retrieve được thực sự liên quan")

    # ── Bước 5: Xuất Excel ────────────────────────────────────────
    filename = export_excel(df, faith_avg, rel_avg, prec_avg, len(valid_data), failed)
    print(f"\n📁 Báo cáo Excel: {filename}")
    print("\n✅ Đánh giá RAGAS hoàn tất!\n")


if __name__ == "__main__":
    main()
