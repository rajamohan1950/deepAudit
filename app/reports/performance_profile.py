from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class PerformanceProfileGenerator(BaseReportGenerator):
    report_type = "performance-profile"
    name = "Performance Profile"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        perf_cats = {6, 7, 8, 9, 10, 11, 12}
        relevant = [s for s in signals if s.category_id in perf_cats]

        by_category = {}
        for s in relevant:
            cat_name = s.category.name if s.category else f"Cat {s.category_id}"
            if cat_name not in by_category:
                by_category[cat_name] = []
            by_category[cat_name].append({
                "signal": s.signal_text[:300],
                "severity": s.severity,
                "score": s.score,
                "evidence": s.evidence[:200],
                "remediation": s.remediation[:200],
                "effort": s.effort,
            })

        return {
            "title": "Performance Profile",
            "total_performance_signals": len(relevant),
            "critical_count": len([s for s in relevant if s.severity == "P0"]),
            "high_count": len([s for s in relevant if s.severity == "P1"]),
            "by_category": by_category,
        }
