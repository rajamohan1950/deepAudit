import logging
from pathlib import Path

from app.ingestion.chunker import CodeChunker
from app.ingestion.relevance_matrix import CATEGORY_RELEVANCE

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_BUDGET = 80_000
APPROX_CHARS_PER_TOKEN = 4


class ContextBundle:
    """Files and context prepared for a specific category's LLM prompt."""

    def __init__(self, category_id: int, category_name: str):
        self.category_id = category_id
        self.category_name = category_name
        self.files: list[dict] = []
        self.total_tokens: int = 0
        self.git_insights: dict = {}

    def add_file(self, path: str, content: str, relevance_score: float):
        tokens = len(content) // APPROX_CHARS_PER_TOKEN
        self.files.append({
            "path": path,
            "content": content,
            "relevance_score": relevance_score,
            "tokens": tokens,
        })
        self.total_tokens += tokens

    def to_prompt_context(self) -> str:
        parts = []
        for f in self.files:
            parts.append(f"--- FILE: {f['path']} ---")
            parts.append(f["content"])
            parts.append("")
        return "\n".join(parts)


class ContextBuilder:
    """Routes relevant files to each category, respecting token budgets."""

    def __init__(self, token_budget: int = DEFAULT_TOKEN_BUDGET):
        self.token_budget = token_budget
        self.chunker = CodeChunker()

    def build_context(
        self,
        category_id: int,
        classified_files: list[dict],
        git_analysis: dict | None = None,
    ) -> ContextBundle:
        if category_id not in CATEGORY_RELEVANCE:
            raise ValueError(f"Unknown category ID: {category_id}")

        cat_config = CATEGORY_RELEVANCE[category_id]
        bundle = ContextBundle(category_id, cat_config["name"])

        if git_analysis:
            bundle.git_insights = {
                "bus_factor": git_analysis.get("bus_factor", 0),
                "secrets_found_count": len(git_analysis.get("secrets_found", [])),
                "high_churn_files": git_analysis.get("high_churn_files", [])[:5],
            }

        scored_files = self._score_files(classified_files, cat_config, git_analysis)
        scored_files.sort(key=lambda x: x["relevance_score"], reverse=True)

        budget_chars = self.token_budget * APPROX_CHARS_PER_TOKEN
        used_chars = 0

        for sf in scored_files:
            content = sf.get("content")
            if not content:
                try:
                    content = Path(sf["absolute_path"]).read_text(
                        encoding="utf-8", errors="ignore"
                    )
                except Exception:
                    continue

            if used_chars + len(content) > budget_chars:
                remaining = budget_chars - used_chars
                if remaining > 500:
                    chunks = self.chunker.chunk_file(content, sf.get("language"))
                    for chunk in chunks:
                        if used_chars + len(chunk) <= budget_chars:
                            bundle.add_file(
                                sf["path"], chunk, sf["relevance_score"]
                            )
                            used_chars += len(chunk)
                        else:
                            break
                break

            bundle.add_file(sf["path"], content, sf["relevance_score"])
            used_chars += len(content)

        logger.info(
            f"Cat {category_id} ({cat_config['name']}): "
            f"{len(bundle.files)} files, ~{bundle.total_tokens} tokens"
        )
        return bundle

    def _score_files(
        self,
        files: list[dict],
        cat_config: dict,
        git_analysis: dict | None,
    ) -> list[dict]:
        scored = []
        high_churn = set()
        if git_analysis:
            for hc in git_analysis.get("high_churn_files", []):
                high_churn.add(hc["path"])

        for f in files:
            score = 0.0
            file_type = f.get("file_type", "")
            path_lower = f["path"].lower()
            name_lower = Path(f["path"]).name.lower()

            if file_type in cat_config.get("always_include_types", []):
                score += 10.0

            if file_type in cat_config.get("file_types", []):
                score += 3.0

            for kw in cat_config.get("path_keywords", []):
                if kw in path_lower:
                    score += 5.0
                    break

            for kw in cat_config.get("file_keywords", []):
                if kw in name_lower:
                    score += 2.0
                    break

            if f["path"] in high_churn:
                score += 1.5

            entry_names = {"main", "app", "server", "index", "startup", "bootstrap"}
            stem = Path(f["path"]).stem.lower()
            if stem in entry_names:
                score += 1.0

            if score > 0:
                f_copy = dict(f)
                f_copy["relevance_score"] = score
                scored.append(f_copy)

        return scored
