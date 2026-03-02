from app.engine.categories.base import BaseCategoryAnalyzer


class Cat19InfraSecurityAnalyzer(BaseCategoryAnalyzer):
    category_id = 19
    name = "Infrastructure & Cloud Security"
    part = "D"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "IAM over-permissioned",
            "Service account key exposure",
            "Network segmentation missing",
            "K8s RBAC too permissive",
            "K8s pod security",
            "K8s network policies missing",
            "K8s secrets unencrypted",
            "Container vulnerabilities",
            "Container running as root",
            "Container writable root filesystem",
            "Storage bucket public access",
            "Database with public IP",
            "Database SSL not enforced",
            "WAF rules incomplete",
            "DNS zone transfer",
            "Subdomain takeover",
            "Cloud metadata exposure",
            "IaC drift",
            "CI/CD pipeline secrets leak",
            "Supply chain attack surface",
            "Container registry without scanning",
            "SSH keys shared",
            "Egress unrestricted",
            "Managed identity not used",
            "Public management ports",
        ]
