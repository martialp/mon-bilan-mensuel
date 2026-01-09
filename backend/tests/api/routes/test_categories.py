"""
Property-based tests for category API endpoints.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st
from sqlmodel import Session

from app.core.config import settings
from app.models import Category, Transaction, TransactionCreate, TransactionType


# Hypothesis strategies for generating test data
@st.composite
def category_data(draw):
    """Generate valid category data."""
    return {
        "name": draw(st.text(min_size=1, max_size=255, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
    }


class TestCategoryEndpointProperties:
    """Property-based tests for Category API endpoints."""

    @given(category_data=category_data())
    def test_category_creation_and_uniqueness_via_api(self, client: TestClient, category_data: dict):
        """
        Property 9: Category Creation and Uniqueness (API Level)
        For any new category name, the system should create the category successfully via API, 
        but attempting to create a category with an existing name should be rejected with proper error.
        
        Feature: personal-finance-tracker, Property 9: Category creation and uniqueness
        **Validates: Requirements 2.3, 5.4**
        """
        # Create first category via API
        response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json=category_data,
        )
        assert response.status_code == 200
        created_category = response.json()
        category_id = created_category["id"]
        
        # Verify category was created successfully
        assert created_category["name"] == category_data["name"]
        assert "id" in created_category
        assert "created_at" in created_category
        
        # Attempt to create duplicate category should fail
        response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json=category_data,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
        assert category_data["name"] in response.json()["detail"]
        
        # Verify original category still exists and is accessible
        response = client.get(f"{settings.API_V1_STR}/categories/{category_id}")
        assert response.status_code == 200
        retrieved_category = response.json()
        assert retrieved_category["name"] == category_data["name"]
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/categories/{category_id}")


def test_category_deletion_without_transactions(client: TestClient):
    """Test that categories without transactions can be deleted successfully."""
    # Create category
    category_data = {"name": "Test Category"}
    response = client.post(
        f"{settings.API_V1_STR}/categories/",
        json=category_data,
    )
    assert response.status_code == 200
    category_id = response.json()["id"]
    
    # Delete category should succeed
    response = client.delete(f"{settings.API_V1_STR}/categories/{category_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Category deleted successfully"
    
    # Verify category is deleted
    response = client.get(f"{settings.API_V1_STR}/categories/{category_id}")
    assert response.status_code == 404


def test_category_deletion_protection(client: TestClient, db: Session):
    """Test that categories with transactions cannot be deleted."""
    # Create category
    category_data = {"name": "Test Category"}
    response = client.post(
        f"{settings.API_V1_STR}/categories/",
        json=category_data,
    )
    assert response.status_code == 200
    category_id = response.json()["id"]
    
    # Create account for transaction
    account_data = {"name": "Test Account", "type": "chequing"}
    response = client.post(
        f"{settings.API_V1_STR}/accounts/",
        json=account_data,
    )
    assert response.status_code == 200
    account_id = response.json()["id"]
    
    # Create a transaction for this category directly in database
    transaction = Transaction(
        date_transaction="2024-01-01",
        description="Test transaction",
        amount_cents=1000,
        type=TransactionType.EXPENSE,
        account_id=uuid.UUID(account_id),
        category_id=uuid.UUID(category_id),
        status="manual"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Attempt to delete category should fail
    response = client.delete(f"{settings.API_V1_STR}/categories/{category_id}")
    assert response.status_code == 400
    assert "Cannot delete category with existing transactions" in response.json()["detail"]
    
    # Verify category still exists
    response = client.get(f"{settings.API_V1_STR}/categories/{category_id}")
    assert response.status_code == 200
    
    # Cleanup - delete transaction first, then category and account
    db.delete(transaction)
    db.commit()
    client.delete(f"{settings.API_V1_STR}/categories/{category_id}")
    client.delete(f"{settings.API_V1_STR}/accounts/{account_id}")


def test_category_not_found(client: TestClient):
    """Test that accessing non-existent category returns 404."""
    response = client.get(f"{settings.API_V1_STR}/categories/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_delete_category_not_found(client: TestClient):
    """Test that deleting non-existent category returns 404."""
    response = client.delete(f"{settings.API_V1_STR}/categories/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_category_not_found(client: TestClient):
    """Test that updating non-existent category returns 404."""
    update_data = {"name": "Updated Name"}
    response = client.put(
        f"{settings.API_V1_STR}/categories/{uuid.uuid4()}",
        json=update_data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_category_uniqueness_validation(client: TestClient):
    """Test that updating category to existing name fails."""
    # Create first category
    category1_data = {"name": "Category 1"}
    response = client.post(
        f"{settings.API_V1_STR}/categories/",
        json=category1_data,
    )
    assert response.status_code == 200
    category1_id = response.json()["id"]
    
    # Create second category
    category2_data = {"name": "Category 2"}
    response = client.post(
        f"{settings.API_V1_STR}/categories/",
        json=category2_data,
    )
    assert response.status_code == 200
    category2_id = response.json()["id"]
    
    # Attempt to update second category to have same name as first
    response = client.put(
        f"{settings.API_V1_STR}/categories/{category2_id}",
        json={"name": "Category 1"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
    
    # Cleanup
    client.delete(f"{settings.API_V1_STR}/categories/{category1_id}")
    client.delete(f"{settings.API_V1_STR}/categories/{category2_id}")


def test_list_categories(client: TestClient):
    """Test that listing categories works correctly."""
    # Create a few categories
    categories = []
    for i in range(3):
        category_data = {"name": f"Test Category {i}"}
        response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json=category_data,
        )
        assert response.status_code == 200
        categories.append(response.json())
    
    # List categories
    response = client.get(f"{settings.API_V1_STR}/categories/")
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert "count" in result
    assert result["count"] >= 3  # At least our 3 categories
    
    # Verify our categories are in the list
    category_names = [cat["name"] for cat in result["data"]]
    for category in categories:
        assert category["name"] in category_names
    
    # Cleanup
    for category in categories:
        client.delete(f"{settings.API_V1_STR}/categories/{category['id']}")