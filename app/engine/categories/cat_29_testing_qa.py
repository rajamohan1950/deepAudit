from app.engine.categories.base import BaseCategoryAnalyzer


class Cat29TestingQaAnalyzer(BaseCategoryAnalyzer):
    category_id = 29
    name = "Testing & QA"
    part = "G"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "Unit test coverage unknown",
            "Integration tests missing",
            "E2E tests missing",
            "Contract testing not implemented",
            "Performance testing not automated",
            "Security testing not in pipeline",
            "Fuzz testing missing",
            "Mutation testing not run",
            "Test data management (real PII)",
            "Test environment instability",
            "Test execution too slow",
            "Regression suite incomplete",
            "Edge case coverage",
            "Negative testing",
            "Chaos/fault injection missing",
            "Accessibility testing",
            "API contract versioning not tested",
            "DB migration rollback tested",
            "Config testing",
            "Concurrency testing",
            "Data consistency testing",
            "Visual regression testing",
            "Mobile/responsive testing",
            "Cross-browser testing",
            "Test env doesn't match prod",
        ]
