"""Dynamic pricing engine — calculates audit cost based on repo size, urgency, and scope."""

import logging
import math

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

SIZE_MULTIPLIERS = [
    (50_000, 1.0),
    (200_000, 1.5),
    (1_000_000, 2.5),
    (5_000_000, 4.0),
]

URGENCY_MULTIPLIERS = {
    "standard": 1.0,
    "priority": 2.0,
    "emergency": 5.0,
    "instant": 10.0,
}

SLA_LABELS = {
    "standard": "24 hours",
    "priority": "4 hours",
    "emergency": "1 hour",
    "instant": "30 minutes",
}

VOLUME_DISCOUNTS = [
    (100, 0.40),
    (50, 0.30),
    (10, 0.15),
]

PLANS = {
    "free": {
        "name": "Free",
        "base_price": 0,
        "audits_per_month": 1,
        "max_loc": 50_000,
        "categories": 10,
        "reports": 3,
        "private_repos": False,
        "features": ["Public repos only", "Security basics (10 categories)", "3 reports", "Community support"],
    },
    "starter": {
        "name": "Starter",
        "base_price": 99,
        "annual_price": 79,
        "audits_per_month": 5,
        "max_loc": 200_000,
        "categories": 40,
        "reports": 11,
        "private_repos": True,
        "features": ["Public + private repos", "All 40 categories", "All 11 reports", "Email support", "Up to 200K LOC"],
    },
    "pro": {
        "name": "Pro",
        "base_price": 499,
        "annual_price": 399,
        "audits_per_month": 20,
        "max_loc": None,
        "categories": 40,
        "reports": 11,
        "private_repos": True,
        "features": ["Unlimited LOC", "Custom rules", "CSV/PDF export", "Priority queue (2x faster)", "CI/CD integration", "Slack/webhook alerts"],
    },
    "enterprise": {
        "name": "Enterprise",
        "base_price": 2499,
        "annual_price": 1999,
        "audits_per_month": None,
        "max_loc": None,
        "categories": 40,
        "reports": 11,
        "private_repos": True,
        "features": ["Unlimited audits", "White-label reports", "1-hour SLA", "SSO/SAML", "Dedicated account manager", "SOC2/HIPAA compliance package", "Custom categories"],
    },
}


class PriceEstimate(BaseModel):
    plan: str
    base_price_monthly: float
    size_multiplier: float
    urgency_multiplier: str
    urgency_label: str
    volume_discount_pct: float
    estimated_price: float
    per_audit_price: float
    annual_savings_pct: float


def _size_multiplier(loc: int) -> float:
    for threshold, mult in SIZE_MULTIPLIERS:
        if loc <= threshold:
            return mult
    return 6.0


@router.get("/plans")
async def get_plans():
    return {"plans": PLANS}


@router.get("/estimate")
async def estimate_price(
    loc: int = Query(10000, description="Lines of code in the repo"),
    urgency: str = Query("standard", description="standard|priority|emergency|instant"),
    audits_per_month: int = Query(1, ge=1),
    plan: str = Query("starter", description="free|starter|pro|enterprise"),
):
    plan_info = PLANS.get(plan, PLANS["starter"])
    base = plan_info["base_price"]
    size_mult = _size_multiplier(loc)
    urg_mult = URGENCY_MULTIPLIERS.get(urgency, 1.0)

    vol_discount = 0.0
    for threshold, discount in VOLUME_DISCOUNTS:
        if audits_per_month >= threshold:
            vol_discount = discount
            break

    if plan == "free":
        per_audit = 0
        monthly = 0
    else:
        per_audit = base * size_mult * urg_mult / max(plan_info.get("audits_per_month") or audits_per_month, 1)
        monthly = base * size_mult * urg_mult * (1 - vol_discount)

    annual_price = plan_info.get("annual_price", base)
    annual_savings = round((1 - annual_price / base) * 100, 1) if base > 0 else 0

    return PriceEstimate(
        plan=plan_info["name"],
        base_price_monthly=base,
        size_multiplier=size_mult,
        urgency_multiplier=urgency,
        urgency_label=SLA_LABELS.get(urgency, "24 hours"),
        volume_discount_pct=vol_discount * 100,
        estimated_price=round(monthly, 2),
        per_audit_price=round(per_audit, 2),
        annual_savings_pct=annual_savings,
    )
