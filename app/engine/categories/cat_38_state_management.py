from app.engine.categories.base import BaseCategoryAnalyzer


class Cat38StateManagementAnalyzer(BaseCategoryAnalyzer):
    category_id = 38
    name = "State Management"
    part = "H"
    min_signals = 10

    def get_checklist(self) -> list[str]:
        return [
            "Session state in-process",
            "Sticky sessions without fallback",
            "Session state too large",
            "State replication lag",
            "Stateful service blocking scaling",
            "State not cleaned after workflow",
            "State recovery after crash undefined",
            "Idempotency state cleanup",
            "Feature flag state cached too long",
            "WebSocket state on pod restart",
        ]
