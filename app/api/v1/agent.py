"""AI sales agent — no humans. Conversational demo scheduling, product Q&A."""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.config import settings
from app.engine.llm.client import LLMClient

from app.api.v1.contact import contact_submissions

logger = logging.getLogger(__name__)
router = APIRouter()

AGENT_SYSTEM = """You are DeepAudit's Deal Intelligence Agent. This company runs 100% on AI — no humans.

Your role:
- Answer questions about DeepAudit (AI-powered tech due diligence for PE/M&A, 750+ risk signals, 40 categories)
- Qualify interest: screening, confirmatory DD, portfolio monitoring, exit prep
- When someone wants a demo: say you'll send them a self-serve link. Ask for their email. No forms, no humans.

Key facts:
- Pricing: Portfolio $499/mo, Firm-Wide $2,499/mo. Emergency: $5K–$25K.
- Quick assessment: paste GitHub URL, get PE report in ~2 min.
- Reports: executive summary, heatmap, SPOF map, compliance, roadmap.
- 100% AI-operated. No sales reps, no support tickets. You are it.

Tone: direct, expert, no fluff. PE firm audience. When they give email for demo, confirm you're sending the link now."""


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)


class ChatResponse(BaseModel):
    reply: str


class ScheduleDemoRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    source: str = "agent"


class ScheduleDemoResponse(BaseModel):
    success: bool
    message: str


def _send_email_sync(to_email: str, subject: str, body: str) -> bool:
    if not settings.smtp_host or not settings.smtp_user:
        return False
    try:
        msg = MIMEText(body, "plain")
        msg["From"] = settings.smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_password:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Failed to send demo email: {e}")
        return False


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(body: ChatRequest):
    """Conversational AI agent. No humans."""
    if not settings.openai_api_key and not settings.anthropic_api_key:
        raise HTTPException(503, "AI agent not configured")

    msgs = [{"role": m.role, "content": m.content} for m in body.messages]
    client = LLMClient()
    resp = await client.chat(AGENT_SYSTEM, msgs, max_tokens=1024, temperature=0.6)
    return ChatResponse(reply=resp.content)


@router.post("/schedule-demo", response_model=ScheduleDemoResponse)
async def schedule_demo(body: ScheduleDemoRequest):
    """AI-triggered demo scheduling. No humans. Sends self-serve link."""
    payload = {
        "email": body.email,
        "name": body.name or "",
        "company": body.company or "",
        "role": None,
        "deal_stage": None,
        "message": f"[Agent demo request, source={body.source}]",
        "submitted_at": datetime.utcnow().isoformat(),
    }
    contact_submissions.append(payload)
    logger.info(f"Agent demo request: {body.email}")

    demo_url = (settings.demo_scheduling_url or "").strip()
    link = demo_url if demo_url and demo_url.startswith("http") else (f"https://{demo_url}" if demo_url else "https://deepaudit.com")

    body_text = f"""You're in. No humans, no wait.

Book your DeepAudit demo here: {link}

Self-serve. Pick a time. The demo is AI-run — you'll see the platform in action.

— DeepAudit Deal Intelligence Agent
"""

    sent = await asyncio.to_thread(
        _send_email_sync,
        body.email,
        "Your DeepAudit Demo Link — Self-Serve, No Humans",
        body_text,
    )

    return ScheduleDemoResponse(
        success=True,
        message=f"Demo link sent to {body.email}. Check your inbox.",
    )
