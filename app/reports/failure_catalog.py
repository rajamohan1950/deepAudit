from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class FailureCatalogGenerator(BaseReportGenerator):
    report_type = "failure-catalog"
    name = "Failure Mode Catalog"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        failure_cats = {13, 14, 15, 16, 17}
        relevant = [s for s in signals if s.category_id in failure_cats]

        entries = []
        for s in relevant:
            entries.append({
                "category": s.category.name if s.category else "",
                "signal": s.signal_text[:300],
                "severity": s.severity,
                "failure_mode": s.failure_scenario[:400],
                "remediation": s.remediation[:300],
                "effort": s.effort,
            })

        entries.sort(key=lambda x: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(x["severity"], 4))

        return {
            "title": "Failure Mode Catalog",
            "total_failure_modes": len(entries),
            "entries": entries,
        }
