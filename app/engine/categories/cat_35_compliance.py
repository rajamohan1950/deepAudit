from app.engine.categories.base import BaseCategoryAnalyzer


class Cat35ComplianceAnalyzer(BaseCategoryAnalyzer):
    category_id = 35
    name = "Compliance & Regulatory"
    part = "H"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Audit trail not immutable",
            "Non-repudiation not implemented",
            "Regulatory reporting not automated",
            "Data retention not enforced by automation",
            "Right to erasure not fully implemented",
            "Consent management incomplete",
            "Third-party vendor compliance unverified",
            "Penetration test not performed",
            "SOC2 evidence manual",
            "No compliance-as-code",
            "Access review not regular",
            "Segregation of duties violated",
            "Change management not documented",
            "Business continuity plan not tested",
            "Data classification not enforced",
        ]
