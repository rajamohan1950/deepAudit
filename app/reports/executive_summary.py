from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class ExecutiveSummaryGenerator(BaseReportGenerator):
    report_type = "executive-summary"
    name = "Executive Summary"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        by_sev = {"P0": [], "P1": [], "P2": [], "P3": []}
        for s in signals:
            by_sev.get(s.severity, []).append(s)

        top_critical = sorted(
            by_sev["P0"] + by_sev["P1"],
            key=lambda s: s.score,
            reverse=True,
        )[:15]

        effort_map = {"S": 0.1, "M": 0.5, "L": 2, "XL": 8}
        total_weeks = sum(
            effort_map.get(s.effort, 1) for s in signals
        )

        return {
            "title": "DeepAudit Executive Summary",
            "total_signals": len(signals),
            "severity_breakdown": {
                sev: len(sigs) for sev, sigs in by_sev.items()
            },
            "top_15_critical_findings": [
                {
                    "rank": i + 1,
                    "signal": s.signal_text[:200],
                    "severity": s.severity,
                    "score": s.score,
                    "category": s.category.name if s.category else "",
                    "evidence": s.evidence[:150],
                    "remediation": s.remediation[:200],
                    "effort": s.effort,
                }
                for i, s in enumerate(top_critical)
            ],
            "estimated_remediation_weeks": round(total_weeks, 1),
            "audit_cost_usd": audit_data.get("total_cost", 0),
            "audit_tokens_used": audit_data.get("total_tokens", 0),
        }
