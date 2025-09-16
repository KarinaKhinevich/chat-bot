"""
Pytest configuration and fixtures for the chat-bot application.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from chat_bot.main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    
    Returns:
        TestClient: Synchronous test client for FastAPI
    """
    return TestClient(app)


@pytest.fixture
async def async_client():
    """
    Create an async test client for the FastAPI application.
    
    Yields:
        AsyncClient: Asynchronous test client for FastAPI
    """
    from httpx import ASGITransport
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_health_response():
    """
    Sample health check response for testing.
    
    Returns:
        dict: Expected health check response
    """
    return {"status": "OK"}