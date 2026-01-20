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


class TestCurrencyConversionLineDetection:
    """Unit tests for currency conversion line detection.
    
    **Feature: pdf-currency-line-fix**
    
    These tests verify that the _is_currency_conversion_line method correctly
    identifies currency conversion lines that appear in foreign currency
    transactions in Desjardins Mastercard statements.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @pytest.fixture
    def extractor(self) -> PDFExtractor:
        """Create a PDFExtractor instance for testing."""
        return PDFExtractor()

    # ==================== Valid Currency Conversion Lines ====================
    # These lines should be detected as currency conversion lines
    # Pattern: ^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$

    def test_euro_currency_line_detected(self, extractor: PDFExtractor):
        """
        Test that a standard EURO currency conversion line is detected.
        
        **Validates: Requirement 1.1** - Identify lines matching strict pattern
        """
        line = "2,18 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is True

    def test_usd_currency_line_detected(self, extractor: PDFExtractor):
        """
        Test that a standard USD currency conversion line is detected.
        
        **Validates: Requirement 1.1** - Identify lines matching strict pattern
        """
        line = "15,00 USD TX: 1.345678"
        assert extractor._is_currency_conversion_line(line) is True

    def test_gbp_currency_line_detected(self, extractor: PDFExtractor):
        """
        Test that a GBP (3-letter) currency conversion line is detected.
        
        **Validates: Requirement 1.2** - Currency code 2-4 letters
        """
        line = "100,50 GBP TX: 1.789012"
        assert extractor._is_currency_conversion_line(line) is True

    def test_currency_line_with_dot_decimal_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines using dot as decimal separator are detected.
        
        **Validates: Requirement 1.2** - Pattern allows comma or dot
        """
        line = "25.99 USD TX: 1.234567"
        assert extractor._is_currency_conversion_line(line) is True

    def test_currency_line_with_leading_whitespace_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines with leading whitespace are detected.
        
        **Validates: Requirement 1.2** - Pattern allows leading whitespace
        """
        line = "  2,18 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is True

    def test_currency_line_with_trailing_whitespace_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines with trailing whitespace are detected.
        
        **Validates: Requirement 1.2** - Pattern allows trailing whitespace
        """
        line = "2,18 EURO TX: 1.527522  "
        assert extractor._is_currency_conversion_line(line) is True

    def test_currency_line_with_space_after_tx_colon_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines with space after TX: are detected.
        
        **Validates: Requirement 1.2** - Pattern allows optional space after TX:
        """
        line = "2,18 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is True

    def test_currency_line_without_space_after_tx_colon_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines without space after TX: are detected.
        
        **Validates: Requirement 1.2** - Pattern allows no space after TX:
        """
        line = "2,18 EURO TX:1.527522"
        assert extractor._is_currency_conversion_line(line) is True

    def test_two_letter_currency_code_detected(self, extractor: PDFExtractor):
        """
        Test that 2-letter currency codes are detected.
        
        **Validates: Requirement 1.2** - Currency code 2-4 letters
        """
        line = "50,00 US TX: 1.350000"
        assert extractor._is_currency_conversion_line(line) is True

    def test_four_letter_currency_code_detected(self, extractor: PDFExtractor):
        """
        Test that 4-letter currency codes are detected.
        
        **Validates: Requirement 1.2** - Currency code 2-4 letters
        """
        line = "75,25 EURO TX: 1.123456"
        assert extractor._is_currency_conversion_line(line) is True

    def test_large_amount_currency_line_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines with large amounts are detected.
        
        **Validates: Requirement 1.1** - Amount is a decimal number
        """
        line = "9999,99 USD TX: 1.456789"
        assert extractor._is_currency_conversion_line(line) is True

    def test_small_exchange_rate_detected(self, extractor: PDFExtractor):
        """
        Test that currency lines with small exchange rates are detected.
        
        **Validates: Requirement 1.1** - Exchange rate is a decimal number
        """
        line = "100,00 JPY TX: 0.009123"
        assert extractor._is_currency_conversion_line(line) is True

    # ==================== Non-Currency Lines (Should NOT be detected) ====================
    # These lines should NOT be detected as currency conversion lines

    def test_empty_line_not_detected(self, extractor: PDFExtractor):
        """
        Test that empty lines are NOT detected as currency conversion lines.
        
        **Validates: Requirement 1.3** - Edge case: empty lines
        """
        assert extractor._is_currency_conversion_line("") is False

    def test_whitespace_only_line_not_detected(self, extractor: PDFExtractor):
        """
        Test that whitespace-only lines are NOT detected.
        
        **Validates: Requirement 1.3** - Edge case: whitespace only
        """
        assert extractor._is_currency_conversion_line("   ") is False

    def test_merchant_description_not_detected(self, extractor: PDFExtractor):
        """
        Test that regular merchant descriptions are NOT detected.
        
        **Validates: Requirement 1.3** - NOT match merchant descriptions
        """
        line = "MUSIC-A STOCKHOLM AB"
        assert extractor._is_currency_conversion_line(line) is False

    def test_merchant_with_amount_not_detected(self, extractor: PDFExtractor):
        """
        Test that merchant descriptions containing amounts are NOT detected.
        
        **Validates: Requirement 1.3** - NOT match partial patterns
        """
        line = "STORE 123,45 MAIN ST"
        assert extractor._is_currency_conversion_line(line) is False

    def test_currency_pattern_as_substring_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines where currency pattern appears as substring are NOT detected.
        
        **Validates: Requirement 1.3** - Pattern must match entire line
        """
        line = "PAYMENT 2,18 EURO TX: 1.527522 CONFIRMED"
        assert extractor._is_currency_conversion_line(line) is False

    def test_currency_pattern_with_prefix_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with text before the currency pattern are NOT detected.
        
        **Validates: Requirement 1.3** - Pattern must match entire line
        """
        line = "REF: 2,18 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_currency_pattern_with_suffix_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with text after the currency pattern are NOT detected.
        
        **Validates: Requirement 1.3** - Pattern must match entire line
        """
        line = "2,18 EURO TX: 1.527522 CAD"
        assert extractor._is_currency_conversion_line(line) is False

    def test_missing_tx_marker_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines missing the TX: marker are NOT detected.
        
        **Validates: Requirement 1.2** - Must have TX: marker
        """
        line = "2,18 EURO 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_lowercase_tx_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with lowercase 'tx:' are NOT detected.
        
        **Validates: Requirement 1.2** - TX must be uppercase
        """
        line = "2,18 EURO tx: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_lowercase_currency_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with lowercase currency codes are NOT detected.
        
        **Validates: Requirement 1.2** - Currency must be uppercase
        """
        line = "2,18 euro TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_missing_amount_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines missing the amount are NOT detected.
        
        **Validates: Requirement 1.2** - Must have amount
        """
        line = "EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_missing_exchange_rate_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines missing the exchange rate are NOT detected.
        
        **Validates: Requirement 1.2** - Must have exchange rate
        """
        line = "2,18 EURO TX:"
        assert extractor._is_currency_conversion_line(line) is False

    def test_invalid_amount_format_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with invalid amount format (no decimal) are NOT detected.
        
        **Validates: Requirement 1.2** - Amount must have 2 decimal places
        """
        line = "218 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_amount_with_three_decimals_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with 3 decimal places in amount are NOT detected.
        
        **Validates: Requirement 1.2** - Amount must have exactly 2 decimal places
        """
        line = "2,189 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_amount_with_one_decimal_not_detected(self, extractor: PDFExtractor):
        """
        Test that lines with 1 decimal place in amount are NOT detected.
        
        **Validates: Requirement 1.2** - Amount must have exactly 2 decimal places
        """
        line = "2,1 EURO TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_single_letter_currency_not_detected(self, extractor: PDFExtractor):
        """
        Test that single-letter currency codes are NOT detected.
        
        **Validates: Requirement 1.2** - Currency code must be 2-4 letters
        """
        line = "2,18 E TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_five_letter_currency_not_detected(self, extractor: PDFExtractor):
        """
        Test that 5-letter currency codes are NOT detected.
        
        **Validates: Requirement 1.2** - Currency code must be 2-4 letters
        """
        line = "2,18 EUROS TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False

    def test_date_line_not_detected(self, extractor: PDFExtractor):
        """
        Test that date lines are NOT detected as currency conversion lines.
        
        **Validates: Requirement 1.3** - NOT match other line types
        """
        line = "15 JAN"
        assert extractor._is_currency_conversion_line(line) is False

    def test_amount_only_line_not_detected(self, extractor: PDFExtractor):
        """
        Test that amount-only lines are NOT detected.
        
        **Validates: Requirement 1.3** - NOT match partial patterns
        """
        line = "123,45"
        assert extractor._is_currency_conversion_line(line) is False

    def test_currency_with_numbers_not_detected(self, extractor: PDFExtractor):
        """
        Test that currency codes containing numbers are NOT detected.
        
        **Validates: Requirement 1.2** - Currency must be letters only
        """
        line = "2,18 EU2O TX: 1.527522"
        assert extractor._is_currency_conversion_line(line) is False


class TestCurrencyConversionLineDetectionProperty:
    r"""Property-based tests for currency conversion line detection.
    
    **Feature: pdf-currency-line-fix, Property 1: Currency Conversion Line Detection Accuracy**
    
    For any string that matches the pattern `^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$`,
    the `_is_currency_conversion_line` method SHALL return True. For any string that does not match
    this exact pattern (including strings where the pattern appears as a substring of a longer line),
    the method SHALL return False.
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    # ==================== Hypothesis Strategies ====================
    # Strategies for generating valid and invalid currency conversion lines

    @staticmethod
    def valid_currency_line_strategy() -> st.SearchStrategy[str]:
        r"""
        Strategy to generate valid currency conversion lines.
        
        Pattern: ^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$
        
        Components:
        - Optional leading whitespace
        - Amount: digits, comma or dot, exactly 2 decimal digits
        - Space(s)
        - Currency code: 2-4 uppercase letters
        - Space(s)
        - TX: marker (uppercase)
        - Optional space after colon
        - Exchange rate: digits, dot or comma, decimal digits
        - Optional trailing whitespace
        """
        return st.builds(
            lambda leading_ws, amount_int, decimal_sep, amount_dec, mid_ws1, currency, mid_ws2, tx_space, rate_int, rate_sep, rate_dec, trailing_ws: (
                f"{leading_ws}{amount_int}{decimal_sep}{amount_dec:02d}{mid_ws1}{currency}{mid_ws2}TX:{tx_space}{rate_int}{rate_sep}{rate_dec}{trailing_ws}"
            ),
            leading_ws=st.sampled_from(["", " ", "  ", "   "]),
            amount_int=st.integers(min_value=0, max_value=99999),
            decimal_sep=st.sampled_from([",", "."]),
            amount_dec=st.integers(min_value=0, max_value=99),  # Exactly 2 digits
            mid_ws1=st.sampled_from([" ", "  "]),
            currency=st.text(
                alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                min_size=2,
                max_size=4,
            ),
            mid_ws2=st.sampled_from([" ", "  "]),
            tx_space=st.sampled_from(["", " "]),
            rate_int=st.integers(min_value=0, max_value=99),
            rate_sep=st.sampled_from([",", "."]),
            rate_dec=st.integers(min_value=1, max_value=999999),  # At least 1 digit after decimal
            trailing_ws=st.sampled_from(["", " ", "  "]),
        )

    @staticmethod
    def invalid_line_strategy() -> st.SearchStrategy[str]:
        """
        Strategy to generate lines that should NOT be detected as currency conversion lines.
        
        This includes:
        - Random text (merchant descriptions)
        - Partial patterns (missing components)
        - Lines with wrong format
        """
        return st.one_of(
            # Random text (merchant descriptions)
            st.text(
                alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -_"),
                min_size=1,
                max_size=50,
            ).filter(lambda x: "TX:" not in x.upper()),
            # Empty or whitespace only
            st.sampled_from(["", " ", "  ", "\t", "\n"]),
            # Amount only (no currency or TX)
            st.builds(
                lambda amt: f"{amt},00",
                amt=st.integers(min_value=1, max_value=9999),
            ),
            # Currency code only
            st.text(
                alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                min_size=2,
                max_size=4,
            ),
            # Missing TX: marker
            st.builds(
                lambda amt, curr, rate: f"{amt},00 {curr} {rate}",
                amt=st.integers(min_value=1, max_value=999),
                curr=st.text(
                    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                    min_size=2,
                    max_size=4,
                ),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
            # Lowercase tx: marker
            st.builds(
                lambda amt, curr, rate: f"{amt},00 {curr} tx: {rate}",
                amt=st.integers(min_value=1, max_value=999),
                curr=st.text(
                    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                    min_size=2,
                    max_size=4,
                ),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
            # Lowercase currency
            st.builds(
                lambda amt, curr, rate: f"{amt},00 {curr.lower()} TX: {rate}",
                amt=st.integers(min_value=1, max_value=999),
                curr=st.text(
                    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                    min_size=2,
                    max_size=4,
                ),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
            # Wrong decimal places in amount (1 or 3 instead of 2)
            st.builds(
                lambda amt, curr, rate: f"{amt},1 {curr} TX: {rate}",
                amt=st.integers(min_value=1, max_value=999),
                curr=st.text(
                    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                    min_size=2,
                    max_size=4,
                ),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
            st.builds(
                lambda amt, curr, rate: f"{amt},123 {curr} TX: {rate}",
                amt=st.integers(min_value=1, max_value=999),
                curr=st.text(
                    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                    min_size=2,
                    max_size=4,
                ),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
            # Currency code too short (1 letter) or too long (5+ letters)
            st.builds(
                lambda amt, rate: f"{amt},00 A TX: {rate}",
                amt=st.integers(min_value=1, max_value=999),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
            st.builds(
                lambda amt, rate: f"{amt},00 ABCDE TX: {rate}",
                amt=st.integers(min_value=1, max_value=999),
                rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
            ),
        )

    @staticmethod
    def substring_pattern_strategy() -> st.SearchStrategy[str]:
        """
        Strategy to generate lines where the currency pattern appears as a substring.
        
        These should NOT be detected as currency conversion lines because the pattern
        must match the entire line, not just a substring.
        """
        valid_pattern = st.builds(
            lambda amt, curr, rate: f"{amt},00 {curr} TX: {rate:.6f}",
            amt=st.integers(min_value=1, max_value=999),
            curr=st.sampled_from(["USD", "EUR", "EURO", "GBP", "JPY", "CAD"]),
            rate=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
        )
        
        return st.one_of(
            # Pattern with prefix
            st.builds(
                lambda prefix, pattern: f"{prefix} {pattern}",
                prefix=st.sampled_from(["REF:", "PAYMENT", "NOTE:", "ID:", "CONFIRMED"]),
                pattern=valid_pattern,
            ),
            # Pattern with suffix
            st.builds(
                lambda pattern, suffix: f"{pattern} {suffix}",
                pattern=valid_pattern,
                suffix=st.sampled_from(["CAD", "CONFIRMED", "DONE", "OK", "PROCESSED"]),
            ),
            # Pattern with both prefix and suffix
            st.builds(
                lambda prefix, pattern, suffix: f"{prefix} {pattern} {suffix}",
                prefix=st.sampled_from(["REF:", "PAYMENT", "NOTE:"]),
                pattern=valid_pattern,
                suffix=st.sampled_from(["CAD", "CONFIRMED", "DONE"]),
            ),
        )

    # ==================== Property Tests ====================

    @given(line=valid_currency_line_strategy.__func__())
    @settings(max_examples=100)
    def test_valid_currency_lines_detected(self, line: str):
        r"""
        **Feature: pdf-currency-line-fix, Property 1: Currency Conversion Line Detection Accuracy**
        
        For any string that matches the pattern `^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$`,
        the `_is_currency_conversion_line` method SHALL return True.
        
        This test generates valid currency conversion lines using Hypothesis and verifies
        that all of them are correctly detected.
        
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        extractor = PDFExtractor()
        assert extractor._is_currency_conversion_line(line) is True, (
            f"Expected line to be detected as currency conversion line: '{line}'"
        )

    @given(line=invalid_line_strategy.__func__())
    @settings(max_examples=100)
    def test_invalid_lines_not_detected(self, line: str):
        """
        **Feature: pdf-currency-line-fix, Property 1: Currency Conversion Line Detection Accuracy**
        
        For any string that does not match the exact pattern, the `_is_currency_conversion_line`
        method SHALL return False.
        
        This test generates various invalid lines (merchant descriptions, partial patterns,
        wrong formats) and verifies that none of them are incorrectly detected.
        
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        extractor = PDFExtractor()
        assert extractor._is_currency_conversion_line(line) is False, (
            f"Expected line NOT to be detected as currency conversion line: '{line}'"
        )

    @given(line=substring_pattern_strategy.__func__())
    @settings(max_examples=100)
    def test_substring_patterns_not_detected(self, line: str):
        """
        **Feature: pdf-currency-line-fix, Property 1: Currency Conversion Line Detection Accuracy**
        
        For any string where the currency conversion pattern appears as a substring of a longer
        line, the `_is_currency_conversion_line` method SHALL return False.
        
        This test generates lines where a valid currency pattern is embedded within other text
        (prefix, suffix, or both) and verifies that they are NOT detected.
        
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        extractor = PDFExtractor()
        assert extractor._is_currency_conversion_line(line) is False, (
            f"Expected substring pattern NOT to be detected: '{line}'"
        )


class TestCurrencyConversionLineFiltering:
    """Unit tests for currency conversion line filtering.
    
    **Feature: pdf-currency-line-fix**
    
    These tests verify that the _filter_currency_conversion_lines method correctly
    removes currency conversion lines from description lists while preserving
    all other lines in their original order.
    
    **Validates: Requirements 2.1, 2.2**
    """

    @pytest.fixture
    def extractor(self) -> PDFExtractor:
        """Create a PDFExtractor instance for testing."""
        return PDFExtractor()

    # ==================== Currency Lines Removed ====================
    # Tests that verify currency conversion lines are removed from description lists
    # Validates: Requirement 2.1

    def test_single_currency_line_removed(self, extractor: PDFExtractor):
        """
        Test that a single currency conversion line is removed from a list.
        
        **Validates: Requirement 2.1** - Remove currency conversion lines before alignment
        """
        description_lines = [
            "MUSIC-A STOCKHOLM AB",
            "2,18 EURO TX: 1.527522",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert "2,18 EURO TX: 1.527522" not in result
        assert len(result) == 1

    def test_multiple_currency_lines_removed(self, extractor: PDFExtractor):
        """
        Test that multiple currency conversion lines are all removed.
        
        **Validates: Requirement 2.1** - Remove ALL currency conversion lines
        """
        description_lines = [
            "MERCHANT ONE",
            "2,18 EURO TX: 1.527522",
            "MERCHANT TWO",
            "15,00 USD TX: 1.345678",
            "MERCHANT THREE",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert "2,18 EURO TX: 1.527522" not in result
        assert "15,00 USD TX: 1.345678" not in result
        assert len(result) == 3

    def test_currency_line_at_beginning_removed(self, extractor: PDFExtractor):
        """
        Test that a currency line at the beginning of the list is removed.
        
        **Validates: Requirement 2.1** - Remove regardless of position
        """
        description_lines = [
            "2,18 EURO TX: 1.527522",
            "MERCHANT DESCRIPTION",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert "2,18 EURO TX: 1.527522" not in result
        assert "MERCHANT DESCRIPTION" in result
        assert len(result) == 1

    def test_currency_line_at_end_removed(self, extractor: PDFExtractor):
        """
        Test that a currency line at the end of the list is removed.
        
        **Validates: Requirement 2.1** - Remove regardless of position
        """
        description_lines = [
            "MERCHANT DESCRIPTION",
            "2,18 EURO TX: 1.527522",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert "2,18 EURO TX: 1.527522" not in result
        assert "MERCHANT DESCRIPTION" in result
        assert len(result) == 1

    def test_currency_line_in_middle_removed(self, extractor: PDFExtractor):
        """
        Test that a currency line in the middle of the list is removed.
        
        **Validates: Requirement 2.1** - Remove regardless of position
        """
        description_lines = [
            "MERCHANT ONE",
            "2,18 EURO TX: 1.527522",
            "MERCHANT TWO",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert "2,18 EURO TX: 1.527522" not in result
        assert len(result) == 2

    def test_various_currency_formats_removed(self, extractor: PDFExtractor):
        """
        Test that various currency conversion line formats are all removed.
        
        **Validates: Requirement 2.1** - Remove all matching patterns
        """
        description_lines = [
            "MERCHANT ONE",
            "2,18 EURO TX: 1.527522",
            "MERCHANT TWO",
            "15,00 USD TX: 1.345678",
            "MERCHANT THREE",
            "100,50 GBP TX: 1.789012",
            "MERCHANT FOUR",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        # All currency lines should be removed
        assert "2,18 EURO TX: 1.527522" not in result
        assert "15,00 USD TX: 1.345678" not in result
        assert "100,50 GBP TX: 1.789012" not in result
        # All merchant lines should remain
        assert len(result) == 4

    # ==================== Non-Currency Lines Preserved ====================
    # Tests that verify non-currency lines are preserved in order
    # Validates: Requirement 2.2

    def test_non_currency_lines_preserved_in_order(self, extractor: PDFExtractor):
        """
        Test that non-currency lines are preserved in their original order.
        
        **Validates: Requirement 2.2** - Preserve all other description lines unchanged
        """
        description_lines = [
            "MERCHANT ONE",
            "2,18 EURO TX: 1.527522",
            "MERCHANT TWO",
            "MERCHANT THREE",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == ["MERCHANT ONE", "MERCHANT TWO", "MERCHANT THREE"]

    def test_order_preserved_with_multiple_currency_lines(self, extractor: PDFExtractor):
        """
        Test that order is preserved when multiple currency lines are interspersed.
        
        **Validates: Requirement 2.2** - Preserve order of remaining lines
        """
        description_lines = [
            "FIRST",
            "2,18 EURO TX: 1.527522",
            "SECOND",
            "15,00 USD TX: 1.345678",
            "THIRD",
            "100,50 GBP TX: 1.789012",
            "FOURTH",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == ["FIRST", "SECOND", "THIRD", "FOURTH"]

    def test_empty_list_returns_empty(self, extractor: PDFExtractor):
        """
        Test that an empty list returns an empty list.
        
        **Validates: Requirement 2.2** - Edge case: empty input
        """
        result = extractor._filter_currency_conversion_lines([])
        
        assert result == []

    def test_list_with_only_currency_lines_returns_empty(self, extractor: PDFExtractor):
        """
        Test that a list containing only currency lines returns an empty list.
        
        **Validates: Requirements 2.1, 2.2** - All currency lines removed, nothing left
        """
        description_lines = [
            "2,18 EURO TX: 1.527522",
            "15,00 USD TX: 1.345678",
            "100,50 GBP TX: 1.789012",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == []

    def test_list_with_no_currency_lines_unchanged(self, extractor: PDFExtractor):
        """
        Test that a list with no currency lines is returned unchanged.
        
        **Validates: Requirement 2.2** - Preserve all non-currency lines
        """
        description_lines = [
            "MERCHANT ONE",
            "MERCHANT TWO",
            "MERCHANT THREE",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == description_lines

    def test_single_non_currency_line_preserved(self, extractor: PDFExtractor):
        """
        Test that a single non-currency line is preserved.
        
        **Validates: Requirement 2.2** - Single line case
        """
        description_lines = ["MERCHANT DESCRIPTION"]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == ["MERCHANT DESCRIPTION"]

    def test_whitespace_lines_preserved(self, extractor: PDFExtractor):
        """
        Test that whitespace-only lines are preserved (not currency lines).
        
        **Validates: Requirement 2.2** - Whitespace lines are not currency lines
        """
        description_lines = [
            "MERCHANT ONE",
            "   ",
            "MERCHANT TWO",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == description_lines

    def test_lines_with_partial_currency_pattern_preserved(self, extractor: PDFExtractor):
        """
        Test that lines containing currency pattern as substring are preserved.
        
        **Validates: Requirement 2.2** - Only exact matches are removed
        """
        description_lines = [
            "PAYMENT 2,18 EURO TX: 1.527522 CONFIRMED",
            "MERCHANT DESCRIPTION",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        # The line with partial pattern should be preserved
        assert result == description_lines

    def test_realistic_transaction_block(self, extractor: PDFExtractor):
        """
        Test filtering with a realistic transaction block from a statement.
        
        **Validates: Requirements 2.1, 2.2** - Real-world scenario
        """
        # Simulates a multi-line cell with foreign currency transaction
        description_lines = [
            "MUSIC-A STOCKHOLM AB",
            "2,18 EURO TX: 1.527522",
            "RESTAURANT LOCAL QC",
            "GROCERY STORE MTL",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == [
            "MUSIC-A STOCKHOLM AB",
            "RESTAURANT LOCAL QC",
            "GROCERY STORE MTL",
        ]

    def test_multiple_foreign_transactions_block(self, extractor: PDFExtractor):
        """
        Test filtering with multiple foreign currency transactions.
        
        **Validates: Requirements 2.1, 2.2** - Multiple foreign transactions
        """
        description_lines = [
            "MUSIC-A STOCKHOLM AB",
            "2,18 EURO TX: 1.527522",
            "Serv-A Paris FR",
            "3,00 EURO TX: 1.110000",
            "RESTAURANT LOCAL QC",
        ]
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        assert result == [
            "MUSIC-A STOCKHOLM AB",
            "Serv-A Paris FR",
            "RESTAURANT LOCAL QC",
        ]


# ==================== Module-level Strategies for Property 2 ====================
# These strategies are defined at module level to avoid circular reference issues


def _currency_line_for_filtering_strategy() -> st.SearchStrategy[str]:
    r"""
    Strategy to generate valid currency conversion lines for filtering tests.
    
    Pattern: ^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$
    """
    return st.builds(
        lambda amount_int, decimal_sep, amount_dec, currency, rate_int, rate_sep, rate_dec: (
            f"{amount_int}{decimal_sep}{amount_dec:02d} {currency} TX: {rate_int}{rate_sep}{rate_dec}"
        ),
        amount_int=st.integers(min_value=1, max_value=9999),
        decimal_sep=st.sampled_from([",", "."]),
        amount_dec=st.integers(min_value=0, max_value=99),
        currency=st.sampled_from(["USD", "EUR", "EURO", "GBP", "JPY", "CAD", "CHF", "AUD"]),
        rate_int=st.integers(min_value=0, max_value=9),
        rate_sep=st.sampled_from([",", "."]),
        rate_dec=st.integers(min_value=100000, max_value=999999),
    )


def _non_currency_line_for_filtering_strategy() -> st.SearchStrategy[str]:
    """
    Strategy to generate non-currency lines (merchant descriptions).
    
    These lines should NOT match the currency conversion pattern.
    Generates realistic merchant-like descriptions.
    """
    return st.one_of(
        # Merchant names with location
        st.builds(
            lambda name, location: f"{name} {location}",
            name=st.sampled_from([
                "RESTAURANT", "GROCERY STORE", "GAS STATION", "PHARMACY",
                "COFFEE SHOP", "BOOKSTORE", "HARDWARE STORE", "BAKERY",
                "MUSIC-A STOCKHOLM AB", "Serv-A Paris FR", "HOTEL LONDON",
            ]),
            location=st.sampled_from(["MTL", "QC", "ON", "BC", "AB", "FR", "UK", "US", ""]),
        ),
        # Simple merchant names
        st.sampled_from([
            "AMAZON.CA",
            "NETFLIX.COM",
            "SPOTIFY",
            "UBER TRIP",
            "METRO INC",
            "COSTCO WHOLESALE",
            "WALMART CANADA",
            "TIM HORTONS",
            "STARBUCKS",
            "MCDONALDS",
        ]),
        # Merchant names with numbers (but not currency pattern)
        st.builds(
            lambda name, num: f"{name} #{num}",
            name=st.sampled_from(["STORE", "LOCATION", "BRANCH", "OUTLET"]),
            num=st.integers(min_value=1, max_value=9999),
        ),
    )


def _mixed_lines_for_filtering_strategy() -> st.SearchStrategy[list[tuple[str, bool]]]:
    """
    Strategy to generate mixed lists of currency and non-currency lines.
    
    Returns a list of tuples: (line, is_currency_line)
    This allows us to track which lines are currency lines for verification.
    """
    currency_line = _currency_line_for_filtering_strategy().map(
        lambda line: (line, True)
    )
    non_currency_line = _non_currency_line_for_filtering_strategy().map(
        lambda line: (line, False)
    )
    
    return st.lists(
        st.one_of(currency_line, non_currency_line),
        min_size=0,
        max_size=20,
    )


class TestCurrencyLineFilteringPreservationProperty:
    r"""Property-based tests for currency line filtering preservation.
    
    **Feature: pdf-currency-line-fix, Property 2: Currency Line Filtering Preserves Non-Currency Lines**
    
    For any list of description lines, after filtering with `_filter_currency_conversion_lines`:
    - All lines that are NOT currency conversion lines SHALL be present in the output in the same order
    - All lines that ARE currency conversion lines SHALL be absent from the output
    - The output length SHALL equal the input length minus the count of currency conversion lines
    
    **Validates: Requirements 2.1, 2.2**
    """

    # ==================== Property Tests ====================

    @given(mixed_lines=_mixed_lines_for_filtering_strategy())
    @settings(max_examples=100)
    def test_non_currency_lines_preserved_in_order(self, mixed_lines: list[tuple[str, bool]]):
        """
        **Feature: pdf-currency-line-fix, Property 2: Currency Line Filtering Preserves Non-Currency Lines**
        
        For any list of description lines, all lines that are NOT currency conversion lines
        SHALL be present in the output in the same order.
        
        This test generates mixed lists of currency and non-currency lines and verifies
        that all non-currency lines appear in the output in their original order.
        
        **Validates: Requirements 2.1, 2.2**
        """
        extractor = PDFExtractor()
        
        # Extract just the lines (without the is_currency flag)
        input_lines = [line for line, _ in mixed_lines]
        
        # Get expected non-currency lines in order
        expected_non_currency = [line for line, is_currency in mixed_lines if not is_currency]
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(input_lines)
        
        # Verify all non-currency lines are present in order
        assert result == expected_non_currency, (
            f"Non-currency lines not preserved in order.\n"
            f"Input: {input_lines}\n"
            f"Expected: {expected_non_currency}\n"
            f"Got: {result}"
        )

    @given(mixed_lines=_mixed_lines_for_filtering_strategy())
    @settings(max_examples=100)
    def test_currency_lines_absent_from_output(self, mixed_lines: list[tuple[str, bool]]):
        """
        **Feature: pdf-currency-line-fix, Property 2: Currency Line Filtering Preserves Non-Currency Lines**
        
        For any list of description lines, all lines that ARE currency conversion lines
        SHALL be absent from the output.
        
        This test generates mixed lists and verifies that no currency conversion lines
        appear in the filtered output.
        
        **Validates: Requirements 2.1, 2.2**
        """
        extractor = PDFExtractor()
        
        # Extract just the lines
        input_lines = [line for line, _ in mixed_lines]
        
        # Get currency lines that should be removed
        currency_lines = [line for line, is_currency in mixed_lines if is_currency]
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(input_lines)
        
        # Verify no currency lines are in the result
        for currency_line in currency_lines:
            assert currency_line not in result, (
                f"Currency line should have been removed: '{currency_line}'\n"
                f"Input: {input_lines}\n"
                f"Result: {result}"
            )

    @given(mixed_lines=_mixed_lines_for_filtering_strategy())
    @settings(max_examples=100)
    def test_output_length_equals_input_minus_currency_count(self, mixed_lines: list[tuple[str, bool]]):
        """
        **Feature: pdf-currency-line-fix, Property 2: Currency Line Filtering Preserves Non-Currency Lines**
        
        For any list of description lines, the output length SHALL equal the input length
        minus the count of currency conversion lines.
        
        This test verifies the mathematical relationship between input size, currency line
        count, and output size.
        
        **Validates: Requirements 2.1, 2.2**
        """
        extractor = PDFExtractor()
        
        # Extract just the lines
        input_lines = [line for line, _ in mixed_lines]
        
        # Count currency lines
        currency_count = sum(1 for _, is_currency in mixed_lines if is_currency)
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(input_lines)
        
        # Verify length relationship
        expected_length = len(input_lines) - currency_count
        assert len(result) == expected_length, (
            f"Output length mismatch.\n"
            f"Input length: {len(input_lines)}\n"
            f"Currency count: {currency_count}\n"
            f"Expected output length: {expected_length}\n"
            f"Actual output length: {len(result)}\n"
            f"Input: {input_lines}\n"
            f"Result: {result}"
        )

    @given(
        non_currency_lines=st.lists(
            _non_currency_line_for_filtering_strategy(),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_list_without_currency_lines_unchanged(self, non_currency_lines: list[str]):
        """
        **Feature: pdf-currency-line-fix, Property 2: Currency Line Filtering Preserves Non-Currency Lines**
        
        For any list containing only non-currency lines, the output SHALL equal the input
        (same elements, same order, same length).
        
        This is a special case that also validates backward compatibility.
        
        **Validates: Requirements 2.1, 2.2**
        """
        extractor = PDFExtractor()
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(non_currency_lines)
        
        # Verify output equals input
        assert result == non_currency_lines, (
            f"List without currency lines should be unchanged.\n"
            f"Input: {non_currency_lines}\n"
            f"Result: {result}"
        )

    @given(
        currency_lines=st.lists(
            _currency_line_for_filtering_strategy(),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_list_with_only_currency_lines_returns_empty(self, currency_lines: list[str]):
        """
        **Feature: pdf-currency-line-fix, Property 2: Currency Line Filtering Preserves Non-Currency Lines**
        
        For any list containing only currency conversion lines, the output SHALL be empty.
        
        This is an edge case where all lines are filtered out.
        
        **Validates: Requirements 2.1, 2.2**
        """
        extractor = PDFExtractor()
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(currency_lines)
        
        # Verify output is empty
        assert result == [], (
            f"List with only currency lines should return empty.\n"
            f"Input: {currency_lines}\n"
            f"Result: {result}"
        )


class TestFixtureBasedExtraction:
    """Fixture-based tests for correct PDF extraction.
    
    **Feature: pdf-currency-line-fix**
    
    These tests use the actual Desjardins Mastercard statement fixture to verify
    that transactions are correctly extracted with proper amounts and that
    currency conversion lines are filtered out.
    
    **Validates: Requirements 3.2, 3.3, 3.4, 4.2, 4.3**
    """

    @pytest.fixture
    def extractor(self) -> PDFExtractor:
        """Create a PDFExtractor instance for testing."""
        return PDFExtractor()

    @pytest.fixture
    def fixture_pdf_path(self) -> Path:
        """Get the path to the test fixture PDF."""
        return Path(__file__).parent.parent / "fixtures" / "desjardins_mastercard_statement.pdf"

    @pytest.fixture
    def extraction_result(self, extractor: PDFExtractor, fixture_pdf_path: Path) -> "ExtractionResult":
        """Extract transactions from the fixture PDF."""
        from app.services.pdf_extractor import ExtractionResult
        
        assert fixture_pdf_path.exists(), f"Fixture PDF not found at {fixture_pdf_path}"
        result = extractor.extract(fixture_pdf_path)
        assert result.success, f"Extraction failed: {result.errors}"
        return result

    # ==================== Specific Transaction Amount Tests ====================
    # These tests verify that specific foreign currency transactions have correct amounts
    # after currency conversion lines are filtered out

    def test_music_a_stockholm_ab_has_correct_amount(self, extraction_result: "ExtractionResult"):
        """
        Test that MUSIC-A STOCKHOLM AB has amount 20.57.
        
        This is a foreign currency transaction (Swedish Krona) that should have
        its currency conversion line filtered out, leaving only the merchant
        description with the correct CAD amount.
        
        **Validates: Requirement 3.2** - Extract "MUSIC-A STOCKHOLM AB" with amount 20.57
        """
        # Find the transaction with MUSIC-A STOCKHOLM AB in description
        matching_transactions = [
            t for t in extraction_result.transactions
            if "MUSIC-A STOCKHOLM AB" in t.description.upper()
        ]
        
        assert len(matching_transactions) >= 1, (
            "Expected to find at least one transaction with 'MUSIC-A STOCKHOLM AB' in description. "
            f"Found transactions: {[t.description for t in extraction_result.transactions]}"
        )
        
        # Verify the amount is 20.57
        transaction = matching_transactions[0]
        # Parse the amount string (may be "20,57" or "20.57")
        amount_str = transaction.amount_str.replace(",", ".").replace(" ", "").rstrip("-")
        amount = float(amount_str)
        
        assert amount == 20.57, (
            f"Expected MUSIC-A STOCKHOLM AB to have amount 20.57, "
            f"but got {amount} (raw: '{transaction.amount_str}')"
        )

    def test_serv_a_paris_fr_has_correct_amount(self, extraction_result: "ExtractionResult"):
        """
        Test that Serv-A Paris FR has amount 3.33.
        
        This is a foreign currency transaction (Euro) that should have
        its currency conversion line filtered out, leaving only the merchant
        description with the correct CAD amount.
        
        **Validates: Requirement 3.3** - Extract "Serv-A Paris FR" with amount 3.33
        """
        # Find the transaction with Serv-A Paris FR in description
        matching_transactions = [
            t for t in extraction_result.transactions
            if "SERV-A PARIS FR" in t.description.upper()
        ]
        
        assert len(matching_transactions) >= 1, (
            "Expected to find at least one transaction with 'Serv-A Paris FR' in description. "
            f"Found transactions: {[t.description for t in extraction_result.transactions]}"
        )
        
        # Verify the amount is 3.33
        transaction = matching_transactions[0]
        # Parse the amount string (may be "3,33" or "3.33")
        amount_str = transaction.amount_str.replace(",", ".").replace(" ", "").rstrip("-")
        amount = float(amount_str)
        
        assert amount == 3.33, (
            f"Expected Serv-A Paris FR to have amount 3.33, "
            f"but got {amount} (raw: '{transaction.amount_str}')"
        )

    def test_restaurant_aaa_ville_d_qc_has_correct_amount(self, extraction_result: "ExtractionResult"):
        """
        Test that RESTAURANT AAA___ VILLE-D QC has amount 41.40.
        
        This is the last expense transaction in the statement. If currency
        conversion lines are not properly filtered, this transaction would
        be missing or have an incorrect amount.
        
        Note: The fixture PDF uses "VILLE-EEE" as a placeholder for the actual location.
        
        **Validates: Requirement 4.2** - Extract "RESTAURANT AAA___ VILLE-D QC" with amount 41.40
        """
        # Find the transaction with RESTAURANT AAA and VILLE-D in description
        # Note: There are multiple RESTAURANT AAA transactions, we need the one with VILLE-D
        matching_transactions = [
            t for t in extraction_result.transactions
            if "RESTAURANT AAA" in t.description.upper() and "VILLE-D" in t.description.upper()
        ]
        
        assert len(matching_transactions) >= 1, (
            "Expected to find at least one transaction with 'RESTAURANT AAA' and 'VILLE-D' in description. "
            f"Found transactions: {[t.description for t in extraction_result.transactions if 'RESTAURANT AAA' in t.description.upper()]}"
        )
        
        # Verify the amount is 41.40
        transaction = matching_transactions[0]
        # Parse the amount string (may be "41,40" or "41.40")
        amount_str = transaction.amount_str.replace(",", ".").replace(" ", "").rstrip("-")
        amount = float(amount_str)
        
        assert amount == 41.40, (
            f"Expected RESTAURANT AAA___ VILLE-D QC to have amount 41.40, "
            f"but got {amount} (raw: '{transaction.amount_str}')"
        )

    # ==================== Transaction Count Test ====================
    # This test verifies the total number of expense transactions

    def test_total_expense_transactions_count(self, extraction_result: "ExtractionResult"):
        """
        Test that exactly 83 expense transactions are extracted.
        
        If currency conversion lines are not properly filtered, the count
        would be incorrect (either too many or too few transactions).
        
        **Validates: Requirement 4.3** - Extract exactly 83 expense transactions
        """
        # Count expense transactions (those without CR suffix indicating credits)
        # Desjardins uses "CR" suffix for credits, not "-"
        expense_transactions = [
            t for t in extraction_result.transactions
            if not t.amount_str.strip().upper().endswith("CR")
        ]
        
        assert len(expense_transactions) == 83, (
            f"Expected exactly 83 expense transactions, but got {len(expense_transactions)}. "
            f"Total transactions: {len(extraction_result.transactions)}"
        )

    # ==================== No Currency Text in Descriptions Test ====================
    # This test verifies that currency conversion text is not in any description

    def test_no_currency_conversion_text_in_descriptions(self, extraction_result: "ExtractionResult"):
        """
        Test that no transaction description contains currency conversion text.
        
        Currency conversion lines like "2,18 EURO TX: 1.527522" should be
        filtered out completely, not included in transaction descriptions.
        
        **Validates: Requirement 3.4** - No description contains "EURO TX:" or "USD TX:"
        """
        currency_patterns = ["EURO TX:", "USD TX:", "GBP TX:", "JPY TX:", "CAD TX:", "CHF TX:"]
        
        for transaction in extraction_result.transactions:
            description_upper = transaction.description.upper()
            for pattern in currency_patterns:
                assert pattern not in description_upper, (
                    f"Found currency conversion text '{pattern}' in transaction description: "
                    f"'{transaction.description}'"
                )

    def test_no_tx_colon_pattern_in_any_description(self, extraction_result: "ExtractionResult"):
        """
        Test that no transaction description contains the TX: pattern.
        
        This is a broader check that catches any currency code followed by TX:.
        
        **Validates: Requirement 3.4** - No description contains currency conversion text
        """
        import re
        
        # Pattern to match any currency code followed by TX:
        tx_pattern = re.compile(r"[A-Z]{2,4}\s+TX:", re.IGNORECASE)
        
        for transaction in extraction_result.transactions:
            match = tx_pattern.search(transaction.description)
            assert match is None, (
                f"Found TX: pattern in transaction description: '{transaction.description}'"
            )


# ==================== Module-level Strategies for Property 4 ====================
# These strategies generate domestic transaction description lines (no currency conversion)


def _domestic_description_line_strategy() -> st.SearchStrategy[str]:
    """
    Strategy to generate domestic transaction description lines.
    
    These are lines that would appear in a statement with only domestic transactions.
    They should NOT match the currency conversion pattern.
    """
    return st.one_of(
        # Merchant names with Canadian locations
        st.builds(
            lambda name, location: f"{name} {location}".strip(),
            name=st.sampled_from([
                "RESTAURANT", "GROCERY STORE", "GAS STATION", "PHARMACY",
                "COFFEE SHOP", "BOOKSTORE", "HARDWARE STORE", "BAKERY",
                "METRO INC", "COSTCO WHOLESALE", "WALMART CANADA",
                "TIM HORTONS", "STARBUCKS", "MCDONALDS", "SUBWAY",
                "CANADIAN TIRE", "HOME DEPOT", "LOBLAWS", "SOBEYS",
                "SHOPPERS DRUG MART", "JEAN COUTU", "RONA", "IKEA",
            ]),
            location=st.sampled_from([
                "MTL", "QC", "ON", "BC", "AB", "SK", "MB", "NS", "NB", "PE",
                "MONTREAL", "TORONTO", "VANCOUVER", "CALGARY", "OTTAWA",
                "VILLE-MARIE", "LAVAL", "LONGUEUIL", "GATINEAU", "",
            ]),
        ),
        # Online merchants
        st.sampled_from([
            "AMAZON.CA",
            "AMAZON PRIME",
            "NETFLIX.COM",
            "SPOTIFY",
            "APPLE.COM/BILL",
            "GOOGLE *SERVICES",
            "MICROSOFT*XBOX",
            "STEAM PURCHASE",
            "PAYPAL *MERCHANT",
            "UBER TRIP",
            "UBER EATS",
            "DOORDASH",
            "SKIP THE DISHES",
        ]),
        # Merchant names with store numbers
        st.builds(
            lambda name, num: f"{name} #{num}",
            name=st.sampled_from([
                "STORE", "LOCATION", "BRANCH", "OUTLET",
                "METRO", "IGA", "PROVIGO", "MAXI",
            ]),
            num=st.integers(min_value=1, max_value=9999),
        ),
        # Utility and service providers
        st.sampled_from([
            "HYDRO-QUEBEC",
            "BELL CANADA",
            "ROGERS WIRELESS",
            "TELUS MOBILITY",
            "VIDEOTRON",
            "FIDO",
            "KOODO",
            "VIRGIN MOBILE",
            "ENBRIDGE GAS",
            "TORONTO HYDRO",
        ]),
        # Generic alphanumeric merchant descriptions
        st.text(
            alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_"),
            min_size=5,
            max_size=30,
        ).filter(
            # Ensure it doesn't accidentally match currency pattern
            lambda x: "TX:" not in x.upper() and not x.isspace()
        ),
    )


def _domestic_description_list_strategy() -> st.SearchStrategy[list[str]]:
    """
    Strategy to generate lists of domestic transaction description lines.
    
    These lists represent description columns from statements with only
    domestic transactions - no currency conversion lines at all.
    """
    return st.lists(
        _domestic_description_line_strategy(),
        min_size=0,
        max_size=50,
    )


class TestBackwardCompatibilityProperty:
    r"""Property-based tests for backward compatibility with domestic transactions.
    
    **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
    
    For any list of description lines that contains zero currency conversion lines,
    the `_filter_currency_conversion_lines` method SHALL return the input list unchanged
    (same elements, same order, same length).
    
    This property ensures that the currency line filtering fix does not affect
    statements that contain only domestic transactions.
    
    **Validates: Requirements 5.1, 5.2**
    """

    @given(description_lines=_domestic_description_list_strategy())
    @settings(max_examples=100)
    def test_domestic_transactions_unchanged(self, description_lines: list[str]):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        For any list of description lines that contains zero currency conversion lines,
        the `_filter_currency_conversion_lines` method SHALL return the input list unchanged
        (same elements, same order, same length).
        
        This test generates lists of domestic transaction descriptions (no currency
        conversion lines) and verifies that the filtering method returns them unchanged.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        # Verify output equals input exactly
        assert result == description_lines, (
            f"Domestic transaction list should be unchanged.\n"
            f"Input: {description_lines}\n"
            f"Result: {result}\n"
            f"Input length: {len(description_lines)}\n"
            f"Result length: {len(result)}"
        )

    @given(description_lines=_domestic_description_list_strategy())
    @settings(max_examples=100)
    def test_domestic_transactions_same_length(self, description_lines: list[str]):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        For any list of description lines that contains zero currency conversion lines,
        the output length SHALL equal the input length.
        
        This is a specific check on the length invariant for backward compatibility.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        # Verify length is unchanged
        assert len(result) == len(description_lines), (
            f"Output length should equal input length for domestic transactions.\n"
            f"Input length: {len(description_lines)}\n"
            f"Result length: {len(result)}\n"
            f"Input: {description_lines}\n"
            f"Result: {result}"
        )

    @given(description_lines=_domestic_description_list_strategy())
    @settings(max_examples=100)
    def test_domestic_transactions_same_order(self, description_lines: list[str]):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        For any list of description lines that contains zero currency conversion lines,
        the output SHALL preserve the same order as the input.
        
        This verifies that no reordering occurs during filtering.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        # Verify order is preserved (element by element comparison)
        for i, (input_line, output_line) in enumerate(zip(description_lines, result)):
            assert input_line == output_line, (
                f"Order not preserved at index {i}.\n"
                f"Expected: '{input_line}'\n"
                f"Got: '{output_line}'\n"
                f"Full input: {description_lines}\n"
                f"Full result: {result}"
            )

    @given(description_lines=_domestic_description_list_strategy())
    @settings(max_examples=100)
    def test_domestic_transactions_same_elements(self, description_lines: list[str]):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        For any list of description lines that contains zero currency conversion lines,
        the output SHALL contain exactly the same elements as the input.
        
        This verifies that no elements are added, removed, or modified.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        # Filter the lines
        result = extractor._filter_currency_conversion_lines(description_lines)
        
        # Verify all input elements are in output
        for line in description_lines:
            assert line in result, (
                f"Input element missing from output: '{line}'\n"
                f"Input: {description_lines}\n"
                f"Result: {result}"
            )
        
        # Verify no extra elements in output
        for line in result:
            assert line in description_lines, (
                f"Extra element in output: '{line}'\n"
                f"Input: {description_lines}\n"
                f"Result: {result}"
            )

    def test_empty_list_backward_compatible(self):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        An empty list (edge case) should return an empty list unchanged.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        result = extractor._filter_currency_conversion_lines([])
        
        assert result == [], "Empty list should return empty list"

    def test_single_domestic_line_backward_compatible(self):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        A single domestic transaction line should be returned unchanged.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        input_lines = ["METRO INC MONTREAL QC"]
        result = extractor._filter_currency_conversion_lines(input_lines)
        
        assert result == input_lines, (
            f"Single domestic line should be unchanged.\n"
            f"Input: {input_lines}\n"
            f"Result: {result}"
        )

    def test_typical_domestic_statement_backward_compatible(self):
        """
        **Feature: pdf-currency-line-fix, Property 4: Backward Compatibility for Domestic Transactions**
        
        A typical domestic statement with multiple transactions should be unchanged.
        
        **Validates: Requirements 5.1, 5.2**
        """
        extractor = PDFExtractor()
        
        # Simulate a typical domestic statement description column
        input_lines = [
            "METRO INC MONTREAL QC",
            "TIM HORTONS #1234",
            "AMAZON.CA",
            "HYDRO-QUEBEC",
            "COSTCO WHOLESALE MTL",
            "UBER TRIP",
            "NETFLIX.COM",
            "SHOPPERS DRUG MART",
            "CANADIAN TIRE LAVAL",
            "BELL CANADA",
        ]
        
        result = extractor._filter_currency_conversion_lines(input_lines)
        
        assert result == input_lines, (
            f"Typical domestic statement should be unchanged.\n"
            f"Input: {input_lines}\n"
            f"Result: {result}"
        )
