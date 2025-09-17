"""
File handling utilities for document uploads.
"""

import os
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException

from chat_bot.schemas import DocumentType


# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf": DocumentType.PDF,
    "text/plain": DocumentType.TXT,
}


def ensure_upload_directory():
    """Create upload directory if it doesn't exist."""
    UPLOAD_DIR.mkdir(exist_ok=True)


def validate_file(file: UploadFile) -> DocumentType:
    """
    Validate uploaded file.
    
    Args:
        file: The uploaded file
        
    Returns:
        DocumentType: The validated document type
        
    Raises:
        HTTPException: If file validation fails
    """
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Allowed types: PDF, TXT"
        )
    
    return ALLOWED_MIME_TYPES[content_type]


def generate_unique_filename(original_filename: str) -> Tuple[str, str]:
    """
    Generate a unique filename while preserving the original extension.
    
    Args:
        original_filename: The original filename
        
    Returns:
        Tuple[str, str]: (unique_filename, document_id)
    """
    document_id = str(uuid.uuid4())
    file_extension = Path(original_filename).suffix.lower()
    unique_filename = f"{document_id}{file_extension}"
    return unique_filename, document_id


async def save_uploaded_file(file: UploadFile, filename: str) -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file: The uploaded file
        filename: The filename to save as
        
    Returns:
        str: The file path where the file was saved
        
    Raises:
        HTTPException: If file saving fails
    """
    try:
        ensure_upload_directory()
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return str(file_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


def get_file_size(file_path: str) -> int:
    """
    Get the size of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)