"""
Property-based tests for account API endpoints.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st
from sqlmodel import Session

from app.core.config import settings
from app.models import Account, AccountCreate, AccountType, Transaction, TransactionCreate, TransactionType


# Hypothesis strategies for generating test data
@st.composite
def account_data(draw):
    """Generate valid account data."""
    return {
        "name": draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        "type": draw(st.sampled_from([t.value for t in AccountType])),
        "institution": draw(st.one_of(st.none(), st.text(max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "description": draw(st.one_of(st.none(), st.text(max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
    }


@st.composite
def account_update_data(draw):
    """Generate valid account update data."""
    return {
        "name": draw(st.one_of(st.none(), st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "type": draw(st.one_of(st.none(), st.sampled_from([t.value for t in AccountType]))),
        "institution": draw(st.one_of(st.none(), st.text(max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "description": draw(st.one_of(st.none(), st.text(max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
    }


class TestAccountEndpointProperties:
    """Property-based tests for Account API endpoints."""

    @given(account_data=account_data())
    def test_account_data_retrieval(self, client: TestClient, account_data: dict):
        """
        Property 15: Account Data Retrieval
        For any stored account, retrieving it should return all required fields 
        (name, type, institution) for identification.
        
        Feature: personal-finance-tracker, Property 15: Account data retrieval
        **Validates: Requirements 3.3**
        """
        # Create account via API
        response = client.post(
            f"{settings.API_V1_STR}/accounts/",
            json=account_data,
        )
        assert response.status_code == 200
        created_account = response.json()
        account_id = created_account["id"]
        
        # Retrieve account via API
        response = client.get(f"{settings.API_V1_STR}/accounts/{account_id}")
        assert response.status_code == 200
        retrieved_account = response.json()
        
        # Verify all required fields are present and correct
        assert retrieved_account["name"] == account_data["name"]
        assert retrieved_account["type"] == account_data["type"]
        assert retrieved_account["institution"] == account_data["institution"]
        assert retrieved_account["description"] == account_data["description"]
        assert "id" in retrieved_account
        assert "created_at" in retrieved_account
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/accounts/{account_id}")

    @given(account_data=account_data())
    def test_account_deletion_protection(self, client: TestClient, db: Session, account_data: dict):
        """
        Property 16: Account Deletion Protection
        For any account that has associated transactions, deletion attempts 
        should be prevented while maintaining referential integrity.
        
        Feature: personal-finance-tracker, Property 16: Account deletion protection
        **Validates: Requirements 3.4**
        """
        # Create account via API
        response = client.post(
            f"{settings.API_V1_STR}/accounts/",
            json=account_data,
        )
        assert response.status_code == 200
        created_account = response.json()
        account_id = created_account["id"]
        
        # Create a transaction for this account directly in database
        transaction = Transaction(
            date_transaction="2024-01-01",
            description="Test transaction",
            amount_cents=1000,
            type=TransactionType.EXPENSE,
            account_id=uuid.UUID(account_id),
            status="manual"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Attempt to delete account should fail
        response = client.delete(f"{settings.API_V1_STR}/accounts/{account_id}")
        assert response.status_code == 400
        assert "Cannot delete account with existing transactions" in response.json()["detail"]
        
        # Verify account still exists
        response = client.get(f"{settings.API_V1_STR}/accounts/{account_id}")
        assert response.status_code == 200
        
        # Cleanup - delete transaction first, then account
        db.delete(transaction)
        db.commit()
        client.delete(f"{settings.API_V1_STR}/accounts/{account_id}")

    @given(account_data=account_data(), update_data=account_update_data())
    def test_account_update_preservation(self, client: TestClient, db: Session, account_data: dict, update_data: dict):
        """
        Property 17: Account Update Preservation
        For any account with associated transactions, updating account details 
        should preserve all transaction relationships.
        
        Feature: personal-finance-tracker, Property 17: Account update preservation
        **Validates: Requirements 3.5**
        """
        # Create account via API
        response = client.post(
            f"{settings.API_V1_STR}/accounts/",
            json=account_data,
        )
        assert response.status_code == 200
        created_account = response.json()
        account_id = created_account["id"]
        
        # Create a transaction for this account directly in database
        transaction = Transaction(
            date_transaction="2024-01-01",
            description="Test transaction",
            amount_cents=1000,
            type=TransactionType.EXPENSE,
            account_id=uuid.UUID(account_id),
            status="manual"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Update account via API
        # Filter out None values from update_data
        filtered_update_data = {k: v for k, v in update_data.items() if v is not None}
        if filtered_update_data:  # Only update if there's something to update
            response = client.put(
                f"{settings.API_V1_STR}/accounts/{account_id}",
                json=filtered_update_data,
            )
            assert response.status_code == 200
        
        # Verify transaction relationship is preserved
        db.refresh(transaction)
        assert transaction.account_id == uuid.UUID(account_id)
        
        # Verify account still exists and is accessible
        response = client.get(f"{settings.API_V1_STR}/accounts/{account_id}")
        assert response.status_code == 200
        
        # Cleanup
        db.delete(transaction)
        db.commit()
        client.delete(f"{settings.API_V1_STR}/accounts/{account_id}")


def test_account_deletion_without_transactions(client: TestClient):
    """Test that accounts without transactions can be deleted successfully."""
    # Create account
    account_data = {
        "name": "Test Account",
        "type": "chequing",
        "institution": "Test Bank"
    }
    response = client.post(
        f"{settings.API_V1_STR}/accounts/",
        json=account_data,
    )
    assert response.status_code == 200
    account_id = response.json()["id"]
    
    # Delete account should succeed
    response = client.delete(f"{settings.API_V1_STR}/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"
    
    # Verify account is deleted
    response = client.get(f"{settings.API_V1_STR}/accounts/{account_id}")
    assert response.status_code == 404


def test_account_not_found(client: TestClient):
    """Test that accessing non-existent account returns 404."""
    response = client.get(f"{settings.API_V1_STR}/accounts/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


def test_delete_account_not_found(client: TestClient):
    """Test that deleting non-existent account returns 404."""
    response = client.delete(f"{settings.API_V1_STR}/accounts/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


def test_update_account_not_found(client: TestClient):
    """Test that updating non-existent account returns 404."""
    update_data = {"name": "Updated Name"}
    response = client.put(
        f"{settings.API_V1_STR}/accounts/{uuid.uuid4()}",
        json=update_data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"