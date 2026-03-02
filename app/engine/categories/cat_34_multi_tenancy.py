from app.engine.categories.base import BaseCategoryAnalyzer


class Cat34MultiTenancyAnalyzer(BaseCategoryAnalyzer):
    category_id = 34
    name = "Multi-Tenancy & Isolation"
    part = "G"
    min_signals = 10

    def get_checklist(self) -> list[str]:
        return [
            "Data isolation not enforced",
            "Noisy neighbor",
            "No per-tenant rate limiting",
            "Tenant ID not validated in every query",
            "Cross-tenant cache pollution",
            "Tenant-specific config not isolated",
            "No per-tenant usage tracking",
            "Tenant deletion incomplete",
            "No tenant-specific SLA",
            "Background jobs shared queue",
        ]
