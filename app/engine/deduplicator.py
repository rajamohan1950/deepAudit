"""Signal deduplication to prevent overlapping findings across categories."""

import logging
from difflib import SequenceMatcher

from app.engine.llm.response_parser import ParsedSignal

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.75


class SignalDeduplicator:
    """Removes duplicate or near-duplicate signals."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self.seen_signals: list[ParsedSignal] = []

    def deduplicate(self, new_signals: list[ParsedSignal]) -> list[ParsedSignal]:
        unique = []
        duplicates = 0

        for signal in new_signals:
            if self._is_duplicate(signal):
                duplicates += 1
                continue
            unique.append(signal)
            self.seen_signals.append(signal)

        if duplicates:
            logger.info(f"Deduplication: removed {duplicates}, kept {len(unique)}")

        return unique

    def _is_duplicate(self, signal: ParsedSignal) -> bool:
        for existing in self.seen_signals:
            if self._signals_match(signal, existing):
                return True
        return False

    def _signals_match(self, a: ParsedSignal, b: ParsedSignal) -> bool:
        if a.evidence == b.evidence and a.evidence:
            text_sim = self._similarity(a.signal_text, b.signal_text)
            if text_sim > 0.5:
                return True

        overall = self._similarity(
            f"{a.signal_text} {a.evidence}",
            f"{b.signal_text} {b.evidence}",
        )
        return overall > self.threshold

    def _similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def reset(self):
        self.seen_signals.clear()
