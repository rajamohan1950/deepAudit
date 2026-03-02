import time

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from app.config import settings


async def check_rate_limit(
    request: Request,
    tenant_id: str,
    redis: Redis | None = None,
) -> None:
    if redis is None:
        return

    key = f"rate_limit:{tenant_id}:{int(time.time()) // 60}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)

    limit = settings.rate_limit_requests_per_minute
    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {limit} requests per minute.",
            headers={"Retry-After": "60"},
        )
