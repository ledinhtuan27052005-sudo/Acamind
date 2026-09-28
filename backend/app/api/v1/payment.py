import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.postgres import get_db
from app.models.document import User, Payment
from app.core.security import get_current_user, get_optional_user
from app.core.config import settings
from app.core.plan_utils import PLAN_LIMITS

router = APIRouter()

# ── Helpers ───────────────────────────────────────────────────────────────────

PLAN_PRICES = {
    "pro":        149_000,
    "researcher": 499_000,
}

def _gen_ref_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "ACM" + "".join(random.choices(chars, k=9))  # e.g. ACM3X9KF2PL


def _vietqr_url(amount: int, ref_code: str) -> str:
    """Generate VietQR image URL (no API key needed)."""
    name = settings.BANK_ACCOUNT_NAME.replace(" ", "%20")
    desc = ref_code.replace(" ", "%20")
    return (
        f"https://img.vietqr.io/image/{settings.BANK_CODE}-{settings.BANK_ACCOUNT_NO}"
        f"-compact2.png?amount={amount}&addInfo={desc}&accountName={name}"
    )


def _expire_pending(db: Session):
    """Mark expired pending payments."""
    db.query(Payment).filter(
        Payment.status == "pending",
        Payment.expires_at < datetime.now(),
    ).update({"status": "expired"})
    db.commit()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreatePaymentRequest(BaseModel):
    plan: str  # "pro" | "researcher"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/create")
def create_payment(
    req: CreatePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo yêu cầu thanh toán mới, trả về mã tham chiếu + QR URL."""
    if req.plan not in PLAN_PRICES:
        raise HTTPException(400, f"Gói không hợp lệ. Chọn: {list(PLAN_PRICES.keys())}")

    # Check if user already has a better or equal plan
    current_plan = getattr(current_user, "plan", "free") or "free"
    if current_plan == req.plan:
        raise HTTPException(400, "Bạn đã có gói này rồi.")
    if current_user.role == "admin":
        raise HTTPException(400, "Admin không cần nâng cấp gói.")

    # Expire old pending payments for this user + plan
    _expire_pending(db)
    db.query(Payment).filter(
        Payment.user_id == current_user.id,
        Payment.plan == req.plan,
        Payment.status == "pending",
    ).update({"status": "expired"})
    db.commit()

    amount = PLAN_PRICES[req.plan]
    ref_code = _gen_ref_code()
    # Ensure uniqueness
    while db.query(Payment).filter(Payment.ref_code == ref_code).first():
        ref_code = _gen_ref_code()

    expires_at = datetime.now() + timedelta(minutes=settings.PAYMENT_EXPIRE_MINUTES)

    payment = Payment(
        user_id=current_user.id,
        plan=req.plan,
        amount=amount,
        ref_code=ref_code,
        status="pending",
        expires_at=expires_at,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "payment_id": str(payment.id),
        "ref_code": ref_code,
        "plan": req.plan,
        "plan_label": PLAN_LIMITS[req.plan]["label"],
        "amount": amount,
        "bank_code": settings.BANK_CODE,
        "bank_account_no": settings.BANK_ACCOUNT_NO,
        "bank_account_name": settings.BANK_ACCOUNT_NAME,
        "qr_url": _vietqr_url(amount, ref_code),
        "expires_at": expires_at.isoformat(),
        "expire_minutes": settings.PAYMENT_EXPIRE_MINUTES,
    }


@router.get("/status/{ref_code}")
def check_payment_status(
    ref_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll trạng thái giao dịch theo mã tham chiếu."""
    _expire_pending(db)
    payment = db.query(Payment).filter(
        Payment.ref_code == ref_code,
        Payment.user_id == current_user.id,
    ).first()
    if not payment:
        raise HTTPException(404, "Không tìm thấy giao dịch")

    return {
        "status": payment.status,
        "plan": payment.plan,
        "amount": payment.amount,
        "ref_code": payment.ref_code,
        "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
        "expires_at": payment.expires_at.isoformat(),
    }


@router.get("/history")
def payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lịch sử thanh toán của user hiện tại."""
    _expire_pending(db)
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": str(p.id),
            "plan": p.plan,
            "plan_label": PLAN_LIMITS.get(p.plan, {}).get("label", p.plan),
            "amount": p.amount,
            "ref_code": p.ref_code,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        }
        for p in payments
    ]


# ── Casso Webhook ─────────────────────────────────────────────────────────────

@router.post("/webhook/casso")
async def casso_webhook(
    request: Request,
    db: Session = Depends(get_db),
    secure_token: Optional[str] = Header(None, alias="secure-token"),
    apikey: Optional[str] = Header(None, alias="Apikey"),
):
    """
    Casso gửi POST đến endpoint này mỗi khi có giao dịch mới.
    Cấu hình tại: Casso.vn → Kết nối → Webhook → URL = https://your-domain/api/v1/payment/webhook/casso
    """
    # Verify secret key if configured (Casso dùng header "secure-token")
    token = secure_token or apikey
    if settings.CASSO_WEBHOOK_SECRET:
        if token != settings.CASSO_WEBHOOK_SECRET:
            raise HTTPException(401, "Invalid webhook secret")

    body = await request.json()

    # Casso payload: {"error": 0, "data": [{...}, ...]}
    transactions = body.get("data", [])
    if not isinstance(transactions, list):
        transactions = [transactions]

    processed = []
    for txn in transactions:
        description: str = str(txn.get("description", "") or txn.get("memo", "") or "")
        amount: int = int(txn.get("amount", 0))

        # Find a matching pending payment by scanning for ref_code in description
        # ref_code format: ACM + 9 uppercase alphanumeric chars
        import re
        matches = re.findall(r'(?:ACM|ENT)[A-Z0-9]{9}', description.upper())

        for ref_code in matches:
            # Enterprise offer payment
            if ref_code.startswith("ENT"):
                from app.models.document import EnterpriseOffer
                from app.api.v1.enterprise import _activate_enterprise_offer
                offer = db.query(EnterpriseOffer).filter(
                    EnterpriseOffer.ref_code == ref_code,
                    EnterpriseOffer.status.in_(["draft", "active"]),
                ).first()
                if not offer:
                    continue
                if offer.expires_at and offer.expires_at < datetime.now():
                    offer.status = "expired"
                    db.commit()
                    continue
                if amount < offer.amount:
                    print(f"[ENTERPRISE] Underpayment for {ref_code}: got {amount}, need {offer.amount}")
                    continue
                _activate_enterprise_offer(offer, db)
                processed.append(ref_code)
                continue

            payment = db.query(Payment).filter(
                Payment.ref_code == ref_code,
                Payment.status == "pending",
            ).first()

            if not payment:
                continue

            # Check expiry
            if payment.expires_at < datetime.now():
                payment.status = "expired"
                db.commit()
                continue

            # Verify amount (accept exact match or overpayment)
            if amount < payment.amount:
                print(f"[PAYMENT] Underpayment for {ref_code}: got {amount}, need {payment.amount}")
                continue

            # Upgrade user plan
            user = db.query(User).filter(User.id == payment.user_id).first()
            if user:
                user.plan = payment.plan
                # Also upgrade role to researcher if plan is researcher
                if payment.plan == "researcher" and user.role not in ("admin",):
                    user.role = "researcher"

            payment.status = "completed"
            payment.completed_at = datetime.now()
            db.commit()

            print(f"[PAYMENT] ✓ Upgraded user {user.email if user else payment.user_id} → {payment.plan} (ref: {ref_code}, amount: {amount})")
            processed.append(ref_code)

    return {"ok": True, "processed": processed}


# ── SePay Webhook (alternative) ───────────────────────────────────────────────

@router.post("/webhook/sepay")
async def sepay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    SePay webhook endpoint.
    SePay payload: {"content": "...", "transferAmount": 99000, ...}
    """
    body = await request.json()

    description: str = str(
        body.get("content", "") or body.get("description", "") or ""
    )
    amount: int = int(body.get("transferAmount", 0) or body.get("amount", 0))

    import re
    matches = re.findall(r'(?:ACM|ENT)[A-Z0-9]{9}', description.upper())

    for ref_code in matches:
        if ref_code.startswith("ENT"):
            from app.models.document import EnterpriseOffer
            from app.api.v1.enterprise import _activate_enterprise_offer
            offer = db.query(EnterpriseOffer).filter(
                EnterpriseOffer.ref_code == ref_code,
                EnterpriseOffer.status.in_(["draft", "active"]),
            ).first()
            if not offer:
                continue
            if offer.expires_at and offer.expires_at < datetime.now():
                offer.status = "expired"
                db.commit()
                continue
            if amount < offer.amount:
                continue
            _activate_enterprise_offer(offer, db)
            continue

        payment = db.query(Payment).filter(
            Payment.ref_code == ref_code,
            Payment.status == "pending",
        ).first()

        if not payment or payment.expires_at < datetime.now():
            continue
        if amount < payment.amount:
            continue

        user = db.query(User).filter(User.id == payment.user_id).first()
        if user:
            user.plan = payment.plan
            if payment.plan == "researcher" and user.role not in ("admin",):
                user.role = "researcher"

        payment.status = "completed"
        payment.completed_at = datetime.now()
        db.commit()
        print(f"[PAYMENT/SEPAY] ✓ Upgraded {user.email if user else payment.user_id} → {payment.plan}")

    return {"success": True}


# ── Admin: list all payments ──────────────────────────────────────────────────

@router.get("/admin/list")
def admin_list_payments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin: danh sách tất cả giao dịch, có thể lọc theo status."""
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin mới có thể xem danh sách thanh toán")

    _expire_pending(db)
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    payments = query.order_by(Payment.created_at.desc()).limit(100).all()

    result = []
    for p in payments:
        u = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            "id": str(p.id),
            "user_id": str(p.user_id),
            "user_email": u.email if u else "Unknown",
            "user_name": u.full_name if u else None,
            "plan": p.plan,
            "plan_label": PLAN_LIMITS.get(p.plan, {}).get("label", p.plan),
            "amount": p.amount,
            "ref_code": p.ref_code,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            "expires_at": p.expires_at.isoformat(),
        })
    return result


# ── Admin: manual confirm ─────────────────────────────────────────────────────

@router.post("/admin/confirm/{ref_code}")
def admin_confirm_payment(
    ref_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin xác nhận thủ công khi webhook không hoạt động."""
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin mới có thể xác nhận thanh toán")

    payment = db.query(Payment).filter(Payment.ref_code == ref_code).first()
    if not payment:
        raise HTTPException(404, "Không tìm thấy giao dịch")
    if payment.status == "completed":
        raise HTTPException(400, "Giao dịch đã được xác nhận trước đó")

    user = db.query(User).filter(User.id == payment.user_id).first()
    if user:
        user.plan = payment.plan
        if payment.plan == "researcher" and user.role not in ("admin",):
            user.role = "researcher"

    payment.status = "completed"
    payment.completed_at = datetime.now()
    db.commit()

    return {
        "message": f"Đã nâng cấp {user.email if user else str(payment.user_id)} lên gói {payment.plan}",
        "ref_code": ref_code,
    }
