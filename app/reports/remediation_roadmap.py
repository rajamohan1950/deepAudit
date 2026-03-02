from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class RemediationRoadmapGenerator(BaseReportGenerator):
    report_type = "remediation-roadmap"
    name = "Remediation Roadmap"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        effort_map = {"S": "hours", "M": "days", "L": "weeks", "XL": "months"}

        week_1_2 = [s for s in signals if s.severity == "P0"]
        week_3_4 = [s for s in signals if s.severity == "P1"]
        month_2_3 = [s for s in signals if s.severity == "P2"]
        quarter_2 = [s for s in signals if s.severity == "P3"]

        def _format_items(signal_list: list[Signal]) -> list[dict]:
            items = []
            for s in sorted(signal_list, key=lambda x: x.score, reverse=True):
                items.append({
                    "sequence_number": s.sequence_number,
                    "signal": s.signal_text[:200],
                    "category": s.category.name if s.category else "",
                    "score": s.score,
                    "evidence": s.evidence[:150],
                    "remediation": s.remediation[:200],
                    "effort": s.effort,
                    "effort_description": effort_map.get(s.effort, "unknown"),
                })
            return items

        return {
            "title": "Remediation Roadmap",
            "phases": [
                {
                    "name": "Week 1-2: P0 Critical",
                    "description": "Security critical, SPOF, data integrity, active exploits",
                    "item_count": len(week_1_2),
                    "items": _format_items(week_1_2),
                },
                {
                    "name": "Week 3-4: P1 High",
                    "description": "High security, performance, reliability, AI safety",
                    "item_count": len(week_3_4),
                    "items": _format_items(week_3_4),
                },
                {
                    "name": "Month 2-3: P2 Medium",
                    "description": "Observability, testing, defense-in-depth",
                    "item_count": len(month_2_3),
                    "items": _format_items(month_2_3),
                },
                {
                    "name": "Quarter 2: P3 Backlog",
                    "description": "Tech debt, process, documentation, i18n",
                    "item_count": len(quarter_2),
                    "items": _format_items(quarter_2),
                },
            ],
            "total_items": len(signals),
        }
