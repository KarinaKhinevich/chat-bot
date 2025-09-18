"""Document parser module for handling multiple document types."""

import logging
from typing import Any, Dict, Tuple

from fastapi import HTTPException, UploadFile

from chat_bot.core import DocumentTypeEnum

from .parsers import PDFParser, TXTParser

# Configure logger for this module
logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Universal document parser that coordinates parsing operations.

    Supported document types:
    - PDF: Portable Document Format files
    - TXT: Plain text files with encoding detection
    """

    def __init__(self) -> None:
        """
        Initialize the document parser with available parser implementations.

        Sets up the internal parser registry mapping document types to their
        corresponding parser instances. This design allows for easy extension
        with additional document types in the future.
        """
        # Initialize parser instances for supported document types
        self._parsers: Dict[DocumentTypeEnum, Any] = {
            DocumentTypeEnum.PDF: PDFParser(),
            DocumentTypeEnum.TXT: TXTParser(),
        }

    async def parse(
        self, document: UploadFile, document_type: DocumentTypeEnum
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a document based on its type and extract content with metadata.

        Args:
            document (UploadFile): The uploaded document to parse.
            document_type (DocumentTypeEnum): The type of document to parse.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - str: The extracted text content from the document
                - Dict[str, Any]: Metadata dictionary with document information

        Raises:
            ValueError: If the specified document type is not supported
            HTTPException: If parsing fails due to file format issues, corruption,
                         or other parsing-specific errors
            TypeError: If invalid arguments are provided
        """
        # Validate input parameters
        # TODO: Re-enable type check when figure out why UploadFile check fails
        # if not isinstance(document, UploadFile):
        #     raise TypeError(f"Document must be an UploadFile instance, got {type(document)}")

        if not isinstance(document_type, DocumentTypeEnum):
            raise TypeError("Document type must be a DocumentTypeEnum instance")

        logger.info(
            f"Initiating document parsing: {document.filename} "
            f"(type: {document_type.value})"
        )

        # Check if document type is supported
        if document_type not in self._parsers:
            logger.error(f"Unsupported document type: {document_type.value}.")
            raise ValueError(f"Unsupported document type: {document_type.value}.")

        try:
            # Get the appropriate parser for the document type
            parser = self._parsers[document_type]

            # Run the parser to extract content and metadata
            page_content, metadata = await parser.parse(document)

            logger.info(f"Successfully parsed document: {document.filename}.")

            return page_content, metadata

        except HTTPException:
            # Re-raise HTTP exceptions from parsers
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error parsing document {document.filename}: {str(e)}"
            )

            raise HTTPException(
                status_code=500, detail=f"Internal parsing error: {str(e)}"
            ) from e
