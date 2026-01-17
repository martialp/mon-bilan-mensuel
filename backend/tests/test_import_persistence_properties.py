"""
Property-based tests for Import Persistence and Session Tracking.

These tests validate the atomicity of import operations and proper session tracking
using Hypothesis for property-based testing.

Property 10: Import Persistence Atomicity
Property 11: Import Session Tracking

**Validates: Requirements 4.8, 4.9, 5.1, 5.3, 5.4**
"""

import uuid
from datetime import date, datetime
from typing import Any

import pytest
from hypothesis import given, settings as hypothesis_settings, strategies as st, assume
from sqlmodel import Session, select, func

from app.core.db import engine
from app.models import (
    Account,
    AccountType,
    ImportSession,
    ImportStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from app.services.statement_parser import ParsedTransaction
from app.services.transaction_importer import TransactionImporter


# Hypothesis strategies for generating test data
@st.composite
def valid_parsed_transaction(draw, index: int = 0):
    """Generate a valid ParsedTransaction with all required fields."""
    base_desc = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126)
        ).filter(lambda x: x.strip())
    )
    # Add index to ensure uniqueness
    unique_desc = f"{base_desc}_{index}_{uuid.uuid4().hex[:8]}"
    
    return ParsedTransaction(
        date_transaction=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
        description=unique_desc,
        amount_cents=draw(st.integers(min_value=1, max_value=99999999)),
        transaction_type=draw(st.sampled_from([TransactionType.EXPENSE, TransactionType.INCOME])),
    )


@st.composite
def valid_transaction_list(draw, min_size=1, max_size=10):
    """Generate a list of valid ParsedTransactions with unique combinations."""
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    transactions = []
    
    for i in range(count):
        txn = draw(valid_parsed_transaction(index=i))
        transactions.append(txn)
    
    return transactions


def create_test_account(session: Session) -> Account:
    """Helper to create a test account."""
    account = Account(
        name=f"Test Account {uuid.uuid4().hex[:8]}",
        type=AccountType.CREDIT_CARD,
        institution="Test Bank"
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def cleanup_account_data(session: Session, account_id: uuid.UUID) -> None:
    """Helper to cleanup all data related to an account."""
    # Delete transactions
    stmt = select(Transaction).where(Transaction.account_id == account_id)
    for txn in session.exec(stmt).all():
        session.delete(txn)
    
    # Delete import sessions
    stmt = select(ImportSession).where(ImportSession.account_id == account_id)
    for imp_session in session.exec(stmt).all():
        session.delete(imp_session)
    
    # Delete account
    account = session.get(Account, account_id)
    if account:
        session.delete(account)
    
    session.commit()


class TestImportPersistenceAtomicity:
    """
    Property 10: Import Persistence Atomicity
    For any confirmed import, all extracted transactions SHALL be persisted to the database;
    for any rejected import, zero transactions SHALL be persisted.
    
    Feature: mastercard-pdf-import, Property 10: Import persistence atomicity
    **Validates: Requirements 4.8, 4.9**
    """

    @given(transactions=valid_transaction_list(min_size=1, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_confirmed_import_persists_all_transactions(
        self,
        transactions: list[ParsedTransaction],
    ):
        """
        Test that when an import is confirmed, ALL extracted transactions
        are persisted to the database atomically.
        """
        importer = TransactionImporter()
        statement_date = date(2025, 1, 15)
        source_file = f"test_statement_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
            try:
                # Count transactions before import
                stmt = select(func.count()).select_from(Transaction).where(
                    Transaction.account_id == account.id
                )
                count_before = session.exec(stmt).one()
                assert count_before == 0
                
                # Import transactions
                result = importer.import_transactions(
                    session=session,
                    transactions=transactions,
                    account_id=account.id,
                    source_file=source_file,
                    statement_date=statement_date,
                )
                
                # Verify import succeeded
                assert result.success is True
                assert result.transactions_imported == len(transactions)
                
                # Count transactions after import
                count_after = session.exec(stmt).one()
                
                # ALL transactions should be persisted
                assert count_after == len(transactions)
                
                # Verify each transaction was persisted correctly
                stmt = select(Transaction).where(Transaction.account_id == account.id)
                db_transactions = session.exec(stmt).all()
                
                assert len(db_transactions) == len(transactions)
                
                # Verify transaction data integrity
                for db_txn in db_transactions:
                    assert db_txn.source_file == source_file
                    assert db_txn.statement_date == statement_date
                    assert db_txn.status == TransactionStatus.AUTO
                
            finally:
                cleanup_account_data(session, account.id)

    @given(transactions=valid_transaction_list(min_size=1, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_rejected_import_persists_zero_transactions(
        self,
        transactions: list[ParsedTransaction],
    ):
        """
        Test that when an import is rejected (simulated by not calling import),
        zero transactions are persisted to the database.
        
        This test simulates the rejection flow where transactions are extracted
        but the user rejects the import before confirmation.
        """
        statement_date = date(2025, 1, 15)
        source_file = f"test_statement_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
            try:
                # Create an import session in PENDING status (simulating upload)
                import_session = ImportSession(
                    file_name=source_file,
                    account_id=account.id,
                    status=ImportStatus.PENDING,
                    transaction_count=len(transactions),
                    statement_date=statement_date,
                )
                session.add(import_session)
                session.commit()
                session.refresh(import_session)
                
                # Count transactions before rejection
                stmt = select(func.count()).select_from(Transaction).where(
                    Transaction.account_id == account.id
                )
                count_before = session.exec(stmt).one()
                assert count_before == 0
                
                # Simulate rejection by updating status (no transactions imported)
                import_session.status = ImportStatus.REJECTED
                import_session.completed_at = datetime.utcnow()
                session.add(import_session)
                session.commit()
                
                # Count transactions after rejection
                count_after = session.exec(stmt).one()
                
                # ZERO transactions should be persisted
                assert count_after == 0
                
                # Verify import session status
                session.refresh(import_session)
                assert import_session.status == ImportStatus.REJECTED
                
            finally:
                cleanup_account_data(session, account.id)

    @given(
        transactions=valid_transaction_list(min_size=2, max_size=5),
        fail_at_index=st.integers(min_value=0, max_value=4)
    )
    @hypothesis_settings(max_examples=100)
    def test_partial_failure_persists_zero_transactions(
        self,
        transactions: list[ParsedTransaction],
        fail_at_index: int,
    ):
        """
        Test that if an import fails partway through, zero transactions
        are persisted (atomic rollback).
        """
        # Ensure fail_at_index is within bounds
        assume(fail_at_index < len(transactions))
        
        statement_date = date(2025, 1, 15)
        source_file = f"test_statement_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
            try:
                # Count transactions before import attempt
                stmt = select(func.count()).select_from(Transaction).where(
                    Transaction.account_id == account.id
                )
                count_before = session.exec(stmt).one()
                assert count_before == 0
                
                # Modify one transaction to be invalid (empty description)
                invalid_transactions = list(transactions)
                invalid_transactions[fail_at_index] = ParsedTransaction(
                    date_transaction=transactions[fail_at_index].date_transaction,
                    description="",  # Invalid: empty description
                    amount_cents=transactions[fail_at_index].amount_cents,
                    transaction_type=transactions[fail_at_index].transaction_type,
                )
                
                # Attempt import with invalid transaction
                importer = TransactionImporter()
                result = importer.import_transactions(
                    session=session,
                    transactions=invalid_transactions,
                    account_id=account.id,
                    source_file=source_file,
                    statement_date=statement_date,
                )
                
                # Import should fail
                assert result.success is False
                assert result.transactions_imported == 0
                
                # Count transactions after failed import
                count_after = session.exec(stmt).one()
                
                # ZERO transactions should be persisted (atomic rollback)
                assert count_after == 0
                
            finally:
                cleanup_account_data(session, account.id)


class TestImportSessionTracking:
    """
    Property 11: Import Session Tracking
    For any completed import, an ImportSession record SHALL exist with the correct
    file_name, transaction_count matching the number of imported transactions, and
    all imported transactions SHALL have source_file set to the import file name.
    
    Feature: mastercard-pdf-import, Property 11: Import session tracking
    **Validates: Requirements 5.1, 5.3, 5.4**
    """

    @given(transactions=valid_transaction_list(min_size=1, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_import_session_created_with_correct_metadata(
        self,
        transactions: list[ParsedTransaction],
    ):
        """
        Test that an ImportSession record is created with correct file_name
        and transaction_count after a successful import.
        """
        importer = TransactionImporter()
        statement_date = date(2025, 1, 15)
        source_file = f"test_statement_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
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
                assert result.import_session_id is not None
                
                # Verify ImportSession record exists
                import_session = session.get(ImportSession, result.import_session_id)
                assert import_session is not None
                
                # Verify file_name matches
                assert import_session.file_name == source_file
                
                # Verify transaction_count matches
                assert import_session.transaction_count == len(transactions)
                
                # Verify status is COMPLETED
                assert import_session.status == ImportStatus.COMPLETED
                
                # Verify account_id matches
                assert import_session.account_id == account.id
                
            finally:
                cleanup_account_data(session, account.id)

    @given(transactions=valid_transaction_list(min_size=1, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_all_transactions_have_source_file_set(
        self,
        transactions: list[ParsedTransaction],
    ):
        """
        Test that all imported transactions have source_file set to the
        import file name.
        """
        importer = TransactionImporter()
        statement_date = date(2025, 1, 15)
        source_file = f"test_statement_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
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
                
                # Retrieve all imported transactions
                stmt = select(Transaction).where(Transaction.account_id == account.id)
                db_transactions = session.exec(stmt).all()
                
                # Verify ALL transactions have source_file set correctly
                for db_txn in db_transactions:
                    assert db_txn.source_file == source_file
                
            finally:
                cleanup_account_data(session, account.id)

    @given(transactions=valid_transaction_list(min_size=1, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_transaction_count_matches_imported_count(
        self,
        transactions: list[ParsedTransaction],
    ):
        """
        Test that the ImportSession.transaction_count matches the actual
        number of transactions imported.
        """
        importer = TransactionImporter()
        statement_date = date(2025, 1, 15)
        source_file = f"test_statement_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
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
                assert result.import_session_id is not None
                
                # Get ImportSession
                import_session = session.get(ImportSession, result.import_session_id)
                assert import_session is not None
                
                # Count actual transactions in database
                stmt = select(func.count()).select_from(Transaction).where(
                    Transaction.account_id == account.id
                )
                actual_count = session.exec(stmt).one()
                
                # Verify counts match
                assert import_session.transaction_count == actual_count
                assert import_session.transaction_count == result.transactions_imported
                assert import_session.transaction_count == len(transactions)
                
            finally:
                cleanup_account_data(session, account.id)

    @given(
        transactions1=valid_transaction_list(min_size=1, max_size=3),
        transactions2=valid_transaction_list(min_size=1, max_size=3),
    )
    @hypothesis_settings(max_examples=100)
    def test_multiple_imports_tracked_separately(
        self,
        transactions1: list[ParsedTransaction],
        transactions2: list[ParsedTransaction],
    ):
        """
        Test that multiple imports create separate ImportSession records
        and transactions are correctly linked to their respective sessions.
        """
        importer = TransactionImporter()
        statement_date1 = date(2025, 1, 15)
        statement_date2 = date(2025, 2, 15)
        source_file1 = f"statement_jan_{uuid.uuid4().hex[:8]}.pdf"
        source_file2 = f"statement_feb_{uuid.uuid4().hex[:8]}.pdf"
        
        with Session(engine) as session:
            account = create_test_account(session)
            
            try:
                # First import
                result1 = importer.import_transactions(
                    session=session,
                    transactions=transactions1,
                    account_id=account.id,
                    source_file=source_file1,
                    statement_date=statement_date1,
                )
                
                assert result1.success is True
                
                # Second import
                result2 = importer.import_transactions(
                    session=session,
                    transactions=transactions2,
                    account_id=account.id,
                    source_file=source_file2,
                    statement_date=statement_date2,
                )
                
                assert result2.success is True
                
                # Verify two separate ImportSession records exist
                stmt = select(ImportSession).where(ImportSession.account_id == account.id)
                import_sessions = session.exec(stmt).all()
                assert len(import_sessions) == 2
                
                # Verify each session has correct metadata
                session1 = session.get(ImportSession, result1.import_session_id)
                session2 = session.get(ImportSession, result2.import_session_id)
                
                assert session1.file_name == source_file1
                assert session1.transaction_count == len(transactions1)
                
                assert session2.file_name == source_file2
                assert session2.transaction_count == len(transactions2)
                
                # Verify transactions are linked to correct source files
                stmt = select(Transaction).where(Transaction.source_file == source_file1)
                txns1 = session.exec(stmt).all()
                assert len(txns1) == len(transactions1)
                
                stmt = select(Transaction).where(Transaction.source_file == source_file2)
                txns2 = session.exec(stmt).all()
                assert len(txns2) == len(transactions2)
                
            finally:
                cleanup_account_data(session, account.id)
