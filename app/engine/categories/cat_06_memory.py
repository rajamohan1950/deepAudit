from app.engine.categories.base import BaseCategoryAnalyzer


class Cat06MemoryAnalyzer(BaseCategoryAnalyzer):
    category_id = 6
    name = "Memory Leaks & Management"
    part = "B"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "Audit heap memory leaks: objects not released, growing collections",
            "Audit native/off-heap leaks: C extensions, JNI, FFI allocations",
            "Audit event listener leaks: addEventListener without removeEventListener",
            "Audit closure/callback leaks: closures holding large references",
            "Audit cache unbounded growth: LRU, TTL, or size limits on caches",
            "Audit connection object leaks: connections not closed in finally/with",
            "Audit stream/file handle leaks: streams closed in finally or context managers",
            "Audit buffer pool exhaustion: buffers returned to pool, no permanent retention",
            "Audit thread/goroutine leaks: threads joined, goroutines have exit conditions",
            "Audit string interning abuse: unbounded intern cache growth",
            "Audit static collection growth: module-level lists/maps without bounds",
            "Audit circular references: cycles preventing GC in reference-counted runtimes",
            "Audit memory fragmentation: large contiguous allocations in long-running processes",
            "Audit OOM killer behavior: graceful degradation, circuit breakers before OOM",
            "Audit container memory limit mismatch: limits align with process expectations",
            "Audit K8s OOMKilled masking: identify root cause, not just pod restart",
            "Audit memory-mapped file leaks: mmap unmapped when done",
            "Audit large object allocation in hot path: move to cold path or pool",
            "Audit finalizer queue backup: finalizers not blocking GC",
            "Audit session object bloat: session size limits, cleanup of stale sessions",
            "Audit middleware state accumulation: per-request state cleared",
            "Audit image/doc processing without streaming: avoid loading full file into memory",
            "Audit WebSocket connection accumulation: idle timeout, max connections",
            "Audit metrics cardinality explosion: limit label combinations, aggregation",
            "Audit gRPC channel leak: channels properly closed, connection pooling",
            "Audit DNS resolver cache growth: TTL, max cache size",
            "Audit embedding vector cache growth: eviction policy, size limits",
        ]
