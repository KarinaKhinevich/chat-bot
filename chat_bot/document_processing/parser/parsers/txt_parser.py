"""
TXT parser class for plain text document parsing.

This module provides a parser implementation for plain text files (.txt).
It handles various text encodings and extracts content with basic metadata.
"""

import logging
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException
import chardet

from .base_parser import BaseParser

# Configure logger for this module
logger = logging.getLogger(__name__)


class TXTParser(BaseParser):
    """
    Parser implementation for plain text (.txt) documents.
    """
    
    async def parse(self, document: UploadFile) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a plain text document and extract its content and metadata.
        
        Args:
            document (UploadFile): The uploaded text document to parse.
        
        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - str: The decoded text content of the document
                - Dict[str, Any]: Metadata dictionary with keys:
                    - 'title': The original filename

        Raises:
            HTTPException: If the file cannot be read or decoded
            UnicodeDecodeError: If encoding detection fails completely
        """
        try:
            # Read the entire file content as bytes
            file_bytes = await document.read()
            await document.seek(0)

            if not file_bytes:
                logger.warning(f"Empty file detected: {document.filename}")
                return "", {"title": document.filename or "untitled.txt"}
            
            # Detect encoding using chardet library
            encoding_info = chardet.detect(file_bytes)
            detected_encoding = encoding_info.get("encoding", "utf-8")
            encoding_confidence = encoding_info.get("confidence", 0.0)
            
            # Decode content
            try:
                page_content = file_bytes.decode(detected_encoding, errors="ignore")
            except (UnicodeDecodeError, LookupError) as e:
                logger.warning(
                    f"Failed to decode with {detected_encoding}, falling back to UTF-8: {e}"
                )
                page_content = file_bytes.decode("utf-8", errors="ignore")
            
            # Prepare metadata with encoding information
            metadata: Dict[str, Any] = {
                "title": document.filename or "untitled.txt",
            }
            
            return page_content, metadata
            
        except Exception as e:
            error_message = f"Failed to parse TXT document {document.filename}: {str(e)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=422,
                detail=f"Text parsing error: {str(e)}"
            ) from e
