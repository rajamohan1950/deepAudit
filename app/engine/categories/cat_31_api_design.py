from app.engine.categories.base import BaseCategoryAnalyzer


class Cat31ApiDesignAnalyzer(BaseCategoryAnalyzer):
    category_id = 31
    name = "API Design & Contracts"
    part = "G"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "No versioning strategy",
            "Inconsistent response format",
            "Missing pagination on list endpoints",
            "Rate limiting missing/bypassable",
            "No OpenAPI/Swagger documentation",
            "Missing error codes (generic 500)",
            "Idempotency keys not supported",
            "No deprecation strategy",
            "GraphQL query depth/complexity not limited",
            "WebSocket message validation missing",
            "Missing correlation ID in headers",
            "No request timeout on client side",
            "Missing Retry-After on 429",
            "No API changelog",
            "Breaking change detection not automated",
        ]
