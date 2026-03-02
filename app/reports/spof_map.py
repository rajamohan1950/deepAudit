from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class SpofMapGenerator(BaseReportGenerator):
    report_type = "spof-map"
    name = "Single Points of Failure Map"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        spof_signals = [s for s in signals if s.category_id == 13]

        spofs = []
        for s in spof_signals:
            spofs.append({
                "signal": s.signal_text[:300],
                "severity": s.severity,
                "score": s.score,
                "evidence": s.evidence,
                "blast_radius": s.failure_scenario[:300],
                "remediation": s.remediation[:300],
                "effort": s.effort,
            })

        spofs.sort(key=lambda x: x["score"], reverse=True)

        return {
            "title": "Single Points of Failure Map",
            "total_spofs": len(spofs),
            "critical_spofs": len([s for s in spofs if s["severity"] == "P0"]),
            "high_spofs": len([s for s in spofs if s["severity"] == "P1"]),
            "spofs": spofs,
        }
