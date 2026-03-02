from app.models.signal import Signal
from app.reports.base import BaseReportGenerator


class ComplianceMatrixGenerator(BaseReportGenerator):
    report_type = "compliance-matrix"
    name = "Compliance Gap Matrix"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        compliance_cats = {4, 5, 19, 26, 35}
        relevant = [s for s in signals if s.category_id in compliance_cats]

        compliance_reqs = audit_data.get("system_context", {}).get(
            "compliance_requirements", []
        )

        gaps = []
        for s in relevant:
            gap = {
                "signal": s.signal_text[:300],
                "severity": s.severity,
                "score": s.score,
                "category": s.category.name if s.category else "",
                "evidence": s.evidence[:200],
                "remediation": s.remediation[:200],
                "effort": s.effort,
                "applicable_frameworks": [],
            }

            sig_lower = s.signal_text.lower() + " " + s.evidence.lower()
            for req in compliance_reqs:
                req_lower = req.lower()
                if req_lower in sig_lower or self._framework_relevant(req_lower, s):
                    gap["applicable_frameworks"].append(req)

            gaps.append(gap)

        gaps.sort(key=lambda x: x["score"], reverse=True)

        return {
            "title": "Compliance Gap Matrix",
            "applicable_frameworks": compliance_reqs,
            "total_gaps": len(gaps),
            "critical_gaps": len([g for g in gaps if g["severity"] in ("P0", "P1")]),
            "gaps": gaps,
        }

    def _framework_relevant(self, framework: str, signal: Signal) -> bool:
        mapping = {
            "soc2": {4, 5, 19, 26, 35},
            "gdpr": {4, 35},
            "hipaa": {4, 5, 35},
            "pci-dss": {3, 4, 5, 19},
            "pci": {3, 4, 5, 19},
        }
        relevant_cats = mapping.get(framework, set())
        return signal.category_id in relevant_cats
