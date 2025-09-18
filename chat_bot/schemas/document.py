"""Document upload related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response model for successful document upload."""

    success: bool = True
    message: str = "Document uploaded successfully"
    document_id: str = Field(
        ..., description="Unique identifier for the uploaded document"
    )
    filename: str = Field(..., description="Original filename of the uploaded document")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")
    document_type: str = Field(..., description="Type of the uploaded document")
    upload_timestamp: datetime = Field(
        default_factory=datetime.now, description="Upload timestamp"
    )
    file_path: str = Field(
        ..., description="Database reference where the file is stored"
    )


class DocumentUploadError(BaseModel):
    """Error response for document upload failures."""

    success: bool = False
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    details: Optional[str] = Field(None, description="Additional error details")


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""

    document_id: str
    summary: str
    filename: str
    file_size: int
    document_type: str
    upload_timestamp: datetime
    file_path: str


class DocumentListResponse(BaseModel):
    """Response model for document list."""

    success: bool = True
    documents: list[DocumentInfo] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class DocumentContentResponse(BaseModel):
    """Response model for document content retrieval."""

    document_id: str
    filename: str
    content_type: str
    file_size: int
