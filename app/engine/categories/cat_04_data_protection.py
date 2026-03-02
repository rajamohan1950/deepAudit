from app.engine.categories.base import BaseCategoryAnalyzer


class Cat04DataProtectionAnalyzer(BaseCategoryAnalyzer):
    category_id = 4
    name = "Data Protection & Privacy"
    part = "A"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Audit encryption at rest: database, volumes, backups use AES-256 or equivalent",
            "Audit encryption in transit: TLS 1.2+ for all external and internal traffic",
            "Audit key management: HSM or KMS, key rotation, separation of duties",
            "Audit PII inventory: catalog of all PII fields, retention, and purpose",
            "Audit data masking in non-prod: PII redacted or tokenized in dev/staging",
            "Audit PII in logs/errors: no SSN, credit card, passwords in log output",
            "Audit sensitive data in URLs: tokens, IDs in path/query use POST or headers",
            "Audit client-side storage: localStorage/sessionStorage for sensitive data",
            "Audit data retention enforcement: automated deletion per policy",
            "Audit backup encryption: backups encrypted with strong keys",
            "Audit secrets management: Vault, AWS Secrets Manager, no env vars for prod secrets",
            "Audit secrets in git history: no credentials committed, scan for leaks",
            "Audit API response over-fetching: return only requested/needed fields",
            "Audit cache headers for sensitive data: no-store, no-cache for PII responses",
            "Audit CDN cache poisoning: vary headers, cache keys exclude user-specific data",
            "Audit audit trail for data access: who accessed what PII and when",
            "Audit cross-border data transfer: GDPR, adequacy decisions, transfer mechanisms",
            "Audit right to portability: export in machine-readable format",
            "Audit anonymization effectiveness: k-anonymity, re-identification risk",
            "Audit vendor data sharing: DPA, purpose limitation, subprocessor list",
            "Audit data in message queues: encryption, retention, consumer access control",
            "Audit temporary file cleanup: secure delete, no PII in temp paths",
        ]
