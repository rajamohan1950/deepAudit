import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"P0", "P1", "P2", "P3"}
VALID_EFFORTS = {"S", "M", "L", "XL"}
VALID_SCORE_TYPES = {"cvss", "risk"}


@dataclass
class ParsedSignal:
    category_id: int
    signal_text: str
    severity: str
    score: float
    score_type: str
    evidence: str
    failure_scenario: str
    remediation: str
    effort: str
    confidence: float = 0.8
    references: list[str] | None = None

    def is_valid(self) -> tuple[bool, str]:
        if not self.signal_text or len(self.signal_text) < 10:
            return False, "Signal text too short or empty"
        if self.severity not in VALID_SEVERITIES:
            return False, f"Invalid severity: {self.severity}"
        if self.effort not in VALID_EFFORTS:
            return False, f"Invalid effort: {self.effort}"
        if not self.evidence or len(self.evidence) < 3:
            return False, "Missing evidence"
        if not self.failure_scenario or len(self.failure_scenario) < 5:
            return False, "Missing failure scenario"
        if not self.remediation or len(self.remediation) < 5:
            return False, "Missing remediation"
        if not (0 <= self.score <= 10):
            return False, f"Score out of range: {self.score}"

        return True, ""


class ResponseParser:
    """Parses LLM JSON responses into validated Signal objects."""

    def parse(self, raw_response: str, category_id: int) -> list[ParsedSignal]:
        json_data = self._extract_json(raw_response)
        if not json_data:
            logger.error(f"Could not extract JSON from LLM response for cat {category_id}")
            return []

        signals_data = json_data if isinstance(json_data, list) else json_data.get("signals", [])

        if not signals_data:
            logger.warning(f"No signals found in response for cat {category_id}")
            return []

        parsed = []
        rejected = 0
        for i, sig_data in enumerate(signals_data):
            try:
                signal = self._parse_one(sig_data, category_id)
                valid, reason = signal.is_valid()
                if valid:
                    parsed.append(signal)
                else:
                    rejected += 1
                    logger.debug(f"Rejected signal {i} for cat {category_id}: {reason}")
            except Exception as e:
                rejected += 1
                logger.debug(f"Failed to parse signal {i} for cat {category_id}: {e}")

        if rejected > 0:
            logger.info(
                f"Cat {category_id}: parsed {len(parsed)}, rejected {rejected} signals"
            )

        return parsed

    def _extract_json(self, raw: str) -> dict | list | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", raw)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = raw.find(start_char)
            end = raw.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    continue

        return None

    def _parse_one(self, data: dict, category_id: int) -> ParsedSignal:
        severity = str(data.get("severity", data.get("sev", "P2"))).upper()
        if severity not in VALID_SEVERITIES:
            severity = "P2"

        effort = str(data.get("effort", "M")).upper()
        if effort not in VALID_EFFORTS:
            effort = "M"

        score = float(data.get("score", 5.0))
        score = max(0.0, min(10.0, score))

        score_type = str(data.get("score_type", "risk")).lower()
        if score_type not in VALID_SCORE_TYPES:
            score_type = "cvss" if category_id <= 5 else "risk"

        return ParsedSignal(
            category_id=category_id,
            signal_text=str(data.get("signal_text", data.get("signal", ""))),
            severity=severity,
            score=score,
            score_type=score_type,
            evidence=str(data.get("evidence", "")),
            failure_scenario=str(
                data.get("failure_scenario", data.get("attack_scenario", ""))
            ),
            remediation=str(data.get("remediation", data.get("fix", ""))),
            effort=effort,
            confidence=float(data.get("confidence", 0.8)),
            references=data.get("references", []),
        )
