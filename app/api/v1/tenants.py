import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import generate_api_key, hash_api_key
from app.middleware.tenant_context import get_current_tenant
from app.models.audit import Audit
from app.models.tenant import Tenant
from app.schemas.tenant import (
    TenantCreate,
    TenantCreateResponse,
    TenantResponse,
    TenantUsage,
)

router = APIRouter()


@router.post(
    "",
    response_model=TenantCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Tenant).where(Tenant.email == body.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant with this email already exists.",
        )

    raw_key = generate_api_key()
    tenant = Tenant(
        name=body.name,
        email=body.email,
        api_key_hash=hash_api_key(raw_key),
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    return TenantCreateResponse(
        tenant=TenantResponse.model_validate(tenant),
        api_key=raw_key,
    )


@router.get("/me", response_model=TenantResponse)
async def get_my_profile(
    tenant: Tenant = Depends(get_current_tenant),
):
    return TenantResponse.model_validate(tenant)


@router.get("/me/usage", response_model=TenantUsage)
async def get_my_usage(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(Audit.id).label("total_audits"),
            func.coalesce(func.sum(Audit.total_signals), 0).label("total_signals"),
            func.coalesce(func.sum(Audit.total_tokens_used), 0).label("total_tokens"),
            func.coalesce(func.sum(Audit.total_cost_usd), 0).label("total_cost"),
        ).where(Audit.tenant_id == tenant.id)
    )
    row = result.one()
    return TenantUsage(
        total_audits=row.total_audits,
        total_signals=row.total_signals,
        total_tokens_used=row.total_tokens,
        total_cost_usd=float(row.total_cost),
    )
