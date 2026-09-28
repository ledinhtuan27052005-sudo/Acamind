import calendar
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.postgres import get_db
from app.models.document import OrgInviteCode, OrgMember, Organization, User

router = APIRouter()

DURATION_LABELS = {1: "1 tháng", 3: "3 tháng", 12: "1 năm", 48: "4 năm"}
VALID_DURATIONS = (1, 3, 12, 48)


def _add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _gen_code(db: Session) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "ORG" + "".join(random.choices(chars, k=8))
        if not db.query(OrgInviteCode).filter(OrgInviteCode.code == code).first():
            return code


def _org_out(org: Organization, db: Session) -> dict:
    active = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.status == "active"
    ).count()
    return {
        "id": str(org.id),
        "name": org.name,
        "max_slots": org.max_slots,
        "max_monthly_docs": org.max_monthly_docs,
        "member_count": active,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


def _invite_out(c: OrgInviteCode) -> dict:
    return {
        "id": str(c.id),
        "code": c.code,
        "duration_months": c.duration_months,
        "duration_label": DURATION_LABELS.get(c.duration_months, f"{c.duration_months} tháng"),
        "max_uses": c.max_uses,
        "used_count": c.used_count,
        "valid_until": c.valid_until.isoformat() if c.valid_until else None,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateOrgRequest(BaseModel):
    name: str
    max_slots: Optional[int] = None

class UpdateOrgRequest(BaseModel):
    name: Optional[str] = None
    max_slots: Optional[int] = None
    max_monthly_docs: Optional[int] = None  # None = xóa giới hạn

class CreateInviteRequest(BaseModel):
    duration_months: int
    max_uses: Optional[int] = None
    valid_days: Optional[int] = None

class JoinRequest(BaseModel):
    code: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/create")
def create_org(
    req: CreateOrgRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.plan != "enterprise":
        raise HTTPException(403, "Chỉ tài khoản Enterprise mới có thể tạo tổ chức")
    if db.query(Organization).filter(Organization.owner_id == current_user.id).first():
        raise HTTPException(400, "Bạn đã có tổ chức rồi")
    org = Organization(owner_id=current_user.id, name=req.name.strip(), max_slots=req.max_slots)
    db.add(org)
    db.commit()
    db.refresh(org)
    return _org_out(org, db)


@router.get("/me")
def get_my_org(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if org:
        return {"role": "owner", **_org_out(org, db)}
    member = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == current_user.id)
        .order_by(OrgMember.joined_at.desc())
        .first()
    )
    if member:
        o = db.query(Organization).filter(Organization.id == member.org_id).first()
        return {
            "role": "member",
            "org_id": str(member.org_id),
            "org_name": o.name if o else "Unknown",
            "expires_at": member.expires_at.isoformat(),
            "duration_label": DURATION_LABELS.get(member.duration_months, f"{member.duration_months} tháng"),
            "status": member.status,
        }
    return {"role": None}


@router.patch("/settings")
def update_org_settings(
    req: UpdateOrgRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enterprise owner cập nhật cài đặt tổ chức (tên, slots, giới hạn tài liệu/tháng)."""
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(403, "Bạn chưa có tổ chức")
    if req.name is not None:
        org.name = req.name.strip()
    if req.max_slots is not None:
        org.max_slots = req.max_slots if req.max_slots > 0 else None
    if req.max_monthly_docs is not None:
        org.max_monthly_docs = req.max_monthly_docs if req.max_monthly_docs > 0 else None
    else:
        # explicit None in body means remove limit
        if "max_monthly_docs" in req.model_fields_set:
            org.max_monthly_docs = None
    db.commit()
    return _org_out(org, db)


@router.post("/invite-codes")
def create_invite(
    req: CreateInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(403, "Bạn chưa có tổ chức")
    if req.duration_months not in VALID_DURATIONS:
        raise HTTPException(400, f"Thời hạn không hợp lệ. Chọn: {list(VALID_DURATIONS)}")
    valid_until = datetime.now() + timedelta(days=req.valid_days) if req.valid_days else None
    invite = OrgInviteCode(
        org_id=org.id,
        code=_gen_code(db),
        duration_months=req.duration_months,
        max_uses=req.max_uses,
        valid_until=valid_until,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _invite_out(invite)


@router.get("/invite-codes")
def list_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(403, "Bạn chưa có tổ chức")
    codes = (
        db.query(OrgInviteCode)
        .filter(OrgInviteCode.org_id == org.id)
        .order_by(OrgInviteCode.created_at.desc())
        .all()
    )
    return [_invite_out(c) for c in codes]


@router.delete("/invite-codes/{code}")
def deactivate_invite(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(403, "Bạn chưa có tổ chức")
    invite = db.query(OrgInviteCode).filter(
        OrgInviteCode.code == code, OrgInviteCode.org_id == org.id
    ).first()
    if not invite:
        raise HTTPException(404, "Không tìm thấy mã")
    invite.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/join")
def join_org(
    req: JoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(OrgMember).filter(
        OrgMember.user_id == current_user.id, OrgMember.status == "active"
    ).first()
    if existing:
        raise HTTPException(400, "Bạn đã là thành viên của một tổ chức rồi")

    invite = db.query(OrgInviteCode).filter(
        OrgInviteCode.code == req.code.upper().strip()
    ).first()
    if not invite or not invite.is_active:
        raise HTTPException(404, "Mã mời không hợp lệ hoặc đã bị hủy")
    if invite.valid_until and invite.valid_until < datetime.now():
        raise HTTPException(400, "Mã mời đã hết hạn")
    if invite.max_uses and invite.used_count >= invite.max_uses:
        raise HTTPException(400, "Mã mời đã đạt giới hạn sử dụng")

    org = db.query(Organization).filter(Organization.id == invite.org_id).first()
    if org.max_slots:
        count = db.query(OrgMember).filter(
            OrgMember.org_id == org.id, OrgMember.status == "active"
        ).count()
        if count >= org.max_slots:
            raise HTTPException(400, "Tổ chức đã đầy slot")

    expires_at = _add_months(datetime.now(), invite.duration_months)

    member = OrgMember(
        org_id=org.id,
        user_id=current_user.id,
        invite_code_id=invite.id,
        duration_months=invite.duration_months,
        expires_at=expires_at,
    )
    db.add(member)

    current_user.plan = "enterprise"
    current_user.plan_expires_at = expires_at
    invite.used_count += 1
    db.commit()

    return {
        "message": f"Đã tham gia tổ chức {org.name}",
        "org_name": org.name,
        "expires_at": expires_at.isoformat(),
        "duration_label": DURATION_LABELS.get(invite.duration_months, f"{invite.duration_months} tháng"),
    }


@router.get("/members")
def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(403, "Bạn chưa có tổ chức")
    members = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org.id)
        .order_by(OrgMember.joined_at.desc())
        .all()
    )
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        result.append({
            "id": str(m.id),
            "user_id": str(m.user_id),
            "user_email": u.email if u else "Unknown",
            "user_name": u.full_name if u else None,
            "duration_label": DURATION_LABELS.get(m.duration_months, f"{m.duration_months} tháng"),
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            "expires_at": m.expires_at.isoformat(),
            "status": m.status,
        })
    return result


@router.delete("/members/{user_id}")
def kick_member(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    if not org:
        raise HTTPException(403, "Bạn chưa có tổ chức")
    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(404, "Không tìm thấy thành viên")
    member.status = "revoked"
    db.commit()
    return {"ok": True, "message": "Đã thu hồi. Thành viên giữ quyền đến hết hạn."}


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/list")
def admin_list_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    orgs = db.query(Organization).order_by(Organization.created_at.desc()).all()
    result = []
    for org in orgs:
        owner = db.query(User).filter(User.id == org.owner_id).first()
        result.append({
            **_org_out(org, db),
            "owner_email": owner.email if owner else "Unknown",
            "owner_name": owner.full_name if owner else None,
        })
    return result


@router.post("/admin/create")
def admin_create_org(
    req: CreateOrgRequest,
    owner_email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Chỉ admin")
    owner = db.query(User).filter(User.email == owner_email).first()
    if not owner:
        raise HTTPException(404, f"Không tìm thấy user {owner_email}")
    if db.query(Organization).filter(Organization.owner_id == owner.id).first():
        raise HTTPException(400, f"{owner_email} đã có tổ chức")
    owner.plan = "enterprise"
    org = Organization(owner_id=owner.id, name=req.name.strip(), max_slots=req.max_slots)
    db.add(org)
    db.commit()
    db.refresh(org)
    return _org_out(org, db)
