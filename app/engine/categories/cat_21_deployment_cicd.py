from app.engine.categories.base import BaseCategoryAnalyzer


class Cat21DeploymentCicdAnalyzer(BaseCategoryAnalyzer):
    category_id = 21
    name = "Deployment, CI/CD & Release"
    part = "D"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Manual deployment",
            "No rollback capability",
            "No canary/blue-green/rolling",
            "DB migration not backward compatible",
            "DDL migration locks table",
            "No smoke test post-deploy",
            "No health check validation after deploy",
            "Environment drift",
            "Secrets in deployment manifests",
            "No artifact signing",
            "CI/CD overprivileged credentials",
            "No branch protection",
            "No code review enforcement",
            "Build not reproducible",
            "Dependencies not pinned",
            "No SBOM generated",
            "Stale feature flags",
            "Feature flag evaluation performance",
            "Hotfix process undefined",
            "Deployment metrics not tracked (DORA)",
            "Config change not versioned",
        ]
