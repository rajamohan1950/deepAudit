from app.engine.categories.base import BaseCategoryAnalyzer


class Cat12GracefulShutdownAnalyzer(BaseCategoryAnalyzer):
    category_id = 12
    name = "Graceful Shutdown & Lifecycle"
    part = "B"
    min_signals = 10

    def get_checklist(self) -> list[str]:
        return [
            "No SIGTERM handler",
            "No connection draining",
            "In-flight requests dropped",
            "DB transactions uncommitted on shutdown",
            "Message ack lost",
            "Background job interruption",
            "K8s preStop hook missing",
            "terminationGracePeriodSeconds too short",
            "LB deregistration delay",
            "Health endpoint 200 during shutdown",
            "Persistent connections not closed",
            "File locks not released",
        ]
