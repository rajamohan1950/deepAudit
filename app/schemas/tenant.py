import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    plan: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantCreateResponse(BaseModel):
    tenant: TenantResponse
    api_key: str = Field(
        ..., description="API key — displayed only once at creation time"
    )


class TenantUsage(BaseModel):
    total_audits: int
    total_signals: int
    total_tokens_used: int
    total_cost_usd: float
