from fastapi import APIRouter
from app.api.v1 import document, chat, auth, admin, onboarding, profile, application, plan, payment, org, enterprise, notification, library

api_router = APIRouter()
api_router.include_router(document.router,     prefix="/document",    tags=["Documents"])
api_router.include_router(chat.router,         prefix="/chat",        tags=["Chat"])
api_router.include_router(auth.router,         prefix="/auth",        tags=["Authentication"])
api_router.include_router(admin.router,        prefix="/admin",       tags=["Admin"])
api_router.include_router(onboarding.router,   prefix="/onboarding",  tags=["Onboarding"])
api_router.include_router(profile.router,      prefix="/profile",     tags=["Profile"])
api_router.include_router(application.router,  prefix="/application", tags=["Application"])
api_router.include_router(plan.router,         prefix="/plan",        tags=["Plan"])
api_router.include_router(payment.router,      prefix="/payment",     tags=["Payment"])
api_router.include_router(org.router,          prefix="/org",         tags=["Organization"])
api_router.include_router(enterprise.router,   prefix="/enterprise",  tags=["Enterprise"])
api_router.include_router(notification.router, prefix="/notification", tags=["Notification"])
api_router.include_router(library.router,      prefix="/library",      tags=["Library"])

from app.api.v1 import features
api_router.include_router(features.router, prefix="/features", tags=["Features"])
from app.api.v1 import processing
api_router.include_router(processing.router, prefix="/document", tags=["Processing"])
