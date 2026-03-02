from app.engine.categories.base import BaseCategoryAnalyzer


class Cat23AimlRisksAnalyzer(BaseCategoryAnalyzer):
    category_id = 23
    name = "AI/ML Model Risks"
    part = "E"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "Direct prompt injection",
            "Indirect prompt injection",
            "Hallucination in high-stakes decisions",
            "Model drift",
            "Training data poisoning",
            "Training data PII leakage",
            "Embedding adversarial attack",
            "Token cost explosion",
            "Guardrail bypass",
            "PII in LLM responses",
            "LLM output not validated before action",
            "No human-in-the-loop",
            "Explainability gap",
            "Model version not pinned",
            "No A/B testing for models",
            "Embedding model change breaks similarity",
            "RAG retrieval poisoning",
            "LLM rate limit hit no fallback",
            "LLM response parsing failure",
            "Sensitive data sent to LLM API",
            "Model evaluation not tracked",
            "Feedback loop missing",
        ]
