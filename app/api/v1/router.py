from fastapi import APIRouter

from app.api.v1 import audits, contact, health, quick_audit, reports, signals, tenants, webhooks

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(
    signals.router, prefix="/audits/{audit_id}/signals", tags=["signals"]
)
api_router.include_router(
    reports.router, prefix="/audits/{audit_id}/reports", tags=["reports"]
)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(quick_audit.router, prefix="/quick-audit", tags=["quick-audit"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
