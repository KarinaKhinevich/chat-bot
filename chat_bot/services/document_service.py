"""
Document service for database operations.
"""

from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import uuid
from datetime import datetime

from chat_bot.core import DocumentTypeEnum
from chat_bot.models import Document
from chat_bot.schemas import DocumentUploadResponse
from .openai_service import summarize_document

logger = logging.getLogger(__name__)

class DocumentService:
    """Service class for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_document(self, file: UploadFile, document_type: DocumentTypeEnum) -> DocumentUploadResponse:
        """
        Create a new document in the database.
        
        Args:
            file: The uploaded file
            document_type: Type of the document (PDF or TXT)
            
        Returns:
            DocumentUploadResponse: Information about the created document
            
        Raises:
            HTTPException: If document creation fails
        """
        try:
            # Read file content
            content = await file.read()
            
            # Generate summary using OpenAI (with fallback)
            try:
                summary = await summarize_document(content)
            except Exception as e:
                # If summary generation fails, use empty string
                summary = ""
                logger.warning(f"Failed to generate summary: {str(e)}")
            
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
                upload_timestamp=datetime.utcnow()
            )
            
            # Save to database
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            return DocumentUploadResponse(
                document_id=str(db_document.id),
                filename=db_document.original_filename,
                file_size=db_document.file_size,
                document_type=db_document.document_type.value,
                upload_timestamp=db_document.upload_timestamp,
                file_path=f"database://documents/{db_document.id}"
            )
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save document to database: {str(e)}"
            )
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Optional[Document]: The document if found, None otherwise
        """
        try:
            doc_uuid = uuid.UUID(document_id)
            return self.db.query(Document).filter(Document.id == doc_uuid).first()
        except ValueError:
            return None
    
    def get_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get a list of documents.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List[Document]: List of documents
        """
        return self.db.query(Document).offset(skip).limit(limit).all()
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            doc_uuid = uuid.UUID(document_id)
            document = self.db.query(Document).filter(Document.id == doc_uuid).first()
            
            if document:
                self.db.delete(document)
                self.db.commit()
                return True
            return False
            
        except ValueError:
            return False
    
    def get_document_content(self, document_id: str) -> Optional[bytes]:
        """
        Get document content by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Optional[bytes]: Document content if found, None otherwise
        """
        document = self.get_document(document_id)
        return document.content if document else None
    
    def get_document_summary(self, document_id: str) -> Optional[str]:
        """
        Get document summary by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Optional[str]: Document summary if found, None otherwise
        """
        document = self.get_document(document_id)
        return document.summary if document else None