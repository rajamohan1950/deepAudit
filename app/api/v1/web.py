"""Web-facing API endpoints — accept api_key as query param for browser use."""

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_tenant_by_api_key
from app.models.audit import Audit
from app.models.signal import Signal
from app.models.report import Report
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)
router = APIRouter()


async def _resolve_tenant(db: AsyncSession, api_key: str) -> Tenant:
    tenant = await get_tenant_by_api_key(db, api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return tenant


async def _resolve_audit(db: AsyncSession, audit_id: uuid.UUID, tenant_id: uuid.UUID) -> Audit:
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.tenant_id == tenant_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@router.get("/audit/{audit_id}")
async def web_get_audit(
    audit_id: uuid.UUID,
    key: str = Query(..., description="API key"),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _resolve_tenant(db, key)
    audit = await _resolve_audit(db, audit_id, tenant.id)

    phases = []
    for p in sorted(audit.phases, key=lambda x: x.phase_number):
        phases.append({
            "phase_number": p.phase_number,
            "status": p.status,
            "categories": p.categories_included,
            "signals_found": p.signals_found,
            "started_at": p.started_at.isoformat() if p.started_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        })

    return {
        "id": str(audit.id),
        "status": audit.status,
        "current_phase": audit.current_phase,
        "total_signals": audit.total_signals,
        "total_cost_usd": audit.total_cost_usd,
        "error_message": audit.error_message,
        "source": audit.source_config,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "started_at": audit.started_at.isoformat() if audit.started_at else None,
        "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
        "phases": phases,
    }


@router.get("/audit/{audit_id}/signals")
async def web_get_signals(
    audit_id: uuid.UUID,
    key: str = Query(..., description="API key"),
    severity: str | None = Query(None),
    category_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _resolve_tenant(db, key)
    await _resolve_audit(db, audit_id, tenant.id)

    query = select(Signal).where(Signal.audit_id == audit_id)
    if severity:
        query = query.where(Signal.severity == severity)
    if category_id:
        query = query.where(Signal.category_id == category_id)

    query = query.order_by(Signal.sequence_number.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    signals = result.scalars().all()

    return {
        "signals": [
            {
                "id": str(s.id),
                "sequence_number": s.sequence_number,
                "category_id": s.category_id,
                "signal_text": s.signal_text,
                "severity": s.severity,
                "score": s.score,
                "evidence": s.evidence,
                "failure_scenario": s.failure_scenario,
                "remediation": s.remediation,
                "effort": s.effort,
            }
            for s in signals
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit/{audit_id}/reports")
async def web_get_reports(
    audit_id: uuid.UUID,
    key: str = Query(..., description="API key"),
    db: AsyncSession = Depends(get_db),
):
    tenant = await _resolve_tenant(db, key)
    await _resolve_audit(db, audit_id, tenant.id)

    result = await db.execute(
        select(Report).where(Report.audit_id == audit_id)
    )
    reports = result.scalars().all()

    return {
        "reports": [
            {
                "id": str(r.id),
                "report_type": r.report_type,
                "title": r.title,
                "content": r.content,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]
    }
