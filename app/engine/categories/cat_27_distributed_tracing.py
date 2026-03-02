from app.engine.categories.base import BaseCategoryAnalyzer


class Cat27DistributedTracingAnalyzer(BaseCategoryAnalyzer):
    category_id = 27
    name = "Distributed Tracing"
    part = "F"
    min_signals = 10

    def get_checklist(self) -> list[str]:
        return [
            "No distributed tracing",
            "Trace ID not propagated across boundaries",
            "Trace ID not in logs",
            "DB queries not traced",
            "External API calls not traced",
            "Message queue not traced",
            "Trace sampling drops important spans",
            "Trace storage retention too short",
            "No trace-based alerting",
            "Trace UI not accessible to on-call",
        ]
