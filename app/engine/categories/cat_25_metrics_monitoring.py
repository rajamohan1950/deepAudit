from app.engine.categories.base import BaseCategoryAnalyzer


class Cat25MetricsMonitoringAnalyzer(BaseCategoryAnalyzer):
    category_id = 25
    name = "Metrics & Monitoring"
    part = "F"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "RED metrics missing",
            "USE metrics missing",
            "SLO/SLI not defined",
            "Error budget not tracked",
            "Business metrics not in monitoring",
            "Dependency health metrics missing",
            "Metric cardinality explosion",
            "Histogram buckets wrong",
            "No baseline established",
            "Metric resolution too low",
            "Metric retention too short",
            "Counter reset not handled",
            "Custom app metrics missing",
            "Infra not correlated with app metrics",
            "No cost metrics",
            "Metric pipeline SPOF",
            "No synthetic monitoring",
            "Health check doesn't test functionality",
            "Metrics scrape interval too long",
            "No per-tenant metrics",
        ]
