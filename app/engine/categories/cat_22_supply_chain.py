from app.engine.categories.base import BaseCategoryAnalyzer


class Cat22SupplyChainAnalyzer(BaseCategoryAnalyzer):
    category_id = 22
    name = "Third-Party & Supply Chain"
    part = "D"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Dependency with known CVE",
            "Transitive dependency vulnerability",
            "Diamond dependency conflict",
            "Abandoned dependency",
            "Dependency license non-compliance",
            "Lockfile not committed",
            "Dependency confusion attack",
            "Third-party SDK auto-updates",
            "Vendor SLA not monitored",
            "Vendor API deprecation untracked",
            "Vendor data handling unaudited",
            "No fallback for critical vendor",
            "External JS without SRI",
            "Third-party cookie compliance",
            "Vendor uptime not in SLA",
        ]
