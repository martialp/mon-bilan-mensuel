"""
Property-based tests for transaction API endpoints.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    Account, AccountType, Category, Transaction, TransactionCreate, 
    TransactionStatus, TransactionType
)


# Hypothesis strategies for generating test data
@st.composite
def transaction_data(draw, account_id=None, category_id=None):
    """Generate valid transaction data."""
    return {
        "date_transaction": draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))).isoformat(),
        "date_inscription": draw(st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)).map(lambda d: d.isoformat()))),
        "description": draw(st.text(min_size=1, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        "amount_cents": draw(st.integers(min_value=1, max_value=999999999)),
        "type": draw(st.sampled_from([t.value for t in TransactionType])),
        "note": draw(st.one_of(st.none(), st.text(max_size=1000, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "source_file": draw(st.one_of(st.none(), st.text(max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "statement_date": draw(st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)).map(lambda d: d.isoformat()))),
        "account_id": str(account_id) if account_id else str(uuid.uuid4()),
        "category_id": str(category_id) if category_id else None,
    }


@st.composite
def transaction_update_data(draw):
    """Generate valid transaction update data."""
    return {
        "date_transaction": draw(st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)).map(lambda d: d.isoformat()))),
        "description": draw(st.one_of(st.none(), st.text(min_size=1, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "amount_cents": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=999999999))),
        "type": draw(st.one_of(st.none(), st.sampled_from([t.value for t in TransactionType]))),
        "category_id": draw(st.one_of(st.none(), st.uuids().map(str))),
        "note": draw(st.one_of(st.none(), st.text(max_size=1000, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
    }


def create_test_account(db: Session) -> Account:
    """Helper function to create a test account."""
    account = Account(
        name="Test Account",
        type=AccountType.CHEQUING,
        institution="Test Bank"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_test_category(db: Session, name: str = "Test Category") -> Category:
    """Helper function to create a test category."""
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


class TestTransactionEndpointProperties:
    """Property-based tests for Transaction API endpoints."""

    @given(transaction_data=transaction_data())
    def test_duplicate_transaction_prevention(self, client: TestClient, db: Session, transaction_data: dict):
        """
        Property 4: Duplicate Transaction Prevention
        For any transaction that already exists in the database, attempting to create 
        an identical transaction (same account_id, date_transaction, description, 
        amount_cents, statement_date) should be prevented and return a clear conflict explanation.
        
        Feature: personal-finance-tracker, Property 4: Duplicate transaction prevention
        **Validates: Requirements 1.4, 5.2, 7.3**
        """
        # Create test account
        account = create_test_account(db)
        transaction_data["account_id"] = str(account.id)
        
        # Create first transaction via API
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        assert response.status_code == 200
        first_transaction = response.json()
        
        # Attempt to create duplicate transaction should fail
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{first_transaction['id']}")
        db.delete(account)
        db.commit()

    @given(transaction_data=transaction_data(), update_data=transaction_update_data())
    def test_transaction_update_integrity(self, client: TestClient, db: Session, transaction_data: dict, update_data: dict):
        """
        Property 6: Transaction Update Integrity
        For any existing transaction, updating its fields should preserve data integrity 
        and maintain all relationships while persisting the changes.
        
        Feature: personal-finance-tracker, Property 6: Transaction update integrity
        **Validates: Requirements 1.6**
        """
        # Create test account and category
        account = create_test_account(db)
        category = create_test_category(db)
        transaction_data["account_id"] = str(account.id)
        transaction_data["category_id"] = str(category.id)
        
        # Create transaction via API
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        assert response.status_code == 200
        created_transaction = response.json()
        transaction_id = created_transaction["id"]
        
        # Filter out None values from update_data and ensure category exists if provided
        filtered_update_data = {k: v for k, v in update_data.items() if v is not None}
        if "category_id" in filtered_update_data:
            # Create a new category for the update
            update_category = create_test_category(db, name=f"Update Category {uuid.uuid4()}")
            filtered_update_data["category_id"] = str(update_category.id)
        
        if filtered_update_data:  # Only update if there's something to update
            # Update transaction via API
            response = client.put(
                f"{settings.API_V1_STR}/transactions/{transaction_id}",
                json=filtered_update_data,
            )
            assert response.status_code == 200
            updated_transaction = response.json()
            
            # Verify data integrity - updated fields should be changed
            for key, value in filtered_update_data.items():
                assert updated_transaction[key] == value
            
            # Verify relationships are maintained
            assert updated_transaction["account_id"] == str(account.id)
            assert "id" in updated_transaction
            assert "created_at" in updated_transaction
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{transaction_id}")
        if "category_id" in filtered_update_data:
            db.delete(update_category)
        db.delete(category)
        db.delete(account)
        db.commit()

    def test_transaction_status_filtering(self, client: TestClient, db: Session):
        """
        Property 8: Transaction Status Filtering
        For any set of transactions, filtering for uncategorized transactions should return 
        only those with category_id NULL, and filtering for transactions needing confirmation 
        should return only those with status 'auto'.
        
        Feature: personal-finance-tracker, Property 8: Transaction status filtering
        **Validates: Requirements 2.2**
        """
        # Create test account and category
        account = create_test_account(db)
        category = create_test_category(db)
        
        # Create transactions with different statuses directly in database
        # Uncategorized transaction (category_id = NULL)
        uncategorized_transaction = Transaction(
            date_transaction=date(2024, 1, 1),
            description="Uncategorized transaction",
            amount_cents=1000,
            type=TransactionType.EXPENSE,
            account_id=account.id,
            category_id=None,  # NULL category
            status=TransactionStatus.MANUAL
        )
        
        # Auto-categorized transaction needing confirmation
        auto_transaction = Transaction(
            date_transaction=date(2024, 1, 2),
            description="Auto transaction",
            amount_cents=2000,
            type=TransactionType.EXPENSE,
            account_id=account.id,
            category_id=category.id,
            status=TransactionStatus.AUTO  # Needs confirmation
        )
        
        # Confirmed transaction (should not appear in either filter)
        confirmed_transaction = Transaction(
            date_transaction=date(2024, 1, 3),
            description="Confirmed transaction",
            amount_cents=3000,
            type=TransactionType.EXPENSE,
            account_id=account.id,
            category_id=category.id,
            status=TransactionStatus.CONFIRMED
        )
        
        db.add_all([uncategorized_transaction, auto_transaction, confirmed_transaction])
        db.commit()
        db.refresh(uncategorized_transaction)
        db.refresh(auto_transaction)
        db.refresh(confirmed_transaction)
        
        # Test uncategorized transactions endpoint
        response = client.get(f"{settings.API_V1_STR}/transactions/uncategorized")
        assert response.status_code == 200
        uncategorized_data = response.json()
        
        # Should contain only the uncategorized transaction
        assert uncategorized_data["count"] >= 1
        uncategorized_ids = [t["id"] for t in uncategorized_data["data"]]
        assert str(uncategorized_transaction.id) in uncategorized_ids
        assert str(auto_transaction.id) not in uncategorized_ids
        assert str(confirmed_transaction.id) not in uncategorized_ids
        
        # Verify all returned transactions have category_id = null
        for transaction in uncategorized_data["data"]:
            assert transaction["category_id"] is None
        
        # Test pending confirmation transactions endpoint
        response = client.get(f"{settings.API_V1_STR}/transactions/pending-confirmation")
        assert response.status_code == 200
        pending_data = response.json()
        
        # Should contain only the auto transaction
        assert pending_data["count"] >= 1
        pending_ids = [t["id"] for t in pending_data["data"]]
        assert str(auto_transaction.id) in pending_ids
        assert str(uncategorized_transaction.id) not in pending_ids
        assert str(confirmed_transaction.id) not in pending_ids
        
        # Verify all returned transactions have status = 'auto'
        for transaction in pending_data["data"]:
            assert transaction["status"] == "auto"
        
        # Cleanup
        db.delete(uncategorized_transaction)
        db.delete(auto_transaction)
        db.delete(confirmed_transaction)
        db.delete(category)
        db.delete(account)
        db.commit()


def test_transaction_not_found(client: TestClient):
    """Test that accessing non-existent transaction returns 404."""
    response = client.get(f"{settings.API_V1_STR}/transactions/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_delete_transaction_not_found(client: TestClient):
    """Test that deleting non-existent transaction returns 404."""
    response = client.delete(f"{settings.API_V1_STR}/transactions/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_update_transaction_not_found(client: TestClient):
    """Test that updating non-existent transaction returns 404."""
    update_data = {"description": "Updated Description"}
    response = client.put(
        f"{settings.API_V1_STR}/transactions/{uuid.uuid4()}",
        json=update_data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_create_transaction_invalid_account(client: TestClient):
    """Test that creating transaction with invalid account returns 400."""
    transaction_data = {
        "date_transaction": "2024-01-01",
        "description": "Test transaction",
        "amount_cents": 1000,
        "type": "expense",
        "account_id": str(uuid.uuid4()),  # Non-existent account
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        json=transaction_data,
    )
    assert response.status_code == 400
    assert "Account not found" in response.json()["detail"]


def test_create_transaction_invalid_category(client: TestClient, db: Session):
    """Test that creating transaction with invalid category returns 400."""
    # Create test account
    account = create_test_account(db)
    
    transaction_data = {
        "date_transaction": "2024-01-01",
        "description": "Test transaction",
        "amount_cents": 1000,
        "type": "expense",
        "account_id": str(account.id),
        "category_id": str(uuid.uuid4()),  # Non-existent category
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        json=transaction_data,
    )
    assert response.status_code == 400
    assert "Category not found" in response.json()["detail"]
    
    # Cleanup
    db.delete(account)
    db.commit()


def test_categorize_transaction(client: TestClient, db: Session):
    """Test manual categorization of transaction."""
    # Create test account and category
    account = create_test_account(db)
    category = create_test_category(db)
    
    # Create transaction via API
    transaction_data = {
        "date_transaction": "2024-01-01",
        "description": "Test transaction",
        "amount_cents": 1000,
        "type": "expense",
        "account_id": str(account.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        json=transaction_data,
    )
    assert response.status_code == 200
    transaction = response.json()
    transaction_id = transaction["id"]
    
    # Categorize transaction
    response = client.put(
        f"{settings.API_V1_STR}/transactions/{transaction_id}/categorize",
        params={"category_id": str(category.id)},
    )
    assert response.status_code == 200
    categorized_transaction = response.json()
    
    # Verify categorization
    assert categorized_transaction["category_id"] == str(category.id)
    assert categorized_transaction["status"] == "manual"
    
    # Cleanup
    client.delete(f"{settings.API_V1_STR}/transactions/{transaction_id}")
    db.delete(category)
    db.delete(account)
    db.commit()


def test_confirm_transaction(client: TestClient, db: Session):
    """Test confirmation of auto-categorized transaction."""
    # Create test account and category
    account = create_test_account(db)
    category = create_test_category(db)
    
    # Create auto-categorized transaction directly in database
    transaction = Transaction(
        date_transaction=date(2024, 1, 1),
        description="Auto transaction",
        amount_cents=1000,
        type=TransactionType.EXPENSE,
        account_id=account.id,
        category_id=category.id,
        status=TransactionStatus.AUTO
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Confirm transaction
    response = client.put(f"{settings.API_V1_STR}/transactions/{transaction.id}/confirm")
    assert response.status_code == 200
    confirmed_transaction = response.json()
    
    # Verify confirmation
    assert confirmed_transaction["status"] == "confirmed"
    assert confirmed_transaction["category_id"] == str(category.id)
    
    # Cleanup
    db.delete(transaction)
    db.delete(category)
    db.delete(account)
    db.commit()


def test_confirm_non_auto_transaction(client: TestClient, db: Session):
    """Test that confirming non-auto transaction returns 400."""
    # Create test account
    account = create_test_account(db)
    
    # Create manual transaction directly in database
    transaction = Transaction(
        date_transaction=date(2024, 1, 1),
        description="Manual transaction",
        amount_cents=1000,
        type=TransactionType.EXPENSE,
        account_id=account.id,
        status=TransactionStatus.MANUAL
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Attempt to confirm manual transaction should fail
    response = client.put(f"{settings.API_V1_STR}/transactions/{transaction.id}/confirm")
    assert response.status_code == 400
    assert "Only auto-categorized transactions can be confirmed" in response.json()["detail"]
    
    # Cleanup
    db.delete(transaction)
    db.delete(account)
    db.commit()