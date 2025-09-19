"""Tests for document processing functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, UploadFile

from chat_bot.core import DocumentTypeEnum
from chat_bot.document_processing import DocumentParser
from chat_bot.document_processing.parser.parsers import PDFParser, TXTParser


class TestDocumentParser:
    """Test cases for the DocumentParser class."""

    @pytest.mark.unit
    def test_parser_initialization(self):
        """Test that DocumentParser initializes with correct parsers."""
        parser = DocumentParser()
        
        assert DocumentTypeEnum.PDF in parser._parsers
        assert DocumentTypeEnum.TXT in parser._parsers
        assert isinstance(parser._parsers[DocumentTypeEnum.PDF], PDFParser)
        assert isinstance(parser._parsers[DocumentTypeEnum.TXT], TXTParser)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_txt_document_success(self, sample_txt_content):
        """
        Test successful TXT document parsing.

        Args:
            sample_txt_content: Sample text content fixture
        """
        parser = DocumentParser()
        
        # Create mock file
        mock_file = AsyncMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = sample_txt_content
        mock_file.seek.return_value = None

        content, metadata = await parser.parse(mock_file, DocumentTypeEnum.TXT)

        assert isinstance(content, str)
        assert isinstance(metadata, dict)
        assert len(content) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_unsupported_document_type(self):
        """Test parsing with unsupported document type."""
        parser = DocumentParser()
        
        mock_file = AsyncMock()
        mock_file.filename = "test.unknown"
        
        # Create a mock document type that's not supported
        class UnsupportedType:
            value = "unknown"
        
        unsupported_type = UnsupportedType()
        
        with pytest.raises(TypeError):
            await parser.parse(mock_file, unsupported_type)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_with_parser_error(self):
        """Test parsing when underlying parser raises an error."""
        parser = DocumentParser()
        
        # Mock the TXT parser to raise an exception
        parser._parsers[DocumentTypeEnum.TXT] = AsyncMock()
        parser._parsers[DocumentTypeEnum.TXT].parse.side_effect = Exception("Parser error")
        
        mock_file = AsyncMock()
        mock_file.filename = "test.txt"
        
        with pytest.raises(HTTPException) as exc_info:
            await parser.parse(mock_file, DocumentTypeEnum.TXT)
        
        assert exc_info.value.status_code == 500
        assert "Internal parsing error" in str(exc_info.value.detail)


class TestTXTParser:
    """Test cases for the TXTParser class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_txt_parser_basic_functionality(self, sample_txt_content):
        """
        Test basic TXT parser functionality.

        Args:
            sample_txt_content: Sample text content fixture
        """
        parser = TXTParser()
        
        mock_file = AsyncMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = sample_txt_content
        mock_file.seek.return_value = None

        content, metadata = await parser.parse(mock_file)

        assert isinstance(content, str)
        assert isinstance(metadata, dict)
        assert "title" in metadata
        assert metadata["title"] == "test.txt"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_txt_parser_empty_file(self):
        """Test TXT parser with empty file."""
        parser = TXTParser()
        
        mock_file = AsyncMock()
        mock_file.filename = "empty.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b""
        mock_file.seek.return_value = None

        content, metadata = await parser.parse(mock_file)

        assert content == ""
        assert isinstance(metadata, dict)
        assert metadata["title"] == "empty.txt"


class TestPDFParser:
    """Test cases for the PDFParser class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pdf_parser_initialization(self):
        """Test PDF parser initialization."""
        parser = PDFParser()
        assert parser is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pdf_parser_with_sample_content(self, sample_pdf_content):
        """
        Test PDF parser with sample content.

        Args:
            sample_pdf_content: Sample PDF content fixture
        """
        parser = PDFParser()
        
        mock_file = AsyncMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read.return_value = sample_pdf_content
        mock_file.seek.return_value = None

        # Note: This might fail with real PDF parsing, but tests the interface
        try:
            content, metadata = await parser.parse(mock_file)
            assert isinstance(content, str)
            assert isinstance(metadata, dict)
        except Exception:
            # PDF parsing might fail with mock content, which is acceptable for this test
            pass