from app.engine.categories.base import BaseCategoryAnalyzer


class Cat17DistributedSystemsAnalyzer(BaseCategoryAnalyzer):
    category_id = 17
    name = "Distributed System Failures"
    part = "C"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "CAP trade-offs not decided",
            "Network partition not tested",
            "Clock skew",
            "Message delivery guarantees unclear",
            "Event ordering across partitions",
            "Consistency model confusion",
            "2PC coordinator failure",
            "Saga rollback cascading",
            "Service discovery failure",
            "gRPC deadline not propagated",
            "Context cancellation not propagated",
            "Distributed cache inconsistency",
            "Leader election bug",
            "Quorum misconfigured",
            "Split-brain recovery undefined",
        ]
