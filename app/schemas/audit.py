import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.system_context import SystemContext


class AuditSource(BaseModel):
    type: Literal["github", "gitlab", "bitbucket", "upload"] = Field(
        ..., description="Source type for the codebase"
    )
    repo_url: str | None = Field(
        None, description="Repository URL (required for github/gitlab/bitbucket)"
    )
    branch: str | None = Field(
        None, description="Branch to audit. Defaults to repository default branch."
    )
    access_token: str | None = Field(
        None, description="Personal access token for private repositories"
    )
    paths_include: list[str] = Field(
        default=[],
        description="Only audit these paths (empty = entire repo)",
    )
    paths_exclude: list[str] = Field(
        default=["vendor/", "node_modules/", ".git/", "__pycache__/", "dist/", "build/"],
        description="Exclude these paths from audit",
    )


class AuditConfig(BaseModel):
    llm_provider: Literal["openai", "anthropic"] | None = Field(
        None, description="Override default LLM provider"
    )
    llm_model: str | None = Field(
        None, description="Override default LLM model"
    )
    categories: list[int] | Literal["all"] = Field(
        default="all", description="Categories to audit (1-40) or 'all'"
    )
    severity_filter: list[str] | None = Field(
        None, description="Only return signals of these severities: P0, P1, P2, P3"
    )
    max_signals_per_category: int = Field(
        default=30, ge=5, le=50, description="Target signals per category"
    )


class AuditCreate(BaseModel):
    source: AuditSource
    system_context: SystemContext
    config: AuditConfig = Field(default_factory=AuditConfig)


class AuditPhaseResponse(BaseModel):
    phase_number: int
    status: str
    categories_included: list[int]
    signals_found: int
    tokens_used: int
    cost_usd: float
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    source_config: dict
    system_context: dict
    audit_config: dict
    status: str
    current_phase: int
    total_signals: int
    total_tokens_used: int
    total_cost_usd: float
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    phases: list[AuditPhaseResponse] = []

    model_config = {"from_attributes": True}


class AuditListResponse(BaseModel):
    audits: list[AuditResponse]
    total: int
    page: int
    page_size: int


class AuditProgress(BaseModel):
    audit_id: uuid.UUID
    status: str
    current_phase: int
    total_phases: int = 10
    signals_so_far: int
    phases: list[AuditPhaseResponse]
