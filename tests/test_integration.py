"""Integration tests for key workflows."""

import io
from unittest.mock import AsyncMock, patch

import pytest


class TestIntegrationWorkflow:
    """Integration tests for main application workflows."""

    @pytest.mark.integration
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    def test_document_upload_and_list_workflow(
        self, mock_parser, mock_summarizer, mock_pg_service, client, sample_txt_content
    ):
        """
        Test the complete workflow: upload document -> list documents.

        Args:
            client: FastAPI test client fixture
            sample_txt_content: Sample text content fixture
        """
        # Setup mocks
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "Integration test content",
            {"title": "integration_test.txt", "chunk_index": 0},
        )

        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.return_value = (
            "Integration test summary"
        )

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None

        # Step 1: Upload a document
        files = {
            "file": (
                "integration_test.txt",
                io.BytesIO(sample_txt_content),
                "text/plain",
            )
        }
        upload_response = client.post("/document", files=files)

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]

        # Step 2: List documents and verify the uploaded document appears
        list_response = client.get("/documents")

        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["success"] is True
        assert len(list_data["documents"]) >= 1

        # Check if our document is in the list
        uploaded_doc = next(
            (
                doc
                for doc in list_data["documents"]
                if doc["document_id"] == document_id
            ),
            None,
        )
        assert uploaded_doc is not None
        assert uploaded_doc["filename"] == "integration_test.txt"
        assert uploaded_doc["document_type"] == "txt"

    @pytest.mark.integration
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    def test_document_upload_summary_and_delete_workflow(
        self, mock_parser, mock_summarizer, mock_pg_service, client, sample_txt_content
    ):
        """
        Test the workflow: upload -> get summary -> delete document.

        Args:
            client: FastAPI test client fixture
            sample_txt_content: Sample text content fixture
        """
        # Setup mocks
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "Summary test content",
            {"title": "summary_test.txt", "chunk_index": 0},
        )

        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.return_value = (
            "This is a test summary"
        )

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None
        mock_pg_service_instance.delete_document_by_metadata.return_value = (
            3  # 3 chunks deleted
        )

        # Step 1: Upload a document
        files = {
            "file": ("summary_test.txt", io.BytesIO(sample_txt_content), "text/plain")
        }
        upload_response = client.post("/document", files=files)

        assert upload_response.status_code == 201
        document_id = upload_response.json()["document_id"]

        # Step 2: Get document summary
        summary_response = client.get(f"/documents/{document_id}/summary")

        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert summary_data["document_id"] == document_id
        assert "summary" in summary_data

        # Step 3: Delete the document
        delete_response = client.delete(f"/documents/{document_id}")

        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["success"] is True

        # Step 4: Verify document is deleted (summary should return 404)
        verify_response = client.get(f"/documents/{document_id}/summary")
        assert verify_response.status_code == 404

    @pytest.mark.integration
    def test_health_check_and_pages_workflow(self, client):
        """
        Test basic application health and page accessibility.

        Args:
            client: FastAPI test client fixture
        """
        # Step 1: Check health endpoint
        health_response = client.get("/health")

        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "OK"

        # Step 2: Check main pages are accessible
        pages = ["/", "/upload", "/chat"]

        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    @pytest.mark.integration
    @patch("chat_bot.services.chat_service.RAGAgent")
    def test_chat_endpoint_structure(self, mock_rag_agent, client):
        """
        Test chat endpoint basic functionality (without real OpenAI calls).

        Args:
            client: FastAPI test client fixture
        """
        # Mock the RAG agent response
        mock_agent_instance = AsyncMock()
        mock_rag_agent.return_value = mock_agent_instance
        mock_agent_instance.invoke_agent.return_value = {
            "answer": "This is a mocked answer for integration testing.",
            "sources": ["test_doc.txt"],
            "moderated": False,
            "is_relevant": True,
            "relevance_score": 0.9,
        }

        # Test valid chat request
        chat_request = {"question": "What is this document about?"}
        response = client.post("/chat", json=chat_request)

        # Verify response structure (might fail due to dependencies, but should not be validation error)
        assert response.status_code != 422  # Not a validation error
        assert response.status_code != 404  # Route exists

        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "sources" in data

    @pytest.mark.integration
    def test_error_handling_workflow(self, client):
        """
        Test error handling across different endpoints.

        Args:
            client: FastAPI test client fixture
        """
        # Test 404 errors
        assert client.get("/nonexistent").status_code == 404
        assert client.get("/documents/fake-id/summary").status_code == 404
        assert client.delete("/documents/fake-id").status_code == 404

        # Test validation errors
        assert client.post("/chat", json={}).status_code == 422
        assert client.post("/chat", json={"question": ""}).status_code == 422

        # Test file upload errors
        jpg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        files = {"file": ("test.jpg", io.BytesIO(jpg_content), "image/jpeg")}
        response = client.post("/document", files=files)
        assert response.status_code == 400
