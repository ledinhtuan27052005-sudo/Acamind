import calendar
import random
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.postgres import get_db
from app.models.document import EnterpriseOffer, EnterpriseTicket, Organization, User
from app.services.email import send_enterprise_ticket_to_admin, send_offer_to_customer

router = APIRouter()

DEFAULT_OWNER_MONTHLY = 550
DEFAULT_OWNER_ANNUAL = 7000


def _add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _gen_token() -> str:
    return secrets.token_urlsafe(16)


def _gen_ref_code(db: Session) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "ENT" + "".join(random.choices(chars, k=9))
        if not db.query(EnterpriseOffer).filter(EnterpriseOffer.ref_code == code).first():
            return code


def _ticket_out(t: EnterpriseTicket) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "email": t.email,
        "school_name": t.school_name,
        "phone": t.phone,
        "message": t.message,
        "status": t.status,
        "admin_note": t.admin_note,
        "user_id": str(t.user_id) if t.user_id else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def _offer_out(o: EnterpriseOffer) -> dict:
    return {
        "id": str(o.id),
        "ticket_id": str(o.ticket_id) if o.ticket_id else None,
        "token": o.token,
        "school_name": o.school_name,
        "contact_email": o.contact_email,
        "amount": o.amount,
        "duration_months": o.duration_months,
        "package_type": o.package_type,
        "max_slots": o.max_slots,
        "max_monthly_docs_member": o.max_monthly_docs_member,
        "max_monthly_docs_owner": o.max_monthly_docs_owner,
        "max_annual_docs_owner": o.max_annual_docs_owner,
        "ref_code": o.ref_code,
        "status": o.status,
        "activated_email": o.activated_email,
        "expires_at": o.expires_at.isoformat() if o.expires_at else None,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "completed_at": o.completed_at.isoformat() if o.completed_at else None,
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class ContactRequest(BaseModel):
    name: str
    email: str
    school_name: str
    phone: Optional[str] = None
    message: Optional[str] = None


class ClaimOfferRequest(BaseModel):
    email: str


class CreateOfferRequest(BaseModel):
    ticket_id: Optional[str] = None
    school_name: str
    contact_email: str
    amount: int
    duration_months: int = 12
    package_type: str = "monthly"   # "monthly" | "annual"
    max_slots: Optional[int] = None
    max_monthly_docs_member: Optional[int] = None
    max_monthly_docs_owner: Optional[int] = None
    max_annual_docs_owner: Optional[int] = None
    expires_in_days: int = 30


class UpdateTicketRequest(BaseModel):
    status: Optional[str] = None   # open | in_progress | closed
    admin_note: Optional[str] = None


# ── Public: contact form ──────────────────────────────────────────────────────

@router.post("/contact")
def submit_contact(
    req: ContactRequest,
    db: Session = Depends(get_db),
):
    ticket = EnterpriseTicket(
        name=req.name.strip(),
        email=req.email.strip().lower(),
        school_name=req.school_name.strip(),
        phone=req.phone,
        message=req.message,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    send_enterprise_ticket_to_admin(
        name=req.name,
        email=req.email,
        school=req.school_name,
        phone=req.phone or "",
        message=req.message or "",
        ticket_id=str(ticket.id),
    )

    return {"ok": True, "ticket_id": str(ticket.id)}


# ── Public: offer page ────────────────────────────────────────────────────────

@router.get("/offer/{token}")
def get_offer(token: str, db: Session = Depends(get_db)):
    offer = db.query(EnterpriseOffer).filter(EnterpriseOffer.token == token).first()
    if not offer:
        raise HTTPException(404, "Không tìm thấy form thanh toán")
    if offer.status == "expired":
        raise HTTPException(410, "Form thanh toán đã hết hạn")
    if offer.expires_at and offer.expires_at < datetime.now():
        offer.status = "expired"
        db.commit()
        raise HTTPException(410, "Form thanh toán đã hết hạn")
    return _offer_out(offer)


@router.post("/offer/{token}/claim")
def claim_offer(
    token: str,
    req: ClaimOfferRequest,
    db: Session = Depends(get_db),
):
    """Người dùng nhập email → nhận QR thanh toán."""
    offer = db.query(EnterpriseOffer).filter(EnterpriseOffer.token == token).first()
    if not offer:
        raise HTTPException(404, "Không tìm thấy form thanh toán")
    if offer.status not in ("draft", "active"):
        raise HTTPException(400, f"Form đã ở trạng thái '{offer.status}'")
    if offer.expires_at and offer.expires_at < datetime.now():
        offer.status = "expired"
        db.commit()
        raise HTTPException(410, "Form thanh toán đã hết hạn")

    email = req.email.strip().lower()
    offer.activated_email = email
    offer.status = "active"

    user = db.query(User).filter(User.email == email).first()
    if user:
        offer.activated_user_id = user.id
    db.commit()

    from app.core.config import settings

    def _vietqr(amount: int, ref_code: str) -> str:
        name = settings.BANK_ACCOUNT_NAME.replace(" ", "%20")
        return (
            f"https://img.vietqr.io/image/{settings.BANK_CODE}-{settings.BANK_ACCOUNT_NO}"
            f"-compact2.png?amount={amount}&addInfo={ref_code}&accountName={name}"
        )

    return {
        "ref_code": offer.ref_code,
        "amount": offer.amount,
        "school_name": offer.school_name,
        "duration_months": offer.duration_months,
        "package_type": offer.package_type,
        "bank_code": settings.BANK_CODE,
        "bank_account_no": settings.BANK_ACCOUNT_NO,
        "bank_account_name": settings.BANK_ACCOUNT_NAME,
        "qr_url": _vietqr(offer.amount, offer.ref_code),
        "expires_at": offer.expires_at.isoformat() if offer.expires_at else None,
    }


@router.get("/offer/{token}/status")
def poll_offer_status(token: str, db: Session = Depends(get_db)):
    """Frontend polls this to detect activation."""
    offer = db.query(EnterpriseOffer).filter(EnterpriseOffer.token == token).first()
    if not offer:
        raise HTTPException(404, "Không tìm thấy form")
    return {"status": offer.status, "activated_email": offer.activated_email}


# ── Admin: tickets ────────────────────────────────────────────────────────────

@router.get("/admin/tickets")
def admin_list_tickets(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    q = db.query(EnterpriseTicket)
    if status:
        q = q.filter(EnterpriseTicket.status == status)
    tickets = q.order_by(EnterpriseTicket.created_at.desc()).all()
    return [_ticket_out(t) for t in tickets]


@router.patch("/admin/tickets/{ticket_id}")
def admin_update_ticket(
    ticket_id: str,
    req: UpdateTicketRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    ticket = db.query(EnterpriseTicket).filter(EnterpriseTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Không tìm thấy ticket")
    if req.status is not None:
        ticket.status = req.status
    if req.admin_note is not None:
        ticket.admin_note = req.admin_note
    db.commit()
    return _ticket_out(ticket)


# ── Admin: offers ─────────────────────────────────────────────────────────────

@router.get("/admin/offers")
def admin_list_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    offers = db.query(EnterpriseOffer).order_by(EnterpriseOffer.created_at.desc()).all()
    return [_offer_out(o) for o in offers]


@router.post("/admin/offers")
def admin_create_offer(
    req: CreateOfferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")

    # Auto-fill owner limits based on package type
    owner_monthly = req.max_monthly_docs_owner
    owner_annual = req.max_annual_docs_owner
    if req.package_type == "annual":
        if owner_annual is None:
            owner_annual = DEFAULT_OWNER_ANNUAL
    else:
        if owner_monthly is None:
            owner_monthly = DEFAULT_OWNER_MONTHLY

    token = _gen_token()
    while db.query(EnterpriseOffer).filter(EnterpriseOffer.token == token).first():
        token = _gen_token()

    ref_code = _gen_ref_code(db)
    expires_at = datetime.now() + timedelta(days=req.expires_in_days)

    offer = EnterpriseOffer(
        ticket_id=req.ticket_id,
        token=token,
        school_name=req.school_name.strip(),
        contact_email=req.contact_email.strip().lower(),
        amount=req.amount,
        duration_months=req.duration_months,
        package_type=req.package_type,
        max_slots=req.max_slots,
        max_monthly_docs_member=req.max_monthly_docs_member,
        max_monthly_docs_owner=owner_monthly,
        max_annual_docs_owner=owner_annual,
        ref_code=ref_code,
        expires_at=expires_at,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)

    # Send email to customer with the offer URL
    from app.core.config import settings
    frontend_origin = settings.FRONTEND_URL.rstrip("/")
    offer_url = f"{frontend_origin}/enterprise/offer/{token}"
    send_offer_to_customer(
        to_email=req.contact_email,
        school_name=req.school_name,
        offer_url=offer_url,
        amount=req.amount,
        duration_months=req.duration_months,
    )

    return {**_offer_out(offer), "offer_url": offer_url}


@router.post("/admin/offers/{offer_id}/confirm")
def admin_confirm_offer(
    offer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin manual confirmation if webhook missed."""
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    offer = db.query(EnterpriseOffer).filter(EnterpriseOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(404, "Không tìm thấy offer")
    if offer.status == "paid":
        raise HTTPException(400, "Offer đã được kích hoạt rồi")
    _activate_enterprise_offer(offer, db)
    return {"ok": True, "message": f"Đã kích hoạt Enterprise cho {offer.activated_email or offer.contact_email}"}


def _activate_enterprise_offer(offer: EnterpriseOffer, db: Session):
    """Create org + upgrade user plan. Called by webhook or manual confirm."""
    email = offer.activated_email or offer.contact_email
    user = db.query(User).filter(User.email == email).first()

    expires_at = _add_months(datetime.now(), offer.duration_months)

    if user:
        user.plan = "enterprise"
        user.plan_expires_at = expires_at

        # Create org if doesn't exist
        existing_org = db.query(Organization).filter(Organization.owner_id == user.id).first()
        if not existing_org:
            org = Organization(
                owner_id=user.id,
                name=offer.school_name,
                max_slots=offer.max_slots,
                max_monthly_docs=offer.max_monthly_docs_member,
                max_monthly_docs_owner=offer.max_monthly_docs_owner,
                max_annual_docs_owner=offer.max_annual_docs_owner,
                package_type=offer.package_type,
            )
            db.add(org)
        else:
            existing_org.max_slots = offer.max_slots
            existing_org.max_monthly_docs = offer.max_monthly_docs_member
            existing_org.max_monthly_docs_owner = offer.max_monthly_docs_owner
            existing_org.max_annual_docs_owner = offer.max_annual_docs_owner
            existing_org.package_type = offer.package_type

    offer.status = "paid"
    offer.completed_at = datetime.now()
    if user:
        offer.activated_user_id = user.id
    db.commit()
    print(f"[ENTERPRISE] ✓ Activated {email} → enterprise (offer {offer.ref_code})")
