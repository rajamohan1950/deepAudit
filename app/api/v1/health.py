from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session_factory

router = APIRouter()


@router.get("/ready")
async def readiness_check():
    checks = {"database": False, "status": "unhealthy"}
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    all_healthy = checks["database"]
    checks["status"] = "healthy" if all_healthy else "unhealthy"
    return checks
