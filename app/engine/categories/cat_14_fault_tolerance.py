from app.engine.categories.base import BaseCategoryAnalyzer


class Cat14FaultToleranceAnalyzer(BaseCategoryAnalyzer):
    category_id = 14
    name = "Fault Tolerance & Resilience"
    part = "C"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "Circuit breaker missing",
            "Circuit breaker misconfigured",
            "Retry without backoff",
            "Retry without jitter",
            "Retry without max",
            "Multi-layer retry amplification",
            "Timeout not configured",
            "Timeout chain bug",
            "Bulkhead missing",
            "Fallback undefined",
            "Graceful degradation not designed",
            "Health check too simple",
            "Health check too aggressive",
            "Liveness vs readiness confusion",
            "Cascading failure chain",
            "Back-pressure missing",
            "Dead letter queue missing",
            "Poison message handling",
            "Split-brain",
            "Failover never tested",
            "RTO not measured",
            "RPO not measured",
            "Dependency isolation missing",
            "Load shedding not implemented",
            "Admission control missing",
            "Self-DDOS via retries",
            "Chaos testing never performed",
        ]
