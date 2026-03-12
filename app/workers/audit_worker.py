"""ARQ background worker for async audit execution."""

import logging

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.engine.orchestrator import AuditOrchestrator

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    """Run schema migrations when the worker starts."""
    from app.database import ensure_schema
    await ensure_schema()
    logger.info("Worker schema migrations ensured")


async def run_audit_job(ctx: dict, audit_id: str) -> dict:
    logger.info(f"Worker picked up audit job: {audit_id}")
    orchestrator = AuditOrchestrator()

    try:
        await orchestrator.run_audit(audit_id)
        return {"audit_id": audit_id, "status": "completed"}
    except Exception as e:
        logger.exception(f"Audit job {audit_id} failed: {e}")
        return {"audit_id": audit_id, "status": "failed", "error": str(e)}


async def enqueue_audit_job(audit_id: str) -> None:
    redis_settings = _parse_redis_url(settings.redis_url)
    pool = await create_pool(redis_settings)
    await pool.enqueue_job("run_audit_job", audit_id)
    logger.info(f"Enqueued audit job: {audit_id}")
    await pool.close()


def _parse_redis_url(url: str) -> RedisSettings:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or "0"),
        password=parsed.password,
    )


class WorkerSettings:
    """ARQ worker configuration."""
    on_startup = startup
    functions = [run_audit_job]
    redis_settings = _parse_redis_url(settings.redis_url)
    max_jobs = 3
    job_timeout = 7200
    health_check_interval = 30
