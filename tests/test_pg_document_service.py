"""Tests for PGDocumentService (vector store functionality)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from chat_bot.services.pg_document_service import PGDocumentService


class TestPGDocumentService:
    """Test cases for the PGDocumentService class."""

    @pytest.mark.unit
    def test_pg_document_service_initialization(self):
        """Test PGDocumentService initialization."""
        mock_engine = MagicMock(spec=AsyncEngine)
        service = PGDocumentService(mock_engine)

        assert service.pg_engine == mock_engine
        assert service is not None
        assert hasattr(service, "chunker")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_document_success(self):
        """Test successful document creation in vector store."""
        mock_engine = MagicMock(spec=AsyncEngine)

        # Mock the initialization to avoid OpenAI API calls
        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings, patch(
            "chat_bot.services.pg_document_service.DocumentChunker"
        ) as mock_chunker_class, patch.object(
            PGDocumentService, "init_pgvector"
        ) as mock_init_pgvector:
            # Setup mocks
            mock_embeddings_instance = MagicMock()
            mock_embeddings.return_value = mock_embeddings_instance

            mock_chunker = MagicMock()
            mock_chunker_class.return_value = mock_chunker
            mock_chunker.index_document.return_value = [
                {"content": "chunk1", "metadata": {"chunk_index": 0}},
                {"content": "chunk2", "metadata": {"chunk_index": 1}},
            ]

            mock_vectorstore = AsyncMock()
            mock_init_pgvector.return_value = mock_vectorstore
            mock_vectorstore.aadd_documents.return_value = None

            service = PGDocumentService(mock_engine)

            page_content = "This is test document content for vector storage."
            metadata = {"document_id": "test-id", "filename": "test.txt"}

            await service.create_document(page_content, metadata)

            mock_chunker.index_document.assert_called_once_with(page_content, metadata)
            mock_vectorstore.aadd_documents.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_document_by_metadata_success(self):
        """Test successful document deletion by metadata."""
        mock_engine = MagicMock(spec=AsyncEngine)

        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings, patch(
            "chat_bot.services.pg_document_service.DocumentChunker"
        ) as mock_chunker_class, patch(
            "chat_bot.services.pg_document_service.engine"
        ) as mock_db_engine:
            # Setup mocks
            mock_embeddings_instance = MagicMock()
            mock_embeddings.return_value = mock_embeddings_instance

            mock_chunker = MagicMock()
            mock_chunker_class.return_value = mock_chunker

            # Mock database connection
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 5
            mock_conn.execute.return_value = mock_result
            mock_db_engine.begin.return_value.__aenter__.return_value = mock_conn

            service = PGDocumentService(mock_engine)

            deleted_count = await service.delete_document_by_metadata("test-doc-id")

            assert deleted_count == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_document_empty_content(self):
        """Test creating document with empty content."""
        mock_engine = MagicMock(spec=AsyncEngine)

        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings, patch(
            "chat_bot.services.pg_document_service.DocumentChunker"
        ) as mock_chunker_class, patch.object(
            PGDocumentService, "init_pgvector"
        ) as mock_init_pgvector:
            # Setup mocks
            mock_embeddings_instance = MagicMock()
            mock_embeddings.return_value = mock_embeddings_instance

            mock_chunker = MagicMock()
            mock_chunker_class.return_value = mock_chunker
            mock_chunker.index_document.return_value = []  # No chunks for empty content

            mock_vectorstore = AsyncMock()
            mock_init_pgvector.return_value = mock_vectorstore

            service = PGDocumentService(mock_engine)

            # Should handle empty content gracefully
            await service.create_document("", {"document_id": "empty-doc"})

            mock_chunker.index_document.assert_called_once_with(
                "", {"document_id": "empty-doc"}
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_document_chunking_error(self):
        """Test error handling during document chunking."""
        mock_engine = MagicMock(spec=AsyncEngine)

        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings, patch(
            "chat_bot.services.pg_document_service.DocumentChunker"
        ) as mock_chunker_class:
            # Setup mocks
            mock_embeddings_instance = MagicMock()
            mock_embeddings.return_value = mock_embeddings_instance

            mock_chunker = MagicMock()
            mock_chunker_class.return_value = mock_chunker
            mock_chunker.index_document.side_effect = Exception("Chunking failed")

            service = PGDocumentService(mock_engine)

            # The chunking happens outside the try-catch, so we get the raw exception
            with pytest.raises(Exception) as exc_info:
                await service.create_document("test content", {"document_id": "test"})

            assert "Chunking failed" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        """Test deleting a document that doesn't exist."""
        mock_engine = MagicMock(spec=AsyncEngine)

        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings, patch(
            "chat_bot.services.pg_document_service.DocumentChunker"
        ) as mock_chunker_class, patch(
            "chat_bot.services.pg_document_service.engine"
        ) as mock_db_engine:
            # Setup mocks
            mock_embeddings_instance = MagicMock()
            mock_embeddings.return_value = mock_embeddings_instance

            mock_chunker = MagicMock()
            mock_chunker_class.return_value = mock_chunker

            # Mock database connection
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 0  # No chunks deleted
            mock_conn.execute.return_value = mock_result
            mock_db_engine.begin.return_value.__aenter__.return_value = mock_conn

            service = PGDocumentService(mock_engine)

            deleted_count = await service.delete_document_by_metadata("nonexistent-id")

            assert deleted_count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vector_store_initialization_error(self):
        """Test error handling during vector store initialization."""
        mock_engine = MagicMock(spec=AsyncEngine)

        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings:
            # Make OpenAI embeddings initialization fail
            mock_embeddings.side_effect = Exception("OpenAI API key not found")

            with pytest.raises(Exception) as exc_info:
                PGDocumentService(mock_engine)

            assert "OpenAI API key not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_chunk_document_basic(self):
        """Test basic document chunking functionality."""
        mock_engine = MagicMock(spec=AsyncEngine)

        with patch(
            "chat_bot.services.pg_document_service.OpenAIEmbeddings"
        ) as mock_embeddings, patch(
            "chat_bot.services.pg_document_service.DocumentChunker"
        ) as mock_chunker_class:
            # Setup mocks
            mock_embeddings_instance = MagicMock()
            mock_embeddings.return_value = mock_embeddings_instance

            mock_chunker = MagicMock()
            mock_chunker_class.return_value = mock_chunker
            mock_chunker.index_document.return_value = [
                {"content": "chunk1", "metadata": {"chunk_index": 0}},
                {"content": "chunk2", "metadata": {"chunk_index": 1}},
            ]

            service = PGDocumentService(mock_engine)

            # This test verifies the service can handle chunking setup
            assert service is not None
            assert service.pg_engine == mock_engine
            assert hasattr(service, "chunker")
