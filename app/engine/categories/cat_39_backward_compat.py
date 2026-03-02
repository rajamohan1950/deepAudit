from app.engine.categories.base import BaseCategoryAnalyzer


class Cat39BackwardCompatAnalyzer(BaseCategoryAnalyzer):
    category_id = 39
    name = "Backward Compatibility & Migration"
    part = "H"
    min_signals = 10

    def get_checklist(self) -> list[str]:
        return [
            "API breaking change without versioning",
            "DB schema migration without backward compat",
            "Message format change breaks consumers",
            "Config format change breaks deployments",
            "Library upgrade breaks dependent services",
            "Proto/Avro field renumbering",
            "Feature removal without deprecation",
            "Data migration only forward tested",
            "Mobile app forced update",
            "Webhook payload change breaks consumers",
        ]
