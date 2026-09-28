import uuid
import os
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.db.postgres import get_db
from app.models.document import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.services.email import generate_otp, send_otp_email

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    otp: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    credential: str

class SendOtpRequest(BaseModel):
    email: str

@router.post("/send-otp")
def send_otp(req: SendOtpRequest, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    if not email or '@' not in email:
        raise HTTPException(400, "Email không hợp lệ")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email đã được sử dụng")

    # Rate limit: 1 OTP per 60s
    recent = db.execute(
        text("SELECT created_at FROM email_otps WHERE email = :e ORDER BY created_at DESC LIMIT 1"),
        {"e": email},
    ).first()
    if recent and (datetime.now() - recent.created_at).total_seconds() < 60:
        raise HTTPException(429, "Vui lòng chờ 60 giây trước khi gửi lại")

    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=10)

    db.execute(text("DELETE FROM email_otps WHERE email = :e"), {"e": email})
    db.execute(
        text("INSERT INTO email_otps (id, email, otp, expires_at) VALUES (gen_random_uuid(), :e, :o, :ex)"),
        {"e": email, "o": otp, "ex": expires_at},
    )
    db.commit()

    sent = send_otp_email(email, otp)
    result: dict = {"message": f"Đã gửi mã OTP đến {email}"}
    if not sent:
        # Chỉ lộ OTP trong response khi DEBUG=true (môi trường dev).
        # Production (DEBUG=false): OTP sẽ không hiện trong response, dù SMTP lỗi.
        if settings.DEBUG:
            result["debug_otp"] = otp
    return result


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email đã được sử dụng")
    if len(req.password) < 6:
        raise HTTPException(400, "Mật khẩu phải có ít nhất 6 ký tự")

    # Verify OTP
    if not req.otp:
        raise HTTPException(400, "Vui lòng xác thực OTP trước khi đăng ký")
    row = db.execute(
        text("SELECT otp, expires_at FROM email_otps WHERE email = :e ORDER BY created_at DESC LIMIT 1"),
        {"e": email},
    ).first()
    if not row:
        raise HTTPException(400, "Chưa gửi mã OTP hoặc mã đã hết hạn")
    if row.otp != req.otp:
        raise HTTPException(400, "Mã OTP không đúng")
    if row.expires_at < datetime.now():
        raise HTTPException(400, "Mã OTP đã hết hạn, vui lòng gửi lại")
    db.execute(text("DELETE FROM email_otps WHERE email = :e"), {"e": email})

    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        role="student",
    )
    db.add(user)
    db.commit()
    return {"message": "Đăng ký thành công", "user_id": str(user.id)}

def _user_dict(user):
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "avatar_url": user.avatar_url,
        "is_oauth": bool(user.is_oauth),
    }

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    dummy = "$2b$12$dummyhashtopreventtimingattackpadding12345678"
    stored = user.hashed_password if user else dummy
    if not verify_password(req.password, stored) or not user:
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": _user_dict(user)}


@router.post("/google")
async def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": req.credential},
            timeout=10,
        )
    if r.status_code != 200:
        raise HTTPException(401, "Token Google không hợp lệ")

    info = r.json()

    if settings.GOOGLE_CLIENT_ID and info.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(401, "Token không hợp lệ (sai Client ID)")

    email = info.get("email", "").lower().strip()
    name = info.get("name") or info.get("given_name") or ""
    if not email:
        raise HTTPException(400, "Không lấy được email từ Google")

    picture = info.get("picture")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hash_password(os.urandom(32).hex()),
            full_name=name,
            role="student",
            avatar_url=picture,
            is_oauth=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        changed = False
        if picture and not user.avatar_url:
            user.avatar_url = picture
            changed = True
        if not user.is_oauth:
            user.is_oauth = True
            changed = True
        if changed:
            db.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": _user_dict(user)}
