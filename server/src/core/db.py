"""
Async SQLAlchemy engine, session factory and declarative base.
All ORM models import `Base` from here.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from .config import settings


class Base(DeclarativeBase):
    pass


# Engine — created lazily so settings are fully resolved first
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables. Called on server startup."""
    # Import models here to ensure they are registered on Base.metadata
    from ..models import db_user, db_repository, db_submission  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            columns = (await conn.execute(text("PRAGMA table_info(users)"))).all()
            existing = {row[1] for row in columns}
            if "intra_id" not in existing:
                await conn.execute(text("ALTER TABLE users ADD COLUMN intra_id INTEGER"))
            if "intra_login" not in existing:
                await conn.execute(text("ALTER TABLE users ADD COLUMN intra_login VARCHAR(255)"))
            await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_intra_id ON users (intra_id)"))
