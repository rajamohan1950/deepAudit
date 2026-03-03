"""Private repository audit endpoint with secure code access."""

import logging
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
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


class PrivateAuditRequest(BaseModel):
    github_url: str = Field(
        ...,
        description="URL of the private GitHub repository",
        examples=["https://github.com/acme-corp/internal-api"],
    )
    access_token: str | None = Field(
        None,
        description="GitHub Personal Access Token or deploy key for repo access",
    )
    email: EmailStr = Field(..., description="Contact email")
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    nda_accepted: bool = Field(..., description="Must be True — confirms NDA acceptance")


class PrivateAuditResponse(BaseModel):
    audit_id: str
    api_key: str | None = Field(None, description="API key (only returned on first call for this email)")
    dashboard_url: str


async def _validate_github_access(repo_url: str, token: str) -> None:
    """Verify the token can reach the repo via the GitHub API."""
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.head(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )

    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token is invalid or expired.",
        )
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found — check the URL and token permissions.",
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API returned {resp.status_code} when validating access.",
        )


@router.post(
    "",
    response_model=PrivateAuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Audit a private repository (enterprise feature)",
)
async def private_audit(
    body: PrivateAuditRequest,
    db: AsyncSession = Depends(get_db),
):
    url = body.github_url.rstrip("/")
    if not GITHUB_URL_RE.match(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub URL. Expected format: https://github.com/owner/repo",
        )

    if not body.nda_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the NDA (nda_accepted=true) to audit a private repository.",
        )

    if body.access_token:
        await _validate_github_access(url, body.access_token)

    raw_key = None
    result = await db.execute(select(Tenant).where(Tenant.email == body.email))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raw_key = generate_api_key()
        tenant = Tenant(
            name=body.company,
            email=body.email,
            api_key_hash=hash_api_key(raw_key),
        )
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)

    source_config = {
        "type": "github",
        "repo_url": url,
        "branch": None,
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
        "description": f"Private audit of {url} for {body.company}",
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
        db.add(AuditPhase(
            audit_id=audit.id,
            phase_number=phase_num,
            status="pending",
            categories_included=phase_map[phase_num],
        ))

    await db.flush()
    await db.refresh(audit)
    await enqueue_audit_job(str(audit.id))

    aid = str(audit.id)
    return PrivateAuditResponse(
        audit_id=aid,
        api_key=raw_key,
        dashboard_url=f"/api/v1/audits/{aid}",
    )
