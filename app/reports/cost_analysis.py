from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class CostAnalysisGenerator(BaseReportGenerator):
    report_type = "cost-analysis"
    name = "Cost Analysis"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        cost_cats = {33, 24}
        relevant = [s for s in signals if s.category_id in cost_cats]

        opportunities = []
        for s in relevant:
            opportunities.append({
                "signal": s.signal_text[:300],
                "severity": s.severity,
                "score": s.score,
                "evidence": s.evidence[:200],
                "remediation": s.remediation[:200],
                "effort": s.effort,
            })

        opportunities.sort(key=lambda x: x["score"], reverse=True)

        return {
            "title": "Cost Analysis & Optimization",
            "total_cost_signals": len(opportunities),
            "optimization_opportunities": opportunities,
            "audit_execution_cost": {
                "tokens_used": audit_data.get("total_tokens", 0),
                "cost_usd": audit_data.get("total_cost", 0),
            },
        }
