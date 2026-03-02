import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_tenant_by_api_key, require_api_key
from app.models.tenant import Tenant


@dataclass
class TenantContext:
    tenant_id: uuid.UUID
    tenant_name: str
    plan: str
    settings: dict


async def get_current_tenant(
    api_key: str = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    tenant = await get_tenant_by_api_key(db, api_key)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return tenant


async def get_tenant_context(
    tenant: Tenant = Depends(get_current_tenant),
) -> TenantContext:
    return TenantContext(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        plan=tenant.plan,
        settings=tenant.settings or {},
    )
