"""Tests for routes and endpoints."""

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

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_home_route_async(self, async_client):
        """
        Test home route with async client.

        Args:
            async_client: Async FastAPI test client fixture
        """
        response = await async_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.unit
    def test_upload_route_returns_html(self, client):
        """
        Test that upload route returns HTML response.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/upload")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_route_async(self, async_client):
        """
        Test upload route with async client.

        Args:
            async_client: Async FastAPI test client fixture
        """
        response = await async_client.get("/upload")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.unit
    def test_documents_list_route(self, client):
        """
        Test that documents list route returns JSON.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/documents")

        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers["content-type"]

        data = response.json()
        assert data["success"] is True
        assert "documents" in data
        assert "total" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_documents_list_route_async(self, async_client):
        """
        Test documents list route with async client.

        Args:
            async_client: Async FastAPI test client fixture
        """
        response = await async_client.get("/documents")

        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers["content-type"]

        data = response.json()
        assert data["success"] is True
        assert "documents" in data
        assert "total" in data

    @pytest.mark.unit
    def test_documents_list_with_pagination(self, client):
        """
        Test documents list with pagination parameters.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/documents?skip=0&limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.unit
    def test_document_summary_not_found(self, client):
        """
        Test document summary endpoint with non-existent document.

        Args:
            client: FastAPI test client fixture
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/documents/{fake_id}/summary")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.unit
    def test_document_delete_not_found(self, client):
        """
        Test document deletion with non-existent document.

        Args:
            client: FastAPI test client fixture
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/documents/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.unit
    def test_chat_route_returns_html(self, client):
        """
        Test that chat route returns HTML response.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/chat")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.unit
    def test_chat_post_endpoint_structure(self, client):
        """
        Test chat POST endpoint with valid request structure.

        Args:
            client: FastAPI test client fixture
        """
        chat_request = {"question": "What is this document about?"}

        # Note: This will likely fail due to OpenAI dependency, but tests the route structure
        response = client.post("/chat", json=chat_request)

        # Should not be 404 (route exists) or 422 (validation error)
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.unit
    def test_chat_post_invalid_request(self, client):
        """
        Test chat POST endpoint with invalid request.

        Args:
            client: FastAPI test client fixture
        """
        # Test empty question
        response = client.post("/chat", json={"question": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test missing question field
        response = client.post("/chat", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test question too long
        long_question = "x" * 501
        response = client.post("/chat", json={"question": long_question})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.unit
    def test_invalid_route_returns_404(self, client):
        """
        Test that invalid routes return 404.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/nonexistent-route")

        assert response.status_code == status.HTTP_404_NOT_FOUND
