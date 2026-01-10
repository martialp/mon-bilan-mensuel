"""
Property-based tests for error handling.

These tests validate universal properties for input validation, form validation feedback,
error message specificity, and comprehensive error handling using Hypothesis.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings as hypothesis_settings
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    Account, AccountType, Category, Transaction, TransactionType, TransactionStatus
)


# Hypothesis strategies for generating invalid test data
@st.composite
def invalid_amount_cents(draw):
    """Generate invalid amount_cents values (zero, negative, or non-integer)."""
    return draw(st.one_of(
        st.integers(max_value=0),  # Zero or negative
        st.just(None),  # Missing value
    ))


@st.composite
def invalid_transaction_type(draw):
    """Generate invalid transaction type values."""
    valid_types = {"expense", "income", "transfer"}
    invalid_type = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
    # Ensure we don't accidentally generate a valid type
    if invalid_type.lower() in valid_types:
        return "invalid_type_" + invalid_type
    return invalid_type


@st.composite
def invalid_account_type(draw):
    """Generate invalid account type values."""
    valid_types = {"credit_card", "chequing", "savings", "investment", "other"}
    invalid_type = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
    # Ensure we don't accidentally generate a valid type
    if invalid_type.lower() in valid_types:
        return "invalid_type_" + invalid_type
    return invalid_type


@st.composite
def whitespace_only_string(draw):
    """Generate strings containing only whitespace characters."""
    return draw(st.text(
        min_size=1, 
        max_size=50, 
        alphabet=st.sampled_from([' ', '\t', '\n', '\r'])
    ))


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


class TestComprehensiveInputValidation:
    """
    Property 5: Comprehensive Input Validation
    For any invalid transaction data (negative amounts, missing required fields, invalid types),
    the system should validate input before database persistence and provide specific error messages.
    
    Feature: personal-finance-tracker, Property 5: Comprehensive input validation
    **Validates: Requirements 1.5, 7.1, 7.4**
    """

    @given(invalid_amount=invalid_amount_cents())
    @hypothesis_settings(max_examples=100)
    def test_invalid_amount_cents_rejected(self, client: TestClient, db: Session, invalid_amount):
        """Test that invalid amount_cents values are rejected with specific error messages."""
        account = create_test_account(db)
        
        transaction_data = {
            "date_transaction": "2024-01-01",
            "description": "Test transaction",
            "amount_cents": invalid_amount,
            "type": "expense",
            "account_id": str(account.id),
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        # Should be rejected with validation error
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        
        # Cleanup
        db.delete(account)
        db.commit()

    @given(invalid_type=invalid_transaction_type())
    @hypothesis_settings(max_examples=100)
    def test_invalid_transaction_type_rejected(self, client: TestClient, db: Session, invalid_type: str):
        """Test that invalid transaction types are rejected with specific error messages."""
        account = create_test_account(db)
        
        transaction_data = {
            "date_transaction": "2024-01-01",
            "description": "Test transaction",
            "amount_cents": 1000,
            "type": invalid_type,
            "account_id": str(account.id),
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        # Should be rejected with validation error
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        
        # Cleanup
        db.delete(account)
        db.commit()

    @given(invalid_type=invalid_account_type())
    @hypothesis_settings(max_examples=100)
    def test_invalid_account_type_rejected(self, client: TestClient, invalid_type: str):
        """Test that invalid account types are rejected with specific error messages."""
        account_data = {
            "name": "Test Account",
            "type": invalid_type,
            "institution": "Test Bank",
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/accounts/",
            json=account_data,
        )
        
        # Should be rejected with validation error
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail

    def test_missing_required_fields_rejected(self, client: TestClient, db: Session):
        """Test that missing required fields are rejected with specific error messages."""
        account = create_test_account(db)
        
        # Missing date_transaction
        transaction_data = {
            "description": "Test transaction",
            "amount_cents": 1000,
            "type": "expense",
            "account_id": str(account.id),
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        
        # Missing description
        transaction_data = {
            "date_transaction": "2024-01-01",
            "amount_cents": 1000,
            "type": "expense",
            "account_id": str(account.id),
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        assert response.status_code == 422
        
        # Missing account_id
        transaction_data = {
            "date_transaction": "2024-01-01",
            "description": "Test transaction",
            "amount_cents": 1000,
            "type": "expense",
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        assert response.status_code == 422
        
        # Cleanup
        db.delete(account)
        db.commit()


class TestFormValidationFeedback:
    """
    Property 26: Form Validation Feedback
    For any form submission with missing or invalid required fields, the system should
    return specific validation messages identifying the problematic fields.
    
    Feature: personal-finance-tracker, Property 26: Form validation feedback
    **Validates: Requirements 6.2**
    """

    def test_account_form_validation_feedback(self, client: TestClient):
        """Test that account form validation returns field-specific error messages."""
        # Missing name field
        account_data = {
            "type": "chequing",
            "institution": "Test Bank",
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/accounts/",
            json=account_data,
        )
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        # Verify the error identifies the problematic field
        error_fields = [err.get("loc", [])[-1] for err in error_detail["detail"] if "loc" in err]
        assert "name" in error_fields

    def test_transaction_form_validation_feedback(self, client: TestClient, db: Session):
        """Test that transaction form validation returns field-specific error messages."""
        account = create_test_account(db)
        
        # Invalid date format
        transaction_data = {
            "date_transaction": "invalid-date",
            "description": "Test transaction",
            "amount_cents": 1000,
            "type": "expense",
            "account_id": str(account.id),
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        # Verify the error identifies the problematic field
        error_fields = [err.get("loc", [])[-1] for err in error_detail["detail"] if "loc" in err]
        assert "date_transaction" in error_fields
        
        # Cleanup
        db.delete(account)
        db.commit()

    def test_category_form_validation_feedback(self, client: TestClient):
        """Test that category form validation returns field-specific error messages."""
        # Missing name field
        category_data = {}
        
        response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json=category_data,
        )
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        # Verify the error identifies the problematic field
        error_fields = [err.get("loc", [])[-1] for err in error_detail["detail"] if "loc" in err]
        assert "name" in error_fields


class TestErrorMessageSpecificity:
    """
    Property 28: Error Message Specificity
    For any error condition during data entry, the system should return user-friendly
    error messages with specific details about the problem.
    
    Feature: personal-finance-tracker, Property 28: Error message specificity
    **Validates: Requirements 6.5**
    """

    def test_not_found_error_specificity(self, client: TestClient):
        """Test that not found errors include specific resource information."""
        non_existent_id = str(uuid.uuid4())
        
        # Account not found
        response = client.get(f"{settings.API_V1_STR}/accounts/{non_existent_id}")
        assert response.status_code == 404
        assert "Account not found" in response.json()["detail"]
        
        # Transaction not found
        response = client.get(f"{settings.API_V1_STR}/transactions/{non_existent_id}")
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]
        
        # Category not found
        response = client.get(f"{settings.API_V1_STR}/categories/{non_existent_id}")
        assert response.status_code == 404
        assert "Category not found" in response.json()["detail"]

    def test_duplicate_error_specificity(self, client: TestClient, db: Session):
        """Test that duplicate errors include specific conflict information."""
        account = create_test_account(db)
        
        # Create first transaction with statement_date to trigger unique constraint
        transaction_data = {
            "date_transaction": "2024-01-01",
            "description": "Test transaction for duplicate",
            "amount_cents": 1000,
            "type": "expense",
            "account_id": str(account.id),
            "statement_date": "2024-01-31",  # Include statement_date for unique constraint
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        assert response.status_code == 200
        first_transaction = response.json()
        
        # Attempt duplicate with same unique constraint fields
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        
        assert response.status_code == 409
        error_detail = response.json()["detail"]
        # Error should explain the conflict
        assert "already exists" in error_detail.lower()
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{first_transaction['id']}")
        db.delete(account)
        db.commit()

    def test_referential_integrity_error_specificity(self, client: TestClient, db: Session):
        """Test that referential integrity errors include specific relationship information."""
        account = create_test_account(db)
        
        # Create a transaction for the account
        transaction = Transaction(
            date_transaction=date(2024, 1, 1),
            description="Test transaction",
            amount_cents=1000,
            type=TransactionType.EXPENSE,
            account_id=account.id,
            status=TransactionStatus.MANUAL
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Attempt to delete account with transactions
        response = client.delete(f"{settings.API_V1_STR}/accounts/{account.id}")
        
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        # Error should explain the relationship constraint
        assert "transactions" in error_detail.lower()
        
        # Cleanup
        db.delete(transaction)
        db.delete(account)
        db.commit()

    def test_invalid_reference_error_specificity(self, client: TestClient, db: Session):
        """Test that invalid reference errors include specific information."""
        account = create_test_account(db)
        
        # Create transaction with non-existent category
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
        error_detail = response.json()["detail"]
        # Error should identify the invalid reference
        assert "Category not found" in error_detail
        
        # Cleanup
        db.delete(account)
        db.commit()


class TestComprehensiveErrorHandling:
    """
    Property 29: Comprehensive Error Handling
    For any system error or database failure, the system should maintain data consistency,
    log detailed debugging information, and provide meaningful user feedback.
    
    Feature: personal-finance-tracker, Property 29: Comprehensive error handling
    **Validates: Requirements 7.2, 7.5**
    """

    def test_database_constraint_violation_handling(self, client: TestClient, db: Session):
        """Test that database constraint violations are handled gracefully."""
        # Create a category
        category_data = {"name": f"Test Category {uuid.uuid4()}"}
        response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json=category_data,
        )
        assert response.status_code == 200
        first_category = response.json()
        
        # Attempt to create duplicate category (unique constraint violation)
        response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json={"name": first_category["name"]},
        )
        
        # Should return user-friendly error, not raw database error
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "already exists" in error_detail.lower()
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/categories/{first_category['id']}")

    def test_transaction_rollback_on_error(self, client: TestClient, db: Session):
        """Test that failed operations don't leave partial data."""
        account = create_test_account(db)
        
        # Create first transaction with statement_date to trigger unique constraint
        transaction_data = {
            "date_transaction": "2024-01-01",
            "description": "Test transaction for rollback",
            "amount_cents": 1000,
            "type": "expense",
            "account_id": str(account.id),
            "statement_date": "2024-01-31",  # Include statement_date for unique constraint
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        assert response.status_code == 200
        first_transaction = response.json()
        
        # Get initial count
        response = client.get(f"{settings.API_V1_STR}/transactions/")
        initial_count = response.json()["count"]
        
        # Attempt duplicate (should fail)
        response = client.post(
            f"{settings.API_V1_STR}/transactions/",
            json=transaction_data,
        )
        assert response.status_code == 409
        
        # Verify count hasn't changed (no partial data)
        response = client.get(f"{settings.API_V1_STR}/transactions/")
        final_count = response.json()["count"]
        assert final_count == initial_count
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{first_transaction['id']}")
        db.delete(account)
        db.commit()

    def test_invalid_uuid_handling(self, client: TestClient):
        """Test that invalid UUID formats are handled gracefully."""
        invalid_uuids = ["not-a-uuid", "12345", "abc", ""]
        
        for invalid_uuid in invalid_uuids:
            if invalid_uuid:  # Skip empty string as it would be a different route
                response = client.get(f"{settings.API_V1_STR}/accounts/{invalid_uuid}")
                # Should return 422 (validation error) not 500 (server error)
                assert response.status_code == 422

    def test_categorize_with_invalid_category_handling(self, client: TestClient, db: Session):
        """Test that categorizing with invalid category is handled gracefully."""
        account = create_test_account(db)
        
        # Create transaction
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
        
        # Attempt to categorize with non-existent category
        response = client.put(
            f"{settings.API_V1_STR}/transactions/{transaction['id']}/categorize",
            params={"category_id": str(uuid.uuid4())},
        )
        
        assert response.status_code == 400
        assert "Category not found" in response.json()["detail"]
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{transaction['id']}")
        db.delete(account)
        db.commit()

    def test_confirm_non_auto_transaction_handling(self, client: TestClient, db: Session):
        """Test that confirming non-auto transaction is handled gracefully."""
        account = create_test_account(db)
        
        # Create manual transaction
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
        
        # Attempt to confirm manual transaction
        response = client.put(f"{settings.API_V1_STR}/transactions/{transaction.id}/confirm")
        
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "Only auto-categorized transactions can be confirmed" in error_detail
        
        # Cleanup
        db.delete(transaction)
        db.delete(account)
        db.commit()
