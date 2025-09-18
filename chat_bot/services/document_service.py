"""
Document service for async database operations.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from chat_bot.core import DocumentTypeEnum
from chat_bot.models import Document
from chat_bot.schemas import DocumentUploadResponse

logger = logging.getLogger(__name__)


class DocumentService:
    """Service class for async document operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(
        self, file: UploadFile, document_type: DocumentTypeEnum, summary: str
    ) -> DocumentUploadResponse:
        """
        Create a new document in the database.

        Args:
            file: The uploaded file
            document_type: Type of the document (PDF or TXT)
            summary: Generated summary of the document

        Returns:
            DocumentUploadResponse: Information about the created document

        Raises:
            HTTPException: If document creation fails
        """
        try:
            # Read file content
            content = await file.read()

            # Reset file pointer for size calculation
            await file.seek(0)
            file_size = len(content)

            # Generate unique document ID
            document_id = uuid.uuid4()

            # Create document record
            db_document = Document(
                id=document_id,
                filename=f"{document_id}.{document_type.value}",
                original_filename=file.filename,
                file_size=file_size,
                document_type=document_type,
                content=content,
                summary=summary,  # Add the generated summary
                mime_type=file.content_type,
                upload_timestamp=datetime.utcnow(),
            )

            # Save to database
            self.db.add(db_document)
            await self.db.commit()
            await self.db.refresh(db_document)

            return DocumentUploadResponse(
                document_id=str(db_document.id),
                filename=db_document.original_filename,
                file_size=db_document.file_size,
                document_type=db_document.document_type.value,
                upload_timestamp=db_document.upload_timestamp,
                file_path=f"database://documents/{db_document.id}",
            )

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to save document to database: {str(e)}"
            )

    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: The document ID

        Returns:
            Optional[Document]: The document if found, None otherwise
        """
        try:
            doc_uuid = uuid.UUID(document_id)
            result = await self.db.execute(
                select(Document).filter(Document.id == doc_uuid)
            )
            return result.scalars().first()
        except ValueError:
            return None

    async def get_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get a list of documents.

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            List[Document]: List of documents
        """
        result = await self.db.execute(select(Document).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            document_id: The document ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            doc_uuid = uuid.UUID(document_id)

            # Use delete statement for async operation
            result = await self.db.execute(
                delete(Document).filter(Document.id == doc_uuid)
            )
            await self.db.commit()

            # Check if any rows were affected
            return result.rowcount > 0

        except ValueError:
            return False

    async def get_document_content(self, document_id: str) -> Optional[bytes]:
        """
        Get document content by ID.

        Args:
            document_id: The document ID

        Returns:
            Optional[bytes]: Document content if found, None otherwise
        """
        document = await self.get_document(document_id)
        return document.content if document else None

    async def get_document_summary(self, document_id: str) -> Optional[str]:
        """
        Get document summary by ID.

        Args:
            document_id: The document ID

        Returns:
            Optional[str]: Document summary if found, None otherwise
        """
        document = await self.get_document(document_id)
        return document.summary if document else None
