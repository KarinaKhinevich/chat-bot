"""
PDF parser class for Portable Document Format parsing.

This module provides a parser implementation for PDF files using pdfplumber.
It extracts text content from all pages and basic metadata from the document.
"""

import io
import logging
from typing import Any, Dict, Tuple

import pdfplumber
from fastapi import HTTPException, UploadFile

from .base_parser import BaseParser

# Configure logger for this module
logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Parser implementation for PDF documents using pdfplumber."""

    async def parse(self, document: UploadFile) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a PDF document and extract text content and metadata.

        Args:
            document (UploadFile): The uploaded PDF document to parse.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - str: Concatenated text content from all pages
                - Dict[str, Any]: Metadata dictionary with keys:
                    - 'title': The original filename

        Raises:
            HTTPException: If the PDF cannot be opened, read, or is corrupted
            ValueError: If the file is not a valid PDF format
        """
        try:
            # Read the entire PDF file into memory as bytes
            file_bytes = await document.read()
            await document.seek(0)

            if not file_bytes:
                logger.warning(f"Empty file detected: {document.filename}")
                return "", {"title": document.filename or "untitled.pdf"}

            page_content: str = ""
            # Use pdfplumber to open and process the PDF
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                # Extract text from each page
                for page in pdf.pages:
                    try:
                        # Extract text from current page
                        page_text = page.extract_text()

                        if page_text and page_text.strip():
                            # Page contains extractable text
                            page_content += page_text.strip()

                    except Exception as page_error:
                        # Handle individual page extraction errors
                        logger.warning(
                            f"Error extracting text from page: {str(page_error)}"
                        )

            # Prepare metadata
            metadata: Dict[str, Any] = {
                "title": document.filename or "untitled.pdf",
            }

            return page_content, metadata

        except Exception as e:
            error_message = (
                f"Failed to parse PDF document {document.filename}: {str(e)}"
            )
            logger.error(error_message)
            raise HTTPException(
                status_code=422, detail=f"PDF parsing error: {str(e)}"
            ) from e
