from app.engine.categories.base import BaseCategoryAnalyzer


class Cat08NetworkIoAnalyzer(BaseCategoryAnalyzer):
    category_id = 8
    name = "Network & I/O Performance"
    part = "B"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Audit connection pool sizing: match concurrency, avoid exhaustion",
            "Audit connection pool leak: connections returned to pool, timeout on checkout",
            "Audit TCP tuning: keepalive, buffer sizes, Nagle for latency-sensitive",
            "Audit DNS resolution latency: caching, prefetch, connection reuse",
            "Audit TLS overhead: session resumption, OCSP stapling, connection reuse",
            "Audit HTTP keep-alive: persistent connections, Connection header handling",
            "Audit chatty protocols: batch requests, reduce round-trips",
            "Audit head-of-line blocking: HTTP/2, multiplexing, or parallel connections",
            "Audit timeout misconfiguration: connect, read, write timeouts set appropriately",
            "Audit socket exhaustion: connection limits, reuse, proper close",
            "Audit retry amplification: exponential backoff, jitter, max retries",
            "Audit circuit breaker missing: failure threshold, half-open, recovery",
            "Audit LB health check misconfiguration: interval, timeout, unhealthy threshold",
            "Audit gRPC keepalive: keepalive time, permit without stream",
            "Audit WebSocket ping/pong: heartbeat to detect dead connections",
            "Audit MTU/MSS issues: fragmentation, jumbo frames where applicable",
            "Audit bandwidth monitoring: throttling, rate limits, backpressure",
            "Audit proxy/sidecar overhead: connection pooling, caching",
            "Audit connection draining: graceful shutdown, in-flight request completion",
            "Audit DNS TTL: balance freshness vs resolution overhead",
            "Audit TCP connection backlog: listen backlog for high connection rate",
        ]
