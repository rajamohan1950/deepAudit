"""Validation utilities for signal quality enforcement."""

import re


VAGUE_STARTERS = {
    "improve", "consider", "review", "look into", "maybe",
    "possibly", "should", "might", "could", "evaluate",
}


def validate_signal_quality(signal: dict) -> tuple[bool, str]:
    text = signal.get("signal_text", "")
    if not text or len(text) < 20:
        return False, "Signal text too short (min 20 chars)"

    evidence = signal.get("evidence", "")
    if not evidence or len(evidence) < 5:
        return False, "Evidence missing or too short"

    scenario = signal.get("failure_scenario", "")
    if not scenario or len(scenario) < 10:
        return False, "Failure scenario missing or too short"

    remediation = signal.get("remediation", "")
    if not remediation or len(remediation) < 10:
        return False, "Remediation missing or too short"

    first_word = remediation.strip().split()[0].lower() if remediation.strip() else ""
    if first_word in VAGUE_STARTERS:
        return False, f"Remediation starts with vague word: '{first_word}'"

    severity = signal.get("severity", "")
    if severity not in ("P0", "P1", "P2", "P3"):
        return False, f"Invalid severity: {severity}"

    effort = signal.get("effort", "")
    if effort not in ("S", "M", "L", "XL"):
        return False, f"Invalid effort: {effort}"

    score = signal.get("score", -1)
    if not (0 <= score <= 10):
        return False, f"Score out of range: {score}"

    return True, ""


def validate_severity_distribution(
    signals: list[dict],
) -> tuple[bool, dict[str, int]]:
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for s in signals:
        sev = s.get("severity", "")
        if sev in counts:
            counts[sev] += 1

    targets = {
        "P0": (30, 50),
        "P1": (100, 150),
        "P2": (250, 300),
        "P3": (150, 200),
    }

    valid = all(
        targets[sev][0] <= counts[sev] <= targets[sev][1]
        for sev in targets
    )

    return valid, counts
