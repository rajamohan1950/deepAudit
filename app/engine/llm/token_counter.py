import logging

logger = logging.getLogger(__name__)

try:
    import tiktoken
    _ENCODER = tiktoken.encoding_for_model("gpt-4o")
except Exception:
    _ENCODER = None
    logger.warning("tiktoken not available, using approximate token counting")


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    if _ENCODER:
        try:
            return len(_ENCODER.encode(text))
        except Exception:
            pass
    return len(text) // 4


def fits_in_budget(text: str, budget: int, model: str = "gpt-4o") -> bool:
    return count_tokens(text, model) <= budget


def truncate_to_budget(text: str, budget: int, model: str = "gpt-4o") -> str:
    current = count_tokens(text, model)
    if current <= budget:
        return text

    ratio = budget / current
    target_chars = int(len(text) * ratio * 0.95)
    return text[:target_chars] + "\n\n[... truncated to fit token budget ...]"
