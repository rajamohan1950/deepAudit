"""Base class for all 40 category analyzers."""

import logging
from abc import ABC, abstractmethod

from app.engine.llm.client import LLMClient, LLMResponse
from app.engine.llm.response_parser import ParsedSignal, ResponseParser
from app.ingestion.context_builder import ContextBundle

logger = logging.getLogger(__name__)


class BaseCategoryAnalyzer(ABC):
    """Abstract base for category-specific audit analyzers.

    Each subclass defines:
    - category_id, name, part, min_signals
    - The checklist of specific things to audit
    - How to build the prompt for the LLM
    """

    category_id: int
    name: str
    part: str
    min_signals: int
    checklist: list[str] = []

    def __init__(self):
        self.parser = ResponseParser()

    @abstractmethod
    def get_checklist(self) -> list[str]:
        """Return the list of specific checks for this category."""
        ...

    def build_category_prompt(
        self,
        system_context: dict,
        context_bundle: ContextBundle,
    ) -> str:
        checklist = self.get_checklist()
        checklist_text = "\n".join(f"  - {item}" for item in checklist)

        code_context = context_bundle.to_prompt_context()

        prompt = f"""## CATEGORY {self.category_id}: {self.name}

Analyze the provided code and configuration for this category.
Produce a MINIMUM of {self.min_signals} specific, actionable signals.

### Checklist — audit EVERY item:
{checklist_text}

### Git Repository Insights:
- Bus Factor: {context_bundle.git_insights.get('bus_factor', 'Unknown')}
- Potential secrets in repo: {context_bundle.git_insights.get('secrets_found_count', 0)}
- High-churn files: {', '.join(f.get('path', '') for f in context_bundle.git_insights.get('high_churn_files', [])[:5]) or 'None identified'}

### Files to Analyze ({len(context_bundle.files)} files, ~{context_bundle.total_tokens} tokens):

{code_context}

### Output Requirements:
Return a JSON object with a "signals" array. Each signal MUST have:
- "signal_text": Specific finding with technical detail (min 20 chars)
- "severity": "P0" | "P1" | "P2" | "P3"
- "score": 0.0-10.0 (CVSS 3.1 for security cats 1-5,19; Risk 1-10 otherwise)
- "score_type": "cvss" | "risk"
- "evidence": File path, line number, config name, service (SPECIFIC)
- "failure_scenario": Exactly HOW this breaks or gets exploited
- "remediation": Specific implementation fix (NOT vague "improve" or "consider")
- "effort": "S" (hours) | "M" (days) | "L" (weeks) | "XL" (months)
- "confidence": 0.0-1.0
- "references": ["OWASP-xxx", "CIS-xxx", "NIST-xxx"] (optional)

REJECTED signals: missing evidence, vague remediation, no failure scenario, too short.
"""
        return prompt

    async def analyze(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        system_context: dict,
        context_bundle: ContextBundle,
    ) -> tuple[list[ParsedSignal], LLMResponse]:
        user_prompt = self.build_category_prompt(system_context, context_bundle)

        response = await llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=16000,
            temperature=0.1,
            json_mode=True,
        )

        signals = self.parser.parse(response.content, self.category_id)

        logger.info(
            f"Cat {self.category_id} ({self.name}): "
            f"{len(signals)} signals, "
            f"{response.total_tokens} tokens, "
            f"${response.cost_usd:.4f}"
        )

        return signals, response
