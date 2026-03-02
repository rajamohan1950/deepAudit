from app.engine.categories.base import BaseCategoryAnalyzer


class Cat09DatabaseAnalyzer(BaseCategoryAnalyzer):
    category_id = 9
    name = "Database & Storage Performance"
    part = "B"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "Audit missing indexes: columns in WHERE, JOIN, ORDER BY have indexes",
            "Audit unused indexes: remove indexes that are never used",
            "Audit N+1 query pattern: batch loads, eager loading, JOIN FETCH",
            "Audit full table scan: queries use indexes, avoid SELECT * on large tables",
            "Audit missing query parameterization: prepared statements, no string concat",
            "Audit lock contention: row-level locks, avoid long-held locks",
            "Audit long-running transactions: shorten scope, avoid holding across I/O",
            "Audit connection pool exhaustion: pool size, max wait, validation query",
            "Audit no slow query monitoring: log queries > threshold, alert",
            "Audit missing statement timeout: query timeout to prevent runaway queries",
            "Audit table bloat: VACUUM, analyze bloat, partitioning",
            "Audit missing partition strategy: partition by date/range for large tables",
            "Audit replication lag: read-after-write consistency, lag monitoring",
            "Audit no read replica routing: route reads to replicas, writes to primary",
            "Audit missing query caching: cache hot queries, invalidate on write",
            "Audit WAL growth: checkpoint tuning, archive, retention",
            "Audit backup never tested: restore drills, backup verification",
            "Audit schema migration locks: online migrations, lock timeout",
            "Audit unencrypted DB connections: TLS for client-to-DB traffic",
            "Audit cursor leak: cursors closed, context managers",
            "Audit missing connection validation: test on checkout, evict stale",
            "Audit inefficient JSONB queries: GIN indexes, containment operators",
            "Audit missing materialized views: for expensive aggregations",
            "Audit write amplification: batch inserts, bulk operations",
            "Audit sequential scan: index usage, statistics up to date",
            "Audit no per-endpoint query timeout: endpoint-specific limits",
            "Audit auto-vacuum misconfigured: scale factor, threshold for busy tables",
        ]
