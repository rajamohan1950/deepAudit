"""Data retention policy enforcement — auto-delete code after audit completion."""

import logging
import shutil
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.artifact import Artifact, RepoSnapshot
from app.models.audit import Audit

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_HOURS = 24


class DataRetentionManager:
    """Enforces data-at-rest retention: cloned repos and artifact content are
    purged after a configurable window while signals and reports are preserved."""

    async def schedule_cleanup(
        self, audit_id: str, retention_hours: int = DEFAULT_RETENTION_HOURS
    ) -> None:
        """Log the scheduled cleanup.  Actual deletion happens when
        ``cleanup_expired`` runs (e.g. via a periodic worker) or can be
        triggered immediately with ``cleanup_audit_data``."""
        delete_after = datetime.now(timezone.utc) + timedelta(hours=retention_hours)
        logger.info(
            "Cleanup scheduled for audit %s — code will be purged after %s "
            "(retention=%dh)",
            audit_id,
            delete_after.isoformat(),
            retention_hours,
        )

    async def cleanup_audit_data(self, audit_id: str) -> None:
        """Delete cloned repo directory, uploaded files, and artifact content
        for a single audit.  Signals and reports are intentionally kept."""
        async with async_session_factory() as db:
            snapshot = await self._get_snapshot(db, audit_id)
            if not snapshot:
                logger.warning("No snapshot found for audit %s — nothing to clean", audit_id)
                return

            self._remove_local_path(snapshot.local_path)

            upload_path = await self._get_upload_path(db, audit_id)
            if upload_path:
                self._remove_local_path(upload_path)

            nullified = await self._nullify_artifact_content(db, snapshot.id)

            snapshot.local_path = None
            await db.commit()

            logger.info(
                "Cleanup complete for audit %s — removed local files, "
                "nullified content for %d artifacts",
                audit_id,
                nullified,
            )

    async def cleanup_expired(
        self, retention_hours: int = DEFAULT_RETENTION_HOURS
    ) -> int:
        """Find all completed/failed audits older than *retention_hours* that
        still have local files or artifact content, and clean them up.

        Returns the number of audits cleaned."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=retention_hours)

        async with async_session_factory() as db:
            result = await db.execute(
                select(Audit).where(
                    Audit.status.in_(("completed", "failed")),
                    Audit.completed_at <= cutoff,
                )
            )
            audits = result.scalars().all()

        cleaned = 0
        for audit in audits:
            try:
                await self.cleanup_audit_data(str(audit.id))
                cleaned += 1
            except Exception:
                logger.exception("Failed to clean audit %s", audit.id)

        logger.info(
            "Expired-audit sweep done — %d/%d audits cleaned (cutoff=%s)",
            cleaned,
            len(audits),
            cutoff.isoformat(),
        )
        return cleaned

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _get_snapshot(db: AsyncSession, audit_id: str) -> RepoSnapshot | None:
        result = await db.execute(
            select(RepoSnapshot).where(
                RepoSnapshot.audit_id == audit_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_upload_path(db: AsyncSession, audit_id: str) -> str | None:
        result = await db.execute(
            select(Audit.source_config).where(Audit.id == audit_id)
        )
        config = result.scalar_one_or_none()
        if config and config.get("type") == "upload":
            return config.get("local_path")
        return None

    @staticmethod
    async def _nullify_artifact_content(db: AsyncSession, snapshot_id) -> int:
        result = await db.execute(
            update(Artifact)
            .where(Artifact.snapshot_id == snapshot_id, Artifact.content.isnot(None))
            .values(content=None)
        )
        return result.rowcount  # type: ignore[return-value]

    @staticmethod
    def _remove_local_path(path: str | None) -> None:
        if not path:
            return
        try:
            shutil.rmtree(path, ignore_errors=True)
            logger.info("Removed local path: %s", path)
        except Exception:
            logger.exception("Failed to remove path: %s", path)
