from app.engine.categories.base import BaseCategoryAnalyzer


class Cat07CpuComputeAnalyzer(BaseCategoryAnalyzer):
    category_id = 7
    name = "CPU & Compute Performance"
    part = "B"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Audit O(n²) in business logic: nested loops over collections, optimize or index",
            "Audit O(n²) in ORM: N+1, Cartesian products, eager loading strategy",
            "Audit unnecessary serialization: avoid repeated JSON encode/decode in loops",
            "Audit regex catastrophic backtracking: linear-time patterns, input length limits",
            "Audit sync blocking in async context: run_in_executor for CPU-bound work",
            "Audit thread pool exhaustion: pool sizing, timeout, bounded queues",
            "Audit event loop blocking: no long CPU work on main loop",
            "Audit spin locks: use proper mutex/semaphore, avoid busy-wait",
            "Audit excessive logging in hot paths: log level, sampling, async logging",
            "Audit reflection overhead: cache reflected metadata, avoid per-request reflection",
            "Audit unoptimized DB queries: missing indexes, full scans, redundant joins",
            "Audit missing EXPLAIN ANALYZE: query plans reviewed for production queries",
            "Audit wrong data structure: list vs set vs dict for lookup/insert patterns",
            "Audit excessive object creation: object pooling, reuse in hot paths",
            "Audit missing connection pooling: pool size, validation, timeout",
            "Audit DNS resolution per request: cache DNS, connection reuse",
            "Audit TLS handshake per request: connection reuse, session resumption",
            "Audit inefficient pagination: keyset/offset, avoid OFFSET on large tables",
            "Audit CPU-bound on I/O threads: offload to worker pool",
            "Audit missing response compression: gzip/brotli for text responses",
            "Audit cold start latency: lazy init, keep-warm, provisioned concurrency",
            "Audit excessive middleware: chain length, per-request overhead",
            "Audit JSON schema validation overhead: validate once, cache compiled schema",
            "Audit sorting in app instead of DB: ORDER BY in query, use indexes",
        ]
