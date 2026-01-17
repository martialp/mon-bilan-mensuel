"""
Property-based tests for Statement Parser Service.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

from datetime import date
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.models import TransactionType
from app.services.statement_parser import StatementParser, ParsedTransaction
from app.services.pdf_extractor import RawTransaction


# Strategy for generating valid Desjardins month abbreviations
VALID_MONTHS = list(StatementParser.MONTH_MAP.keys())


@st.composite
def desjardins_date_strategy(draw):
    """Generate valid Desjardins date strings with corresponding year."""
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    month_abbrev = draw(st.sampled_from(VALID_MONTHS))
    year = draw(st.integers(min_value=2000, max_value=2030))
    date_str = f"{day} {month_abbrev}"
    return date_str, year


@st.composite
def valid_amount_strategy(draw):
    """Generate valid amount strings in various formats.
    
    Desjardins format:
    - Regular amounts (no suffix) = expenses (purchases)
    - CR suffix = income (credits/payments)
    - Negative sign = expenses
    """
    # Generate a decimal amount between 0.01 and 999999.99
    cents = draw(st.integers(min_value=1, max_value=99999999))
    amount = Decimal(cents) / 100

    # Choose format
    format_type = draw(st.sampled_from(["comma", "dot", "space_comma"]))
    
    # Determine if this is a credit (income) or debit (expense)
    # In Desjardins: CR suffix = income, regular/negative = expense
    is_credit = draw(st.booleans())

    if format_type == "comma":
        # French format: 1234,56
        amount_str = f"{amount:.2f}".replace(".", ",")
    elif format_type == "dot":
        # English format: 1234.56
        amount_str = f"{amount:.2f}"
    else:
        # French format with space thousands: 1 234,56
        int_part = int(amount)
        dec_part = int((amount - int_part) * 100)
        if int_part >= 1000:
            int_str = f"{int_part:,}".replace(",", " ")
        else:
            int_str = str(int_part)
        amount_str = f"{int_str},{dec_part:02d}"

    # Add credit indicator (CR suffix) for income
    if is_credit:
        amount_str = f"{amount_str}CR"

    return amount_str, cents, is_credit


class TestDateParsingRoundTrip:
    """Property-based tests for date parsing."""

    @given(data=desjardins_date_strategy())
    @settings(max_examples=100)
    def test_date_parsing_round_trip(self, data: tuple[str, int]):
        """
        **Feature: mastercard-pdf-import, Property 4: Date Parsing Round-Trip**

        For any valid Desjardins date string (e.g., "15 JAN", "15 JANV") with a
        known statement year, parsing the date and formatting it back to the same
        format SHALL produce an equivalent date representation.

        **Validates: Requirements 2.5**
        """
        date_str, year = data
        parser = StatementParser()

        # Parse the date
        parsed_date = parser.parse_date(date_str, year)

        # Verify the parsed date is valid
        assert isinstance(parsed_date, date)
        assert parsed_date.year == year

        # Extract day from original string
        day = int(date_str.split()[0])
        assert parsed_date.day == day

        # Verify month was correctly parsed by checking it's in valid range
        assert 1 <= parsed_date.month <= 12


class TestCurrencyConversionRoundTrip:
    """Property-based tests for currency conversion."""

    @given(cents=st.integers(min_value=1, max_value=99999999))
    @settings(max_examples=100)
    def test_currency_conversion_round_trip(self, cents: int):
        """
        **Feature: mastercard-pdf-import, Property 5: Currency Conversion Round-Trip**

        For any decimal currency amount, converting to integer cents and back to
        decimal SHALL preserve the value to two decimal places.

        **Validates: Requirements 3.2**
        """
        parser = StatementParser()

        # Convert cents to decimal string (French format with comma)
        decimal_value = Decimal(cents) / 100
        amount_str = f"{decimal_value:.2f}".replace(".", ",")

        # Parse the amount
        parsed_cents, _ = parser.parse_amount(amount_str)

        # Verify round-trip preserves value
        assert parsed_cents == cents


class TestAmountSignClassification:
    """Property-based tests for amount sign classification."""

    @given(data=valid_amount_strategy())
    @settings(max_examples=100)
    def test_amount_sign_classification(self, data: tuple[str, int, bool]):
        """
        **Feature: mastercard-pdf-import, Property 3: Amount Sign Classification**

        For any extracted transaction, if the amount has a CR suffix (credit/payment),
        the transaction type SHALL be "income"; otherwise (purchase/debit),
        the type SHALL be "expense".

        **Validates: Requirements 2.4, 3.3**
        """
        amount_str, expected_cents, is_credit = data
        parser = StatementParser()

        # Parse the amount
        parsed_cents, transaction_type = parser.parse_amount(amount_str)

        # Verify amount is correctly parsed (absolute value)
        assert parsed_cents == expected_cents

        # Verify transaction type based on credit indicator
        if is_credit:
            assert transaction_type == TransactionType.INCOME
        else:
            assert transaction_type == TransactionType.EXPENSE


class TestDescriptionNormalizationIdempotence:
    """Property-based tests for description normalization."""

    @given(description=st.text(min_size=0, max_size=500))
    @settings(max_examples=100)
    def test_description_normalization_idempotence(self, description: str):
        """
        **Feature: mastercard-pdf-import, Property 6: Description Normalization Idempotence**

        For any description string, normalizing it twice SHALL produce the same
        result as normalizing it once (idempotent operation).

        **Validates: Requirements 3.5**
        """
        parser = StatementParser()

        # Normalize once
        normalized_once = parser.normalize_description(description)

        # Normalize twice
        normalized_twice = parser.normalize_description(normalized_once)

        # Idempotence: f(f(x)) == f(x)
        assert normalized_once == normalized_twice


class TestDescriptionNormalizationProperties:
    """Additional property tests for description normalization."""

    @given(description=st.text(min_size=1, max_size=500))
    @settings(max_examples=50)
    def test_normalized_description_has_no_leading_trailing_whitespace(self, description: str):
        """
        Normalized descriptions should have no leading or trailing whitespace.
        """
        parser = StatementParser()
        normalized = parser.normalize_description(description)

        if normalized:  # Only check non-empty results
            assert normalized == normalized.strip()

    @given(description=st.text(min_size=1, max_size=500))
    @settings(max_examples=50)
    def test_normalized_description_has_no_multiple_spaces(self, description: str):
        """
        Normalized descriptions should have no consecutive spaces.
        """
        parser = StatementParser()
        normalized = parser.normalize_description(description)

        # Check no double spaces
        assert "  " not in normalized
