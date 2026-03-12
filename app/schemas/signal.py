import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    id: uuid.UUID
    audit_id: uuid.UUID
    category_id: int | None = None
    category_name: str = ""
    sequence_number: int
    signal_text: str
    severity: str
    score: float
    score_type: str
    evidence: str
    failure_scenario: str
    remediation: str
    effort: str
    confidence: float
    references: list[str] = []
    phase_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SignalFilter(BaseModel):
    severity: list[str] | None = Field(None, description="P0, P1, P2, P3")
    category_ids: list[int] | None = Field(None, description="Category IDs 1-40")
    effort: list[str] | None = Field(None, description="S, M, L, XL")
    min_score: float | None = Field(None, ge=0, le=10)
    search: str | None = Field(None, description="Full-text search in signal text")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    sort_by: Literal[
        "sequence_number", "severity", "score", "category_id", "effort"
    ] = "sequence_number"
    sort_order: Literal["asc", "desc"] = "asc"


class SignalSummary(BaseModel):
    total: int
    by_severity: dict[str, int]
    by_category: dict[str, int]
    by_effort: dict[str, int]
    by_phase: dict[str, int]
    severity_distribution_valid: bool = Field(
        ..., description="True if P0:30-50, P1:100-150, P2:250-300, P3:150-200"
    )


class SignalListResponse(BaseModel):
    signals: list[SignalResponse]
    total: int
    page: int
    page_size: int
