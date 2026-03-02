from app.engine.categories.base import BaseCategoryAnalyzer


class Cat36DisasterRecoveryAnalyzer(BaseCategoryAnalyzer):
    category_id = 36
    name = "Disaster Recovery"
    part = "H"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "No DR plan",
            "DR plan never tested",
            "RTO not defined/achievable",
            "RPO not defined/measured",
            "Backup corruption undetected",
            "Backup restoration never tested",
            "Geo-failover not configured",
            "Geo-failover not tested",
            "DNS failover TTL too high",
            "Data sync lag to DR not monitored",
            "DR site capacity insufficient",
            "DR runbook incomplete",
            "No DR communication plan",
            "Application state not in DR",
            "Third-party deps not in DR plan",
        ]
