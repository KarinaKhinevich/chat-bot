"""Tests for document upload functionality."""

import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


class TestDocumentUpload:
    """Test cases for the document upload endpoint."""

    @pytest.mark.unit
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    def test_upload_txt_success(
        self, mock_parser, mock_summarizer, mock_pg_service, client, sample_txt_content
    ):
        """
        Test successful TXT file upload.

        Args:
            client: FastAPI test client fixture
            sample_txt_content: Sample text content fixture
        """
        # Setup mocks
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "Test content",
            {"title": "test.txt", "chunk_index": 0},
        )

        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.return_value = "Test summary"

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None

        # Create test file
        files = {"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")}

        response = client.post("/document", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "test.txt"
        assert data["document_type"] == "txt"
        assert "document_id" in data

    @pytest.mark.unit
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    def test_upload_pdf_success(
        self, mock_parser, mock_summarizer, mock_pg_service, client, sample_pdf_content
    ):
        """
        Test successful PDF file upload.

        Args:
            client: FastAPI test client fixture
            sample_pdf_content: Sample PDF content fixture
        """
        # Setup mocks
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "PDF content",
            {"title": "test.pdf", "chunk_index": 0},
        )

        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.return_value = "PDF summary"

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None

        # Create test file
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }

        response = client.post("/document", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "test.pdf"
        assert data["document_type"] == "pdf"
        assert "document_id" in data

    @pytest.mark.unit
    def test_upload_invalid_file_type(self, client):
        """
        Test upload with invalid file type.

        Args:
            client: FastAPI test client fixture
        """
        # Create invalid file type
        jpg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        files = {"file": ("test.jpg", io.BytesIO(jpg_content), "image/jpeg")}

        response = client.post("/document", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "File type not supported" in data["detail"]

    @pytest.mark.unit
    def test_upload_oversized_file(self, client):
        """
        Test upload with file exceeding size limit.

        Args:
            client: FastAPI test client fixture
        """
        # Create oversized file (>10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}

        response = client.post("/document", files=files)

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        data = response.json()
        assert "File size too large" in data["detail"]

    @pytest.mark.unit
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    def test_upload_with_summary_generation_failure(
        self, mock_parser, mock_summarizer, mock_pg_service, client, sample_txt_content
    ):
        """
        Test upload when summary generation fails but upload continues.

        Args:
            client: FastAPI test client fixture
            sample_txt_content: Sample text content fixture
        """
        # Setup mocks
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "Test content",
            {"title": "test.txt", "chunk_index": 0},
        )

        # Make summary generation fail
        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.side_effect = Exception("Summary generation failed")

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None

        # Create test file
        files = {"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")}

        response = client.post("/document", files=files)

        # Should still succeed even if summary generation fails
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True

    @pytest.mark.unit
    def test_list_documents_empty(self, client):
        """
        Test listing documents when database is empty.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["documents"] == []
        assert data["total"] == 0

    @pytest.mark.unit
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    def test_list_documents_with_content(
        self, mock_parser, mock_summarizer, mock_pg_service, client, sample_txt_content
    ):
        """
        Test listing documents after uploading one.

        Args:
            client: FastAPI test client fixture
            sample_txt_content: Sample text content fixture
        """
        # Setup mocks for upload
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "Test content",
            {"title": "test.txt", "chunk_index": 0},
        )

        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.return_value = "Test summary"

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None

        # Upload a document first
        files = {"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")}
        upload_response = client.post("/document", files=files)
        assert upload_response.status_code == status.HTTP_201_CREATED

        # Then list documents
        response = client.get("/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["documents"]) >= 1
        assert data["total"] >= 1

        # Check document structure
        document = data["documents"][0]
        assert "document_id" in document
        assert document["filename"] == "test.txt"
        assert document["document_type"] == "txt"

    @pytest.mark.unit
    def test_upload_page_accessible(self, client):
        """
        Test that upload page is accessible.

        Args:
            client: FastAPI test client fixture
        """
        response = client.get("/upload")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    @patch("chat_bot.routes.PGDocumentService")
    @patch("chat_bot.routes.Summarizer")
    @patch("chat_bot.routes.DocumentParser")
    async def test_upload_async(
        self,
        mock_parser,
        mock_summarizer,
        mock_pg_service,
        async_client,
        sample_txt_content,
    ):
        """
        Test document upload with async client.

        Args:
            async_client: Async FastAPI test client fixture
            sample_txt_content: Sample text content fixture
        """
        # Setup mocks
        mock_parser_instance = AsyncMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = (
            "Async test content",
            {"title": "async_test.txt", "chunk_index": 0},
        )

        mock_summarizer_instance = AsyncMock()
        mock_summarizer.return_value = mock_summarizer_instance
        mock_summarizer_instance.summarize_document.return_value = "Async test summary"

        mock_pg_service_instance = AsyncMock()
        mock_pg_service.return_value = mock_pg_service_instance
        mock_pg_service_instance.create_document.return_value = None

        # Create test file
        files = {
            "file": ("async_test.txt", io.BytesIO(sample_txt_content), "text/plain")
        }

        response = await async_client.post("/document", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "async_test.txt"
