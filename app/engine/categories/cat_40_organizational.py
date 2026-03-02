from app.engine.categories.base import BaseCategoryAnalyzer


class Cat40OrganizationalAnalyzer(BaseCategoryAnalyzer):
    category_id = 40
    name = "Organizational & Knowledge"
    part = "H"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "No change management process",
            "No RFC/design review",
            "No security champion per team",
            "No security training for developers",
            "No onboarding security checklist",
            "No offboarding process",
            "Knowledge silos (bus factor=1)",
            "No runbook for every alert",
            "No architecture decision records",
            "Post-incident items not tracked",
            "Technical roadmap doesn't include reliability/security",
            "Security deprioritized for features",
            "No game days/DR drills",
            "No cross-training",
            "On-call handbook missing",
        ]
