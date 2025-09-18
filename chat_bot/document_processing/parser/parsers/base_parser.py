"""
Base parser class for document parsing.

This module provides the abstract base class that all document parsers should inherit from.
It defines the common interface for parsing documents and extracting content with metadata.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from fastapi import UploadFile


class BaseParser(ABC):
    """
    Abstract base class for document parsers.

    All document parser implementations must inherit from this class and implement
    the parse method to extract content and metadata from documents.

    This class ensures a consistent interface across all parser implementations
    and provides type safety for the parsing system.
    """

    @abstractmethod
    async def parse(self, document: UploadFile) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a document and extract its content and metadata.

        This method must be implemented by all subclasses to provide document-specific
        parsing logic. The implementation should extract text content and relevant
        metadata from the document.

        Args:
            document (UploadFile): The uploaded document to parse. The file should be
                                 positioned at the beginning for reading.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - str: The extracted text content from the document
                - Dict[str, Any]: Metadata dictionary containing document information
                                such as title, author, creation date, etc.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass
            HTTPException: If the document cannot be parsed due to format issues
            ValueError: If the document format is invalid or corrupted
            UnicodeDecodeError: If text encoding cannot be determined or decoded
        """
        raise NotImplementedError(
            f"Subclass {self.__class__.__name__} must implement the parse method."
        )
