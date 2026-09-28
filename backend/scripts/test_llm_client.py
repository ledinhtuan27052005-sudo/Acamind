"""
Test LLM client (Gemini qua OpenAI-compatible endpoint).

Gồm 3 phần:
  1. OpenAI-compatible HTTP request — request thường.
  2. OpenAI-compatible HTTP request — streaming.
  3. Qua LLMClient của dự án — request thường + streaming.

Chạy:
    ../.venv_new/Scripts/python.exe scripts/test_llm_client.py
"""
from __future__ import annotations

# ── Ép UTF-8 cho stdout/stderr (Windows console mặc định cp1252) ──────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import sys
import time
from pathlib import Path

# Load .env từ backend/ (không phụ thuộc pydantic) — GHI ĐÈ OS env để dùng
# config trong .env.
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

API_KEY = os.environ.get("GEMINI_API_KEY", "")
BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
# Default model — đổi tên model ở đây nếu muốn test với model khác.
MODEL = os.environ.get("LLM_MODEL", "gemini-3.1-flash-lite")

print("=" * 70)
print("Acamind — LLM client smoke test")
print("=" * 70)
print(f"BASE_URL : {BASE_URL}")
print(f"MODEL    : {MODEL}")
if API_KEY:
    print(f"API_KEY  : {API_KEY[:14]}...{API_KEY[-6:]}")
else:
    print("API_KEY  : (empty!)")
print("-" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# Phần 1: Anthropic SDK — request thường
# ─────────────────────────────────────────────────────────────────────────────
def test_anthropic_sdk_request() -> bool:
    print("\n[1] Anthropic SDK — request thường")
    try:
        import anthropic  # noqa: F401
    except ImportError:
        print("  SKIP: chưa cài anthropic SDK. Cài: pip install anthropic")
        return False

    import anthropic
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    t0 = time.time()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system="Bạn là trợ lý ngắn gọn, trả lời bằng tiếng Việt.",
        messages=[
            {"role": "user", "content": "Chào bạn, hôm nay bạn thế nào? Trả lời 1-2 câu."},
        ],
    )
    elapsed = time.time() - t0
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    print(f"  OK {elapsed:.2f}s | model={msg.model} | usage={msg.usage.input_tokens}in/{msg.usage.output_tokens}out")
    print(f"  → {text[:200]}")
    return bool(text.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Phần 2: Anthropic SDK — streaming
# ─────────────────────────────────────────────────────────────────────────────
def test_anthropic_sdk_streaming() -> bool:
    print("\n[2] Anthropic SDK — streaming")
    try:
        import anthropic
    except ImportError:
        print("  SKIP: chưa cài anthropic SDK.")
        return False

    import anthropic
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    t0 = time.time()
    parts = []
    with client.messages.stream(
        model=MODEL,
        max_tokens=256,
        system="Bạn là trợ lý ngắn gọn, trả lời bằng tiếng Việt.",
        messages=[
            {"role": "user", "content": "Đếm từ 1 đến 5, mỗi số trên 1 dòng."},
        ],
    ) as stream:
        for text in stream.text_stream:
            parts.append(text)
            sys.stdout.write(text)
            sys.stdout.flush()
    print()
    elapsed = time.time() - t0
    full = "".join(parts).strip()
    print(f"  OK {elapsed:.2f}s | {len(parts)} chunks | len={len(full)}")
    return bool(full)


# ─────────────────────────────────────────────────────────────────────────────
# Phần 3: LLMClient của dự án — request thường + streaming
# ─────────────────────────────────────────────────────────────────────────────
def test_project_llm_client() -> bool:
    print("\n[3] LLMClient của dự án (app.services.llm_client.LLMClient)")
    sys.path.insert(0, str(BACKEND_DIR))
    from app.services.llm_client import get_default_client

    client = get_default_client()

    # 3a) complete()
    t0 = time.time()
    text = client.complete(
        messages=[{"role": "user", "content": "1+1 bằng mấy? Trả lời 1 dòng."}],
        system="Bạn là trợ lý toán, trả lời ngắn.",
        max_tokens=64,
        temperature=0.0,
    )
    elapsed = time.time() - t0
    print(f"  3a) complete()  {elapsed:.2f}s → {text.strip()[:120]}")
    ok_complete = bool(text.strip())

    # 3b) stream()
    t0 = time.time()
    parts = []
    sys.stdout.write("  3b) stream()    ")
    for delta in client.stream(
        messages=[{"role": "user", "content": "Liệt kê 3 màu cơ bản, mỗi màu 1 dòng."}],
        system="Bạn là trợ lý ngắn gọn.",
        max_tokens=64,
        temperature=0.0,
    ):
        parts.append(delta)
        sys.stdout.write(delta)
        sys.stdout.flush()
    elapsed = time.time() - t0
    print(f"\n           {elapsed:.2f}s | {len(parts)} chunks")
    ok_stream = bool("".join(parts).strip())
    return ok_complete and ok_stream


# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    if not API_KEY:
        print("GEMINI_API_KEY chưa set. Kiểm tra file backend/.env.")
        return 2

    results = {}
    for name, fn in [
        ("anthropic_request", test_anthropic_sdk_request),
        ("anthropic_stream", test_anthropic_sdk_streaming),
        ("project_client", test_project_llm_client),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            results[name] = False

    print("\n" + "=" * 70)
    print("KẾT QUẢ:")
    for k, v in results.items():
        mark = "PASS" if v else "FAIL"
        print(f"  [{mark}] {k}")
    print("=" * 70)
    return 0 if any(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())