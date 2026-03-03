"""Contact form endpoint — stores submissions and optionally emails to configured address."""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

contact_submissions: list[dict] = []


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    company: str = Field(default="", max_length=200)
    role: str | None = Field(None, max_length=100)
    deal_stage: str | None = Field(None, max_length=100)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactResponse(BaseModel):
    success: bool
    message: str


def _send_email_sync(to_email: str, subject: str, body: str) -> bool:
    """Send email via SMTP. Returns True on success."""
    if not settings.smtp_host or not settings.smtp_user:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_password:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Failed to send contact notification email: {e}")
        return False


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_contact(body: ContactRequest):
    payload = {
        "name": body.name,
        "email": body.email,
        "company": body.company,
        "role": body.role,
        "deal_stage": body.deal_stage,
        "message": body.message,
        "submitted_at": datetime.utcnow().isoformat(),
    }
    contact_submissions.append(payload)
    logger.info(f"Contact form submission from {body.email}")

    notify_email = settings.contact_notification_email
    if notify_email:
        subject = f"DeepAudit Contact: {body.name} ({body.company or '—'})"
        body_text = f"""New contact form submission:

Name: {body.name}
Email: {body.email}
Company: {body.company or '—'}
Role: {body.role or '—'}
Deal Stage: {body.deal_stage or '—'}

Message:
{body.message}

Submitted: {payload['submitted_at']}
"""
        await asyncio.to_thread(_send_email_sync, notify_email, subject, body_text)

    return ContactResponse(
        success=True,
        message="Thank you! We'll get back to you within 24 hours.",
    )
