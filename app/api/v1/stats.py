"""Live usage stats — tracks active users via Redis with heartbeat TTL."""

import time
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

_active_sessions: dict[str, float] = {}
SESSION_TTL = 90  # seconds — heartbeat every 30s, expire after 90s


@router.post("/heartbeat")
async def heartbeat(session_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    _active_sessions[session_id] = time.time()
    return {"ok": True}


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    now = time.time()
    active = {k: v for k, v in _active_sessions.items() if now - v < SESSION_TTL}
    _active_sessions.clear()
    _active_sessions.update(active)

    total_audits = 0
    total_signals = 0
    try:
        r1 = await db.execute(text("SELECT count(*) FROM audits"))
        total_audits = r1.scalar() or 0
        r2 = await db.execute(text("SELECT count(*) FROM signals"))
        total_signals = r2.scalar() or 0
    except Exception:
        pass

    return {
        "active_users": len(active),
        "total_audits": total_audits,
        "total_signals": total_signals,
    }
