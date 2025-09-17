"""
API schemas package.

This package contains all Pydantic models used for request/response validation
and serialization in the FastAPI application.
"""

from .common import BaseResponse, ErrorResponse
from .document import (DocumentInfo, DocumentType, DocumentUploadError,
                       DocumentUploadResponse)
from .health import HealthCheck

__all__ = [
    "HealthCheck",
    "BaseResponse",
    "ErrorResponse",
    "DocumentUploadResponse",
    "DocumentUploadError",
    "DocumentInfo",
    "DocumentType",
]
