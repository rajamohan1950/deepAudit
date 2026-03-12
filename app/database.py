from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def ensure_schema() -> None:
    """Drop and recreate tables with wrong schema so create_all() rebuilds them."""
    from sqlalchemy import text, inspect

    async with engine.begin() as conn:
        def _check_columns(sync_conn):
            insp = inspect(sync_conn)
            if not insp.has_table("signals"):
                return True  # table doesn't exist, create_all will handle it
            cols = {c["name"] for c in insp.get_columns("signals")}
            required = {"id", "audit_id", "category_id", "sequence_number", "signal_text", "severity"}
            return required.issubset(cols)

        schema_ok = await conn.run_sync(_check_columns)

        if not schema_ok:
            await conn.execute(text("DROP TABLE IF EXISTS signals CASCADE"))

    # Now let create_all rebuild it with the correct schema
    async with engine.begin() as conn:
        from app.database import Base
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
