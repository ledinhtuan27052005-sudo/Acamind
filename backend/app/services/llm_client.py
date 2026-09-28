
"""
LLM client trung tâm — gọi Gemini API qua OpenAI-compatible endpoint.

Endpoint: https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
Model: gemini-3.1-flash-lite (hoặc model khác từ .env)

Base URL config trong .env: GEMINI_BASE_URL
= https://generativelanguage.googleapis.com/v1beta/openai
Code tự ghép /chat/completions khi gọi API.
"""
from __future__ import annotations

import json
import logging
from typing import Iterator, Optional

import httpx

logger = logging.getLogger(__name__)


def llm_configuration_error() -> str | None:
    """Return a safe, actionable error instead of failing inside a stream."""
    from app.core.config import settings
    if not settings.GEMINI_API_KEY.strip():
        return "AI chưa được cấu hình. Thêm GEMINI_API_KEY vào backend/.env rồi khởi động lại backend."
    return None


class LLMClient:
    """Client LLM — gọi Gemini qua OpenAI-compatible endpoint."""

    def __init__(self, api_key: str, base_url: str, model: str = "gemini-3.1-flash-lite"):
        self.api_key = api_key
        # Base URL: vd "https://generativelanguage.googleapis.com/v1beta/openai"
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or "gemini-3.1-flash-lite"

    # ── Public API ──────────────────────────────────────────────────────────

    def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """Gọi LLM non-stream, trả về chuỗi text (đã strip)."""
        if not self.api_key:
            raise RuntimeError(
                "Chưa cấu hình GEMINI_API_KEY trong .env"
            )

        body = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                self._chat_url(),
                headers=self._headers(),
                json=body,
            )

        if r.status_code != 200:
            logger.error(f"Gemini API error {r.status_code}: {r.text[:500]}")
            r.raise_for_status()

        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message", {}).get("content") or "").strip()

    def complete_image(
        self,
        image_data: bytes,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """Gọi LLM với ảnh (vision). Gemini hỗ trợ vision natively."""
        import base64
        import time
        if not self.api_key:
            raise RuntimeError("Chưa cấu hình API key trong .env")

        b64 = base64.b64encode(image_data).decode("utf-8")

        # OpenAI-compatible vision format
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [],
        }

        if system:
            body["messages"].append({"role": "system", "content": system})

        body["messages"].append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                    },
                },
                {"type": "text", "text": prompt},
            ],
        })

        last_err = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=120.0) as client:
                    r = client.post(
                        self._chat_url(),
                        headers=self._headers(),
                        json=body,
                    )
                r.raise_for_status()
                data = r.json()
                choices = data.get("choices") or []
                if choices:
                    text = (choices[0].get("message", {}).get("content") or "").strip()
                    if text:
                        return text
                last_err = "Response empty"
            except httpx.HTTPError as e:
                last_err = e
                wait = 0.5 * (2 ** attempt)
                logger.warning(
                    f"Vision API attempt {attempt + 1}/3 failed: {e}. Retry in {wait}s"
                )
                time.sleep(wait)

        return f"[Hình ảnh — API lỗi sau 3 lần thử. Vui lòng mô tả nội dung ảnh trong câu hỏi của bạn.]"

    def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.1,
    ) -> Iterator[str]:
        """Gọi LLM streaming, yield từng delta text."""
        if not self.api_key:
            raise RuntimeError(
                "Chưa cấu hình GEMINI_API_KEY trong .env"
            )

        body = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        with httpx.Client(timeout=None) as client:
            with client.stream(
                "POST", self._chat_url(), headers=self._headers(), json=body
            ) as r:
                if r.status_code != 200:
                    # Read error body for logging
                    error_body = ""
                    for chunk in r.iter_bytes():
                        error_body += chunk.decode("utf-8", errors="replace")
                        if len(error_body) > 500:
                            break
                    logger.error(f"Gemini stream error {r.status_code}: {error_body}")
                    r.raise_for_status()

                for line in r.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        if payload in ("[DONE]", ""):
                            if payload == "[DONE]":
                                return
                            continue
                        try:
                            ev = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        choices = ev.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        text = delta.get("content")
                        if text:
                            yield text

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _chat_url(self) -> str:
        """Build chat completions URL.
        
        Base URL đã chứa /v1beta/openai → chỉ thêm /chat/completions.
        """
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, messages: list[dict], system: Optional[str] = None) -> list[dict]:
        """Build OpenAI-compatible messages list."""
        out: list[dict] = []
        if system:
            out.append({"role": "system", "content": system})
        for m in messages:
            role = m.get("role", "user")
            if role == "system":
                out.insert(0, {"role": "system", "content": m.get("content", "")})
            else:
                out.append({"role": role, "content": m.get("content", "")})
        return out


# ── Singleton theo settings ────────────────────────────────────────────────

_default_client: Optional[LLMClient] = None


def get_default_client() -> LLMClient:
    """Lấy singleton LLMClient dựa trên settings. Lazy import tránh circular."""
    global _default_client
    if _default_client is None:
        from app.core.config import settings
        api_key = settings.GEMINI_API_KEY
        _default_client = LLMClient(
            api_key=api_key,
            base_url=settings.GEMINI_BASE_URL,
            model=settings.LLM_MODEL,
        )
    return _default_client
