"""Master report generator — produces all 11 deliverables."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit
from app.models.report import Report
from app.models.signal import Signal
from app.reports.signal_table import SignalTableGenerator
from app.reports.executive_summary import ExecutiveSummaryGenerator
from app.reports.risk_heatmap import RiskHeatmapGenerator
from app.reports.spof_map import SpofMapGenerator
from app.reports.failure_catalog import FailureCatalogGenerator
from app.reports.performance_profile import PerformanceProfileGenerator
from app.reports.aiml_risk_register import AimlRiskRegisterGenerator
from app.reports.cost_analysis import CostAnalysisGenerator
from app.reports.observability_scorecard import ObservabilityScorecardGenerator
from app.reports.compliance_matrix import ComplianceMatrixGenerator
from app.reports.remediation_roadmap import RemediationRoadmapGenerator

logger = logging.getLogger(__name__)

GENERATORS = [
    SignalTableGenerator(),
    ExecutiveSummaryGenerator(),
    RiskHeatmapGenerator(),
    SpofMapGenerator(),
    FailureCatalogGenerator(),
    PerformanceProfileGenerator(),
    AimlRiskRegisterGenerator(),
    CostAnalysisGenerator(),
    ObservabilityScorecardGenerator(),
    ComplianceMatrixGenerator(),
    RemediationRoadmapGenerator(),
]


async def generate_all_reports(db: AsyncSession, audit_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Signal).where(Signal.audit_id == audit_id).order_by(Signal.sequence_number)
    )
    signals = list(result.scalars().all())

    audit_result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = audit_result.scalar_one()

    audit_data = {
        "audit_id": str(audit_id),
        "system_context": audit.system_context,
        "total_tokens": audit.total_tokens_used,
        "total_cost": audit.total_cost_usd,
    }

    for gen in GENERATORS:
        try:
            content = await gen.generate(signals, audit_data)
            report = Report(
                audit_id=audit_id,
                report_type=gen.report_type,
                content=content,
            )
            db.add(report)
            logger.info(f"Generated report: {gen.report_type}")
        except Exception as e:
            logger.error(f"Failed to generate {gen.report_type}: {e}")

    await db.commit()
