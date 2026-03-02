from app.engine.categories.base import BaseCategoryAnalyzer


class Cat10CachingAnalyzer(BaseCategoryAnalyzer):
    category_id = 10
    name = "Caching Performance"
    part = "B"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Audit missing caching for expensive ops: DB queries, external API calls, compute",
            "Audit cache stampede: single-flight, coalescing, or probabilistic early expiry",
            "Audit cache invalidation bugs: correct invalidation on write, no stale reads",
            "Audit cache key collision: namespace, hash, version in key",
            "Audit cache warming missing: preload hot data on startup or after eviction",
            "Audit TTL misconfiguration: TTL matches data freshness requirements",
            "Audit cache size unbounded: maxmemory, eviction policy, size limits",
            "Audit hot key problem: sharding, local cache, or replication for hot keys",
            "Audit cache serialization overhead: efficient format, avoid redundant serialize",
            "Audit distributed cache consistency: eventual consistency, invalidation strategy",
            "Audit cache penetration: cache miss for non-existent keys, bloom filter or null cache",
            "Audit cache avalanche: staggered TTL, circuit breaker, gradual warm-up",
            "Audit dog-pile/lock contention: distributed lock, single-flight per key",
            "Audit cache-aside vs write-through confusion: consistent strategy per use case",
            "Audit Redis/Memcached memory limit: maxmemory-policy, eviction configured",
        ]
