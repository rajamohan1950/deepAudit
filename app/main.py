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
    logger.info("DeepAudit API starting up")

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
