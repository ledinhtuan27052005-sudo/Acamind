"""One visibility rule for indexed documents across API endpoints."""

from fastapi import HTTPException
from sqlalchemy import or_, select

from app.models.document import Document, User


def _public_clause():
    return or_(
        Document.user_id.is_(None),
        Document.user_id.in_(select(User.id).where(User.role == "admin")),
    )


def visible_documents(query, user):
    """System and admin corpus documents are public; other uploads are private."""
    if user is not None and user.role == "admin":
        return query
    if user is None:
        return query.filter(_public_clause())
    return query.filter(or_(_public_clause(), Document.user_id == user.id))


def enforce_document_read(doc, user, db):
    if doc.user_id is None:
        return
    if user is not None and (user.role == "admin" or str(user.id) == str(doc.user_id)):
        return
    uploader_role = db.query(User.role).filter(User.id == doc.user_id).scalar()
    if uploader_role == "admin":
        return
    raise HTTPException(404, "Không tìm thấy tài liệu")


def readable_document_ids(db, user, requested_ids=None):
    """Validate explicit IDs or return the visible ready corpus for retrieval."""
    query = visible_documents(db.query(Document.id).filter(Document.status == "ready"), user)
    if requested_ids is not None:
        ids = list(dict.fromkeys(str(value) for value in requested_ids))
        found = {str(row[0]) for row in query.filter(Document.id.in_(ids)).all()}
        if len(found) != len(ids):
            raise HTTPException(404, "Không tìm thấy tài liệu hoặc bạn không có quyền truy cập")
        return ids
    return [str(row[0]) for row in query.all()]
