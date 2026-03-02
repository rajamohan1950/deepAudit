from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class AimlRiskRegisterGenerator(BaseReportGenerator):
    report_type = "aiml-risk-register"
    name = "AI/ML Risk Register"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        ai_cats = {23, 24}
        relevant = [s for s in signals if s.category_id in ai_cats]

        risks = []
        for s in relevant:
            risks.append({
                "signal": s.signal_text[:300],
                "severity": s.severity,
                "score": s.score,
                "risk_type": "model_risk" if s.category_id == 23 else "operational",
                "evidence": s.evidence[:200],
                "failure_scenario": s.failure_scenario[:300],
                "remediation": s.remediation[:300],
                "effort": s.effort,
            })

        risks.sort(key=lambda x: x["score"], reverse=True)

        return {
            "title": "AI/ML Risk Register",
            "total_ai_risks": len(risks),
            "model_risks": len([r for r in risks if r["risk_type"] == "model_risk"]),
            "operational_risks": len([r for r in risks if r["risk_type"] == "operational"]),
            "risks": risks,
            "token_cost_summary": {
                "total_audit_tokens": audit_data.get("total_tokens", 0),
                "total_audit_cost_usd": audit_data.get("total_cost", 0),
            },
        }
