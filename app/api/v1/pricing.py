"""Premium pricing engine for PE/M&A technical due diligence and compliance readiness."""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

DD_TIERS = {
    "rapid_screen": {
        "name": "Rapid Screen",
        "price_range": "$25,000",
        "price_value": 25000,
        "scope": "Single repo, up to 200K LOC. Executive risk summary, risk heatmap, top 20 critical findings, investment impact assessment.",
        "delivery": "24 hours",
        "target": "Deal screening at LOI stage. Fast kill/proceed signal.",
    },
    "full_dd": {
        "name": "Full Technical DD",
        "price_range": "$50,000",
        "price_value": 50000,
        "scope": "Multi-repo (up to 5), unlimited LOC. All 40 categories, 11 deliverables, SPOF map, scalability assessment, remediation cost model.",
        "delivery": "48–72 hours",
        "target": "Confirmatory DD. Full technical risk picture for IC presentation.",
    },
    "enterprise_dd": {
        "name": "Enterprise DD",
        "price_range": "$75,000–$150,000",
        "price_value": 75000,
        "scope": "Unlimited repos, microservices architecture mapping, infrastructure assessment, team capability scoring, M&A integration risk analysis.",
        "delivery": "5–7 business days",
        "target": "Large-cap acquisitions ($200M+ deals). Complex multi-system environments.",
    },
    "portfolio_intelligence": {
        "name": "Portfolio Intelligence",
        "price_range": "$200,000/year",
        "price_value": 200000,
        "scope": "Quarterly assessment of up to 10 portfolio companies. Trend tracking. Risk regression alerts. Board-ready quarterly reports.",
        "delivery": "Ongoing",
        "target": "PE firms with active tech portfolio. Continuous risk monitoring.",
    },
}

COMPLIANCE_TIERS = {
    "single_framework": {
        "name": "Single Framework",
        "price_range": "$30,000",
        "price_value": 30000,
        "scope": "One framework (e.g., SOC2) against full codebase. Readiness score, control matrix, gap analysis, remediation roadmap, cost estimate.",
        "delivery": "48–72 hours",
        "frameworks": 1,
    },
    "multi_framework": {
        "name": "Multi-Framework Bundle",
        "price_range": "$50,000–$75,000",
        "price_value": 50000,
        "scope": "3–4 frameworks with cross-framework overlap analysis. Combined remediation roadmap. Unified cost-to-compliance model.",
        "delivery": "5 business days",
        "frameworks": 4,
    },
    "full_suite": {
        "name": "Full Compliance Suite",
        "price_range": "$100,000+",
        "price_value": 100000,
        "scope": "All 6 frameworks (SOC2, GDPR, HIPAA, DPDP, ISO27001, CCPA). Integration assessment. Vendor risk evaluation.",
        "delivery": "7–10 business days",
        "frameworks": 6,
    },
    "compliance_monitor": {
        "name": "Compliance Monitor",
        "price_range": "$150,000–$350,000/year",
        "price_value": 150000,
        "scope": "Ongoing quarterly reassessment across all frameworks. Drift detection. Audit trail for external auditors.",
        "delivery": "Continuous",
        "frameworks": 6,
    },
}

SUPPORTED_FRAMEWORKS = [
    {"id": "soc2", "name": "SOC 2 Type II", "jurisdiction": "Global (US origin)", "controls": 54},
    {"id": "gdpr", "name": "GDPR", "jurisdiction": "EU / EEA", "controls": 29},
    {"id": "hipaa", "name": "HIPAA", "jurisdiction": "United States", "controls": 29},
    {"id": "dpdp", "name": "DPDP Act", "jurisdiction": "India", "controls": 15},
    {"id": "iso27001", "name": "ISO 27001:2022", "jurisdiction": "Global", "controls": 93},
    {"id": "ccpa", "name": "CCPA / CPRA", "jurisdiction": "California, USA", "controls": 15},
]


class DDEstimate(BaseModel):
    tier: str
    tier_name: str
    base_price: int
    repo_count: int
    loc_estimate: int
    delivery: str
    includes: list[str]


class ComplianceEstimate(BaseModel):
    tier: str
    tier_name: str
    base_price: int
    frameworks: list[str]
    delivery: str
    includes: list[str]


@router.get("/dd-tiers")
async def get_dd_tiers():
    """Technical Due Diligence pricing tiers."""
    return {"tiers": DD_TIERS}


@router.get("/compliance-tiers")
async def get_compliance_tiers():
    """Compliance Readiness Audit pricing tiers."""
    return {"tiers": COMPLIANCE_TIERS}


@router.get("/frameworks")
async def get_frameworks():
    """Supported compliance frameworks."""
    return {"frameworks": SUPPORTED_FRAMEWORKS, "total_controls": 235}


@router.get("/dd-estimate")
async def estimate_dd(
    repos: int = Query(1, ge=1, le=50, description="Number of repositories"),
    loc: int = Query(100000, description="Estimated lines of code"),
    urgency: str = Query("standard", description="standard|expedited|urgent"),
):
    """Estimate DD engagement tier and pricing."""
    if repos == 1 and loc <= 200000:
        tier = "rapid_screen"
    elif repos <= 5:
        tier = "full_dd"
    else:
        tier = "enterprise_dd"

    tier_info = DD_TIERS[tier]
    base = tier_info["price_value"]

    urgency_mult = {"standard": 1.0, "expedited": 1.5, "urgent": 2.0}.get(urgency, 1.0)
    adjusted = int(base * urgency_mult)

    includes = [
        "Executive Summary with Investment Recommendation",
        "Risk Heatmap (40 categories)",
        "Single Point of Failure Map",
        "Remediation Roadmap with Cost Model",
    ]
    if tier in ("full_dd", "enterprise_dd"):
        includes.extend([
            "All 11 PE-Grade Deliverables",
            "Tech Debt Quantification",
            "Scalability Ceiling Analysis",
            "Compliance Readiness Overview",
        ])
    if tier == "enterprise_dd":
        includes.extend([
            "Microservices Architecture Map",
            "Infrastructure Assessment",
            "Team Capability Scoring",
            "M&A Integration Risk Analysis",
        ])

    return DDEstimate(
        tier=tier,
        tier_name=tier_info["name"],
        base_price=adjusted,
        repo_count=repos,
        loc_estimate=loc,
        delivery=tier_info["delivery"],
        includes=includes,
    )


@router.get("/compliance-estimate")
async def estimate_compliance(
    frameworks: str = Query("soc2", description="Comma-separated framework IDs"),
    loc: int = Query(100000, description="Estimated lines of code"),
):
    """Estimate compliance readiness assessment pricing."""
    fw_list = [f.strip() for f in frameworks.split(",") if f.strip()]
    fw_count = len(fw_list)

    if fw_count <= 1:
        tier = "single_framework"
    elif fw_count <= 4:
        tier = "multi_framework"
    else:
        tier = "full_suite"

    tier_info = COMPLIANCE_TIERS[tier]

    includes = [
        "Compliance Readiness Score (0–100) per framework",
        "Control Mapping Matrix",
        "Gap Severity Classification",
        "Remediation Roadmap",
        "Cost-to-Compliance Estimate",
    ]
    if fw_count > 1:
        includes.extend([
            "Cross-Framework Overlap Analysis",
            "Unified Remediation Priority",
            "Certification Timeline per Framework",
        ])

    return ComplianceEstimate(
        tier=tier,
        tier_name=tier_info["name"],
        base_price=tier_info["price_value"],
        frameworks=fw_list,
        delivery=tier_info["delivery"],
        includes=includes,
    )


@router.get("/unit-economics")
async def unit_economics():
    """Unit economics demonstrating software margins at consulting prices."""
    return {
        "tiers": [
            {"tier": "Rapid Screen", "revenue": 25000, "cogs_range": "$20–$80", "gross_margin": "99.7–99.9%"},
            {"tier": "Full Technical DD", "revenue": 50000, "cogs_range": "$80–$300", "gross_margin": "99.4–99.8%"},
            {"tier": "Enterprise DD", "revenue": "75K–150K", "cogs_range": "$200–$800", "gross_margin": "98.7–99.5%"},
            {"tier": "Portfolio Intelligence", "revenue": "200K/yr", "cogs_range": "$2K–$8K/yr", "gross_margin": "96–99%"},
        ],
        "insight": "Software margins applied to consulting-level pricing. Consulting-quality output at software-level COGS.",
    }
