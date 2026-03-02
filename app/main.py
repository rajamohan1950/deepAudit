import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    title="DeepAudit API",
    description="Comprehensive Software Deep Audit SaaS — 750+ signals across 40 categories",
    version="1.0.0",
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

app.include_router(api_router, prefix="/api/v1")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def landing_page():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "DeepAudit API", "docs": "/docs"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "deepaudit"}
