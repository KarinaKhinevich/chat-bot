"""Tests for utility functions."""

import io
import pytest
from fastapi import HTTPException, UploadFile
from unittest.mock import AsyncMock

from chat_bot.utils.file_handler import validate_file
from chat_bot.core import DocumentTypeEnum


class TestFileValidation:
    """Test cases for file validation functionality."""

    @pytest.mark.unit
    def test_validate_txt_file_success(self, sample_txt_content):
        """
        Test successful TXT file validation.

        Args:
            sample_txt_content: Sample text content fixture
        """
        mock_file = AsyncMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.size = len(sample_txt_content)
        
        result = validate_file(mock_file)
        
        assert result == DocumentTypeEnum.TXT

    @pytest.mark.unit
    def test_validate_pdf_file_success(self, sample_pdf_content):
        """
        Test successful PDF file validation.

        Args:
            sample_pdf_content: Sample PDF content fixture
        """
        mock_file = AsyncMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = len(sample_pdf_content)
        
        result = validate_file(mock_file)
        
        assert result == DocumentTypeEnum.PDF

    @pytest.mark.unit
    def test_validate_unsupported_file_type(self):
        """Test validation with unsupported file type."""
        mock_file = AsyncMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 1000
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "File type not supported" in exc_info.value.detail

    @pytest.mark.unit
    def test_validate_oversized_file(self):
        """Test validation with oversized file."""
        mock_file = AsyncMock()
        mock_file.filename = "large.txt"
        mock_file.content_type = "text/plain"
        mock_file.size = 11 * 1024 * 1024  # 11MB (over 10MB limit)
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_file)
        
        assert exc_info.value.status_code == 413
        assert "File size too large" in exc_info.value.detail

    @pytest.mark.unit
    def test_validate_file_without_extension(self):
        """Test validation with file without extension."""
        mock_file = AsyncMock()
        mock_file.filename = "test_file"  # No extension
        mock_file.content_type = "text/plain"
        mock_file.size = 1000
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_file)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.unit
    def test_validate_empty_filename(self):
        """Test validation with empty filename."""
        mock_file = AsyncMock()
        mock_file.filename = ""
        mock_file.content_type = "text/plain"
        mock_file.size = 1000
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_file)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.unit
    def test_validate_none_filename(self):
        """Test validation with None filename."""
        mock_file = AsyncMock()
        mock_file.filename = None
        mock_file.content_type = "text/plain"
        mock_file.size = 1000
        
        with pytest.raises((HTTPException, TypeError)) as exc_info:
            validate_file(mock_file)
        
        # Either HTTPException or TypeError is acceptable
        if isinstance(exc_info.value, HTTPException):
            assert exc_info.value.status_code == 400
        else:
            assert isinstance(exc_info.value, TypeError)

    @pytest.mark.unit
    def test_validate_case_insensitive_extensions(self):
        """Test validation with different case extensions."""
        # Test uppercase PDF
        mock_file = AsyncMock()
        mock_file.filename = "test.PDF"
        mock_file.content_type = "application/pdf"
        mock_file.size = 1000
        
        result = validate_file(mock_file)
        assert result == DocumentTypeEnum.PDF
        
        # Test uppercase TXT
        mock_file.filename = "test.TXT"
        mock_file.content_type = "text/plain"
        mock_file.size = 1000
        
        result = validate_file(mock_file)
        assert result == DocumentTypeEnum.TXT

    @pytest.mark.unit
    def test_validate_zero_size_file(self):
        """Test validation with zero-size file."""
        mock_file = AsyncMock()
        mock_file.filename = "empty.txt"
        mock_file.content_type = "text/plain"
        mock_file.size = 0
        
        # Should allow empty files (they might still be valid)
        result = validate_file(mock_file)
        assert result == DocumentTypeEnum.TXT

    @pytest.mark.unit
    def test_validate_mismatched_content_type(self):
        """Test validation with mismatched filename and content type."""
        mock_file = AsyncMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "application/pdf"  # Mismatched
        mock_file.size = 1000
        
        # The validation is based on content type, so this should return PDF
        result = validate_file(mock_file)
        assert result == DocumentTypeEnum.PDF