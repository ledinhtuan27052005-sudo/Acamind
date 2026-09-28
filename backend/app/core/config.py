import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# ── Force-load .env TRƯỚC khi Settings() được khởi tạo ────────────────────
# Vấn đề: trên Windows, một số tool set sẵn API key ở mức OS environment.
# GEMINI_API_KEY / GEMINI_BASE_URL ở mức OS environment. pydantic-settings
# v2 mặc định ưu tiên OS env hơn .env file → backend đọc nhầm key cũ
# thay vì key trong backend/.env.
#
# Cách fix: gọi load_dotenv(override=True) để ghi đè OS env bằng giá trị trong
# .env NGAY TRƯỚC khi Settings() khởi tạo. File .env nằm cùng thư mục với
# config.py (backend/app/core/.env → ../../.env).
#
# CHÚ Ý: Khi deploy production, set biến môi trường ở mức container/host
# KHÔNG trùng tên với field trong .env — hoặc xóa .env để giữ behavior OS env.
_DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _DOTENV_PATH.exists():
    load_dotenv(_DOTENV_PATH, override=True)

class Settings(BaseSettings):
    POSTGRES_URL: str
    NEO4J_URL: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    LLM_MODEL: str = "gemini-3.1-flash-lite"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PDF_UPLOAD_DIR: str = "../data/raw_pdfs"
    GOOGLE_CLIENT_ID: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # ── Phase A: Memory builder config ─────────────────────────────────────────
    # MEMORY_LLM_BACKEND: gemini (default) — dùng Gemini qua llm_client.
    MEMORY_LLM_BACKEND: str = "gemini"
    MEMORY_LLM_MODEL: str = "gemini-3.1-flash-lite"

    # ── App config ────────────────────────────────────────────────────────
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Payment / Bank transfer ───────────────────────────────────────────────
    BANK_CODE: str = "VCB"                   # VietQR bank code
    BANK_ACCOUNT_NO: str = ""                # Số tài khoản nhận tiền
    BANK_ACCOUNT_NAME: str = "ACAMIND"       # Tên chủ tài khoản (IN HOA)
    CASSO_WEBHOOK_SECRET: str = ""           # Casso → Settings → Webhook → Secret key
    PAYMENT_EXPIRE_MINUTES: int = 15         # Hết hạn sau 15 phút

    # ── Config ────────────────────────────────────────────────────────────────
    # Load .env từ đường dẫn tuyệt đối (đã được override ở đầu file bằng
    # load_dotenv(override=True)), nên pydantic-settings chỉ cần declare
    # env_file để giữ backward compatibility với code khác.
    model_config = SettingsConfigDict(
        env_file=str(_DOTENV_PATH) if _DOTENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_pdf_upload_dir(self) -> str:
        """Trả về absolute path cho PDF upload directory."""
        path = Path(self.PDF_UPLOAD_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

settings = Settings()
