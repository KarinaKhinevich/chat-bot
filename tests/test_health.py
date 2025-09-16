"""
Tests for health check endpoint.
"""

import pytest
from fastapi import status


class TestHealthCheck:
    """Test cases for the health check endpoint."""
    
    @pytest.mark.unit
    def test_health_check_success(self, client):
        """
        Test that health check endpoint returns success response.
        
        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "OK"}
    
    @pytest.mark.unit
    async def test_health_check_async(self, async_client):
        """
        Test health check endpoint with async client.
        
        Args:
            async_client: Async FastAPI test client fixture
        """
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "OK"}
    
    @pytest.mark.unit
    def test_health_check_response_structure(self, client, sample_health_response):
        """
        Test that health check response matches expected structure.
        
        Args:
            client: FastAPI test client fixture
            sample_health_response: Expected response fixture
        """
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == sample_health_response