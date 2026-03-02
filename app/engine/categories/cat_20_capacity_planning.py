from app.engine.categories.base import BaseCategoryAnalyzer


class Cat20CapacityPlanningAnalyzer(BaseCategoryAnalyzer):
    category_id = 20
    name = "Capacity Planning & Scalability"
    part = "D"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "No load testing",
            "Load test not realistic",
            "Auto-scaling not configured",
            "Auto-scaling too slow",
            "Auto-scaling ceiling too low",
            "Auto-scaling wrong metric",
            "Resource requests/limits not set",
            "Vertical scaling ceiling",
            "Storage growth untracked",
            "Database connection limit approaching",
            "Queue depth unmonitored",
            "Memory growth trend",
            "Non-linear cost scaling",
            "No capacity planning process",
            "Peak load never measured",
            "No performance budget per endpoint",
            "Horizontal scaling blocked by stateful component",
            "Database bottleneck no sharding",
            "External API rate limits not in capacity plan",
            "Spot instances not used",
        ]
