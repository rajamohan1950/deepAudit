from app.engine.categories.base import BaseCategoryAnalyzer


class Cat24AimlOperationsAnalyzer(BaseCategoryAnalyzer):
    category_id = 24
    name = "AI/ML Cost & Operational"
    part = "E"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "No token usage monitoring",
            "No cost alerting",
            "Prompt not optimized",
            "No prompt caching",
            "No model tiering",
            "No batch processing for non-real-time",
            "Fine-tune hosting cost untracked",
            "Embedding recomputation waste",
            "LLM retry without cost consideration",
            "No cost allocation per tenant",
            "Context window waste",
            "Streaming not used",
            "Model output not cached",
            "LLM call timeout too generous",
            "No shadow/evaluation mode",
        ]
