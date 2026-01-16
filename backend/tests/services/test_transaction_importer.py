"""
Property-based tests for Transaction Importer Service.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

from datetime import date
from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st, assume
from sqlmodel import Session

from app.core.db import engine
from app.models import (
    Account,
    AccountType,
    ImportSession,
    ImportStatus,
    Transaction,
    TransactionType,
)
from app.services.statement_parser import ParsedTransaction
from app.services.transaction_importer import TransactionImporter, ImportResult


# Hypothesis strategies for generating test data
@st.composite
def valid_parsed_transaction(draw):
    """Generate a valid ParsedTransaction with all required fields."""
    return ParsedTransaction(
        date_transaction=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
        description=draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip())),
        amount_cents=draw(st.integers(min_value=1, max_value=99999999)),
        transaction_type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
    )


@st.composite
def invalid_parsed_transaction(draw):
    """Generate a ParsedTransaction with at least one invalid field."""
    invalid_type = draw(st.sampled_from(["empty_description", "zero_amount", "negative_amount"]))
    
    if invalid_type == "empty_description":
        return ParsedTransaction(
            date_transaction=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
            description=draw(st.sampled_from(["", "   ", "\t\n"])),
            amount_cents=draw(st.integers(min_value=1, max_value=99999999)),
            transaction_type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
        )
    elif invalid_type == "zero_amount":
        return ParsedTransaction(
            date_transaction=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
            description=draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip())),
            amount_cents=0,
            transaction_type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
        )
    else:  # negative_amount
        return ParsedTransaction(
            date_transaction=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
            description=draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip())),
            amount_cents=draw(st.integers(min_value=-99999999, max_value=-1)),
            transaction_type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
        )


@st.composite
def valid_transaction_list(draw, min_size=1, max_size=10):
    """Generate a list of valid ParsedTransactions with unique combinations."""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    transactions = []
    
    for i in range(count):
        # Generate unique description by appending index
        base_desc = draw(st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip()))
        unique_desc = f"{base_desc}_{i}"
        
        txn = ParsedTransaction(
            date_transaction=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
            description=unique_desc,
            amount_cents=draw(st.integers(min_value=1, max_value=99999999)),
            transaction_type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
        )
        transactions.append(txn)
    
    return transactions


class TestTransactionFieldCompleteness:
    """Property-based tests for transaction field validation."""

    @given(transaction=valid_parsed_transaction())
    @settings(max_examples=100)
    def test_valid_transaction_passes_validation(self, transaction: ParsedTransaction):
        """
        **Feature: mastercard-pdf-import, Property 2: Transaction Field Completeness**

        For any transaction extracted from a valid Desjardins PDF statement, the
        transaction SHALL have a non-null date, non-empty description, and non-zero amount.

        **Validates: Requirements 2.2, 3.1**
        """
        importer = TransactionImporter()
        
        is_valid, error_msg = importer.validate_transaction(transaction)
        
        # Valid transactions should pass validation
        assert is_valid is True
        assert error_msg is None

    @given(transaction=invalid_parsed_transaction())
    @settings(max_examples=100)
    def test_invalid_transaction_fails_validation(self, transaction: ParsedTransaction):
        """
        **Feature: mastercard-pdf-import, Property 2: Transaction Field Completeness (inverse)**

        For any transaction with missing or invalid required fields (empty description,
        zero/negative amount), the validation SHALL fail with an appropriate error message.

        **Validates: Requirements 2.2, 3.1, 3.4**
        """
        importer = TransactionImporter()
        
        is_valid, error_msg = importer.validate_transaction(transaction)
        
        # Invalid transactions should fail validation
        assert is_valid is False
        assert error_msg is not None
        assert len(error_msg) > 0


class TestStatementDateAssociation:
    """Property-based tests for statement date association."""

    @given(transactions=valid_transaction_list(min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_statement_date_association(self, transactions: list[ParsedTransaction]):
        """
        **Feature: mastercard-pdf-import, Property 7: Statement Date Association**

        For any set of transactions imported from a single PDF, all transactions
        SHALL have the same statement_date value matching the PDF's statement date.

        **Validates: Requirements 3.6**
        """
        importer = TransactionImporter()
        statement_date = date(2025, 1, 15)
        source_file = "test_statement.pdf"
        
        with Session(engine) as session:
            # Create a test account
            account = Account(
                name=f"Test Account {uuid4().hex[:8]}",
                type=AccountType.CREDIT_CARD,
                institution="Test Bank"
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            
            try:
                # Import transactions
                result = importer.import_transactions(
                    session=session,
                    transactions=transactions,
                    account_id=account.id,
                    source_file=source_file,
                    statement_date=statement_date,
                )
                
                assert result.success is True
                assert result.transactions_imported == len(transactions)
                
                # Verify all transactions have the same statement_date
                from sqlmodel import select
                stmt = select(Transaction).where(Transaction.account_id == account.id)
                db_transactions = session.exec(stmt).all()
                
                for txn in db_transactions:
                    assert txn.statement_date == statement_date
                    assert txn.source_file == source_file
                
            finally:
                # Cleanup: delete transactions first, then account
                from sqlmodel import select
                stmt = select(Transaction).where(Transaction.account_id == account.id)
                for txn in session.exec(stmt).all():
                    session.delete(txn)
                
                # Delete import session
                stmt = select(ImportSession).where(ImportSession.account_id == account.id)
                for imp_session in session.exec(stmt).all():
                    session.delete(imp_session)
                
                session.delete(account)
                session.commit()


class TestDataConsistencyOnFailure:
    """Property-based tests for data consistency on failure."""

    @given(
        valid_transactions=valid_transaction_list(min_size=1, max_size=3),
        invalid_transaction=invalid_parsed_transaction()
    )
    @settings(max_examples=100)
    def test_data_consistency_on_validation_failure(
        self,
        valid_transactions: list[ParsedTransaction],
        invalid_transaction: ParsedTransaction
    ):
        """
        **Feature: mastercard-pdf-import, Property 12: Data Consistency on Failure**

        For any import that fails at any stage, zero transactions SHALL be persisted
        and the database state SHALL remain unchanged from before the import attempt.

        **Validates: Requirements 6.3**
        """
        importer = TransactionImporter()
        statement_date = date(2025, 1, 15)
        source_file = "test_statement.pdf"
        
        # Mix valid and invalid transactions
        mixed_transactions = valid_transactions + [invalid_transaction]
        
        with Session(engine) as session:
            # Create a test account
            account = Account(
                name=f"Test Account {uuid4().hex[:8]}",
                type=AccountType.CREDIT_CARD,
                institution="Test Bank"
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            
            # Count transactions before import attempt
            from sqlmodel import select, func
            stmt = select(func.count()).select_from(Transaction).where(
                Transaction.account_id == account.id
            )
            count_before = session.exec(stmt).one()
            
            try:
                # Attempt import with mixed transactions (should fail)
                result = importer.import_transactions(
                    session=session,
                    transactions=mixed_transactions,
                    account_id=account.id,
                    source_file=source_file,
                    statement_date=statement_date,
                )
                
                # Import should fail due to invalid transaction
                assert result.success is False
                assert result.transactions_imported == 0
                assert len(result.errors) > 0
                
                # Count transactions after failed import
                count_after = session.exec(stmt).one()
                
                # Database state should be unchanged
                assert count_after == count_before
                
            finally:
                # Cleanup
                session.delete(account)
                session.commit()
