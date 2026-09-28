from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.postgres import get_db

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_user_id(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = _decode_user_id(credentials)
    if not user_id:
        return None
    from app.models.document import User
    return db.query(User).filter(User.id == user_id).first()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(401, "Cần đăng nhập để thực hiện thao tác này")
    user_id = _decode_user_id(credentials)
    if not user_id:
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")
    from app.models.document import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "Tài khoản không tồn tại")
    # Auto-downgrade org members whose membership expired
    if user.plan_expires_at and user.plan_expires_at < datetime.now() and user.plan not in ("free",):
        user.plan = "free"
        user.plan_expires_at = None
        db.commit()
    return user


def require_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Yêu cầu quyền Admin")
    return user


# Legacy — kept for backwards compat
def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    return _decode_user_id(credentials)
