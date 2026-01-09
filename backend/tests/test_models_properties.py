"""
Property-based tests for database models.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

import uuid

import pytest
from hypothesis import given, strategies as st
from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    Account,
    AccountCreate,
    AccountType,
    Category,
    CategoryCreate,
    Transaction,
    TransactionCreate,
    TransactionStatus,
    TransactionType,
)


# Hypothesis strategies for generating test data
@st.composite
def account_data(draw):
    """Generate valid account data."""
    return AccountCreate(
        name=draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        type=draw(st.sampled_from(AccountType)),
        institution=draw(st.one_of(st.none(), st.text(max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        description=draw(st.one_of(st.none(), st.text(max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
    )


@st.composite
def category_data(draw):
    """Generate valid category data."""
    return CategoryCreate(
        name=draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
    )


@st.composite
def transaction_data(draw, account_id=None, category_id=None):
    """Generate valid transaction data."""
    return TransactionCreate(
        date_transaction=draw(st.dates()),
        date_inscription=draw(st.one_of(st.none(), st.dates())),
        description=draw(st.text(min_size=1, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        amount_cents=draw(st.integers(min_value=1, max_value=999999999)),
        type=draw(st.sampled_from(TransactionType)),
        note=draw(st.one_of(st.none(), st.text(max_size=1000, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        source_file=draw(st.one_of(st.none(), st.text(max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        statement_date=draw(st.one_of(st.none(), st.dates())),
        account_id=account_id or uuid.uuid4(),
        category_id=category_id,
    )


class TestAccountProperties:
    """Property-based tests for Account model."""

    @given(account_data=account_data())
    def test_account_creation_and_storage(self, account_data: AccountCreate):
        """
        Property 13: Account Creation and Storage
        For any valid account data with required fields (name, type), 
        creating the account should store all provided fields including 
        optional institution and description.
        
        Feature: personal-finance-tracker, Property 13: Account creation and storage
        **Validates: Requirements 3.1**
        """
        with Session(engine) as session:
            # Create account
            account = Account.model_validate(account_data.model_dump())
            session.add(account)
            session.commit()
            session.refresh(account)
            
            # Retrieve account
            retrieved_account = session.get(Account, account.id)
            
            # Verify all fields are stored correctly
            assert retrieved_account is not None
            assert retrieved_account.name == account_data.name
            assert retrieved_account.type == account_data.type
            assert retrieved_account.institution == account_data.institution
            assert retrieved_account.description == account_data.description
            assert retrieved_account.created_at is not None
            assert isinstance(retrieved_account.id, uuid.UUID)
            
            # Cleanup
            session.delete(retrieved_account)
            session.commit()


class TestCategoryProperties:
    """Property-based tests for Category model."""

    @given(category_data=category_data())
    def test_category_creation_and_uniqueness(self, category_data: CategoryCreate):
        """
        Property 9: Category Creation and Uniqueness
        For any new category name, the system should create the category successfully, 
        but attempting to create a category with an existing name should be rejected.
        
        Feature: personal-finance-tracker, Property 9: Category creation and uniqueness
        **Validates: Requirements 2.3**
        """
        with Session(engine) as session:
            # Create first category
            category1 = Category.model_validate(category_data.model_dump())
            session.add(category1)
            session.commit()
            session.refresh(category1)
            
            # Verify category was created successfully
            assert category1.id is not None
            assert category1.name == category_data.name
            assert category1.created_at is not None
            
            # Attempt to create duplicate category should fail
            category2 = Category.model_validate(category_data.model_dump())
            session.add(category2)
            
            with pytest.raises(Exception):  # Should raise integrity error
                session.commit()
            
            session.rollback()
            
            # Cleanup
            session.delete(category1)
            session.commit()


class TestTransactionProperties:
    """Property-based tests for Transaction model."""

    @given(transaction_data=transaction_data())
    def test_transaction_creation_and_persistence(self, transaction_data: TransactionCreate):
        """
        Property 1: Transaction Creation and Persistence
        For any valid transaction data with required fields (date_transaction, description, 
        amount_cents, type, account_id), creating the transaction should result in it being 
        immediately persisted to the database with all fields intact.
        
        Feature: personal-finance-tracker, Property 1: Transaction creation and persistence
        **Validates: Requirements 1.1**
        """
        with Session(engine) as session:
            # First create an account for the transaction
            account = Account(
                name="Test Account",
                type=AccountType.CHEQUING,
                institution="Test Bank"
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            
            # Update transaction data with the real account ID
            transaction_data.account_id = account.id
            
            # Create transaction
            transaction = Transaction.model_validate(transaction_data.model_dump())
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            
            # Retrieve transaction
            retrieved_transaction = session.get(Transaction, transaction.id)
            
            # Verify all fields are persisted correctly
            assert retrieved_transaction is not None
            assert retrieved_transaction.date_transaction == transaction_data.date_transaction
            assert retrieved_transaction.date_inscription == transaction_data.date_inscription
            assert retrieved_transaction.description == transaction_data.description
            assert retrieved_transaction.amount_cents == transaction_data.amount_cents
            assert retrieved_transaction.type == transaction_data.type
            assert retrieved_transaction.note == transaction_data.note
            assert retrieved_transaction.source_file == transaction_data.source_file
            assert retrieved_transaction.statement_date == transaction_data.statement_date
            assert retrieved_transaction.account_id == account.id
            assert retrieved_transaction.category_id == transaction_data.category_id
            assert retrieved_transaction.status == TransactionStatus.MANUAL  # Default status
            assert retrieved_transaction.created_at is not None
            assert isinstance(retrieved_transaction.id, uuid.UUID)
            
            # Cleanup
            session.delete(retrieved_transaction)
            session.delete(account)
            session.commit()