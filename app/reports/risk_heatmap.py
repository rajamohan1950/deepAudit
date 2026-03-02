from app.models.signal import Signal
from app.reports.base import BaseReportGenerator

CATEGORY_NAMES = {
    1: "Authentication", 2: "Authorization", 3: "Input Validation",
    4: "Data Protection", 5: "Cryptography", 6: "Memory", 7: "CPU",
    8: "Network I/O", 9: "Database", 10: "Caching", 11: "OS/Kernel",
    12: "Graceful Shutdown", 13: "SPOF", 14: "Fault Tolerance",
    15: "Concurrency", 16: "Data Integrity", 17: "Distributed Systems",
    18: "Queue Processing", 19: "Infra Security", 20: "Capacity",
    21: "CI/CD", 22: "Supply Chain", 23: "AI/ML Risks", 24: "AI/ML Ops",
    25: "Metrics", 26: "Logging", 27: "Tracing", 28: "Alerting",
    29: "Testing", 30: "Code Quality", 31: "API Design", 32: "UX/A11y",
    33: "Cost/FinOps", 34: "Multi-Tenancy", 35: "Compliance",
    36: "Disaster Recovery", 37: "i18n", 38: "State Management",
    39: "Backward Compat", 40: "Organizational",
}


class RiskHeatmapGenerator(BaseReportGenerator):
    report_type = "risk-heatmap"
    name = "Risk Heatmap"

    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        matrix = {}
        for cat_id in range(1, 41):
            matrix[str(cat_id)] = {
                "name": CATEGORY_NAMES.get(cat_id, f"Category {cat_id}"),
                "P0": 0, "P1": 0, "P2": 0, "P3": 0, "total": 0,
                "max_score": 0.0,
                "risk_level": "low",
            }

        for s in signals:
            key = str(s.category_id)
            if key in matrix:
                matrix[key][s.severity] += 1
                matrix[key]["total"] += 1
                matrix[key]["max_score"] = max(matrix[key]["max_score"], s.score)

        for cat_data in matrix.values():
            if cat_data["P0"] > 0:
                cat_data["risk_level"] = "critical"
            elif cat_data["P1"] > 3:
                cat_data["risk_level"] = "high"
            elif cat_data["P1"] > 0 or cat_data["P2"] > 5:
                cat_data["risk_level"] = "medium"
            else:
                cat_data["risk_level"] = "low"

        return {
            "title": "Risk Heatmap — 40 Categories x 4 Severity Levels",
            "matrix": matrix,
            "legend": {
                "critical": "P0 signals present — immediate action required",
                "high": "Multiple P1 signals — fix within 1 sprint",
                "medium": "P1 or many P2 signals — fix within 1 quarter",
                "low": "Only P2/P3 signals — backlog",
            },
        }
