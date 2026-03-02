from app.engine.categories.base import BaseCategoryAnalyzer


class Cat02AuthorizationAnalyzer(BaseCategoryAnalyzer):
    category_id = 2
    name = "Authorization & Access Control"
    part = "A"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Audit RBAC/ABAC/ReBAC completeness: all resources have explicit policy coverage",
            "Audit authorization at every layer: API, service, database, and UI",
            "Audit IDOR on ALL endpoints: validate resource ownership before access",
            "Audit horizontal escalation: user A cannot access user B's resources",
            "Audit vertical escalation: non-admin cannot access admin-only functions",
            "Audit missing function-level access control: every endpoint enforces auth",
            "Audit mass assignment/overposting: whitelist allowed fields, reject extra",
            "Audit GraphQL field-level auth: resolvers enforce per-field permissions",
            "Audit file/blob access control: signed URLs, ownership checks, path validation",
            "Audit admin panel isolation: separate auth, network segmentation, audit logging",
            "Audit cross-tenant data access: tenant ID in every query and filter",
            "Audit permission inheritance flaws: child resources inherit parent checks",
            "Audit TOCTOU in auth checks: validate at use time, not just at entry",
            "Audit implicit microservice trust: internal APIs require auth, not just network",
            "Audit database row-level security: RLS policies for multi-tenant tables",
            "Audit API versioning bypass: deprecated versions enforce same auth",
            "Audit feature flag auth bypass: flags do not skip authorization checks",
            "Audit webhook signature verification: HMAC or signature validation on receipt",
            "Audit batch/bulk operation auth: each item validated for user permission",
            "Audit OAuth scope validation: requested scope matches required scope",
            "Audit path-based authorization bypass: path params validated for ownership",
        ]
