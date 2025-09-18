"""Database connection and session management with async SQLAlchemy."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from langchain_postgres import PGEngine

from chat_bot.config import DBSettings
from chat_bot.models import Base

# Initialize database settings
db_settings = DBSettings()

# Create async database engine with asyncpg driver
# Convert postgresql:// to postgresql+asyncpg://
async_db_url = db_settings.URL

# Create async engine
engine = create_async_engine(
    db_settings.URL,
    poolclass=StaticPool,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)
# Initialize PGEngine for vector storage
pg_engine = PGEngine.from_connection_string(url=db_settings.URL)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_tables():
    """Create all database tables asynchronously."""
    # Create SQLAlchemy tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create vector table separately (PGEngine manages its own connections)
    try:
        # Check if vector table exists using a separate connection
        async with engine.begin() as conn:

            def check_table(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.has_table(db_settings.VECTOR_TABLE_NAME)

            exists = await conn.run_sync(check_table)

        if not exists:
            # PGEngine handles its own connection management
            await pg_engine.ainit_vectorstore_table(
                table_name=db_settings.VECTOR_TABLE_NAME,
                vector_size=db_settings.VECTOR_SIZE,
            )
            logger.info("Vector table created.")
        else:
            logger.info("Vector table already exists. Skipping creation.")
    except Exception as e:
        logger.error(f"Error creating vector table: {e}")
        # Continue startup even if vector table creation fails
        logger.warning("Continuing startup without vector table")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database dependency for FastAPI.

    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Yields:
        AsyncSession: SQLAlchemy async database session
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
