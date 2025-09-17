"""
File handling utilities for document uploads.
"""

from pathlib import Path

from fastapi import HTTPException, UploadFile

from chat_bot.core import DocumentTypeEnum
from chat_bot.core import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_FILE_SIZE




def validate_file(file: UploadFile) -> DocumentTypeEnum:
    """
    Validate uploaded file.

    Args:
        file: The uploaded file

    Returns:
        DocumentTypeEnum: The validated document type

    Raises:
        HTTPException: If file validation fails
    """
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Allowed types: PDF, TXT",
        )

    return ALLOWED_MIME_TYPES[content_type]
