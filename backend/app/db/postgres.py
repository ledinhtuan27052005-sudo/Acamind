import socket
import logging
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)
_RESOLVED_URL_CACHE: dict[str, str] = {}


def _resolve_postgres_url(url: str) -> str:
    """Auto-fallback between Docker port (35432/5433) and local PostgreSQL (5432) if configured port is closed."""
    if url in _RESOLVED_URL_CACHE:
        return _RESOLVED_URL_CACHE[url]
    resolved = url
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port
        if port and port != 5432:
            try:
                with socket.create_connection((host, port), timeout=0.4):
                    resolved = url
            except OSError:
                try:
                    with socket.create_connection((host, 5432), timeout=0.4):
                        resolved = url.replace(f":{port}/", ":5432/")
                        logger.info("PostgreSQL port %s unreachable; falling back to local port 5432.", port)
                except OSError:
                    pass
    except Exception:
        pass
    _RESOLVED_URL_CACHE[url] = resolved
    return resolved


engine = create_engine(
    _resolve_postgres_url(settings.POSTGRES_URL),
    pool_size=15,
    max_overflow=25,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
