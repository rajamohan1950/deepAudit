"""Multi-repository audit for PE due diligence — audit multiple repos in one engagement."""

import hashlib
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import generate_api_key, hash_api_key
from app.models.audit import Audit, AuditPhase
from app.models.signal import Signal
from app.models.tenant import Tenant
from app.workers.audit_worker import enqueue_audit_job

logger = logging.getLogger(__name__)
router = APIRouter()

GITHUB_URL_RE = re.compile(r"^https?://github\.com/[\w.\-]+/[\w.\-]+/?$")

PHASE_MAP = {
    1: list(range(1, 6)),
    2: list(range(6, 9)),
    3: list(range(9, 13)),
    4: list(range(13, 16)),
    5: list(range(16, 19)),
    6: list(range(19, 23)),
    7: list(range(23, 25)),
    8: list(range(25, 29)),
    9: list(range(29, 35)),
    10: list(range(35, 41)),
}


class RepoEntry(BaseModel):
    github_url: str = Field(..., description="GitHub repository URL")
    branch: str | None = Field(None, description="Branch to audit (default: repo default)")


class MultiAuditRequest(BaseModel):
    repos: list[RepoEntry] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of repositories to audit (1-20)",
    )
    email: str = Field(..., description="Contact email for the engagement")
    company: str | None = Field(None, description="Company or fund name")
    access_token: str | None = Field(None, description="GitHub PAT for private repos")


class AuditEntry(BaseModel):
    audit_id: str
    repo_url: str
    branch: str | None
    status: str
    poll_url: str
    dashboard_url: str


class MultiAuditResponse(BaseModel):
    tenant_id: str
    api_key: str | None = Field(None, description="API key (only returned when a new tenant is created)")
    total_repos: int
    audits: list[AuditEntry]
    portfolio_url: str


class PortfolioAuditSummary(BaseModel):
    audit_id: str
    repo_url: str
    status: str
    current_phase: int
    total_signals: int
    severity_breakdown: dict[str, int]
    total_cost_usd: float
    created_at: str


class PortfolioResponse(BaseModel):
    tenant_id: str
    company: str | None
    total_audits: int
    audits: list[PortfolioAuditSummary]
    combined_stats: dict


@router.post(
    "",
    response_model=MultiAuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Audit multiple repos in one PE due-diligence engagement",
)
async def create_multi_audit(
    body: MultiAuditRequest,
    db: AsyncSession = Depends(get_db),
):
    for entry in body.repos:
        url = entry.github_url.rstrip("/")
        if not GITHUB_URL_RE.match(url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid GitHub URL: {entry.github_url}. Expected https://github.com/owner/repo",
            )

    raw_key = None

    result = await db.execute(select(Tenant).where(Tenant.email == body.email))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raw_key = generate_api_key()
        tenant = Tenant(
            name=body.company or body.email.split("@")[0],
            email=body.email,
            api_key_hash=hash_api_key(raw_key),
        )
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)

    audit_entries: list[AuditEntry] = []

    for entry in body.repos:
        url = entry.github_url.rstrip("/")

        source_config = {
            "type": "github",
            "repo_url": url,
            "branch": entry.branch,
            "access_token": body.access_token,
            "paths_include": [],
            "paths_exclude": [
                "vendor/", "node_modules/", ".git/",
                "__pycache__/", "dist/", "build/",
            ],
        }
        system_context = {
            "tech_stack": ["Auto-detected"],
            "architecture": "Auto-detected from repository",
            "description": f"Multi-repo PE audit of {url}",
            "engagement_type": "multi_repo",
            "company": body.company,
        }
        audit_config = {
            "categories": "all",
            "max_signals_per_category": 20,
            "llm_provider": None,
            "llm_model": None,
            "severity_filter": None,
        }

        audit = Audit(
            tenant_id=tenant.id,
            source_config=source_config,
            system_context=system_context,
            audit_config=audit_config,
            status="pending",
        )
        db.add(audit)
        await db.flush()

        for phase_num in range(1, 11):
            phase = AuditPhase(
                audit_id=audit.id,
                phase_number=phase_num,
                status="pending",
                categories_included=PHASE_MAP[phase_num],
            )
            db.add(phase)

        await db.commit()
        await db.refresh(audit)
        await enqueue_audit_job(str(audit.id))

        aid = str(audit.id)
        audit_entries.append(AuditEntry(
            audit_id=aid,
            repo_url=url,
            branch=entry.branch,
            status="pending",
            poll_url=f"/api/v1/audits/{aid}",
            dashboard_url=f"/api/v1/audits/{aid}/progress",
        ))

    return MultiAuditResponse(
        tenant_id=str(tenant.id),
        api_key=raw_key,
        total_repos=len(audit_entries),
        audits=audit_entries,
        portfolio_url="/api/v1/multi-audit/portfolio",
    )


@router.get(
    "/portfolio",
    response_model=PortfolioResponse,
    summary="Get portfolio view of all audits for a tenant",
)
async def get_portfolio(
    key: str = Query(..., description="API key for authentication"),
    db: AsyncSession = Depends(get_db),
):
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
        )

    key_hash = hashlib.sha256(key.encode()).hexdigest()
    result = await db.execute(
        select(Tenant).where(Tenant.api_key_hash == key_hash, Tenant.is_active.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    audits_result = await db.execute(
        select(Audit)
        .where(Audit.tenant_id == tenant.id)
        .order_by(Audit.created_at.desc())
    )
    audits = list(audits_result.scalars().all())

    if not audits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audits found for this tenant.",
        )

    combined_signals = 0
    combined_cost = 0.0
    combined_severity: dict[str, int] = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    statuses: dict[str, int] = {}
    audit_summaries: list[PortfolioAuditSummary] = []

    for audit in audits:
        sig_counts = await db.execute(
            select(Signal.severity, func.count())
            .where(Signal.audit_id == audit.id)
            .group_by(Signal.severity)
        )
        sev_breakdown: dict[str, int] = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for severity, count in sig_counts:
            sev_breakdown[severity] = count
            combined_severity[severity] = combined_severity.get(severity, 0) + count

        repo_url = (audit.source_config or {}).get("repo_url", "unknown")
        combined_signals += audit.total_signals
        combined_cost += audit.total_cost_usd or 0.0
        statuses[audit.status] = statuses.get(audit.status, 0) + 1

        audit_summaries.append(PortfolioAuditSummary(
            audit_id=str(audit.id),
            repo_url=repo_url,
            status=audit.status,
            current_phase=audit.current_phase,
            total_signals=audit.total_signals,
            severity_breakdown=sev_breakdown,
            total_cost_usd=audit.total_cost_usd or 0.0,
            created_at=audit.created_at.isoformat() if audit.created_at else "",
        ))

    company = None
    if audits:
        company = (audits[0].system_context or {}).get("company")

    return PortfolioResponse(
        tenant_id=str(tenant.id),
        company=company,
        total_audits=len(audits),
        audits=audit_summaries,
        combined_stats={
            "total_signals": combined_signals,
            "total_cost_usd": round(combined_cost, 2),
            "severity_breakdown": combined_severity,
            "status_breakdown": statuses,
            "audits_completed": statuses.get("completed", 0),
            "audits_in_progress": statuses.get("running", 0) + statuses.get("pending", 0),
        },
    )
