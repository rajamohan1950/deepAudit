import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


REPORT_TYPES = Literal[
    "signal-table",
    "executive-summary",
    "risk-heatmap",
    "spof-map",
    "failure-catalog",
    "performance-profile",
    "aiml-risk-register",
    "cost-analysis",
    "observability-scorecard",
    "compliance-matrix",
    "remediation-roadmap",
]


class ReportResponse(BaseModel):
    id: uuid.UUID
    audit_id: uuid.UUID
    report_type: str
    content: dict
    generated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]


class ReportExportRequest(BaseModel):
    format: Literal["json", "csv", "pdf"] = "json"
