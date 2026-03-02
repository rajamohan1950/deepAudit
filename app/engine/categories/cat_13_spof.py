from app.engine.categories.base import BaseCategoryAnalyzer


class Cat13SPOFAnalyzer(BaseCategoryAnalyzer):
    category_id = 13
    name = "Single Points of Failure"
    part = "C"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "Single DB instance",
            "Single AZ",
            "Single region",
            "Single LB",
            "Single DNS provider",
            "Single CA",
            "Single secrets vault",
            "Single message broker",
            "Single cache instance",
            "Single CI/CD pipeline",
            "Single monitoring system",
            "Single log aggregator",
            "Single external API provider",
            "Single auth/IdP provider",
            "Single container registry",
            "Single artifact repo",
            "Hero engineer",
            "Single network path",
            "Single time source",
            "Shared database across services",
            "Shared K8s cluster",
            "Single API gateway",
            "Single config source",
            "Shared library bug blast radius",
            "Single LLM provider",
            "Single notification provider",
        ]
