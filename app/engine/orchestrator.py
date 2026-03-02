"""Audit orchestrator — executes 10 phases of the deep audit."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.engine.categories.registry import get_analyzer
from app.engine.deduplicator import SignalDeduplicator
from app.engine.llm.client import LLMClient, LLMUsageTracker
from app.engine.llm.prompt_builder import PromptBuilder
from app.engine.phase_registry import get_all_phases
from app.ingestion.classifier import FileClassifier
from app.ingestion.cloner import RepoCloner
from app.ingestion.context_builder import ContextBuilder
from app.ingestion.discovery import FileDiscovery
from app.ingestion.git_analyzer import GitAnalyzer
from app.models.artifact import Artifact, RepoSnapshot
from app.models.audit import Audit, AuditPhase
from app.models.signal import Signal

logger = logging.getLogger(__name__)


class AuditOrchestrator:
    """Runs the complete 10-phase audit lifecycle."""

    def __init__(self):
        self.cloner = RepoCloner()
        self.discovery = FileDiscovery()
        self.classifier = FileClassifier()
        self.git_analyzer = GitAnalyzer()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.deduplicator = SignalDeduplicator()
        self.usage_tracker = LLMUsageTracker()

    async def run_audit(self, audit_id: str) -> None:
        async with async_session_factory() as db:
            audit = await self._load_audit(db, audit_id)
            if not audit:
                logger.error(f"Audit {audit_id} not found")
                return

            try:
                await self._update_status(db, audit, "ingesting")

                source = audit.source_config
                classified_files, git_analysis, snapshot = await self._ingest(
                    db, audit, source
                )

                llm_client = self._create_llm_client(audit.audit_config)
                system_prompt = self.prompt_builder.build_system_prompt()

                await self._update_status(db, audit, "running")
                audit.started_at = datetime.now(timezone.utc)
                await db.commit()

                signal_counter = 0
                phases = get_all_phases()

                for phase_num in sorted(phases.keys()):
                    phase_def = phases[phase_num]
                    category_ids = phase_def["categories"]

                    selected_cats = self._filter_categories(
                        category_ids, audit.audit_config
                    )
                    if not selected_cats:
                        continue

                    audit_phase = await self._get_phase(db, audit.id, phase_num)
                    await self._update_phase(db, audit_phase, "running")
                    audit.current_phase = phase_num
                    await db.commit()

                    phase_signals = []
                    phase_tokens = 0
                    phase_cost = 0.0

                    tasks = []
                    for cat_id in selected_cats:
                        tasks.append(
                            self._run_category(
                                llm_client,
                                system_prompt,
                                audit.system_context,
                                classified_files,
                                git_analysis,
                                cat_id,
                            )
                        )

                    sem = asyncio.Semaphore(settings.max_concurrent_phases)

                    async def bounded_task(coro):
                        async with sem:
                            return await coro

                    results = await asyncio.gather(
                        *[bounded_task(t) for t in tasks],
                        return_exceptions=True,
                    )

                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Category error in phase {phase_num}: {result}")
                            continue
                        cat_signals, cat_tokens, cat_cost = result
                        unique_signals = self.deduplicator.deduplicate(cat_signals)
                        phase_signals.extend(unique_signals)
                        phase_tokens += cat_tokens
                        phase_cost += cat_cost

                    for sig_data in phase_signals:
                        signal_counter += 1
                        signal = Signal(
                            audit_id=audit.id,
                            category_id=sig_data.category_id,
                            sequence_number=signal_counter,
                            signal_text=sig_data.signal_text,
                            severity=sig_data.severity,
                            score=sig_data.score,
                            score_type=sig_data.score_type,
                            evidence=sig_data.evidence,
                            failure_scenario=sig_data.failure_scenario,
                            remediation=sig_data.remediation,
                            effort=sig_data.effort,
                            confidence=sig_data.confidence,
                            references=sig_data.references or [],
                            phase_number=phase_num,
                        )
                        db.add(signal)

                    await self._update_phase(
                        db, audit_phase, "completed",
                        signals_found=len(phase_signals),
                        tokens_used=phase_tokens,
                        cost_usd=phase_cost,
                    )

                    audit.total_signals = signal_counter
                    audit.total_tokens_used += phase_tokens
                    audit.total_cost_usd += phase_cost
                    await db.commit()

                    logger.info(
                        f"Phase {phase_num} complete: "
                        f"{len(phase_signals)} signals, "
                        f"{phase_tokens} tokens, ${phase_cost:.4f}"
                    )

                audit.status = "generating_reports"
                await db.commit()

                from app.reports.generator import generate_all_reports
                await generate_all_reports(db, audit.id)

                await self._update_status(db, audit, "completed")
                audit.completed_at = datetime.now(timezone.utc)
                await db.commit()

                logger.info(
                    f"Audit {audit_id} completed: "
                    f"{signal_counter} signals, "
                    f"{audit.total_tokens_used} tokens, "
                    f"${audit.total_cost_usd:.2f}"
                )

            except Exception as e:
                logger.exception(f"Audit {audit_id} failed: {e}")
                audit.status = "failed"
                audit.error_message = str(e)[:2000]
                await db.commit()

            finally:
                if audit.source_config.get("type") in ("github", "gitlab", "bitbucket"):
                    snapshot_result = await db.execute(
                        select(RepoSnapshot).where(RepoSnapshot.audit_id == audit.id)
                    )
                    snap = snapshot_result.scalar_one_or_none()
                    if snap and snap.local_path:
                        self.cloner.cleanup(snap.local_path)

    async def _ingest(
        self, db: AsyncSession, audit: Audit, source: dict
    ) -> tuple[list[dict], dict, RepoSnapshot]:
        source_type = source.get("type", "upload")

        if source_type in ("github", "gitlab", "bitbucket"):
            clone_result = await self.cloner.clone(
                repo_url=source["repo_url"],
                branch=source.get("branch"),
                access_token=source.get("access_token"),
                audit_id=str(audit.id),
            )
            repo_path = clone_result["local_path"]
        else:
            raise ValueError(f"Source type '{source_type}' requires pre-uploaded files")

        discovery = FileDiscovery(
            paths_include=source.get("paths_include", []),
            paths_exclude=source.get("paths_exclude", []),
        )
        raw_files = discovery.discover(repo_path)
        classified_files = self.classifier.classify(raw_files)
        git_analysis = self.git_analyzer.analyze(repo_path)

        file_index = {
            "total": len(classified_files),
            "by_type": {},
            "by_language": {},
        }
        for f in classified_files:
            ft = f.get("file_type", "unknown")
            file_index["by_type"][ft] = file_index["by_type"].get(ft, 0) + 1
            lang = f.get("language")
            if lang:
                file_index["by_language"][lang] = file_index["by_language"].get(lang, 0) + 1

        snapshot = RepoSnapshot(
            audit_id=audit.id,
            repo_url=source.get("repo_url"),
            branch=clone_result.get("branch") if source_type != "upload" else None,
            commit_sha=clone_result.get("commit_sha") if source_type != "upload" else None,
            total_files=len(classified_files),
            file_index=file_index,
            git_analysis=git_analysis,
            local_path=repo_path if source_type != "upload" else None,
        )
        db.add(snapshot)

        for f in classified_files[:500]:
            try:
                content = open(f["absolute_path"], "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                content = None

            artifact = Artifact(
                snapshot_id=snapshot.id,
                file_path=f["path"],
                file_type=f["file_type"],
                language=f.get("language"),
                size_bytes=f["size_bytes"],
                content=content,
                metadata={"extension": f["extension"]},
            )
            db.add(artifact)

        await db.commit()
        logger.info(f"Ingestion complete: {len(classified_files)} files classified")

        return classified_files, git_analysis, snapshot

    async def _run_category(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        system_context: dict,
        classified_files: list[dict],
        git_analysis: dict,
        category_id: int,
    ) -> tuple[list, int, float]:
        analyzer = get_analyzer(category_id)

        context_bundle = self.context_builder.build_context(
            category_id, classified_files, git_analysis
        )

        signals, response = await analyzer.analyze(
            llm_client, system_prompt, system_context, context_bundle
        )

        self.usage_tracker.record(response, category_id)

        return signals, response.total_tokens, response.cost_usd

    def _create_llm_client(self, audit_config: dict) -> LLMClient:
        return LLMClient(
            provider=audit_config.get("llm_provider") or settings.default_llm_provider,
            model=audit_config.get("llm_model") or settings.default_llm_model,
        )

    def _filter_categories(
        self, category_ids: list[int], audit_config: dict
    ) -> list[int]:
        requested = audit_config.get("categories", "all")
        if requested == "all":
            return category_ids
        return [c for c in category_ids if c in requested]

    async def _load_audit(self, db: AsyncSession, audit_id: str) -> Audit | None:
        result = await db.execute(
            select(Audit).where(Audit.id == uuid.UUID(audit_id))
        )
        return result.scalar_one_or_none()

    async def _get_phase(
        self, db: AsyncSession, audit_id: uuid.UUID, phase_number: int
    ) -> AuditPhase:
        result = await db.execute(
            select(AuditPhase).where(
                AuditPhase.audit_id == audit_id,
                AuditPhase.phase_number == phase_number,
            )
        )
        return result.scalar_one()

    async def _update_status(
        self, db: AsyncSession, audit: Audit, status: str
    ) -> None:
        audit.status = status
        await db.commit()

    async def _update_phase(
        self,
        db: AsyncSession,
        phase: AuditPhase,
        status: str,
        signals_found: int = 0,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        phase.status = status
        if status == "running":
            phase.started_at = datetime.now(timezone.utc)
        elif status == "completed":
            phase.completed_at = datetime.now(timezone.utc)
            phase.signals_found = signals_found
            phase.tokens_used = tokens_used
            phase.cost_usd = cost_usd
        await db.commit()
