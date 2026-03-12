import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.tenant_context import get_current_tenant
from app.models.audit import Audit, AuditPhase
from app.models.tenant import Tenant
from app.schemas.audit import (
    AuditCreate,
    AuditListResponse,
    AuditProgress,
    AuditResponse,
)
from app.workers.audit_worker import enqueue_audit_job

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=AuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_audit(
    body: AuditCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    if body.source.type in ("github", "gitlab", "bitbucket") and not body.source.repo_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"repo_url is required for source type '{body.source.type}'",
        )

    audit = Audit(
        tenant_id=tenant.id,
        source_config=body.source.model_dump(),
        system_context=body.system_context.model_dump(),
        audit_config=body.config.model_dump(),
        status="pending",
    )
    db.add(audit)
    await db.flush()

    for phase_num in range(1, 11):
        phase = AuditPhase(
            audit_id=audit.id,
            phase_number=phase_num,
            status="pending",
            categories_included=_phase_categories(phase_num),
        )
        db.add(phase)

    await db.commit()
    await db.refresh(audit)

    await enqueue_audit_job(str(audit.id))
    logger.info(f"Audit {audit.id} created and enqueued for tenant {tenant.id}")

    return AuditResponse.model_validate(audit)


@router.get("", response_model=AuditListResponse)
async def list_audits(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
):
    query = select(Audit).where(Audit.tenant_id == tenant.id)
    if status_filter:
        query = query.where(Audit.status == status_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Audit.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    audits = result.scalars().all()

    return AuditListResponse(
        audits=[AuditResponse.model_validate(a) for a in audits],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    audit = await _get_tenant_audit(db, audit_id, tenant.id)
    return AuditResponse.model_validate(audit)


@router.get("/{audit_id}/progress", response_model=AuditProgress)
async def get_audit_progress(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    audit = await _get_tenant_audit(db, audit_id, tenant.id)
    from app.schemas.audit import AuditPhaseResponse

    return AuditProgress(
        audit_id=audit.id,
        status=audit.status,
        current_phase=audit.current_phase,
        signals_so_far=audit.total_signals,
        phases=[AuditPhaseResponse.model_validate(p) for p in audit.phases],
    )


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    audit = await _get_tenant_audit(db, audit_id, tenant.id)
    if audit.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a running audit. Cancel it first.",
        )
    await db.delete(audit)


async def _get_tenant_audit(
    db: AsyncSession, audit_id: uuid.UUID, tenant_id: uuid.UUID
) -> Audit:
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.tenant_id == tenant_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found.",
        )
    return audit


def _phase_categories(phase: int) -> list[int]:
    mapping = {
        1: list(range(1, 6)),      # Cat 1-5: Security
        2: list(range(6, 9)),      # Cat 6-8: Memory, CPU, Network
        3: list(range(9, 13)),     # Cat 9-12: DB, Cache, OS, Shutdown
        4: list(range(13, 16)),    # Cat 13-15: SPOF, Fault Tolerance, Concurrency
        5: list(range(16, 19)),    # Cat 16-18: Data Integrity, Distributed, Queues
        6: list(range(19, 23)),    # Cat 19-22: Infra, Capacity, Deploy, Supply Chain
        7: list(range(23, 25)),    # Cat 23-24: AI/ML
        8: list(range(25, 29)),    # Cat 25-28: Observability
        9: list(range(29, 35)),    # Cat 29-34: Quality, Code, API, UX, Cost, Tenancy
        10: list(range(35, 41)),   # Cat 35-40: Compliance, DR, i18n, State, Compat, Org
    }
    return mapping.get(phase, [])
