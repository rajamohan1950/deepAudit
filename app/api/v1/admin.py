"""Admin traction dashboard — contact submissions, tenants, audits."""

import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_admin(x_admin_secret: str | None = Header(None, alias="X-Admin-Secret")):
    if not settings.admin_secret:
        raise HTTPException(503, "Admin dashboard not configured")
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(403, "Invalid admin secret")


@router.get("/traction")
async def get_traction(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_admin),
):
    """Admin-only: tenants, audits, contact submissions."""
    from app.api.v1.contact import contact_submissions

    tenants_count = 0
    audits_count = 0
    signals_count = 0
    try:
        r1 = await db.execute(text("SELECT count(*) FROM tenants"))
        tenants_count = r1.scalar() or 0
        r2 = await db.execute(text("SELECT count(*) FROM audits"))
        audits_count = r2.scalar() or 0
        r3 = await db.execute(text("SELECT count(*) FROM signals"))
        signals_count = r3.scalar() or 0
    except Exception as e:
        logger.warning(f"Admin traction query failed: {e}")

    return {
        "tenants": tenants_count,
        "audits": audits_count,
        "signals": signals_count,
        "contact_submissions": len(contact_submissions),
        "contact_submissions_list": contact_submissions[-50:][::-1],
    }
