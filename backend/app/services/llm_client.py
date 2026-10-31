"""Provider-neutral LLM client for Ollama and Gemini's OpenAI-compatible API."""
from __future__ import annotations

import json
import logging
import time
from typing import Iterator, Optional

import httpx

logger = logging.getLogger(__name__)

_PERSISTENT_HTTP_CLIENT = httpx.Client(
    timeout=httpx.Timeout(90.0, connect=10.0),
    trust_env=False,
    limits=httpx.Limits(max_keepalive_connections=12, max_connections=24, keepalive_expiry=300.0),
)


def llm_configuration_error() -> str | None:
    """Return a safe, actionable error instead of failing inside a stream."""
    from app.core.config import settings
    provider = (settings.LLM_PROVIDER or "ollama").strip().lower()
    if provider == "ollama":
        if not settings.OLLAMA_BASE_URL.strip():
            return "Chưa cấu hình OLLAMA_BASE_URL trong backend/.env."
        if not settings.LLM_MODEL.strip():
            return "Chưa cấu hình LLM_MODEL trong backend/.env."
        return None
    if provider == "gemini" and not settings.GEMINI_API_KEY.strip():
        return "Chưa cấu hình GEMINI_API_KEY cho LLM_PROVIDER=gemini trong backend/.env."
    if provider not in {"ollama", "gemini"}:
        return f"LLM_PROVIDER={provider!r} chưa được hỗ trợ; chọn 'ollama' hoặc 'gemini'."
    return None


def ocr_configuration_error() -> str | None:
    """Describe missing settings for the independently configured vision/OCR model."""
    from app.core.config import settings
    provider = (settings.OCR_PROVIDER or "gemini").strip().lower()
    if provider == "gemini":
        if not settings.GEMINI_API_KEY.strip():
            return "Chưa cấu hình GEMINI_API_KEY cho OCR."
        if not settings.GEMINI_BASE_URL.strip() or not settings.OCR_MODEL.strip():
            return "Cần cấu hình GEMINI_BASE_URL và OCR_MODEL cho OCR."
        return None
    if provider == "ollama":
        if not settings.OLLAMA_BASE_URL.strip() or not settings.OCR_MODEL.strip():
            return "Cần cấu hình OLLAMA_BASE_URL và OCR_MODEL cho OCR Ollama."
        return None
    return f"OCR_PROVIDER={provider!r} chưa được hỗ trợ; chọn 'gemini' hoặc 'ollama'."


class LLMClient:
    """Client LLM dùng API OpenAI-compatible của Ollama hoặc Gemini."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "qwen3:4b-instruct",
        provider: str = "ollama",
    ):
        self.api_key = api_key
        self.provider = (provider or "ollama").strip().lower()
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or "qwen3:4b-instruct"

    @property
    def is_configured(self) -> bool:
        if self.provider == "ollama":
            return bool(self.base_url and self.model)
        if self.provider == "gemini":
            return bool(self.base_url and self.api_key)
        return False

    # ── Public API ──────────────────────────────────────────────────────────

    def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """Gọi LLM non-stream, trả về chuỗi text (đã strip)."""
        self._ensure_configured()

        eff_max_tokens = min(max_tokens, 2048) if self.provider == "ollama" else max_tokens
        body = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "max_tokens": eff_max_tokens,
            "temperature": temperature,
        }
        if self.provider == "ollama":
            body["keep_alive"] = "24h"

        r = None
        last_net_err = None
        for attempt in range(3):
            try:
                r = _PERSISTENT_HTTP_CLIENT.post(
                    self._chat_url(),
                    headers=self._headers(),
                    json=body,
                )
                break
            except httpx.HTTPError as net_err:
                last_net_err = net_err
                logger.warning("%s complete network error (attempt %d/3): %s", self.provider, attempt + 1, net_err)
                time.sleep(0.35 * (attempt + 1))

        if r is None:
            if self.provider == "gemini":
                from app.core.config import settings
                if settings.OLLAMA_BASE_URL:
                    logger.warning("Gemini complete() unreachable; falling back to local Ollama (qwen3:4b-instruct)")
                    fb = LLMClient(api_key="", base_url=settings.OLLAMA_BASE_URL, model="qwen3:4b-instruct", provider="ollama")
                    return fb.complete(messages, system=system, max_tokens=max_tokens, temperature=temperature)
            raise last_net_err  # type: ignore[misc]

        if r.status_code != 200:
            logger.error("%s API error %s: %s", self.provider, r.status_code, r.text[:500])
            if self.provider == "gemini" and r.status_code in (404, 429, 503):
                for fb_model in ("gemini-3.5-flash-lite", "gemini-2.5-flash"):
                    if self.model != fb_model:
                        logger.warning("Model %s returned %s; retrying with %s", self.model, r.status_code, fb_model)
                        self.model = fb_model
                        return self.complete(messages, system=system, max_tokens=max_tokens, temperature=temperature)
            if self.provider == "gemini":
                from app.core.config import settings
                if settings.OLLAMA_BASE_URL:
                    logger.warning("Gemini complete() failed (%s); falling back to local Ollama (qwen3:4b-instruct)", r.status_code)
                    fb = LLMClient(api_key="", base_url=settings.OLLAMA_BASE_URL, model="qwen3:4b-instruct", provider="ollama")
                    return fb.complete(messages, system=system, max_tokens=max_tokens, temperature=temperature)
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
        mime_type: str = "image/jpeg",
    ) -> str:
        """Call the configured model with an image; the model must support vision."""
        import base64
        self._ensure_configured()

        b64 = base64.b64encode(image_data).decode("utf-8")

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
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{b64}",
                    },
                },
            ],
        })

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
            except httpx.HTTPError as e:
                wait = 0.5 * (2 ** attempt)
                logger.warning(f"Vision API attempt {attempt + 1}/3 failed: {e}. Retry in {wait}s")
                time.sleep(wait)

        return "[Hình ảnh — API lỗi sau 3 lần thử. Vui lòng mô tả nội dung ảnh trong câu hỏi của bạn.]"

    def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.1,
    ) -> Iterator[str]:
        """Gọi LLM streaming, yield từng delta text với cơ chế retry chống đứt kết nối DNS/TCP."""
        self._ensure_configured()

        eff_max_tokens = min(max_tokens, 2048) if self.provider == "ollama" else max_tokens
        body = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "max_tokens": eff_max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if self.provider == "ollama":
            body["keep_alive"] = "24h"

        last_net_err = None
        for attempt in range(3):
            try:
                if True:
                    with _PERSISTENT_HTTP_CLIENT.stream(
                        "POST", self._chat_url(), headers=self._headers(), json=body
                    ) as r:
                        if r.status_code != 200:
                            error_body = ""
                            for chunk in r.iter_bytes():
                                error_body += chunk.decode("utf-8", errors="replace")
                                if len(error_body) > 500:
                                    break
                            logger.error("%s stream error %s: %s", self.provider, r.status_code, error_body)
                            if self.provider == "ollama" and r.status_code == 400 and "context size" in error_body:
                                body["max_tokens"] = min(int(body.get("max_tokens", 1024)), 768)
                                for m in body["messages"]:
                                    if isinstance(m.get("content"), str) and len(m["content"]) > 10000:
                                        m["content"] = m["content"][:10000]
                                continue
                            if self.provider == "gemini" and r.status_code in (404, 429, 503):
                                for fb_model in ("gemini-3.5-flash-lite", "gemini-2.5-flash"):
                                    if self.model != fb_model:
                                        logger.warning("Model %s returned %s; retrying stream with %s", self.model, r.status_code, fb_model)
                                        self.model = fb_model
                                        yield from self.stream(messages, system=system, max_tokens=max_tokens, temperature=temperature)
                                        return
                            if self.provider == "gemini":
                                from app.core.config import settings
                                if settings.OLLAMA_BASE_URL:
                                    logger.warning("Gemini stream() failed (%s); falling back to local Ollama (qwen3:4b-instruct)", r.status_code)
                                    fb = LLMClient(api_key="", base_url=settings.OLLAMA_BASE_URL, model="qwen3:4b-instruct", provider="ollama")
                                    yield from fb.stream(messages, system=system, max_tokens=max_tokens, temperature=temperature)
                                    return
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
                        return
            except httpx.HTTPError as net_err:
                last_net_err = net_err
                logger.warning("%s stream network error (attempt %d/3): %s", self.provider, attempt + 1, net_err)
                time.sleep(0.35 * (attempt + 1))

        if self.provider == "gemini":
            from app.core.config import settings
            if settings.OLLAMA_BASE_URL:
                logger.warning("Gemini stream() unreachable after 3 attempts; falling back to local Ollama (qwen3:4b-instruct)")
                fb = LLMClient(api_key="", base_url=settings.OLLAMA_BASE_URL, model="qwen3:4b-instruct", provider="ollama")
                yield from fb.stream(messages, system=system, max_tokens=max_tokens, temperature=temperature)
                return
        if last_net_err is not None:
            raise last_net_err

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _chat_url(self) -> str:
        """Build OpenAI-compatible chat completions URL."""
        base_url = self.base_url
        if self.provider == "ollama" and not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        return f"{base_url}/chat/completions"

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _ensure_configured(self) -> None:
        if self.is_configured:
            return
        if self.provider == "ollama":
            raise RuntimeError(
                "Ollama chưa được cấu hình. Hãy khởi động Ollama, tải model đã chọn "
                "và kiểm tra OLLAMA_BASE_URL/LLM_MODEL trong backend/.env."
            )
        if self.provider == "gemini" and not self.api_key:
            raise RuntimeError("Chưa cấu hình GEMINI_API_KEY cho Gemini trong backend/.env")
        raise RuntimeError(f"LLM provider không được hỗ trợ: {self.provider}")

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
_ocr_client: Optional[LLMClient] = None


def get_default_client() -> LLMClient:
    """Lấy singleton LLMClient dựa trên settings. Lazy import tránh circular."""
    global _default_client
    if _default_client is None:
        from app.core.config import settings
        provider = (settings.LLM_PROVIDER or "ollama").strip().lower()
        if provider == "ollama":
            base_url = settings.OLLAMA_BASE_URL
            api_key = ""
        else:
            base_url = settings.GEMINI_BASE_URL
            api_key = settings.GEMINI_API_KEY
        _default_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=settings.LLM_MODEL,
            provider=provider,
        )
    return _default_client


def get_ocr_client() -> LLMClient:
    """Get a separate vision client so scanned-page OCR can use Gemini."""
    global _ocr_client
    if _ocr_client is None:
        from app.core.config import settings
        provider = (settings.OCR_PROVIDER or "gemini").strip().lower()
        if provider == "gemini":
            _ocr_client = LLMClient(
                api_key=settings.GEMINI_API_KEY,
                base_url=settings.GEMINI_BASE_URL,
                model=settings.OCR_MODEL,
                provider="gemini",
            )
        elif provider == "ollama":
            _ocr_client = LLMClient(
                api_key="",
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OCR_MODEL,
                provider="ollama",
            )
        else:
            raise RuntimeError(
                f"OCR_PROVIDER={provider!r} chưa được hỗ trợ; chọn 'gemini' hoặc 'ollama'."
            )
    return _ocr_client
