"""CVSS 3.1 scoring for security signals and Risk 1-10 for non-security."""

import logging

logger = logging.getLogger(__name__)

SECURITY_CATEGORIES = {1, 2, 3, 4, 5, 19}

SEVERITY_THRESHOLDS = {
    "cvss": {"P0": 9.0, "P1": 7.0, "P2": 4.0, "P3": 0.0},
    "risk": {"P0": 9.0, "P1": 7.0, "P2": 4.0, "P3": 0.0},
}


def auto_severity(score: float, score_type: str) -> str:
    thresholds = SEVERITY_THRESHOLDS.get(score_type, SEVERITY_THRESHOLDS["risk"])
    for sev in ("P0", "P1", "P2", "P3"):
        if score >= thresholds[sev]:
            return sev
    return "P3"


def score_type_for_category(category_id: int) -> str:
    return "cvss" if category_id in SECURITY_CATEGORIES else "risk"


def validate_score(score: float, score_type: str) -> float:
    return max(0.0, min(10.0, score))


def estimate_cvss_from_signal(signal_text: str, evidence: str) -> float:
    """Heuristic CVSS estimation when the LLM doesn't provide one."""
    text = (signal_text + " " + evidence).lower()

    score = 5.0

    critical_keywords = [
        "rce", "remote code execution", "sql injection", "command injection",
        "ssrf", "deserialization", "authentication bypass", "privilege escalation",
    ]
    high_keywords = [
        "xss", "csrf", "idor", "broken auth", "sensitive data exposure",
        "injection", "path traversal", "xxe",
    ]
    medium_keywords = [
        "information disclosure", "missing encryption", "weak cipher",
        "cors misconfiguration", "open redirect", "clickjacking",
    ]

    for kw in critical_keywords:
        if kw in text:
            return min(score + 4.5, 10.0)
    for kw in high_keywords:
        if kw in text:
            return min(score + 3.0, 10.0)
    for kw in medium_keywords:
        if kw in text:
            return min(score + 1.5, 10.0)

    return score
