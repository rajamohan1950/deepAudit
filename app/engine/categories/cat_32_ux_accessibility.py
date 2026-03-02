from app.engine.categories.base import BaseCategoryAnalyzer


class Cat32UxAccessibilityAnalyzer(BaseCategoryAnalyzer):
    category_id = 32
    name = "UX, Accessibility & Client-Side"
    part = "G"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Client-side error handling (white screen, spinner forever)",
            "No client-side input validation",
            "Sensitive data in browser (localStorage, console.log)",
            "CSRF protection missing",
            "Clickjacking (X-Frame-Options, CSP)",
            "CSP missing/permissive",
            "Subresource Integrity missing for CDN",
            "Mixed content",
            "WCAG 2.1 AA violations",
            "JavaScript bundle too large",
            "Third-party script risk",
            "Session timeout UX (no warning, data loss)",
            "Error messages not helpful",
            "Loading states missing (double submit)",
            "Offline/poor network handling",
        ]
