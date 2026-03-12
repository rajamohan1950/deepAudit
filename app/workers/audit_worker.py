"""ARQ background worker for async audit execution.

When running without a separate worker service (e.g. on Render free tier),
enqueue_audit_job() fires the audit in-process via asyncio.create_task().
"""

import asyncio
import logging

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


# Keep strong references so tasks aren't garbage-collected
_running_tasks: set[asyncio.Task] = set()


async def enqueue_audit_job(audit_id: str) -> None:
    """Run audit in-process (no separate worker service needed)."""

    async def _run(aid: str) -> None:
        logger.info(f"Running audit {aid} in-process")
        try:
            orch = AuditOrchestrator()
            await orch.run_audit(aid)
        except Exception as e:
            logger.exception(f"In-process audit {aid} failed: {e}")

    task = asyncio.create_task(_run(audit_id))
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)
    logger.info(f"Scheduled audit {audit_id} in-process")


def _parse_redis_url(url: str):
    """Parse Redis URL into ARQ RedisSettings (only when ARQ is available)."""
    from urllib.parse import urlparse
    from arq.connections import RedisSettings
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or "0"),
        password=parsed.password,
    )


try:
    class WorkerSettings:
        """ARQ worker configuration (only used when running a dedicated worker)."""
        on_startup = startup
        functions = [run_audit_job]
        redis_settings = _parse_redis_url(settings.redis_url)
        max_jobs = 3
        job_timeout = 7200
        health_check_interval = 30
except Exception:
    pass  # ARQ not installed or Redis not configured — in-process mode only
