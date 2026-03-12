"""PE-grade report generator — produces investment-quality deliverables."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit
from app.models.signal import Signal

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {"P0": 25, "P1": 10, "P2": 3, "P3": 1}
EFFORT_HOURS = {"S": 2, "M": 8, "L": 40, "XL": 160}
ASSUMED_HOURLY_RATE = 175

PHASE_NAMES = {
    1: "Security Fundamentals",
    2: "Performance & Scalability",
    3: "Reliability & Fault Tolerance",
    4: "Infrastructure & Supply Chain",
    5: "AI/ML Risk & Ops",
    6: "Observability",
    7: "Code Quality & Testing",
    8: "Cost & Multi-Tenancy",
    9: "Compliance & DR",
    10: "Organization & Compatibility",
}

PHASE_CATEGORIES = {
    1: list(range(1, 6)),
    2: list(range(6, 11)),
    3: list(range(11, 17)),
    4: list(range(17, 23)),
    5: [23, 24],
    6: list(range(25, 29)),
    7: list(range(29, 33)),
    8: [33, 34],
    9: [35, 36],
    10: list(range(37, 41)),
}

CATEGORY_NAMES = {
    1: "Authentication", 2: "Authorization", 3: "Input Validation",
    4: "Data Protection", 5: "Cryptography", 6: "Memory", 7: "CPU",
    8: "Network I/O", 9: "Database", 10: "Caching", 11: "OS/Kernel",
    12: "Graceful Shutdown", 13: "SPOF", 14: "Fault Tolerance",
    15: "Concurrency", 16: "Data Integrity", 17: "Distributed Systems",
    18: "Queue Processing", 19: "Infra Security", 20: "Capacity",
    21: "CI/CD", 22: "Supply Chain", 23: "AI/ML Risks", 24: "AI/ML Ops",
    25: "Metrics", 26: "Logging", 27: "Tracing", 28: "Alerting",
    29: "Testing", 30: "Code Quality", 31: "API Design", 32: "UX/A11y",
    33: "Cost/FinOps", 34: "Multi-Tenancy", 35: "Compliance",
    36: "Disaster Recovery", 37: "i18n", 38: "State Management",
    39: "Backward Compat", 40: "Organizational",
}

COMPLIANCE_CONTROL_MAP: dict[str, dict[str, set[int]]] = {
    "soc2": {
        "CC6.1 - Logical Access": {1, 2},
        "CC6.6 - System Boundaries": {3, 19},
        "CC6.7 - Data Transmission": {4, 5},
        "CC7.1 - Monitoring": {25, 26, 27, 28},
        "CC7.2 - Incident Detection": {28, 19},
        "CC8.1 - Change Management": {21, 22},
        "A1.2 - Recovery": {36, 14},
        "CC9.1 - Risk Mitigation": {13, 35},
    },
    "gdpr": {
        "Art.5 - Data Principles": {4, 35},
        "Art.25 - Data by Design": {4, 16},
        "Art.30 - Records of Processing": {26, 35},
        "Art.32 - Security of Processing": {1, 2, 5, 19},
        "Art.33 - Breach Notification": {28, 36},
        "Art.35 - DPIA": {23, 35},
    },
    "hipaa": {
        "164.312(a) - Access Control": {1, 2},
        "164.312(c) - Integrity": {4, 16},
        "164.312(d) - Authentication": {1, 5},
        "164.312(e) - Transmission Security": {5, 8},
        "164.308(a)(5) - Security Awareness": {22, 40},
        "164.308(a)(7) - Contingency Plan": {36, 14},
        "164.312(b) - Audit Controls": {25, 26, 27},
    },
    "pci_dss": {
        "Req 1 - Network Security": {19, 8},
        "Req 3 - Stored Data Protection": {4, 5},
        "Req 6 - Secure Development": {3, 21, 30},
        "Req 7 - Access Restriction": {2},
        "Req 8 - User Authentication": {1},
        "Req 10 - Logging & Monitoring": {25, 26, 27, 28},
        "Req 11 - Security Testing": {29},
    },
    "iso27001": {
        "A.9 - Access Control": {1, 2},
        "A.10 - Cryptography": {5},
        "A.12 - Operations Security": {21, 26, 28},
        "A.13 - Communications Security": {8, 19},
        "A.14 - System Acquisition": {3, 30},
        "A.16 - Incident Management": {28, 36},
        "A.17 - Business Continuity": {14, 36},
        "A.18 - Compliance": {35},
    },
    "nist_csf": {
        "ID.AM - Asset Management": {20, 40},
        "PR.AC - Access Control": {1, 2},
        "PR.DS - Data Security": {4, 5, 16},
        "PR.IP - Protective Processes": {21, 22, 30},
        "DE.AE - Anomaly Detection": {28, 25},
        "DE.CM - Continuous Monitoring": {25, 26, 27},
        "RS.RP - Response Planning": {36},
        "RC.RP - Recovery Planning": {14, 36},
    },
}

SCALABILITY_CATEGORIES = {6, 7, 8, 9, 10, 11, 12}

INFRA_COST_MULTIPLIERS = {
    "2x": {"database": 2.5, "compute": 2.0, "network": 1.8, "cache": 1.5},
    "5x": {"database": 6.0, "compute": 4.5, "network": 4.0, "cache": 3.0},
    "10x": {"database": 12.0, "compute": 9.0, "network": 8.0, "cache": 5.0},
}

BOTTLENECK_CATEGORY_MAP = {
    "database": {9},
    "api_and_network": {8, 31},
    "compute": {6, 7, 11},
    "caching": {10},
    "infrastructure": {19, 20},
    "concurrency": {15, 17},
}

TECH_DEBT_CATEGORY_MAP = {
    "code_quality": {30, 31, 32},
    "architecture": {13, 14, 15, 17, 38},
    "dependency": {22},
    "testing": {29},
    "infrastructure": {19, 20, 21},
    "observability": {25, 26, 27, 28},
}

SPOF_KEYWORDS = {
    "infrastructure": ["single instance", "no failover", "single region", "no redundancy",
                       "single database", "single server", "no backup", "single az",
                       "no replication", "single node"],
    "code": ["singleton", "hardcoded", "global state", "monolith", "tight coupling",
             "god class", "circular dependency", "no abstraction"],
    "people": ["bus factor", "single maintainer", "one person", "undocumented",
               "tribal knowledge", "no documentation", "key person"],
    "process": ["manual deploy", "no ci/cd", "no runbook", "no incident",
                "no monitoring", "no alerting", "manual process", "no automation"],
}


def _risk_score_from_signals(signals: list[Signal]) -> float:
    """Compute an overall 0-100 risk score. Higher = more risk."""
    if not signals:
        return 0.0
    weighted = sum(SEVERITY_WEIGHTS.get(s.severity, 1) * s.score for s in signals)
    max_possible = len(signals) * 25 * 10
    raw = (weighted / max_possible) * 100 if max_possible else 0
    return round(min(raw, 100), 1)


def _traffic_light(score: float) -> str:
    if score >= 65:
        return "Red"
    if score >= 35:
        return "Amber"
    return "Green"


def _investment_recommendation(score: float, p0_count: int) -> str:
    if score >= 70 or p0_count >= 10:
        return "Do Not Proceed"
    if score >= 35 or p0_count >= 3:
        return "Proceed with Conditions"
    return "Proceed"


def _estimate_revenue_impact(signals: list[Signal]) -> dict[str, Any]:
    """Rough revenue impact based on critical findings in key areas."""
    security_critical = [s for s in signals if s.severity == "P0" and s.category_id in {1, 2, 3, 4, 5, 19}]
    reliability_critical = [s for s in signals if s.severity == "P0" and s.category_id in {13, 14, 15, 36}]
    performance_critical = [s for s in signals if s.severity in ("P0", "P1") and s.category_id in {6, 7, 8, 9, 10}]

    risk_factors = []
    if security_critical:
        risk_factors.append({
            "category": "Security Breach Risk",
            "signal_count": len(security_critical),
            "potential_impact": "High — data breach could result in regulatory fines, customer churn, and reputational damage",
            "estimated_cost_range": "$500K–$5M+ depending on data volume and jurisdiction",
        })
    if reliability_critical:
        risk_factors.append({
            "category": "Availability & Downtime Risk",
            "signal_count": len(reliability_critical),
            "potential_impact": "Medium-High — SPOFs and fault-tolerance gaps threaten SLA compliance",
            "estimated_cost_range": "$50K–$500K/year in lost revenue and SLA penalties",
        })
    if performance_critical:
        risk_factors.append({
            "category": "Scalability Risk",
            "signal_count": len(performance_critical),
            "potential_impact": "Medium — performance bottlenecks may limit growth capacity",
            "estimated_cost_range": "$100K–$1M in engineering rework to scale",
        })

    return {
        "risk_factor_count": len(risk_factors),
        "risk_factors": risk_factors,
        "note": "Estimates are directional ranges based on industry benchmarks; actual impact depends on revenue, user base, and regulatory context.",
    }


def _classify_spof(signal: Signal) -> str:
    text = ((signal.signal_text or "") + " " + (signal.evidence or "") + " " + (signal.failure_scenario or "")).lower()
    scores = {}
    for spof_type, keywords in SPOF_KEYWORDS.items():
        scores[spof_type] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "infrastructure"


class PEReportGenerator:
    """Generates investment-quality PE report deliverables from audit signals."""

    VERSION = "2.0"

    def generate_executive_summary(
        self,
        audit_id: str,
        signals: list[Signal],
        audit_metadata: dict,
    ) -> dict:
        risk_score = _risk_score_from_signals(signals)
        p0_count = sum(1 for s in signals if s.severity == "P0")
        p1_count = sum(1 for s in signals if s.severity == "P1")

        by_sev = {"P0": [], "P1": [], "P2": [], "P3": []}
        for s in signals:
            by_sev.get(s.severity, by_sev["P3"]).append(s)

        top_critical = sorted(
            by_sev["P0"] + by_sev["P1"],
            key=lambda s: s.score,
            reverse=True,
        )[:5]

        total_remediation_hours = sum(EFFORT_HOURS.get(s.effort, 8) for s in signals)

        return {
            "report_section": "executive_summary",
            "overall_risk_score": risk_score,
            "traffic_light": _traffic_light(risk_score),
            "recommendation": _investment_recommendation(risk_score, p0_count),
            "severity_breakdown": {sev: len(sigs) for sev, sigs in by_sev.items()},
            "total_signals": len(signals),
            "top_5_critical_findings": [
                {
                    "rank": i + 1,
                    "signal": (s.signal_text or "")[:300],
                    "severity": s.severity,
                    "score": s.score,
                    "category": s.category.name if s.category else CATEGORY_NAMES.get(s.category_id, ""),
                    "evidence": (s.evidence or "")[:200],
                    "remediation": (s.remediation or "")[:250],
                    "effort": s.effort,
                }
                for i, s in enumerate(top_critical)
            ],
            "revenue_impact_assessment": _estimate_revenue_impact(signals),
            "estimated_total_remediation_hours": total_remediation_hours,
            "estimated_total_remediation_cost_usd": total_remediation_hours * ASSUMED_HOURLY_RATE,
            "audit_metadata": {
                "audit_id": audit_id,
                "system_context": audit_metadata.get("system_context", {}),
                "tokens_used": audit_metadata.get("total_tokens", 0),
                "audit_cost_usd": audit_metadata.get("total_cost", 0),
            },
        }

    def generate_risk_heatmap(
        self, signals: list[Signal], evaluated_categories: list[int] | None = None,
    ) -> dict:
        evaluated_set = set(evaluated_categories) if evaluated_categories else None

        matrix: dict[str, dict] = {}
        for cat_id in range(1, 41):
            evaluated = evaluated_set is None or cat_id in evaluated_set
            matrix[str(cat_id)] = {
                "category_name": CATEGORY_NAMES.get(cat_id, f"Category {cat_id}"),
                "signal_count": 0,
                "max_severity": "none",
                "risk_score": 0.0,
                "color": "tbd" if not evaluated else "green",
                "evaluated": evaluated,
                "severity_breakdown": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
            }

        severity_rank = {"P0": 4, "P1": 3, "P2": 2, "P3": 1, "none": 0}

        for s in signals:
            key = str(s.category_id)
            if key not in matrix:
                continue
            entry = matrix[key]
            entry["signal_count"] += 1
            entry["severity_breakdown"][s.severity] = entry["severity_breakdown"].get(s.severity, 0) + 1
            if severity_rank.get(s.severity, 0) > severity_rank.get(entry["max_severity"], 0):
                entry["max_severity"] = s.severity

        for cat_key, entry in matrix.items():
            if not entry["evaluated"]:
                continue  # keep "tbd"
            bd = entry["severity_breakdown"]
            score = bd["P0"] * 25 + bd["P1"] * 10 + bd["P2"] * 3 + bd["P3"] * 1
            entry["risk_score"] = round(min(score, 100), 1)
            if entry["signal_count"] == 0:
                entry["color"] = "red"  # evaluated but 0 signals = suspicious/red
            elif bd["P0"] > 0:
                entry["color"] = "red"
            elif bd["P1"] > 2:
                entry["color"] = "orange"
            elif bd["P1"] > 0 or bd["P2"] > 4:
                entry["color"] = "yellow"
            else:
                entry["color"] = "green"

        phases = []
        for phase_num in range(1, 11):
            cat_ids = PHASE_CATEGORIES.get(phase_num, [])
            phases.append({
                "phase": phase_num,
                "phase_name": PHASE_NAMES.get(phase_num, f"Phase {phase_num}"),
                "categories": [matrix[str(cid)] | {"category_id": cid} for cid in cat_ids if str(cid) in matrix],
            })

        return {
            "report_section": "risk_heatmap",
            "total_categories": 40,
            "phases": phases,
            "matrix": matrix,
            "color_legend": {
                "red": "Critical — P0 signals present or no data found (needs attention)",
                "orange": "High — Multiple P1 signals, fix within first sprint",
                "yellow": "Medium — P1 or clustered P2 signals, fix within one quarter",
                "green": "Low — Minor or no issues detected",
                "tbd": "Not Evaluated — category not included in this scan",
            },
        }

    def generate_spof_map(self, signals: list[Signal]) -> dict:
        spof_signals = [s for s in signals if s.category_id == 13]

        # Also include fault-tolerance signals with high severity as related SPOFs
        related_spof = [
            s for s in signals
            if s.category_id in {14, 36} and s.severity in ("P0", "P1")
        ]

        classified: dict[str, list[dict]] = {
            "infrastructure": [],
            "code": [],
            "people": [],
            "process": [],
        }

        all_spof = spof_signals + related_spof
        seen_ids: set = set()

        for s in all_spof:
            if s.id in seen_ids:
                continue
            seen_ids.add(s.id)
            spof_type = _classify_spof(s)
            classified[spof_type].append({
                "signal": (s.signal_text or "")[:350],
                "severity": s.severity,
                "score": s.score,
                "evidence": (s.evidence or "")[:250],
                "blast_radius": (s.failure_scenario or "")[:350],
                "remediation": (s.remediation or "")[:300],
                "effort": s.effort,
                "estimated_hours": EFFORT_HOURS.get(s.effort, 8),
                "category": s.category.name if s.category else CATEGORY_NAMES.get(s.category_id, ""),
            })

        for items in classified.values():
            items.sort(key=lambda x: x["score"], reverse=True)

        dependency_chain = []
        for s in spof_signals:
            if s.severity == "P0":
                dependency_chain.append({
                    "component": (s.signal_text or "")[:150],
                    "depends_on": (s.evidence or "")[:150],
                    "failure_impact": (s.failure_scenario or "")[:200],
                })

        total = sum(len(v) for v in classified.values())

        return {
            "report_section": "spof_map",
            "total_spofs": total,
            "by_type": {
                spof_type: {
                    "count": len(items),
                    "critical_count": sum(1 for i in items if i["severity"] == "P0"),
                    "items": items,
                }
                for spof_type, items in classified.items()
            },
            "dependency_chain": dependency_chain,
            "summary": {
                "infrastructure_spofs": len(classified["infrastructure"]),
                "code_spofs": len(classified["code"]),
                "people_spofs": len(classified["people"]),
                "process_spofs": len(classified["process"]),
            },
        }

    def generate_compliance_gap_matrix(
        self,
        signals: list[Signal],
        frameworks: list[str] | None = None,
    ) -> dict:
        if frameworks is None:
            frameworks = ["soc2", "gdpr", "hipaa"]

        signal_by_cat: dict[int, list[Signal]] = {}
        for s in signals:
            signal_by_cat.setdefault(s.category_id, []).append(s)

        framework_results = {}

        for fw in frameworks:
            controls = COMPLIANCE_CONTROL_MAP.get(fw, {})
            if not controls:
                framework_results[fw] = {
                    "readiness_score": 0,
                    "control_coverage_pct": 0,
                    "gaps": [],
                    "note": f"Framework '{fw}' not yet mapped.",
                }
                continue

            total_controls = len(controls)
            covered = 0
            gaps = []

            for control_name, required_cats in controls.items():
                control_signals = []
                for cat_id in required_cats:
                    control_signals.extend(signal_by_cat.get(cat_id, []))

                critical_gaps = [s for s in control_signals if s.severity in ("P0", "P1")]

                if not control_signals:
                    covered += 1
                elif not critical_gaps:
                    covered += 0.7
                else:
                    for s in critical_gaps:
                        gap_hours = EFFORT_HOURS.get(s.effort, 8)
                        gaps.append({
                            "control": control_name,
                            "signal": (s.signal_text or "")[:250],
                            "severity": s.severity,
                            "score": s.score,
                            "evidence": (s.evidence or "")[:200],
                            "remediation": (s.remediation or "")[:250],
                            "effort": s.effort,
                            "remediation_hours": gap_hours,
                            "remediation_cost_usd": gap_hours * ASSUMED_HOURLY_RATE,
                        })

            coverage_pct = round((covered / total_controls) * 100, 1) if total_controls else 0
            readiness = max(0, round(coverage_pct - len(gaps) * 2, 1))

            gaps.sort(key=lambda g: SEVERITY_WEIGHTS.get(g["severity"], 1) * g["score"], reverse=True)

            total_gap_cost = sum(g["remediation_cost_usd"] for g in gaps)

            framework_results[fw] = {
                "readiness_score": readiness,
                "control_coverage_pct": coverage_pct,
                "total_controls": total_controls,
                "controls_passing": round(covered, 1),
                "gap_count": len(gaps),
                "gaps": gaps,
                "cost_to_compliance_usd": total_gap_cost,
            }

        # Cross-framework overlap
        all_gap_signals: dict[str, set[str]] = {}
        for fw, result in framework_results.items():
            for gap in result.get("gaps", []):
                sig_key = gap["signal"][:100]
                all_gap_signals.setdefault(sig_key, set()).add(fw)

        cross_framework_gaps = [
            {"signal": sig_key, "frameworks": sorted(fws)}
            for sig_key, fws in all_gap_signals.items()
            if len(fws) > 1
        ]

        total_cost = sum(
            r.get("cost_to_compliance_usd", 0)
            for r in framework_results.values()
        )

        return {
            "report_section": "compliance_gap_matrix",
            "frameworks_analyzed": frameworks,
            "framework_results": framework_results,
            "cross_framework_overlap": cross_framework_gaps,
            "total_cost_to_full_compliance_usd": total_cost,
            "note": "Cost estimates assume $175/hr blended engineering rate. Actual costs vary by team and geography.",
        }

    def generate_tech_debt_ledger(self, signals: list[Signal]) -> dict:
        ledger: dict[str, list[dict]] = {
            "code_quality": [],
            "architecture": [],
            "dependency": [],
            "testing": [],
            "infrastructure": [],
            "observability": [],
        }

        for s in signals:
            for debt_type, cat_ids in TECH_DEBT_CATEGORY_MAP.items():
                if s.category_id in cat_ids:
                    hours = EFFORT_HOURS.get(s.effort, 8)
                    ledger[debt_type].append({
                        "signal": (s.signal_text or "")[:300],
                        "severity": s.severity,
                        "score": s.score,
                        "evidence": (s.evidence or "")[:200],
                        "remediation": (s.remediation or "")[:250],
                        "effort": s.effort,
                        "estimated_hours": hours,
                        "estimated_cost_usd": hours * ASSUMED_HOURLY_RATE,
                        "business_impact": _business_impact_label(s),
                    })
                    break

        for items in ledger.values():
            items.sort(key=lambda x: x["score"], reverse=True)

        summary = {}
        total_hours = 0
        total_cost = 0
        for debt_type, items in ledger.items():
            type_hours = sum(i["estimated_hours"] for i in items)
            type_cost = sum(i["estimated_cost_usd"] for i in items)
            total_hours += type_hours
            total_cost += type_cost
            summary[debt_type] = {
                "item_count": len(items),
                "total_hours": type_hours,
                "total_cost_usd": type_cost,
                "critical_count": sum(1 for i in items if i["severity"] in ("P0", "P1")),
            }

        return {
            "report_section": "tech_debt_ledger",
            "summary": summary,
            "total_items": sum(len(v) for v in ledger.values()),
            "total_estimated_hours": total_hours,
            "total_estimated_cost_usd": total_cost,
            "assumed_hourly_rate_usd": ASSUMED_HOURLY_RATE,
            "ledger": ledger,
            "prioritization_note": "Items sorted by score descending within each category. Address P0/P1 items first.",
        }

    def generate_remediation_roadmap(self, signals: list[Signal]) -> dict:
        phases_config = [
            ("Week 1–2: Critical Fixes (P0)", "P0", "Immediate action — security, data integrity, SPOFs"),
            ("Month 1–2: Major Fixes (P1)", "P1", "High-priority — performance, reliability, compliance gaps"),
            ("Month 3–6: Improvements (P2)", "P2", "Systematic — testing, observability, defense-in-depth"),
            ("Backlog: Minor Items (P3)", "P3", "Continuous — code quality, documentation, tech debt"),
        ]

        roadmap_phases = []
        grand_total_hours = 0
        grand_total_cost = 0

        for phase_label, severity, description in phases_config:
            phase_signals = sorted(
                [s for s in signals if s.severity == severity],
                key=lambda s: s.score,
                reverse=True,
            )

            items = []
            phase_hours = 0
            for s in phase_signals:
                hours = EFFORT_HOURS.get(s.effort, 8)
                phase_hours += hours
                items.append({
                    "signal": s.signal_text[:250],
                    "category": s.category.name if s.category else CATEGORY_NAMES.get(s.category_id, ""),
                    "score": s.score,
                    "evidence": (s.evidence or "")[:150],
                    "remediation": (s.remediation or "")[:250],
                    "effort": s.effort,
                    "estimated_hours": hours,
                })

            phase_cost = phase_hours * ASSUMED_HOURLY_RATE
            grand_total_hours += phase_hours
            grand_total_cost += phase_cost

            engineers_needed = max(1, round(phase_hours / 160))

            roadmap_phases.append({
                "phase": phase_label,
                "description": description,
                "item_count": len(items),
                "total_hours": phase_hours,
                "total_cost_usd": phase_cost,
                "engineers_recommended": engineers_needed,
                "items": items,
            })

        return {
            "report_section": "remediation_roadmap",
            "phases": roadmap_phases,
            "total_items": len(signals),
            "grand_total_hours": grand_total_hours,
            "grand_total_cost_usd": grand_total_cost,
            "assumed_hourly_rate_usd": ASSUMED_HOURLY_RATE,
            "resource_summary": {
                "total_engineer_months": round(grand_total_hours / 160, 1),
                "recommended_team_size": max(1, round(grand_total_hours / 480)),
                "estimated_completion_months": 6,
            },
        }

    def generate_scalability_assessment(self, signals: list[Signal]) -> dict:
        """Model 2x / 5x / 10x growth scenarios and identify scaling bottlenecks."""
        scalability_signals = [s for s in signals if s.category_id in SCALABILITY_CATEGORIES]

        bottleneck_signals: dict[str, list[Signal]] = {k: [] for k in BOTTLENECK_CATEGORY_MAP}
        for s in signals:
            for area, cat_ids in BOTTLENECK_CATEGORY_MAP.items():
                if s.category_id in cat_ids and s.severity in ("P0", "P1", "P2"):
                    bottleneck_signals[area].append(s)

        def _bottleneck_summary(area_signals: list[Signal]) -> list[dict]:
            return [
                {
                    "signal": s.signal_text[:300],
                    "severity": s.severity,
                    "score": s.score,
                    "evidence": (s.evidence or "")[:200],
                    "remediation": (s.remediation or "")[:250],
                    "effort": s.effort,
                }
                for s in sorted(area_signals, key=lambda x: x.score, reverse=True)[:5]
            ]

        def _time_to_failure(area_signals: list[Signal]) -> str:
            p0_count = sum(1 for s in area_signals if s.severity == "P0")
            p1_count = sum(1 for s in area_signals if s.severity == "P1")
            if p0_count >= 2:
                return "Immediate — likely fails under current load spikes"
            if p0_count >= 1 or p1_count >= 3:
                return "1-3 months under increased load"
            if p1_count >= 1:
                return "3-6 months with gradual growth"
            return "6-12+ months — architecture can absorb moderate growth"

        def _remediation_cost(area_signals: list[Signal], multiplier: float) -> int:
            base_hours = sum(EFFORT_HOURS.get(s.effort, 8) for s in area_signals)
            scaled_hours = int(base_hours * (1 + (multiplier - 1) * 0.3))
            return scaled_hours * ASSUMED_HOURLY_RATE

        scenarios: dict[str, dict] = {}
        scale_configs = [
            ("2x", 2, "Current user/load doubled — organic growth or small acquisition"),
            ("5x", 5, "5x growth — typical Series B trajectory"),
            ("10x", 10, "10x growth — Series C / enterprise expansion"),
        ]

        for label, factor, description in scale_configs:
            scenario_bottlenecks: dict[str, dict] = {}
            total_remediation_cost = 0
            total_infra_cost_increase = 0

            for area, area_signals in bottleneck_signals.items():
                eng_cost = _remediation_cost(area_signals, factor)
                total_remediation_cost += eng_cost

                infra_mult = INFRA_COST_MULTIPLIERS[label].get(
                    area if area in INFRA_COST_MULTIPLIERS[label] else "compute", 2.0
                )
                total_infra_cost_increase += int(infra_mult * 1000)

                scenario_bottlenecks[area] = {
                    "signal_count": len(area_signals),
                    "critical_signals": sum(1 for s in area_signals if s.severity == "P0"),
                    "time_to_failure": _time_to_failure(area_signals) if area_signals else "Low risk at this scale",
                    "top_issues": _bottleneck_summary(area_signals),
                    "remediation_cost_usd": eng_cost,
                }

            critical_areas = sorted(
                scenario_bottlenecks.items(),
                key=lambda x: x[1]["signal_count"],
                reverse=True,
            )
            primary_bottleneck = critical_areas[0][0] if critical_areas and critical_areas[0][1]["signal_count"] > 0 else "none"

            scenarios[label] = {
                "description": description,
                "scale_factor": factor,
                "primary_bottleneck": primary_bottleneck,
                "bottlenecks": scenario_bottlenecks,
                "estimated_engineering_cost_usd": total_remediation_cost,
                "estimated_monthly_infra_increase_usd": total_infra_cost_increase,
                "readiness": _scale_readiness(scalability_signals, factor),
            }

        total_scalability_risk = sum(
            SEVERITY_WEIGHTS.get(s.severity, 1) * s.score
            for s in scalability_signals
        )
        max_possible = len(scalability_signals) * 25 * 10 if scalability_signals else 1
        scalability_score = round(100 - min((total_scalability_risk / max_possible) * 100, 100), 1)

        return {
            "report_section": "scalability_assessment",
            "scalability_score": scalability_score,
            "scalability_rating": "Strong" if scalability_score >= 70 else "Moderate" if scalability_score >= 40 else "Weak",
            "total_scalability_signals": len(scalability_signals),
            "scenarios": scenarios,
            "summary": {
                "can_handle_2x": scenarios["2x"]["readiness"] in ("Ready", "Minor work needed"),
                "can_handle_5x": scenarios["5x"]["readiness"] == "Ready",
                "can_handle_10x": scenarios["10x"]["readiness"] == "Ready",
                "biggest_risk_area": scenarios["10x"]["primary_bottleneck"],
                "total_cost_to_10x_usd": scenarios["10x"]["estimated_engineering_cost_usd"],
            },
        }

    def generate_full_pe_report_sync(
        self,
        signals: list[Signal],
        audit_id: str,
        audit_metadata: dict | None = None,
        frameworks: list[str] | None = None,
    ) -> dict:
        """Synchronous variant that works with pre-loaded signals (no DB session)."""
        if audit_metadata is None:
            audit_metadata = {"audit_id": audit_id, "system_context": {}, "total_tokens": 0, "total_cost": 0}
        if frameworks is None:
            frameworks = ["soc2", "gdpr", "hipaa"]

        exec_summary = self.generate_executive_summary(audit_id, signals, audit_metadata)
        risk_heatmap = self.generate_risk_heatmap(signals)
        spof_map = self.generate_spof_map(signals)
        compliance_matrix = self.generate_compliance_gap_matrix(signals, frameworks)
        tech_debt = self.generate_tech_debt_ledger(signals)
        roadmap = self.generate_remediation_roadmap(signals)

        return {
            "report_version": self.VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audit_id": audit_id,
            "audit_scope": {
                "system_context": audit_metadata.get("system_context", {}),
                "total_signals": len(signals),
                "phases_completed": None,
                "audit_cost_usd": audit_metadata.get("total_cost", 0),
            },
            "deliverables": {
                "executive_summary": exec_summary,
                "risk_heatmap": risk_heatmap,
                "spof_map": spof_map,
                "compliance_gap_matrix": compliance_matrix,
                "tech_debt_ledger": tech_debt,
                "remediation_roadmap": roadmap,
            },
        }

    async def generate_full_pe_report(
        self,
        audit_id: uuid.UUID,
        db_session: AsyncSession,
    ) -> dict:
        result = await db_session.execute(
            select(Signal).where(Signal.audit_id == audit_id).order_by(Signal.sequence_number)
        )
        signals = list(result.scalars().all())

        audit_result = await db_session.execute(
            select(Audit).where(Audit.id == audit_id)
        )
        audit = audit_result.scalar_one_or_none()
        if not audit:
            return {"error": f"Audit {audit_id} not found"}

        audit_metadata = {
            "audit_id": str(audit_id),
            "system_context": audit.system_context or {},
            "total_tokens": audit.total_tokens_used,
            "total_cost": audit.total_cost_usd,
        }

        compliance_reqs = (audit.system_context or {}).get("compliance_requirements", [])
        frameworks = compliance_reqs if compliance_reqs else ["soc2", "gdpr", "hipaa"]

        evaluated_cats = (audit.audit_config or {}).get("categories", None)
        if evaluated_cats == "all":
            evaluated_cats = None

        exec_summary = self.generate_executive_summary(str(audit_id), signals, audit_metadata)
        risk_heatmap = self.generate_risk_heatmap(signals, evaluated_categories=evaluated_cats)
        spof_map = self.generate_spof_map(signals)
        compliance_matrix = self.generate_compliance_gap_matrix(signals, frameworks)
        tech_debt = self.generate_tech_debt_ledger(signals)
        roadmap = self.generate_remediation_roadmap(signals)
        scalability = self.generate_scalability_assessment(signals)

        repo_url = (audit.source_config or {}).get("repo_url", "")

        return {
            "report_version": self.VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audit_id": str(audit_id),
            "audit_status": audit.status,
            "repo_url": repo_url,
            "audit_scope": {
                "system_context": audit.system_context,
                "total_signals": len(signals),
                "phases_completed": audit.current_phase,
                "audit_cost_usd": audit.total_cost_usd,
            },
            "deliverables": {
                "executive_summary": exec_summary,
                "risk_heatmap": risk_heatmap,
                "spof_map": spof_map,
                "compliance_gap_matrix": compliance_matrix,
                "tech_debt_ledger": tech_debt,
                "remediation_roadmap": roadmap,
                "scalability_assessment": scalability,
            },
        }


def _business_impact_label(signal: Signal) -> str:
    if signal.severity == "P0":
        return "Critical — immediate business risk"
    if signal.severity == "P1":
        return "High — affects reliability or security posture"
    if signal.severity == "P2":
        return "Medium — degrades operational quality"
    return "Low — long-term maintenance burden"


def _scale_readiness(scalability_signals: list[Signal], factor: int) -> str:
    p0 = sum(1 for s in scalability_signals if s.severity == "P0")
    p1 = sum(1 for s in scalability_signals if s.severity == "P1")

    if factor <= 2:
        if p0 == 0 and p1 <= 2:
            return "Ready"
        if p0 <= 1 and p1 <= 5:
            return "Minor work needed"
        return "Significant rework required"
    if factor <= 5:
        if p0 == 0 and p1 == 0:
            return "Ready"
        if p0 <= 1 and p1 <= 3:
            return "Minor work needed"
        if p0 <= 3:
            return "Significant rework required"
        return "Major re-architecture needed"
    # 10x
    if p0 == 0 and p1 <= 1:
        return "Ready"
    if p0 <= 2 and p1 <= 4:
        return "Significant rework required"
    return "Major re-architecture needed"
