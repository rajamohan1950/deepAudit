"""World's simplest audit API -- just send a GitHub URL."""

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
from app.schemas.audit import AuditResponse
from app.workers.audit_worker import enqueue_audit_job

logger = logging.getLogger(__name__)
router = APIRouter()

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/[\w.\-]+/[\w.\-]+/?$"
)


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
    api_key: str | None = Field(None, description="API key for subsequent requests (only on first call)")


@router.post(
    "",
    response_model=QuickAuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="One-click audit — just paste a GitHub URL",
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
    raw_key = None

    result = await db.execute(select(Tenant).where(Tenant.email == email))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raw_key = generate_api_key()
        tenant = Tenant(
            name=email.split("@")[0],
            email=email,
            api_key_hash=hash_api_key(raw_key),
        )
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)

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
        "description": f"Quick audit of {url}",
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

    phase_map = {
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
    for phase_num in range(1, 11):
        phase = AuditPhase(
            audit_id=audit.id,
            phase_number=phase_num,
            status="pending",
            categories_included=phase_map[phase_num],
        )
        db.add(phase)

    await db.flush()
    await db.refresh(audit)
    await enqueue_audit_job(str(audit.id))

    aid = str(audit.id)
    return QuickAuditResponse(
        audit_id=aid,
        status="pending",
        message="Audit queued! Your repository is being cloned and analyzed across 40 categories.",
        poll_url=f"/api/v1/audits/{aid}",
        progress_url=f"/api/v1/audits/{aid}/progress",
        signals_url=f"/api/v1/audits/{aid}/signals",
        reports_url=f"/api/v1/audits/{aid}/reports",
        api_key=raw_key,
    )
