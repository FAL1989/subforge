"""
Database session management and connection handling
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings

# Synchronous engine and session
engine = create_engine(
    settings.get_database_url(),
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

# Asynchronous engine and session
async_engine = create_async_engine(
    settings.get_async_database_url(),
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()