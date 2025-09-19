"""Tests for DocumentService class."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from chat_bot.core import DocumentTypeEnum
from chat_bot.models import Document
from chat_bot.services.document_service import DocumentService


class TestDocumentService:
    """Test cases for the DocumentService class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_document_success(self, test_db, sample_txt_content):
        """
        Test successful document creation.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create mock file
        mock_file = AsyncMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = sample_txt_content
        mock_file.seek.return_value = None

        result = await service.create_document(
            file=mock_file, document_type=DocumentTypeEnum.TXT, summary="Test summary"
        )

        assert result.success is True
        assert result.filename == "test.txt"
        assert result.document_type == "txt"
        assert result.file_size == len(sample_txt_content)
        assert "document_id" in result.model_dump()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_document_by_id(self, test_db, sample_txt_content):
        """
        Test retrieving a document by ID.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create a document first
        document_id = uuid.uuid4()
        db_document = Document(
            id=document_id,
            filename=f"{document_id}.txt",
            original_filename="test.txt",
            file_size=len(sample_txt_content),
            document_type=DocumentTypeEnum.TXT,
            content=sample_txt_content,
            summary="Test summary",
            mime_type="text/plain",
            upload_timestamp=datetime.utcnow(),
        )

        test_db.add(db_document)
        await test_db.commit()

        # Retrieve the document
        retrieved_doc = await service.get_document(str(document_id))

        assert retrieved_doc is not None
        assert retrieved_doc.id == document_id
        assert retrieved_doc.original_filename == "test.txt"
        assert retrieved_doc.document_type == DocumentTypeEnum.TXT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, test_db):
        """
        Test retrieving a non-existent document.

        Args:
            test_db: Test database session fixture
        """
        service = DocumentService(test_db)

        fake_id = str(uuid.uuid4())
        retrieved_doc = await service.get_document(fake_id)

        assert retrieved_doc is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_documents_list(self, test_db, sample_txt_content):
        """
        Test retrieving a list of documents.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create multiple documents
        for i in range(3):
            document_id = uuid.uuid4()
            db_document = Document(
                id=document_id,
                filename=f"{document_id}.txt",
                original_filename=f"test_{i}.txt",
                file_size=len(sample_txt_content),
                document_type=DocumentTypeEnum.TXT,
                content=sample_txt_content,
                summary=f"Test summary {i}",
                mime_type="text/plain",
                upload_timestamp=datetime.utcnow(),
            )
            test_db.add(db_document)

        await test_db.commit()

        # Retrieve documents
        documents = await service.get_documents(skip=0, limit=10)

        assert len(documents) == 3
        assert all(doc.document_type == DocumentTypeEnum.TXT for doc in documents)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_documents_with_pagination(self, test_db, sample_txt_content):
        """
        Test retrieving documents with pagination.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create 5 documents
        for i in range(5):
            document_id = uuid.uuid4()
            db_document = Document(
                id=document_id,
                filename=f"{document_id}.txt",
                original_filename=f"test_{i}.txt",
                file_size=len(sample_txt_content),
                document_type=DocumentTypeEnum.TXT,
                content=sample_txt_content,
                summary=f"Test summary {i}",
                mime_type="text/plain",
                upload_timestamp=datetime.utcnow(),
            )
            test_db.add(db_document)

        await test_db.commit()

        # Test pagination
        first_page = await service.get_documents(skip=0, limit=2)
        second_page = await service.get_documents(skip=2, limit=2)

        assert len(first_page) == 2
        assert len(second_page) == 2
        assert first_page[0].id != second_page[0].id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_document_success(self, test_db, sample_txt_content):
        """
        Test successful document deletion.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create a document first
        document_id = uuid.uuid4()
        db_document = Document(
            id=document_id,
            filename=f"{document_id}.txt",
            original_filename="test.txt",
            file_size=len(sample_txt_content),
            document_type=DocumentTypeEnum.TXT,
            content=sample_txt_content,
            summary="Test summary",
            mime_type="text/plain",
            upload_timestamp=datetime.utcnow(),
        )

        test_db.add(db_document)
        await test_db.commit()

        # Delete the document
        result = await service.delete_document(str(document_id))

        assert result is True

        # Verify deletion
        retrieved_doc = await service.get_document(str(document_id))
        assert retrieved_doc is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, test_db):
        """
        Test deleting a non-existent document.

        Args:
            test_db: Test database session fixture
        """
        service = DocumentService(test_db)

        fake_id = str(uuid.uuid4())
        result = await service.delete_document(fake_id)

        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_document_content(self, test_db, sample_txt_content):
        """
        Test retrieving document content.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create a document first
        document_id = uuid.uuid4()
        db_document = Document(
            id=document_id,
            filename=f"{document_id}.txt",
            original_filename="test.txt",
            file_size=len(sample_txt_content),
            document_type=DocumentTypeEnum.TXT,
            content=sample_txt_content,
            summary="Test summary",
            mime_type="text/plain",
            upload_timestamp=datetime.utcnow(),
        )

        test_db.add(db_document)
        await test_db.commit()

        # Retrieve content
        content = await service.get_document_content(str(document_id))

        assert content == sample_txt_content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_document_summary(self, test_db, sample_txt_content):
        """
        Test retrieving document summary.

        Args:
            test_db: Test database session fixture
            sample_txt_content: Sample text content fixture
        """
        service = DocumentService(test_db)

        # Create a document first
        document_id = uuid.uuid4()
        test_summary = "This is a test summary"
        db_document = Document(
            id=document_id,
            filename=f"{document_id}.txt",
            original_filename="test.txt",
            file_size=len(sample_txt_content),
            document_type=DocumentTypeEnum.TXT,
            content=sample_txt_content,
            summary=test_summary,
            mime_type="text/plain",
            upload_timestamp=datetime.utcnow(),
        )

        test_db.add(db_document)
        await test_db.commit()

        # Retrieve summary
        summary = await service.get_document_summary(str(document_id))

        assert summary == test_summary
