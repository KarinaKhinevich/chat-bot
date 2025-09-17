"""
Document upload related schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    TXT = "txt"


class DocumentUploadResponse(BaseModel):
    """Response model for successful document upload."""
    
    success: bool = True
    message: str = "Document uploaded successfully"
    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    filename: str = Field(..., description="Original filename of the uploaded document")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")
    document_type: DocumentType = Field(..., description="Type of the uploaded document")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    file_path: str = Field(..., description="Server path where the file is stored")


class DocumentUploadError(BaseModel):
    """Error response for document upload failures."""
    
    success: bool = False
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    details: Optional[str] = Field(None, description="Additional error details")


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""
    
    document_id: str
    filename: str
    file_size: int
    document_type: DocumentType
    upload_timestamp: datetime
    file_path: str