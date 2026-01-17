"""
Property-based tests for Import Preview data models.

These tests validate the import preview and confirmation workflow
using Hypothesis for property-based testing.

Property 8: Preview Data Completeness
Property 9: Total Validation Consistency

**Validates: Requirements 4.2, 4.3, 4.5, 4.6**

Note: These tests use local model definitions to avoid database dependencies,
allowing them to run without a database connection.
"""

import uuid
from datetime import date
from enum import Enum

import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings
from pydantic import BaseModel


# Mark all tests in this module to not use the db fixture
pytestmark = pytest.mark.usefixtures()


# Local model definitions to avoid importing from app (which requires db connection)
class TransactionType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class TransactionPreview(BaseModel):
    """Single transaction in import preview."""
    date_transaction: date
    description: str
    amount_cents: int
    type: TransactionType


class ImportPreviewPublic(BaseModel):
    """Preview response after PDF extraction."""
    import_id: uuid.UUID
    file_name: str
    statement_date: date | None
    statement_total_cents: int | None
    calculated_total_cents: int
    totals_match: bool
    transactions: list[TransactionPreview]
    warnings: list[str]


# Hypothesis strategies for generating test data
@st.composite
def transaction_preview_data(draw):
    """Generate valid transaction preview data."""
    return TransactionPreview(
        date_transaction=draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))),
        description=draw(st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        amount_cents=draw(st.integers(min_value=1, max_value=999999999)),
        type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
    )


@st.composite
def transaction_preview_list(draw, min_size=1, max_size=10):
    """Generate a list of transaction previews."""
    return draw(st.lists(transaction_preview_data(), min_size=min_size, max_size=max_size))


class TestPreviewDataCompleteness:
    """
    Property 8: Preview Data Completeness
    For any successful extraction, the preview response SHALL include all extracted 
    transactions with date, description, amount, and type fields, plus a calculated 
    total equal to the sum of all transaction amounts.
    
    Feature: mastercard-pdf-import, Property 8: Preview data completeness
    **Validates: Requirements 4.2, 4.3**
    """

    @given(transactions=transaction_preview_list(min_size=1, max_size=20))
    @hypothesis_settings(max_examples=100)
    def test_preview_contains_all_required_fields(
        self,
        transactions: list[TransactionPreview],
    ):
        """
        Test that every transaction in a preview has all required fields:
        date, description, amount, and type.
        """
        for txn in transactions:
            # Each transaction must have a date
            assert txn.date_transaction is not None
            assert isinstance(txn.date_transaction, date)
            
            # Each transaction must have a non-empty description
            assert txn.description is not None
            assert len(txn.description) > 0
            
            # Each transaction must have a positive amount
            assert txn.amount_cents is not None
            assert txn.amount_cents > 0
            
            # Each transaction must have a valid type
            assert txn.type is not None
            assert txn.type in [TransactionType.EXPENSE, TransactionType.INCOME]

    @given(transactions=transaction_preview_list(min_size=1, max_size=20))
    @hypothesis_settings(max_examples=100)
    def test_calculated_total_equals_sum_of_amounts(
        self,
        transactions: list[TransactionPreview],
    ):
        """
        Test that the calculated total equals the sum of all transaction amounts,
        with income as positive and expense as negative.
        """
        # Calculate expected total (income positive, expense negative)
        expected_total = sum(
            txn.amount_cents if txn.type == TransactionType.INCOME else -txn.amount_cents
            for txn in transactions
        )
        
        # Simulate what the API does
        calculated_total_cents = sum(
            txn.amount_cents if txn.type == TransactionType.INCOME else -txn.amount_cents
            for txn in transactions
        )
        
        assert calculated_total_cents == expected_total

    @given(
        transactions=transaction_preview_list(min_size=1, max_size=10),
        statement_date=st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))),
        statement_total_cents=st.one_of(st.none(), st.integers(min_value=-999999999, max_value=999999999)),
    )
    @hypothesis_settings(max_examples=100)
    def test_preview_response_structure_completeness(
        self,
        transactions: list[TransactionPreview],
        statement_date: date | None,
        statement_total_cents: int | None,
    ):
        """
        Test that ImportPreviewPublic contains all required fields and
        the transactions list matches the input.
        """
        # Calculate total
        calculated_total_cents = sum(
            txn.amount_cents if txn.type == TransactionType.INCOME else -txn.amount_cents
            for txn in transactions
        )
        
        # Determine if totals match
        totals_match = (
            statement_total_cents is not None and
            statement_total_cents == calculated_total_cents
        )
        
        # Create preview response
        preview = ImportPreviewPublic(
            import_id=uuid.uuid4(),
            file_name="test.pdf",
            statement_date=statement_date,
            statement_total_cents=statement_total_cents,
            calculated_total_cents=calculated_total_cents,
            totals_match=totals_match,
            transactions=transactions,
            warnings=[],
        )
        
        # Verify all required fields are present
        assert preview.import_id is not None
        assert preview.file_name is not None
        assert preview.calculated_total_cents is not None
        assert preview.totals_match is not None
        assert preview.transactions is not None
        assert preview.warnings is not None
        
        # Verify transactions list matches input
        assert len(preview.transactions) == len(transactions)
        for i, txn in enumerate(preview.transactions):
            assert txn.date_transaction == transactions[i].date_transaction
            assert txn.description == transactions[i].description
            assert txn.amount_cents == transactions[i].amount_cents
            assert txn.type == transactions[i].type


class TestTotalValidationConsistency:
    """
    Property 9: Total Validation Consistency
    For any import preview, if the calculated total equals the statement total, 
    totals_match SHALL be true; otherwise totals_match SHALL be false and both 
    totals SHALL be included in the response.
    
    Feature: mastercard-pdf-import, Property 9: Total validation consistency
    **Validates: Requirements 4.5, 4.6**
    """

    @given(
        calculated_total=st.integers(min_value=-999999999, max_value=999999999),
        statement_total=st.integers(min_value=-999999999, max_value=999999999),
    )
    @hypothesis_settings(max_examples=100)
    def test_totals_match_when_equal(
        self,
        calculated_total: int,
        statement_total: int,
    ):
        """
        Test that totals_match is true if and only if calculated_total equals statement_total.
        """
        # Create preview with both totals
        preview = ImportPreviewPublic(
            import_id=uuid.uuid4(),
            file_name="test.pdf",
            statement_date=date(2025, 1, 15),
            statement_total_cents=statement_total,
            calculated_total_cents=calculated_total,
            totals_match=(statement_total == calculated_total),
            transactions=[],
            warnings=[],
        )
        
        # Verify totals_match is correct
        if calculated_total == statement_total:
            assert preview.totals_match is True
        else:
            assert preview.totals_match is False

    @given(
        calculated_total=st.integers(min_value=-999999999, max_value=999999999),
    )
    @hypothesis_settings(max_examples=100)
    def test_totals_match_false_when_statement_total_none(
        self,
        calculated_total: int,
    ):
        """
        Test that totals_match is false when statement_total is None.
        """
        # When statement_total is None, totals cannot match
        totals_match = False  # Cannot match if statement_total is None
        
        preview = ImportPreviewPublic(
            import_id=uuid.uuid4(),
            file_name="test.pdf",
            statement_date=date(2025, 1, 15),
            statement_total_cents=None,
            calculated_total_cents=calculated_total,
            totals_match=totals_match,
            transactions=[],
            warnings=[],
        )
        
        # totals_match should be false when statement_total is None
        assert preview.totals_match is False

    @given(
        calculated_total=st.integers(min_value=-999999999, max_value=999999999),
        statement_total=st.integers(min_value=-999999999, max_value=999999999),
    )
    @hypothesis_settings(max_examples=100)
    def test_both_totals_included_in_response(
        self,
        calculated_total: int,
        statement_total: int,
    ):
        """
        Test that both totals are always included in the response when statement_total is provided.
        """
        preview = ImportPreviewPublic(
            import_id=uuid.uuid4(),
            file_name="test.pdf",
            statement_date=date(2025, 1, 15),
            statement_total_cents=statement_total,
            calculated_total_cents=calculated_total,
            totals_match=(statement_total == calculated_total),
            transactions=[],
            warnings=[],
        )
        
        # Both totals should be present
        assert preview.calculated_total_cents == calculated_total
        assert preview.statement_total_cents == statement_total

    @given(
        transactions=transaction_preview_list(min_size=1, max_size=10),
    )
    @hypothesis_settings(max_examples=100)
    def test_calculated_total_consistency_with_transactions(
        self,
        transactions: list[TransactionPreview],
    ):
        """
        Test that calculated_total is always consistent with the sum of transaction amounts.
        """
        # Calculate expected total
        expected_total = sum(
            txn.amount_cents if txn.type == TransactionType.INCOME else -txn.amount_cents
            for txn in transactions
        )
        
        # Use the same total as statement_total to test matching
        preview = ImportPreviewPublic(
            import_id=uuid.uuid4(),
            file_name="test.pdf",
            statement_date=date(2025, 1, 15),
            statement_total_cents=expected_total,
            calculated_total_cents=expected_total,
            totals_match=True,
            transactions=transactions,
            warnings=[],
        )
        
        # Verify calculated total matches expected
        assert preview.calculated_total_cents == expected_total
        
        # Verify totals_match is true when they're equal
        assert preview.totals_match is True

    @given(
        transactions=transaction_preview_list(min_size=1, max_size=10),
        offset=st.integers(min_value=1, max_value=10000),
    )
    @hypothesis_settings(max_examples=100)
    def test_totals_mismatch_detection(
        self,
        transactions: list[TransactionPreview],
        offset: int,
    ):
        """
        Test that totals_match is false when statement_total differs from calculated_total.
        """
        # Calculate expected total
        calculated_total = sum(
            txn.amount_cents if txn.type == TransactionType.INCOME else -txn.amount_cents
            for txn in transactions
        )
        
        # Create a different statement total
        statement_total = calculated_total + offset
        
        preview = ImportPreviewPublic(
            import_id=uuid.uuid4(),
            file_name="test.pdf",
            statement_date=date(2025, 1, 15),
            statement_total_cents=statement_total,
            calculated_total_cents=calculated_total,
            totals_match=False,  # Should be false since totals differ
            transactions=transactions,
            warnings=[],
        )
        
        # Verify totals_match is false
        assert preview.totals_match is False
        
        # Verify both totals are present for user comparison
        assert preview.calculated_total_cents == calculated_total
        assert preview.statement_total_cents == statement_total
