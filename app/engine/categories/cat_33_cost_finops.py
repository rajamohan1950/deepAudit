from app.engine.categories.base import BaseCategoryAnalyzer


class Cat33CostFinopsAnalyzer(BaseCategoryAnalyzer):
    category_id = 33
    name = "Cost & FinOps"
    part = "G"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "No cost monitoring dashboards",
            "No cost alerting",
            "No cost allocation per team/service/tenant",
            "Unused resources (VMs, EIPs, LBs)",
            "Over-provisioned instances",
            "No reserved instances/savings plan",
            "Storage tier misuse",
            "Egress cost unmonitored",
            "Log storage cost growing",
            "Orphaned snapshots/AMIs/volumes",
            "Dev/staging running 24/7",
            "No spot/preemptible usage",
            "LLM token spend unmonitored",
            "Fine-tune model hosting 24/7",
            "No cost optimization review cadence",
        ]
