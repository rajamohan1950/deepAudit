"""ZIP upload audit endpoint — audit code without a Git hosting provider."""

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import generate_api_key, hash_api_key
from app.models.audit import Audit, AuditPhase
from app.models.tenant import Tenant
from app.workers.audit_worker import enqueue_audit_job

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


class UploadAuditResponse(BaseModel):
    audit_id: str
    api_key: str | None = Field(None, description="API key (only returned on first call for this email)")
    dashboard_url: str


@router.post(
    "",
    response_model=UploadAuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a ZIP archive for audit",
)
async def upload_audit(
    file: UploadFile = File(..., description="ZIP archive of the codebase (max 100 MB)"),
    email: str = Form(..., description="Contact email"),
    company: str = Form(default="", description="Company name (optional)"),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ("application/zip", "application/x-zip-compressed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are accepted.",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )

    extract_dir = Path(tempfile.mkdtemp(
        prefix="deepaudit-upload-",
        dir=settings.repo_storage_path,
    ))
    try:
        tmp_zip = extract_dir / "upload.zip"
        tmp_zip.write_bytes(contents)

        if not zipfile.is_zipfile(tmp_zip):
            shutil.rmtree(extract_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid ZIP archive.",
            )

        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(extract_dir / "src")

        tmp_zip.unlink()
    except zipfile.BadZipFile:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted ZIP archive.",
        )

    raw_key = None
    result = await db.execute(select(Tenant).where(Tenant.email == email))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raw_key = generate_api_key()
        tenant = Tenant(
            name=company or email.split("@")[0],
            email=email,
            api_key_hash=hash_api_key(raw_key),
        )
        db.add(tenant)
        await db.flush()
        await db.refresh(tenant)

    source_config = {
        "type": "upload",
        "local_path": str(extract_dir / "src"),
        "original_filename": file.filename,
        "access_token": None,
        "paths_include": [],
        "paths_exclude": [
            "vendor/", "node_modules/", ".git/",
            "__pycache__/", "dist/", "build/",
        ],
    }
    system_context = {
        "tech_stack": ["Auto-detected"],
        "architecture": "Auto-detected from uploaded archive",
        "description": f"Upload audit of {file.filename}",
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

    await db.commit()
    await db.refresh(audit)
    await enqueue_audit_job(str(audit.id))

    aid = str(audit.id)
    return UploadAuditResponse(
        audit_id=aid,
        api_key=raw_key,
        dashboard_url=f"/api/v1/audits/{aid}",
    )
