"""Quick scan API — fast, limited free assessment via GitHub URL."""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import generate_api_key, hash_api_key
from app.models.audit import Audit, AuditPhase
from app.models.tenant import Tenant
from app.workers.audit_worker import enqueue_audit_job

logger = logging.getLogger(__name__)

router = APIRouter()

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/[\w.\-]+/[\w.\-]+/?$"
)

MAX_LOC_QUICK = 25_000

QUICK_CATEGORIES = [1, 2, 3, 4, 13, 14, 29, 30, 35]

QUICK_PHASE_MAP = {
    1: [1, 2, 3, 4],
    2: [13, 14],
    3: [29, 30, 35],
}


class QuickAuditRequest(BaseModel):
    github_url: str = Field(
        ...,
        description="Public GitHub repository URL",
        examples=["https://github.com/tiangolo/fastapi"],
    )
    branch: str | None = Field(None, description="Branch to audit (default: repo default)")
    email: str | None = Field(None, description="Optional email to associate results with your account")


class QuickAuditResponse(BaseModel):
    audit_id: str
    status: str
    message: str
    poll_url: str
    progress_url: str
    signals_url: str
    reports_url: str
    api_key: str | None = Field(None, description="API key for subsequent requests")
    limits: dict = Field(default_factory=dict)


@router.post(
    "",
    response_model=QuickAuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Quick scan — paste a GitHub URL, get results in ~2 minutes",
)
async def quick_audit(
    body: QuickAuditRequest,
    db: AsyncSession = Depends(get_db),
):
    url = body.github_url.rstrip("/")
    if not GITHUB_URL_RE.match(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub URL. Expected format: https://github.com/owner/repo",
        )

    email = body.email or f"guest-{url.split('/')[-1]}@quickaudit.deepaudit.io"
    raw_key = generate_api_key()

    result = await db.execute(select(Tenant).where(Tenant.email == email))
    tenant = result.scalar_one_or_none()

    if not tenant:
        tenant = Tenant(
            name=email.split("@")[0],
            email=email,
            api_key_hash=hash_api_key(raw_key),
        )
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)
    else:
        tenant.api_key_hash = hash_api_key(raw_key)
        await db.flush()

    source_config = {
        "type": "github",
        "repo_url": url,
        "branch": body.branch,
        "access_token": None,
        "paths_include": [],
        "paths_exclude": ["vendor/", "node_modules/", ".git/", "__pycache__/", "dist/", "build/"],
    }
    system_context = {
        "tech_stack": ["Auto-detected"],
        "architecture": "Auto-detected from repository",
        "description": f"Quick scan of {url}",
    }
    audit_config = {
        "categories": QUICK_CATEGORIES,
        "max_signals_per_category": 10,
        "llm_provider": None,
        "llm_model": None,
        "severity_filter": None,
        "quick_mode": True,
        "quick_timeout_seconds": 120,
        "max_loc": MAX_LOC_QUICK,
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

    for phase_num, cat_ids in QUICK_PHASE_MAP.items():
        phase = AuditPhase(
            audit_id=audit.id,
            phase_number=phase_num,
            status="pending",
            categories_included=cat_ids,
        )
        db.add(phase)

    await db.flush()
    await db.refresh(audit)
    await enqueue_audit_job(str(audit.id))

    aid = str(audit.id)
    return QuickAuditResponse(
        audit_id=aid,
        status="pending",
        message="Quick scan queued! Instant static analysis + 9 key categories. Results in ~2 minutes.",
        poll_url=f"/api/v1/audits/{aid}",
        progress_url=f"/api/v1/audits/{aid}/progress",
        signals_url=f"/api/v1/audits/{aid}/signals",
        reports_url=f"/api/v1/audits/{aid}/reports",
        api_key=raw_key,
        limits={
            "max_loc": MAX_LOC_QUICK,
            "categories": len(QUICK_CATEGORIES),
            "timeout_seconds": 120,
        },
    )
