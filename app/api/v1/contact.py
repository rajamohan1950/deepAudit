"""Contact form endpoint."""

import logging
from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)
router = APIRouter()

contact_submissions: list[dict] = []


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    company: str = Field(default="", max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactResponse(BaseModel):
    success: bool
    message: str


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_contact(body: ContactRequest):
    contact_submissions.append({
        "name": body.name,
        "email": body.email,
        "company": body.company,
        "message": body.message,
        "submitted_at": datetime.utcnow().isoformat(),
    })
    logger.info(f"Contact form submission from {body.email}")
    return ContactResponse(
        success=True,
        message="Thank you! We'll get back to you within 24 hours.",
    )
