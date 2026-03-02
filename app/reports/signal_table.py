from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class SignalTableGenerator(BaseReportGenerator):
    report_type = "signal-table"
    name = "Signal Table"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        rows = []
        for s in signals:
            rows.append({
                "sequence_number": s.sequence_number,
                "category_id": s.category_id,
                "category_name": s.category.name if s.category else "",
                "signal_text": s.signal_text,
                "severity": s.severity,
                "score": s.score,
                "score_type": s.score_type,
                "evidence": s.evidence,
                "failure_scenario": s.failure_scenario,
                "remediation": s.remediation,
                "effort": s.effort,
                "confidence": s.confidence,
                "phase_number": s.phase_number,
            })

        return {
            "total_signals": len(rows),
            "signals": rows,
        }
