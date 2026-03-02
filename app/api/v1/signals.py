import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.tenant_context import get_current_tenant
from app.models.audit import Audit
from app.models.signal import Signal
from app.models.tenant import Tenant
from app.schemas.signal import SignalListResponse, SignalResponse, SignalSummary

router = APIRouter()

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@router.get("", response_model=SignalListResponse)
async def list_signals(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    severity: str | None = Query(None, description="Comma-separated: P0,P1"),
    category_ids: str | None = Query(None, description="Comma-separated: 1,2,3"),
    effort: str | None = Query(None, description="Comma-separated: S,M,L,XL"),
    min_score: float | None = Query(None, ge=0, le=10),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("sequence_number"),
    sort_order: str = Query("asc"),
):
    await _verify_audit_access(db, audit_id, tenant.id)

    query = select(Signal).where(Signal.audit_id == audit_id)

    if severity:
        sevs = [s.strip().upper() for s in severity.split(",")]
        query = query.where(Signal.severity.in_(sevs))
    if category_ids:
        cat_ids = [int(c.strip()) for c in category_ids.split(",")]
        query = query.where(Signal.category_id.in_(cat_ids))
    if effort:
        efforts = [e.strip().upper() for e in effort.split(",")]
        query = query.where(Signal.effort.in_(efforts))
    if min_score is not None:
        query = query.where(Signal.score >= min_score)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Signal.signal_text.ilike(pattern),
                Signal.evidence.ilike(pattern),
                Signal.remediation.ilike(pattern),
            )
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    sort_col = getattr(Signal, sort_by, Signal.sequence_number)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    signals = result.scalars().all()

    return SignalListResponse(
        signals=[_signal_to_response(s) for s in signals],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=SignalSummary)
async def signal_summary(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    await _verify_audit_access(db, audit_id, tenant.id)

    result = await db.execute(
        select(Signal).where(Signal.audit_id == audit_id)
    )
    signals = result.scalars().all()

    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_effort: dict[str, int] = {}
    by_phase: dict[str, int] = {}

    for s in signals:
        by_severity[s.severity] = by_severity.get(s.severity, 0) + 1
        cat_key = str(s.category_id)
        by_category[cat_key] = by_category.get(cat_key, 0) + 1
        by_effort[s.effort] = by_effort.get(s.effort, 0) + 1
        phase_key = str(s.phase_number)
        by_phase[phase_key] = by_phase.get(phase_key, 0) + 1

    p0 = by_severity.get("P0", 0)
    p1 = by_severity.get("P1", 0)
    p2 = by_severity.get("P2", 0)
    p3 = by_severity.get("P3", 0)
    valid = (30 <= p0 <= 50) and (100 <= p1 <= 150) and (250 <= p2 <= 300) and (150 <= p3 <= 200)

    return SignalSummary(
        total=len(signals),
        by_severity=by_severity,
        by_category=by_category,
        by_effort=by_effort,
        by_phase=by_phase,
        severity_distribution_valid=valid,
    )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    audit_id: uuid.UUID,
    signal_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    await _verify_audit_access(db, audit_id, tenant.id)

    result = await db.execute(
        select(Signal).where(Signal.id == signal_id, Signal.audit_id == audit_id)
    )
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found.")
    return _signal_to_response(signal)


def _signal_to_response(signal: Signal) -> SignalResponse:
    resp = SignalResponse.model_validate(signal)
    if signal.category:
        resp.category_name = signal.category.name
    return resp


async def _verify_audit_access(
    db: AsyncSession, audit_id: uuid.UUID, tenant_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(Audit.id).where(Audit.id == audit_id, Audit.tenant_id == tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")
