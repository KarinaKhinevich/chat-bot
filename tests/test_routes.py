"""
Tests for routes and endpoints.
"""

import pytest
from fastapi import status


class TestRoutes:
    """Test cases for application routes."""
    
    @pytest.mark.unit
    def test_home_route_returns_html(self, client):
        """
        Test that home route returns HTML response.
        
        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.integration
    async def test_home_route_async(self, async_client):
        """
        Test home route with async client.
        
        Args:
            async_client: Async FastAPI test client fixture
        """
        response = await async_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]