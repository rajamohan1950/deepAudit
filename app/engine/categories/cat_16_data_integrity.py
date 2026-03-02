from app.engine.categories.base import BaseCategoryAnalyzer


class Cat16DataIntegrityAnalyzer(BaseCategoryAnalyzer):
    category_id = 16
    name = "Data Integrity & Consistency"
    part = "C"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Floating-point for financial",
            "Integer overflow",
            "Currency rounding",
            "Eventual consistency visible",
            "Write ordering not guaranteed",
            "Schema migration data corruption",
            "Orphaned records",
            "Referential integrity app-only",
            "UUID collision",
            "Timestamp precision bugs",
            "Timezone handling",
            "Character encoding",
            "Null handling inconsistency",
            "Off-by-one pagination",
            "Data truncation silent",
            "Sorting locale bugs",
            "Enum addition breaking compat",
            "Proto/Avro schema evolution",
            "CQRS read model divergence",
            "ETL data loss",
            "Deleted data in search/cache",
            "Soft delete inconsistency",
        ]
