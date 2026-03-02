from app.engine.categories.base import BaseCategoryAnalyzer


class Cat03InputValidationAnalyzer(BaseCategoryAnalyzer):
    category_id = 3
    name = "Input Validation & Injection"
    part = "A"
    min_signals = 30

    def get_checklist(self) -> list[str]:
        return [
            "Audit SQL injection: all dialects (MySQL, PostgreSQL, SQLite, etc.) use parameterization",
            "Audit NoSQL injection: MongoDB, DynamoDB, etc. use safe query builders",
            "Audit command injection: shell exec, subprocess, system calls sanitize input",
            "Audit XSS stored: output encoding, CSP, and input sanitization",
            "Audit XSS reflected: URL/query params encoded before rendering",
            "Audit XSS DOM-based: avoid unsafe eval, innerHTML, document.write",
            "Audit SSRF: URL fetchers validate scheme, host allowlist, block internal IPs",
            "Audit XXE: disable external entities, DTD processing in XML parsers",
            "Audit SSTI: template engines do not evaluate user input as code",
            "Audit LDAP/XPath injection: parameterized queries or input sanitization",
            "Audit HTTP header injection: CRLF in headers, Host header manipulation",
            "Audit log injection: newlines, control chars sanitized before logging",
            "Audit deserialization: safe parsers, no pickle/yaml.load of untrusted data",
            "Audit ReDoS: regex patterns avoid catastrophic backtracking",
            "Audit Unicode bypass: normalization, homograph attacks in validation",
            "Audit Content-Type confusion: validate MIME type, ignore client-supplied type",
            "Audit CSV/formula injection: escape leading +, -, =, @ in spreadsheet exports",
            "Audit GraphQL abuse: depth limits, complexity analysis, query allowlisting",
            "Audit PDF generation injection: user input not passed to PDF renderer unsanitized",
            "Audit email injection: headers, body validated for CRLF and header injection",
            "Audit CORS: origin validation, credentials handling, wildcard misuse",
            "Audit prototype pollution: object merge/assign sanitizes __proto__ and constructor",
            "Audit HTTP request smuggling: Content-Length vs Transfer-Encoding handling",
            "Audit HTTP parameter pollution: duplicate params handled consistently",
            "Audit file upload vulnerabilities: type validation, extension, magic bytes, path traversal",
            "Audit JSON/XML bomb: size limits, depth limits, entity expansion",
            "Audit integer overflow: bounds checking, safe arithmetic for user-controlled numbers",
            "Audit business logic injection: workflow/state transitions validate input",
            "Audit open redirect: redirect URLs validated against allowlist",
            "Audit WebSocket injection: message content sanitized before processing",
            "Audit DNS rebinding SSRF: resolve and validate before connecting",
            "Audit HTTP verb tampering: method override headers, TRACE enabled",
        ]
