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
    """Run idempotent schema migrations — safe to call from any process."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'signals' AND column_name = 'category_id'
                ) THEN
                    ALTER TABLE signals ADD COLUMN category_id INTEGER REFERENCES categories(id);
                    CREATE INDEX IF NOT EXISTS ix_signals_category_id ON signals(category_id);
                END IF;
                UPDATE signals SET category_id = 1 WHERE category_id IS NULL;
            END $$;
        """))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
