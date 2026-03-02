from app.engine.categories.base import BaseCategoryAnalyzer


class Cat18QueueProcessingAnalyzer(BaseCategoryAnalyzer):
    category_id = 18
    name = "Queue & Event Processing"
    part = "C"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Message ordering not guaranteed",
            "Exactly-once not implemented",
            "Dead letter queue not monitored",
            "Poison message retry loop",
            "Consumer lag not monitored",
            "Partition rebalancing duplicates",
            "Schema evolution breaking consumers",
            "No backpressure",
            "Queue retention too short",
            "Queue retention too long (PII)",
            "Missing message tracing",
            "Batch consumer partial failure",
            "Message size limit exceeded",
            "Consumer idempotency missing",
            "Event replay missing",
        ]
