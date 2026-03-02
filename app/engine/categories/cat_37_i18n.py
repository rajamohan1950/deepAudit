from app.engine.categories.base import BaseCategoryAnalyzer


class Cat37I18nAnalyzer(BaseCategoryAnalyzer):
    category_id = 37
    name = "Internationalization & Localization"
    part = "H"
    min_signals = 10

    def get_checklist(self) -> list[str]:
        return [
            "Date format not locale-aware",
            "Currency handling incorrect",
            "Number formatting locale-dependent",
            "Character encoding issues",
            "Email/SMS templates not localized",
            "Error messages hardcoded in English",
            "RTL text layout not supported",
            "Sorting locale-unaware (Turkish İ)",
            "Address format assumptions",
            "Phone number format assumptions",
            "Timezone display not user-configurable",
        ]
