from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class ObservabilityScorecardGenerator(BaseReportGenerator):
    report_type = "observability-scorecard"
    name = "Observability Maturity Scorecard"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        obs_cats = {
            25: "Metrics & Monitoring",
            26: "Logging",
            27: "Distributed Tracing",
            28: "Alerting & Incident Response",
        }

        scores = {}
        for cat_id, cat_name in obs_cats.items():
            cat_signals = [s for s in signals if s.category_id == cat_id]
            score = self._calculate_maturity(cat_signals)
            scores[cat_name] = {
                "score": score,
                "rating": self._rating(score),
                "total_signals": len(cat_signals),
                "critical": len([s for s in cat_signals if s.severity in ("P0", "P1")]),
            }

        avg = sum(s["score"] for s in scores.values()) / max(len(scores), 1)

        return {
            "title": "Observability Maturity Scorecard",
            "aggregate_score": round(avg, 1),
            "aggregate_rating": self._rating(avg),
            "subcategories": scores,
            "scale": "1=Non-existent, 2=Ad-hoc, 3=Defined, 4=Managed, 5=Optimized",
        }

    def _calculate_maturity(self, signals: list[Signal]) -> float:
        if not signals:
            return 3.0

        p0_count = len([s for s in signals if s.severity == "P0"])
        p1_count = len([s for s in signals if s.severity == "P1"])
        total = len(signals)

        if p0_count > 2:
            return 1.0
        if p0_count > 0:
            return 2.0
        if p1_count > 5:
            return 2.5
        if p1_count > 2:
            return 3.0
        if total > 10:
            return 3.5
        return 4.0

    def _rating(self, score: float) -> str:
        if score >= 4.5:
            return "Optimized"
        if score >= 3.5:
            return "Managed"
        if score >= 2.5:
            return "Defined"
        if score >= 1.5:
            return "Ad-hoc"
        return "Non-existent"
