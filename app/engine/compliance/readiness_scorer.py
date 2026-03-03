"""Compliance readiness scoring engine.

Maps DeepAudit signals to framework controls and produces a readiness report
with gap analysis, severity classification, cost estimates, and timelines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from app.engine.compliance.frameworks import (
    ComplianceFramework,
    Control,
    get_framework,
)

logger = logging.getLogger(__name__)


class GapSeverity(str, Enum):
    """Gap severity classification for compliance readiness."""
    CRITICAL = "critical"   # Blocks certification — must remediate
    MAJOR = "major"         # Significant work required
    MINOR = "minor"         # Documentation or minor config change
    ADVISORY = "advisory"   # Best-practice improvement, not required


@dataclass
class AuditSignal:
    """Lightweight representation of a DeepAudit finding for compliance mapping."""
    category_id: int
    signal_text: str
    severity: str           # P0, P1, P2, P3
    score: float            # 0.0–10.0
    evidence: str = ""
    remediation: str = ""
    effort: str = "M"       # S, M, L, XL


@dataclass
class ControlGap:
    """A specific gap between current state and a framework control requirement."""
    control_id: str
    control_title: str
    category: str
    severity: GapSeverity
    coverage_pct: float
    matching_signals: list[AuditSignal] = field(default_factory=list)
    description: str = ""
    remediation_summary: str = ""
    estimated_effort: str = "M"


@dataclass
class ComplianceReadinessReport:
    """Full readiness assessment for a single compliance framework."""
    framework_id: str
    framework_name: str
    framework_version: str
    readiness_score: float              # 0–100
    controls_met: list[str]             # control_ids fully satisfied
    controls_partial: list[str]         # control_ids partially satisfied
    controls_missing: list[str]         # control_ids with no coverage
    gaps: list[ControlGap]
    total_controls: int
    estimated_cost_to_compliance: str   # e.g. "$50K-$120K"
    estimated_timeline_months: str      # e.g. "3-6 months"
    category_coverage: dict[str, float] # per-category readiness %

    @property
    def critical_gaps(self) -> list[ControlGap]:
        return [g for g in self.gaps if g.severity == GapSeverity.CRITICAL]

    @property
    def major_gaps(self) -> list[ControlGap]:
        return [g for g in self.gaps if g.severity == GapSeverity.MAJOR]

    def summary(self) -> dict:
        return {
            "framework": self.framework_name,
            "readiness_score": round(self.readiness_score, 1),
            "controls_met": len(self.controls_met),
            "controls_partial": len(self.controls_partial),
            "controls_missing": len(self.controls_missing),
            "total_controls": self.total_controls,
            "critical_gaps": len(self.critical_gaps),
            "major_gaps": len(self.major_gaps),
            "estimated_cost": self.estimated_cost_to_compliance,
            "estimated_timeline": self.estimated_timeline_months,
        }


# Severity thresholds: P0/P1 findings against a control indicate critical/major gaps
_SEVERITY_WEIGHT = {"P0": 1.0, "P1": 0.75, "P2": 0.45, "P3": 0.2}

# Effort-to-cost mapping (USD ranges per unit of work)
_EFFORT_COST_MAP = {
    "S": (2_000, 8_000),
    "M": (8_000, 25_000),
    "L": (25_000, 75_000),
    "XL": (75_000, 200_000),
}

# Effort-to-months mapping
_EFFORT_MONTHS_MAP = {"S": 0.25, "M": 1.0, "L": 2.0, "XL": 4.0}


class ComplianceReadinessScorer:
    """Calculates compliance readiness by mapping audit signals to framework controls."""

    def __init__(self, signals: list[AuditSignal]):
        self._signals = signals
        self._signals_by_category: dict[int, list[AuditSignal]] = {}
        for sig in signals:
            self._signals_by_category.setdefault(sig.category_id, []).append(sig)

    def score(self, framework_id: str) -> ComplianceReadinessReport:
        framework = get_framework(framework_id)
        return self._assess(framework)

    def score_all(self) -> list[ComplianceReadinessReport]:
        from app.engine.compliance.frameworks import FRAMEWORK_REGISTRY
        return [self._assess(fw) for fw in FRAMEWORK_REGISTRY.values()]

    def _assess(self, framework: ComplianceFramework) -> ComplianceReadinessReport:
        controls_met: list[str] = []
        controls_partial: list[str] = []
        controls_missing: list[str] = []
        gaps: list[ControlGap] = []
        category_scores: dict[str, list[float]] = {}

        for control in framework.controls:
            coverage, matched_signals = self._evaluate_control(control)
            cat = control.category
            category_scores.setdefault(cat, []).append(coverage)

            if coverage >= 0.8:
                controls_met.append(control.control_id)
            elif coverage > 0.0:
                controls_partial.append(control.control_id)
                gap = self._build_gap(control, coverage, matched_signals)
                gaps.append(gap)
            else:
                controls_missing.append(control.control_id)
                gap = self._build_gap(control, 0.0, [])
                gaps.append(gap)

        total = len(framework.controls)
        met_weight = len(controls_met) * 1.0
        partial_weight = len(controls_partial) * 0.4
        readiness = ((met_weight + partial_weight) / max(total, 1)) * 100.0

        category_coverage = {}
        for cat, scores in category_scores.items():
            category_coverage[cat] = round(
                (sum(scores) / len(scores)) * 100.0, 1
            ) if scores else 0.0

        gaps.sort(key=lambda g: (
            _gap_severity_rank(g.severity), -g.coverage_pct
        ))

        cost_range = self._estimate_cost(gaps)
        timeline = self._estimate_timeline(gaps)

        return ComplianceReadinessReport(
            framework_id=framework.framework_id,
            framework_name=framework.name,
            framework_version=framework.version,
            readiness_score=round(readiness, 1),
            controls_met=controls_met,
            controls_partial=controls_partial,
            controls_missing=controls_missing,
            gaps=gaps,
            total_controls=total,
            estimated_cost_to_compliance=cost_range,
            estimated_timeline_months=timeline,
            category_coverage=category_coverage,
        )

    def _evaluate_control(
        self, control: Control
    ) -> tuple[float, list[AuditSignal]]:
        """Determine how well the current audit signals cover a control.

        Returns (coverage 0.0–1.0, list of matching signals).
        Coverage is calculated as:
        - Each required audit_signal category that has findings contributes
          proportional coverage, weighted by the *best* finding severity.
        - P3 findings give high coverage (low-severity = mostly addressed).
        - P0 findings give low coverage (critical gap in that area).
        """
        if not control.audit_signals:
            return 0.0, []

        matched: list[AuditSignal] = []
        category_coverages: list[float] = []

        for cat_id in control.audit_signals:
            cat_signals = self._signals_by_category.get(cat_id, [])
            if not cat_signals:
                category_coverages.append(0.0)
                continue

            best_severity = min(
                cat_signals,
                key=lambda s: _severity_rank(s.severity)
            ).severity

            issue_weight = _SEVERITY_WEIGHT.get(best_severity, 0.5)
            cat_coverage = 1.0 - (issue_weight * 0.6)
            category_coverages.append(max(0.0, min(1.0, cat_coverage)))
            matched.extend(cat_signals)

        overall = sum(category_coverages) / len(category_coverages)
        return overall, matched

    def _build_gap(
        self,
        control: Control,
        coverage: float,
        signals: list[AuditSignal],
    ) -> ControlGap:
        severity = self._classify_gap(control, coverage, signals)

        worst_effort = "S"
        for sig in signals:
            if _effort_rank(sig.effort) > _effort_rank(worst_effort):
                worst_effort = sig.effort

        if not signals:
            worst_effort = "M" if severity in (
                GapSeverity.CRITICAL, GapSeverity.MAJOR
            ) else "S"

        remediation_parts = []
        for sig in signals[:3]:
            if sig.remediation:
                remediation_parts.append(sig.remediation)

        return ControlGap(
            control_id=control.control_id,
            control_title=control.title,
            category=control.category,
            severity=severity,
            coverage_pct=round(coverage * 100, 1),
            matching_signals=signals,
            description=control.description,
            remediation_summary=" | ".join(remediation_parts) or (
                f"Implement controls for: {control.title}"
            ),
            estimated_effort=worst_effort,
        )

    def _classify_gap(
        self,
        control: Control,
        coverage: float,
        signals: list[AuditSignal],
    ) -> GapSeverity:
        if coverage == 0.0:
            has_security = any(
                cat_id in {1, 2, 3, 4, 5, 19}
                for cat_id in control.audit_signals
            )
            return GapSeverity.CRITICAL if has_security else GapSeverity.MAJOR

        has_p0 = any(s.severity == "P0" for s in signals)
        has_p1 = any(s.severity == "P1" for s in signals)

        if has_p0 and coverage < 0.5:
            return GapSeverity.CRITICAL
        if has_p1 or coverage < 0.4:
            return GapSeverity.MAJOR
        if coverage < 0.7:
            return GapSeverity.MINOR
        return GapSeverity.ADVISORY

    def _estimate_cost(self, gaps: list[ControlGap]) -> str:
        if not gaps:
            return "$0"

        low_total = 0
        high_total = 0
        for gap in gaps:
            low, high = _EFFORT_COST_MAP.get(gap.estimated_effort, (5_000, 20_000))
            severity_mult = {
                GapSeverity.CRITICAL: 1.5,
                GapSeverity.MAJOR: 1.2,
                GapSeverity.MINOR: 0.6,
                GapSeverity.ADVISORY: 0.3,
            }.get(gap.severity, 1.0)
            low_total += int(low * severity_mult)
            high_total += int(high * severity_mult)

        return f"${_format_cost(low_total)}–${_format_cost(high_total)}"

    def _estimate_timeline(self, gaps: list[ControlGap]) -> str:
        if not gaps:
            return "0 months"

        critical_months = sum(
            _EFFORT_MONTHS_MAP.get(g.estimated_effort, 1.0)
            for g in gaps if g.severity == GapSeverity.CRITICAL
        )
        major_months = sum(
            _EFFORT_MONTHS_MAP.get(g.estimated_effort, 1.0)
            for g in gaps if g.severity == GapSeverity.MAJOR
        )

        parallel_factor = 0.4
        min_months = max(1, int(critical_months * parallel_factor))
        max_months = max(
            min_months + 1,
            int((critical_months + major_months) * parallel_factor) + 1,
        )

        return f"{min_months}–{max_months} months"


def _severity_rank(severity: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(severity, 4)


def _gap_severity_rank(sev: GapSeverity) -> int:
    return {
        GapSeverity.CRITICAL: 0,
        GapSeverity.MAJOR: 1,
        GapSeverity.MINOR: 2,
        GapSeverity.ADVISORY: 3,
    }.get(sev, 4)


def _effort_rank(effort: str) -> int:
    return {"S": 0, "M": 1, "L": 2, "XL": 3}.get(effort, 1)


def _format_cost(amount: int) -> str:
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"{amount // 1_000}K"
    return str(amount)
