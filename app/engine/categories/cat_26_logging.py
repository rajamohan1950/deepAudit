from app.engine.categories.base import BaseCategoryAnalyzer


class Cat26LoggingAnalyzer(BaseCategoryAnalyzer):
    category_id = 26
    name = "Logging"
    part = "F"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Unstructured logs",
            "No correlation/trace ID",
            "Log levels misused",
            "Security events not logged",
            "Audit trail incomplete",
            "Log retention too short",
            "No log sampling",
            "PII in logs",
            "Log injection possible",
            "Request/response body not logged for external calls",
            "Error logs missing request context",
            "Log aggregation SPOF",
            "Structured log fields inconsistent",
            "Log volume not monitored",
            "No log-based alerting",
        ]
