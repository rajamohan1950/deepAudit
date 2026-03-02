import logging
import re

logger = logging.getLogger(__name__)


class CodeChunker:
    """Splits large files into semantically meaningful chunks.

    Instead of splitting at arbitrary line numbers, splits at function/class
    boundaries to preserve context for the LLM.
    """

    FUNCTION_PATTERNS = {
        "python": re.compile(r"^(class |def |async def )", re.MULTILINE),
        "javascript": re.compile(
            r"^(export\s+)?(async\s+)?function\s|^(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\(",
            re.MULTILINE,
        ),
        "typescript": re.compile(
            r"^(export\s+)?(async\s+)?function\s|^(export\s+)?(const|let|var)\s+\w+\s*[:=]|^(export\s+)?class\s|^(export\s+)?interface\s",
            re.MULTILINE,
        ),
        "go": re.compile(r"^func\s|^type\s+\w+\s+struct", re.MULTILINE),
        "java": re.compile(
            r"^\s*(public|private|protected)?\s*(static\s+)?(class|interface|enum|\w+\s+\w+\s*\()",
            re.MULTILINE,
        ),
        "rust": re.compile(r"^(pub\s+)?fn\s|^(pub\s+)?struct\s|^(pub\s+)?impl\s", re.MULTILINE),
    }

    def __init__(self, max_chunk_tokens: int = 4000):
        self.max_chunk_tokens = max_chunk_tokens
        self.approx_chars_per_token = 4

    def chunk_file(self, content: str, language: str | None = None) -> list[str]:
        max_chars = self.max_chunk_tokens * self.approx_chars_per_token

        if len(content) <= max_chars:
            return [content]

        pattern = self.FUNCTION_PATTERNS.get(language)
        if pattern:
            return self._chunk_by_pattern(content, pattern, max_chars)

        return self._chunk_by_lines(content, max_chars)

    def _chunk_by_pattern(
        self, content: str, pattern: re.Pattern, max_chars: int
    ) -> list[str]:
        boundaries = [m.start() for m in pattern.finditer(content)]

        if not boundaries:
            return self._chunk_by_lines(content, max_chars)

        if boundaries[0] > 0:
            boundaries.insert(0, 0)

        chunks = []
        current_start = 0
        current_end = 0

        for i, boundary in enumerate(boundaries):
            next_boundary = boundaries[i + 1] if i + 1 < len(boundaries) else len(content)
            segment_size = next_boundary - current_start

            if segment_size > max_chars and current_end > current_start:
                chunks.append(content[current_start:current_end])
                current_start = boundary
                current_end = next_boundary
            else:
                current_end = next_boundary

        if current_start < len(content):
            remaining = content[current_start:]
            if len(remaining) > max_chars:
                chunks.extend(self._chunk_by_lines(remaining, max_chars))
            else:
                chunks.append(remaining)

        return [c for c in chunks if c.strip()]

    def _chunk_by_lines(self, content: str, max_chars: int) -> list[str]:
        lines = content.splitlines(keepends=True)
        chunks = []
        current_chunk: list[str] = []
        current_size = 0

        for line in lines:
            if current_size + len(line) > max_chars and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(line)
            current_size += len(line)

        if current_chunk:
            chunks.append("".join(current_chunk))

        return [c for c in chunks if c.strip()]
