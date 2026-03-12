import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # Ensure OpenAI key is available at startup
    import os
    if not settings.openai_api_key and os.environ.get("OPENAI_API_KEY"):
        settings.openai_api_key = os.environ["OPENAI_API_KEY"]
    logger.info(f"DeepAudit API starting up (LLM: {settings.default_llm_provider}/{settings.default_llm_model}, key_set={bool(settings.openai_api_key)})")

    from app.database import engine
    from app.models import audit, tenant, signal, report, artifact, category
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(
            tenant.Base.metadata.create_all
        )
        logger.info("Database tables ensured")

    from app.database import ensure_schema
    await ensure_schema()
    logger.info("Schema migrations ensured")

    from app.database import async_session_factory
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT count(*) FROM categories"))
        count = result.scalar()
        if count == 0:
            logger.info("Seeding audit categories...")
            from scripts.seed_categories import CATEGORIES
            from app.models.category import Category
            for cat_id, name, part, part_name, min_signals in CATEGORIES:
                session.add(Category(
                    id=cat_id, name=name, part=part,
                    part_name=part_name,
                    description=f"Category {cat_id}: {name}",
                    min_signals=min_signals, checklist=[],
                ))
            await session.commit()
            logger.info(f"Seeded {len(CATEGORIES)} categories")

    yield
    logger.info("DeepAudit API shutting down")


app = FastAPI(
    title="DeepAudit Intelligence Platform",
    description="Automated Technical Due Diligence & Compliance Readiness for PE/M&A",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_str = "".join(tb)
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    # Map known errors to human-readable messages
    msg = str(exc)
    if "UndefinedColumnError" in type(exc).__name__ or "UndefinedColumn" in msg:
        detail = "Database schema is out of date. The service is updating — please retry in 1 minute."
    elif "could not connect" in msg or "Connection refused" in msg:
        detail = "Database is temporarily unavailable. Please retry in a moment."
    elif "clone" in msg.lower() and ("fatal:" in msg or "failed" in msg.lower()):
        detail = "Failed to clone the repository. Please check the URL is correct and publicly accessible."
    else:
        detail = "An internal error occurred. Our team has been notified."
    return JSONResponse(
        status_code=500,
        content={
            "detail": detail,
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
            "traceback": tb_str[-2000:],
        },
    )


app.include_router(api_router, prefix="/api/v1")


@app.post("/_admin/config", include_in_schema=False)
async def admin_set_config(request: Request):
    """Hot-reload runtime config (secured by admin_secret)."""
    body = await request.json()
    secret = body.get("secret", "")
    if settings.admin_secret and secret != settings.admin_secret:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    updated = {}
    if "openai_api_key" in body:
        settings.openai_api_key = body["openai_api_key"]
        updated["openai_api_key"] = "***set***"
    if "anthropic_api_key" in body:
        settings.anthropic_api_key = body["anthropic_api_key"]
        updated["anthropic_api_key"] = "***set***"
    if "default_llm_provider" in body:
        settings.default_llm_provider = body["default_llm_provider"]
        updated["default_llm_provider"] = body["default_llm_provider"]
    if "default_llm_model" in body:
        settings.default_llm_model = body["default_llm_model"]
        updated["default_llm_model"] = body["default_llm_model"]
    has_key = bool(settings.openai_api_key and len(settings.openai_api_key) > 10)
    return {"updated": updated, "current_provider": settings.default_llm_provider, "current_model": settings.default_llm_model, "openai_key_set": has_key, "key_prefix": settings.openai_api_key[:12] + "..." if has_key else "EMPTY"}


@app.get("/_admin/test-llm", include_in_schema=False)
async def admin_test_llm():
    """Test LLM connectivity."""
    try:
        from app.engine.llm.client import LLMClient
        client = LLMClient()
        resp = await client.generate(
            system_prompt="You are a test bot. Always respond in JSON format.",
            user_prompt='Respond with a JSON object: {"status":"ok"}',
            max_tokens=20,
            temperature=0,
            json_mode=True,
        )
        return {
            "status": "ok",
            "provider": client.provider,
            "model": client.model,
            "response": resp.content[:100],
            "tokens": resp.total_tokens,
            "cost": resp.cost_usd,
            "key_set": bool(settings.openai_api_key),
        }
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "key_set": bool(settings.openai_api_key),
            "key_prefix": settings.openai_api_key[:15] + "..." if settings.openai_api_key else "EMPTY",
            "traceback": traceback.format_exc()[-1000:],
        })

@app.get("/_admin/audit-debug/{audit_id}", include_in_schema=False)
async def admin_audit_debug(audit_id: str):
    """Debug info for a specific audit."""
    from app.database import async_session_factory
    from sqlalchemy import select, func
    from app.models.audit import Audit, AuditPhase
    from app.models.signal import Signal
    import uuid

    async with async_session_factory() as db:
        result = await db.execute(select(Audit).where(Audit.id == uuid.UUID(audit_id)))
        audit = result.scalar_one_or_none()
        if not audit:
            return {"error": "Audit not found"}

        phases = await db.execute(
            select(AuditPhase).where(AuditPhase.audit_id == audit.id)
        )
        phase_list = phases.scalars().all()

        return {
            "audit_id": str(audit.id),
            "status": audit.status,
            "error_message": audit.error_message,
            "total_signals": audit.total_signals,
            "total_tokens": audit.total_tokens_used,
            "total_cost": audit.total_cost_usd,
            "started_at": str(audit.started_at) if audit.started_at else None,
            "completed_at": str(audit.completed_at) if audit.completed_at else None,
            "audit_config": audit.audit_config,
            "phases": [
                {
                    "phase_number": p.phase_number,
                    "status": p.status,
                    "categories": p.categories_included,
                    "signals_found": p.signals_found,
                    "tokens_used": p.tokens_used,
                    "error_message": p.error_message,
                }
                for p in phase_list
            ],
            "llm_config": {
                "provider": settings.default_llm_provider,
                "model": settings.default_llm_model,
                "key_set": bool(settings.openai_api_key),
                "key_prefix": settings.openai_api_key[:12] + "..." if settings.openai_api_key else "EMPTY",
            },
        }


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def landing_page():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "DeepAudit API", "docs": "/docs"}


@app.get("/audit", include_in_schema=False)
async def audit_dashboard():
    page = STATIC_DIR / "audit.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "Audit dashboard", "docs": "/docs"}


@app.get("/diligence", include_in_schema=False)
async def pe_landing():
    page = STATIC_DIR / "diligence.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "DeepAudit Due Diligence", "docs": "/docs"}


@app.get("/compliance", include_in_schema=False)
async def compliance_page():
    page = STATIC_DIR / "compliance.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "Compliance Readiness"}


@app.get("/methodology", include_in_schema=False)
async def methodology_page():
    page = STATIC_DIR / "methodology.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "DeepAudit Methodology", "docs": "/docs"}


@app.get("/terms", include_in_schema=False)
async def terms_page():
    page = STATIC_DIR / "terms.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "Terms of Service"}


@app.get("/privacy", include_in_schema=False)
async def privacy_page():
    page = STATIC_DIR / "privacy.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "Privacy Policy"}


@app.get("/nda", include_in_schema=False)
async def nda_page():
    page = STATIC_DIR / "nda.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "NDA Framework"}


@app.get("/sample-report", include_in_schema=False)
async def sample_report_page():
    page = STATIC_DIR / "sample-report.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "Sample Report"}


@app.get("/admin", include_in_schema=False)
async def admin_page():
    page = STATIC_DIR / "admin.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "Admin dashboard", "docs": "/docs"}


@app.get("/pe-report", include_in_schema=False)
async def pe_report_page():
    page = STATIC_DIR / "pe-report.html"
    if page.exists():
        return FileResponse(str(page))
    return {"message": "PE Report Viewer"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "deepaudit"}
