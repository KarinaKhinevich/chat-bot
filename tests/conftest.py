"""Pytest configuration and fixtures for the chat-bot application."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from chat_bot.database import get_db
from chat_bot.main import app
from chat_bot.models import Base

# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_chat_bot.db"

# Create async test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session factory for testing
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_test_db():
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create and clean up test database for each test."""
    # Create tables using only the test engine (SQLite)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with TestSessionLocal() as session:
        yield session

    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Synchronous test client for FastAPI
    """
    # Override database dependency
    app.dependency_overrides[get_db] = get_test_db

    # Create tables before each test
    import asyncio

    # Run async table creation in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Create tables using the same engine as the test database
    async def create_test_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop.run_until_complete(create_test_tables())

    client = TestClient(app)
    yield client

    # Clean up tables and override
    async def cleanup_test_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    loop.run_until_complete(cleanup_test_tables())
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client():
    """
    Create an async test client for the FastAPI application.

    Yields:
        AsyncClient: Asynchronous test client for FastAPI
    """
    # Override database dependency
    app.dependency_overrides[get_db] = get_test_db

    # Create tables before the test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clean up tables and override
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_health_response():
    """
    Sample health check response for testing.

    Returns:
        dict: Expected health check response
    """
    return {"status": "OK"}


@pytest.fixture
def sample_pdf_content():
    """
    Sample PDF content for testing.

    Returns:
        bytes: Mock PDF file content
    """
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000173 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n293\n%%EOF"


@pytest.fixture
def sample_txt_content():
    """
    Sample text content for testing.

    Returns:
        bytes: Mock text file content
    """
    return b"This is a sample text document for testing purposes. It contains some content to test the document processing functionality."


@pytest.fixture
def sample_chat_request():
    """
    Sample chat request for testing.

    Returns:
        dict: Sample chat request data
    """
    return {"question": "What is this document about?"}


@pytest.fixture
def sample_chat_response():
    """
    Sample chat response for testing.

    Returns:
        dict: Sample chat response data
    """
    return {
        "answer": "This document is about testing the chat functionality.",
        "sources": ["test_document.txt", "another_document.pdf"]
    }


@pytest.fixture
def sample_document_metadata():
    """
    Sample document metadata for testing.

    Returns:
        dict: Sample metadata
    """
    return {
        "document_id": "test-document-id",
        "filename": "test.txt",
        "content_type": "text/plain",
        "chunk_index": 0,
        "total_chunks": 1
    }
