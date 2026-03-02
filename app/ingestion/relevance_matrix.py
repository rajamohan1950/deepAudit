"""Category-to-file relevance mapping.

Maps each of the 40 audit categories to file types and keyword patterns
that are most relevant for analysis. The Context Builder uses this matrix
to route the right files to the right category's LLM prompt.
"""

from app.ingestion.classifier import FileType

CATEGORY_RELEVANCE: dict[int, dict] = {
    1: {
        "name": "Authentication & Identity",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG, FileType.SECURITY],
        "path_keywords": [
            "auth", "login", "signup", "register", "session", "jwt", "token",
            "oauth", "saml", "oidc", "sso", "mfa", "2fa", "totp", "password",
            "credential", "identity", "passport", "guard",
        ],
        "file_keywords": [
            "middleware", "handler", "controller", "route", "endpoint",
        ],
        "always_include_types": [FileType.SECURITY],
    },
    2: {
        "name": "Authorization & Access Control",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "rbac", "abac", "permission", "policy", "access", "role", "guard",
            "authorize", "acl", "scope", "privilege", "admin",
        ],
        "file_keywords": [
            "middleware", "decorator", "interceptor", "filter", "gate",
        ],
        "always_include_types": [],
    },
    3: {
        "name": "Input Validation & Injection",
        "file_types": [FileType.SOURCE_CODE, FileType.API_SPEC],
        "path_keywords": [
            "validator", "sanitize", "filter", "input", "form", "schema",
            "parser", "serialize", "deserialize", "graphql", "resolver",
        ],
        "file_keywords": [
            "handler", "controller", "route", "endpoint", "api", "view",
        ],
        "always_include_types": [FileType.API_SPEC],
    },
    4: {
        "name": "Data Protection & Privacy",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG, FileType.SECURITY],
        "path_keywords": [
            "encrypt", "decrypt", "pii", "gdpr", "privacy", "mask", "redact",
            "sensitive", "secret", "vault", "kms", "data_protection",
        ],
        "file_keywords": [
            "model", "schema", "migration", "log", "logger",
        ],
        "always_include_types": [FileType.SECURITY],
    },
    5: {
        "name": "Cryptography & Key Management",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG, FileType.SECURITY],
        "path_keywords": [
            "crypto", "cipher", "hash", "tls", "ssl", "cert", "certificate",
            "key", "sign", "verify", "hmac", "aes", "rsa", "ecdsa",
        ],
        "file_keywords": ["security", "util"],
        "always_include_types": [FileType.SECURITY],
    },
    6: {
        "name": "Memory Leaks & Memory Management",
        "file_types": [FileType.SOURCE_CODE, FileType.DOCKER, FileType.K8S],
        "path_keywords": [
            "cache", "pool", "buffer", "stream", "connection", "socket",
            "websocket", "worker", "thread", "event", "listener",
        ],
        "file_keywords": ["main", "app", "server", "client", "manager"],
        "always_include_types": [FileType.DOCKER, FileType.K8S],
    },
    7: {
        "name": "CPU & Compute Performance",
        "file_types": [FileType.SOURCE_CODE],
        "path_keywords": [
            "handler", "controller", "service", "processor", "worker",
            "compute", "algorithm", "search", "sort", "query", "loop",
        ],
        "file_keywords": ["hot", "critical", "core", "engine"],
        "always_include_types": [],
    },
    8: {
        "name": "Network & I/O Performance",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "http", "client", "grpc", "connection", "pool", "retry",
            "timeout", "circuit", "breaker", "dns", "proxy", "load_balance",
        ],
        "file_keywords": ["config", "setting"],
        "always_include_types": [],
    },
    9: {
        "name": "Database & Storage Performance",
        "file_types": [FileType.SOURCE_CODE, FileType.DB_MIGRATION, FileType.CONFIG],
        "path_keywords": [
            "model", "schema", "query", "repository", "dao", "orm",
            "database", "db", "migration", "index", "table",
        ],
        "file_keywords": ["sql", "query", "repository"],
        "always_include_types": [FileType.DB_MIGRATION],
    },
    10: {
        "name": "Caching Performance",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "cache", "redis", "memcache", "cdn", "ttl", "invalidat",
            "warm", "evict",
        ],
        "file_keywords": ["decorator", "middleware"],
        "always_include_types": [],
    },
    11: {
        "name": "OS & Kernel Level",
        "file_types": [FileType.DOCKER, FileType.K8S, FileType.IAC, FileType.CONFIG],
        "path_keywords": [
            "sysctl", "ulimit", "kernel", "cgroup", "numa", "tuning",
            "init", "entrypoint",
        ],
        "file_keywords": ["dockerfile", "node", "system"],
        "always_include_types": [FileType.DOCKER, FileType.K8S],
    },
    12: {
        "name": "Graceful Shutdown & Lifecycle",
        "file_types": [FileType.SOURCE_CODE, FileType.K8S, FileType.DOCKER],
        "path_keywords": [
            "shutdown", "graceful", "signal", "sigterm", "lifecycle",
            "drain", "health", "ready", "liveness", "prestop",
        ],
        "file_keywords": ["main", "app", "server", "entrypoint"],
        "always_include_types": [FileType.K8S],
    },
    13: {
        "name": "Single Points of Failure",
        "file_types": [FileType.IAC, FileType.K8S, FileType.DOCKER, FileType.CONFIG],
        "path_keywords": [
            "infra", "deploy", "cluster", "replica", "failover",
            "redundan", "backup", "standby", "primary", "secondary",
        ],
        "file_keywords": ["terraform", "compose", "manifest"],
        "always_include_types": [FileType.IAC, FileType.K8S, FileType.DOCKER],
    },
    14: {
        "name": "Fault Tolerance & Resilience",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "circuit", "breaker", "retry", "fallback", "resilience",
            "bulkhead", "timeout", "health", "degrade",
        ],
        "file_keywords": ["handler", "middleware", "client"],
        "always_include_types": [],
    },
    15: {
        "name": "Concurrency & Race Conditions",
        "file_types": [FileType.SOURCE_CODE],
        "path_keywords": [
            "lock", "mutex", "semaphore", "atomic", "concurrent",
            "transaction", "idempoten", "saga", "compensat",
        ],
        "file_keywords": ["service", "handler", "worker"],
        "always_include_types": [],
    },
    16: {
        "name": "Data Integrity & Consistency",
        "file_types": [FileType.SOURCE_CODE, FileType.DB_MIGRATION],
        "path_keywords": [
            "calculat", "financial", "money", "currency", "decimal",
            "balance", "transaction", "transfer", "payment", "pricing",
        ],
        "file_keywords": ["model", "schema", "migration", "service"],
        "always_include_types": [FileType.DB_MIGRATION],
    },
    17: {
        "name": "Distributed System Failures",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "distributed", "consensus", "leader", "election", "partition",
            "saga", "event_bus", "service_discovery", "mesh",
        ],
        "file_keywords": ["coordinator", "orchestrator"],
        "always_include_types": [],
    },
    18: {
        "name": "Queue & Event Processing",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "kafka", "rabbit", "sqs", "queue", "consumer", "producer",
            "subscriber", "publisher", "event", "message", "dlq", "dead_letter",
        ],
        "file_keywords": ["worker", "handler", "processor"],
        "always_include_types": [],
    },
    19: {
        "name": "Infrastructure & Cloud Security",
        "file_types": [FileType.IAC, FileType.K8S, FileType.DOCKER, FileType.CONFIG],
        "path_keywords": [
            "iam", "policy", "security_group", "network", "firewall",
            "waf", "vpc", "subnet", "ingress", "egress", "rbac",
        ],
        "file_keywords": ["terraform", "cloudformation", "pulumi"],
        "always_include_types": [FileType.IAC, FileType.K8S, FileType.DOCKER],
    },
    20: {
        "name": "Capacity Planning & Scalability",
        "file_types": [FileType.K8S, FileType.IAC, FileType.CONFIG],
        "path_keywords": [
            "autoscal", "hpa", "vpa", "scaling", "capacity", "resource",
            "limit", "request", "quota", "load_test",
        ],
        "file_keywords": ["manifest", "deployment", "config"],
        "always_include_types": [FileType.K8S, FileType.IAC],
    },
    21: {
        "name": "Deployment, CI/CD & Release",
        "file_types": [FileType.CICD, FileType.DOCKER, FileType.K8S, FileType.BUILD],
        "path_keywords": [
            "deploy", "pipeline", "ci", "cd", "release", "canary",
            "rollback", "workflow", "action", "jenkins", "gitlab",
        ],
        "file_keywords": [],
        "always_include_types": [FileType.CICD, FileType.DOCKER, FileType.BUILD],
    },
    22: {
        "name": "Third-Party & Supply Chain",
        "file_types": [FileType.DEPENDENCY, FileType.LOCKFILE, FileType.CONFIG],
        "path_keywords": ["vendor", "third_party", "external"],
        "file_keywords": [],
        "always_include_types": [FileType.DEPENDENCY, FileType.LOCKFILE],
    },
    23: {
        "name": "AI/ML Model Risks",
        "file_types": [FileType.AI_ML, FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "llm", "openai", "anthropic", "prompt", "embedding", "rag",
            "vector", "model", "ai", "ml", "guardrail", "safety",
            "hallucin", "injection",
        ],
        "file_keywords": ["agent", "chain", "pipeline"],
        "always_include_types": [FileType.AI_ML],
    },
    24: {
        "name": "AI/ML Cost & Operational",
        "file_types": [FileType.AI_ML, FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "token", "cost", "usage", "billing", "tier", "batch",
            "cache", "prompt", "fine_tun", "finetun",
        ],
        "file_keywords": ["llm", "openai", "anthropic", "ai"],
        "always_include_types": [FileType.AI_ML],
    },
    25: {
        "name": "Metrics & Monitoring",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "metric", "monitor", "prometheus", "grafana", "datadog",
            "slo", "sli", "dashboard", "instrument",
        ],
        "file_keywords": ["middleware", "exporter"],
        "always_include_types": [],
    },
    26: {
        "name": "Logging",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "log", "logger", "logging", "syslog", "elk", "fluentd",
            "structured", "audit_log",
        ],
        "file_keywords": ["config", "middleware"],
        "always_include_types": [],
    },
    27: {
        "name": "Distributed Tracing",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "trace", "tracing", "span", "jaeger", "zipkin", "opentelemetry",
            "otel", "correlation", "propagat",
        ],
        "file_keywords": ["middleware", "interceptor"],
        "always_include_types": [],
    },
    28: {
        "name": "Alerting & Incident Response",
        "file_types": [FileType.CONFIG, FileType.DOCUMENTATION, FileType.SOURCE_CODE],
        "path_keywords": [
            "alert", "pagerduty", "opsgenie", "runbook", "incident",
            "oncall", "escalat", "notify", "webhook",
        ],
        "file_keywords": [],
        "always_include_types": [FileType.DOCUMENTATION],
    },
    29: {
        "name": "Testing & QA",
        "file_types": [FileType.TEST, FileType.CICD, FileType.CONFIG],
        "path_keywords": [
            "test", "spec", "fixture", "mock", "stub", "coverage",
            "pytest", "jest", "mocha", "cypress", "playwright",
        ],
        "file_keywords": [],
        "always_include_types": [FileType.TEST, FileType.CICD],
    },
    30: {
        "name": "Code Quality & Technical Debt",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG, FileType.BUILD],
        "path_keywords": [
            "lint", "format", "sonar", "eslint", "pylint", "ruff",
            "pre-commit", "husky",
        ],
        "file_keywords": [".eslintrc", ".prettierrc", "sonar", "ruff.toml"],
        "always_include_types": [FileType.CONFIG],
    },
    31: {
        "name": "API Design & Contracts",
        "file_types": [FileType.API_SPEC, FileType.SOURCE_CODE],
        "path_keywords": [
            "api", "openapi", "swagger", "graphql", "grpc", "proto",
            "version", "v1", "v2", "route", "endpoint",
        ],
        "file_keywords": ["router", "controller", "handler"],
        "always_include_types": [FileType.API_SPEC],
    },
    32: {
        "name": "UX, Accessibility & Client-Side",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "component", "page", "layout", "form", "error", "loading",
            "csp", "cors", "csrf", "helmet", "accessibility", "a11y",
        ],
        "file_keywords": ["tsx", "jsx", "vue", "svelte", "html"],
        "always_include_types": [],
    },
    33: {
        "name": "Cost & FinOps",
        "file_types": [FileType.IAC, FileType.K8S, FileType.CONFIG],
        "path_keywords": [
            "cost", "budget", "billing", "pricing", "instance",
            "storage", "reserved", "spot", "preemptible",
        ],
        "file_keywords": ["terraform", "cloudformation"],
        "always_include_types": [FileType.IAC, FileType.K8S],
    },
    34: {
        "name": "Multi-Tenancy & Isolation",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG, FileType.DB_MIGRATION],
        "path_keywords": [
            "tenant", "organization", "workspace", "isolation",
            "multi_tenant", "partition", "shard",
        ],
        "file_keywords": ["model", "middleware", "filter", "context"],
        "always_include_types": [],
    },
    35: {
        "name": "Compliance & Regulatory",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG, FileType.DOCUMENTATION],
        "path_keywords": [
            "audit", "compliance", "gdpr", "hipaa", "soc2", "pci",
            "consent", "retention", "erasure", "dpa",
        ],
        "file_keywords": ["policy", "control"],
        "always_include_types": [FileType.DOCUMENTATION],
    },
    36: {
        "name": "Disaster Recovery",
        "file_types": [FileType.IAC, FileType.CONFIG, FileType.DOCUMENTATION],
        "path_keywords": [
            "backup", "restore", "disaster", "recovery", "failover",
            "replication", "geo", "dr", "rto", "rpo",
        ],
        "file_keywords": [],
        "always_include_types": [FileType.IAC, FileType.DOCUMENTATION],
    },
    37: {
        "name": "Internationalization & Localization",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "i18n", "l10n", "locale", "translation", "intl",
            "timezone", "currency", "format", "rtl",
        ],
        "file_keywords": [],
        "always_include_types": [],
    },
    38: {
        "name": "State Management",
        "file_types": [FileType.SOURCE_CODE, FileType.CONFIG],
        "path_keywords": [
            "session", "state", "store", "redux", "zustand", "context",
            "websocket", "workflow", "machine", "fsm",
        ],
        "file_keywords": ["handler", "manager"],
        "always_include_types": [],
    },
    39: {
        "name": "Backward Compatibility & Migration",
        "file_types": [FileType.SOURCE_CODE, FileType.DB_MIGRATION, FileType.API_SPEC],
        "path_keywords": [
            "migration", "upgrade", "deprecat", "version", "compat",
            "legacy", "v1", "v2",
        ],
        "file_keywords": [],
        "always_include_types": [FileType.DB_MIGRATION, FileType.API_SPEC],
    },
    40: {
        "name": "Organizational & Knowledge",
        "file_types": [FileType.DOCUMENTATION, FileType.CONFIG, FileType.CICD],
        "path_keywords": [
            "readme", "contributing", "codeowners", "adr",
            "runbook", "onboard", "offboard", "oncall",
        ],
        "file_keywords": [],
        "always_include_types": [FileType.DOCUMENTATION, FileType.CICD],
    },
}
