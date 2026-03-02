import hashlib
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    return f"da_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_tenant_by_api_key(
    db: AsyncSession, api_key: str
) -> Tenant | None:
    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(Tenant).where(
            Tenant.api_key_hash == key_hash,
            Tenant.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def require_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )
    return api_key
