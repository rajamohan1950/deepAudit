import json
import logging
import time
from dataclasses import dataclass, field

import anthropic
import openai

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_COSTS_PER_1K = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
}


@dataclass
class LLMResponse:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    latency_ms: int = 0


@dataclass
class LLMUsageTracker:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    calls: list[dict] = field(default_factory=list)

    def record(self, response: LLMResponse, category_id: int | None = None):
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self.total_cost_usd += response.cost_usd
        self.call_count += 1
        self.calls.append({
            "category_id": category_id,
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd,
            "latency_ms": response.latency_ms,
        })


class LLMClient:
    """Unified client for OpenAI and Anthropic APIs."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider or settings.default_llm_provider
        self.model = model or settings.default_llm_model

        if self.provider == "openai":
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            self.anthropic_client = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key
            )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 16000,
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> LLMResponse:
        start = time.monotonic()
        attempt = 0
        max_retries = settings.llm_max_retries

        while attempt <= max_retries:
            try:
                if self.provider == "openai":
                    response = await self._call_openai(
                        system_prompt, user_prompt, max_tokens, temperature, json_mode
                    )
                elif self.provider == "anthropic":
                    response = await self._call_anthropic(
                        system_prompt, user_prompt, max_tokens, temperature
                    )
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")

                response.latency_ms = int((time.monotonic() - start) * 1000)
                response.cost_usd = self._calculate_cost(
                    response.input_tokens, response.output_tokens
                )
                return response

            except (openai.RateLimitError, anthropic.RateLimitError):
                attempt += 1
                wait = min(2 ** attempt, 60)
                logger.warning(
                    f"Rate limited by {self.provider}, retry {attempt}/{max_retries} "
                    f"in {wait}s"
                )
                import asyncio
                await asyncio.sleep(wait)

            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    logger.error(f"LLM call failed after {max_retries} retries: {e}")
                    raise
                logger.warning(f"LLM call error (attempt {attempt}): {e}")
                import asyncio
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"LLM call failed after {max_retries} retries")

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await self.openai_client.chat.completions.create(**kwargs)
        choice = resp.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            total_tokens=resp.usage.total_tokens if resp.usage else 0,
            model=self.model,
        )

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        resp = await self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = ""
        for block in resp.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            total_tokens=resp.usage.input_tokens + resp.usage.output_tokens,
            model=self.model,
        )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        costs = MODEL_COSTS_PER_1K.get(self.model, {"input": 0.01, "output": 0.03})
        return (
            (input_tokens / 1000) * costs["input"]
            + (output_tokens / 1000) * costs["output"]
        )
