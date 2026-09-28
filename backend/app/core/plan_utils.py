from datetime import date
from sqlalchemy.orm import Session

PLAN_LIMITS = {
    "free": {
        "label": "Free",
        "max_docs": None,
        "max_monthly_docs": 3,       # 3 tài liệu/tháng
        "max_monthly_chat": 600,     # 600 câu/tháng
        "max_daily_chat": None,
        "price_vnd": 0,
        "features": [
            "3 tài liệu / tháng",
            "600 câu hỏi / tháng",
            "Tóm tắt & hỏi đáp AI",
            "Dịch tài liệu cơ bản",
        ],
    },
    "pro": {
        "label": "Pro",
        "max_docs": None,
        "max_monthly_docs": 20,      # 20 tài liệu/tháng
        "max_monthly_chat": 1000,
        "max_daily_chat": None,
        "price_vnd": 149000,
        "features": [
            "20 tài liệu / tháng",
            "1.000 câu hỏi / tháng",
            "Memory Chat dài hạn",
            "Dịch & giải thích thuật ngữ",
            "Chế độ học (Learning Mode)",
            "Phân loại tài liệu thông minh",
        ],
    },
    "researcher": {
        "label": "Researcher",
        "max_docs": None,
        "max_monthly_docs": 80,      # 80 tài liệu/tháng
        "max_monthly_chat": 5000,
        "max_daily_chat": None,
        "price_vnd": 499000,
        "features": [
            "80 tài liệu / tháng",
            "5.000 câu hỏi / tháng",
            "Literature Review AI",
            "So sánh & phân tích tài liệu",
            "Trending Topics & Timeline",
            "Tạo slide thuyết trình AI",
        ],
    },
    "enterprise": {
        "label": "Enterprise",
        "max_docs": None,
        "max_monthly_docs": None,    # tuỳ chỉnh theo tổ chức
        "max_monthly_chat": None,
        "max_daily_chat": None,
        "price_vnd": 3000000,        # từ 3.000.000đ/tháng
        "features": [
            "Tài liệu không giới hạn (fair use)",
            "Câu hỏi không giới hạn",
            "Team workspace & quản lý thành viên",
            "Dashboard quản lý tổ chức",
            "Bảo mật cao cấp & API riêng",
            "Hỗ trợ 24/7",
        ],
    },
}


def get_limits(user) -> dict:
    """Return plan limits for a user (or guest)."""
    if user is None:
        return PLAN_LIMITS["free"]
    if user.role == "admin":
        return PLAN_LIMITS["enterprise"]
    plan = getattr(user, "plan", None) or "free"
    if user.role == "researcher" and plan == "free":
        plan = "researcher"
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def count_user_docs(user_id, db: Session) -> int:
    from app.models.document import Document
    return db.query(Document).filter(Document.user_id == user_id).count()


def count_monthly_docs(user_id, db: Session) -> int:
    from sqlalchemy import text
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM documents
            WHERE user_id = :uid
              AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
        """),
        {"uid": str(user_id)},
    ).scalar()
    return int(result or 0)


def count_annual_docs(user_id, db: Session) -> int:
    from sqlalchemy import text
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM documents
            WHERE user_id = :uid
              AND DATE_TRUNC('year', created_at) = DATE_TRUNC('year', CURRENT_DATE)
        """),
        {"uid": str(user_id)},
    ).scalar()
    return int(result or 0)


def count_today_chats(user_id, db: Session) -> int:
    from sqlalchemy import text
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM chat_history
            WHERE user_id = :uid
              AND DATE(created_at) = :today
        """),
        {"uid": str(user_id), "today": date.today()},
    ).scalar()
    return int(result or 0)
