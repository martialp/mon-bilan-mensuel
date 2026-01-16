"""
Property-based tests for PDF Extractor Service.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from app.services.pdf_extractor import PDFExtractor


class TestFileValidationProperty:
    """Property-based tests for file validation."""

    @given(
        file_size=st.integers(
            min_value=PDFExtractor.MAX_FILE_SIZE_BYTES + 1,
            max_value=PDFExtractor.MAX_FILE_SIZE_BYTES * 2,
        )
    )
    @settings(max_examples=10)
    def test_file_size_exceeds_limit_rejected(self, file_size: int):
        """
        **Feature: mastercard-pdf-import, Property 1: File Validation Boundary**

        For any file uploaded to the system, if the file size exceeds 10MB,
        the system SHALL reject the upload with an appropriate error message.

        **Validates: Requirements 1.2**
        """
        extractor = PDFExtractor()

        # Create a temporary file that exceeds the size limit
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            # Write enough bytes to exceed the limit
            f.write(b"0" * file_size)
            temp_path = Path(f.name)

        try:
            is_valid, error = extractor.validate_file(temp_path)

            assert is_valid is False
            assert error is not None
            assert "10MB" in error or "limit" in error.lower()
        finally:
            temp_path.unlink()

    @given(extension=st.sampled_from([".txt", ".doc", ".xlsx", ".jpg", ".png", ".html"]))
    @settings(max_examples=10)
    def test_non_pdf_files_rejected(self, extension: str):
        """
        **Feature: mastercard-pdf-import, Property 1: File Validation Boundary**

        For any file uploaded to the system, if the file is not a valid PDF,
        the system SHALL reject the upload with an appropriate error message.

        **Validates: Requirements 1.1, 1.4**
        """
        extractor = PDFExtractor()

        # Create a temporary file with non-PDF extension
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
            f.write(b"This is not a PDF file content")
            temp_path = Path(f.name)

        try:
            is_valid, error = extractor.validate_file(temp_path)

            assert is_valid is False
            assert error is not None
            assert "PDF" in error
        finally:
            temp_path.unlink()

    def test_corrupted_pdf_rejected(self):
        """
        **Feature: mastercard-pdf-import, Property 1: File Validation Boundary**

        For any file uploaded to the system, if the PDF is corrupted or unreadable,
        the system SHALL reject the upload with an appropriate error message.

        **Validates: Requirements 1.4, 1.6**
        """
        extractor = PDFExtractor()

        # Create a file with .pdf extension but invalid content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"This is not valid PDF content - just random bytes")
            temp_path = Path(f.name)

        try:
            is_valid, error = extractor.validate_file(temp_path)

            assert is_valid is False
            assert error is not None
            assert "read" in error.lower() or "unable" in error.lower()
        finally:
            temp_path.unlink()

    def test_nonexistent_file_rejected(self):
        """
        Test that non-existent files are properly rejected.

        **Validates: Requirements 1.4**
        """
        extractor = PDFExtractor()

        fake_path = Path("/nonexistent/path/to/file.pdf")
        is_valid, error = extractor.validate_file(fake_path)

        assert is_valid is False
        assert error is not None
        assert "exist" in error.lower()

    @given(
        file_size=st.integers(
            min_value=100,
            max_value=PDFExtractor.MAX_FILE_SIZE_BYTES - 1,
        )
    )
    @settings(max_examples=5)
    def test_valid_size_pdf_with_invalid_content_rejected(self, file_size: int):
        """
        Test that files within size limit but with invalid PDF content are rejected.

        **Validates: Requirements 1.1, 1.4**
        """
        extractor = PDFExtractor()

        # Create a file within size limit but with invalid content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"X" * min(file_size, 10000))  # Cap at 10KB for speed
            temp_path = Path(f.name)

        try:
            is_valid, error = extractor.validate_file(temp_path)

            # Should be rejected because content is not valid PDF
            assert is_valid is False
            assert error is not None
        finally:
            temp_path.unlink()
