from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.tenant_context import TenantContext, get_tenant_context
from app.models.tenant import Tenant
from app.middleware.tenant_context import get_current_tenant

__all__ = [
    "get_db",
    "get_current_tenant",
    "get_tenant_context",
    "DbSession",
    "CurrentTenant",
    "CurrentTenantContext",
]

DbSession = Depends(get_db)
CurrentTenant = Depends(get_current_tenant)
CurrentTenantContext = Depends(get_tenant_context)
