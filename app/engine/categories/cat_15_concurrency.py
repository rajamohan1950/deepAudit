from app.engine.categories.base import BaseCategoryAnalyzer


class Cat15ConcurrencyAnalyzer(BaseCategoryAnalyzer):
    category_id = 15
    name = "Concurrency & Race Conditions"
    part = "C"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Read-modify-write without atomicity",
            "Double-spend",
            "Lost update",
            "Dirty read",
            "Phantom read",
            "Deadlock",
            "Lock ordering inconsistency",
            "Optimistic locking missing",
            "Pessimistic locking too broad",
            "Shared mutable state",
            "Non-atomic composite operation",
            "Event ordering issues",
            "Idempotency not implemented",
            "Idempotency key predictable",
            "Distributed lock without TTL",
            "Distributed lock not released",
            "Counter via read+write",
            "K8s scaling race",
            "Message deduplication missing",
            "Saga compensation incomplete",
        ]
