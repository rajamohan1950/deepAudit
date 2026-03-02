from app.engine.categories.base import BaseCategoryAnalyzer


class Cat28AlertingIncidentAnalyzer(BaseCategoryAnalyzer):
    category_id = 28
    name = "Alerting & Incident Response"
    part = "F"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Alert coverage gaps",
            "Alert fatigue",
            "Static thresholds only",
            "No SLO burn-rate alerts",
            "No anomaly detection",
            "No dead man's switch",
            "Runbooks missing/outdated",
            "Escalation policy not tested",
            "No PagerDuty/OpsGenie",
            "On-call imbalanced",
            "Incident severity classification missing",
            "No incident commander role",
            "No communication plan",
            "No status page",
            "Postmortem process missing",
            "Postmortem items not tracked",
            "MTTD not measured",
            "MTTR not measured",
            "No incident trends analysis",
            "No chaos engineering/GameDays",
        ]
