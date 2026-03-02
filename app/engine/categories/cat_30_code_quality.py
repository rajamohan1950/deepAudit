from app.engine.categories.base import BaseCategoryAnalyzer


class Cat30CodeQualityAnalyzer(BaseCategoryAnalyzer):
    category_id = 30
    name = "Code Quality & Technical Debt"
    part = "G"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "No static analysis",
            "High cyclomatic complexity",
            "Dead code and unused deps",
            "Duplicated code",
            "Missing documentation",
            "Missing comments for complex logic",
            "Inconsistent coding standards",
            "Error handling inconsistency",
            "Generic exception catch",
            "Resource cleanup missing",
            "Magic numbers/strings",
            "God classes/functions",
            "Circular dependencies",
            "Deprecated API usage",
            "Framework version inconsistency",
            "Dependency version not pinned",
            "Build not reproducible",
            "Git hygiene",
            "No pre-commit hooks",
            "TODO/FIXME growing",
            "No ADRs",
        ]
