"""
Property-based tests for integration and data integrity.

These tests validate complete user workflows and data consistency across operations
using Hypothesis for property-based testing.

Property 24: Cross-Account Data Integrity
Property 25: Data Retrieval Consistency

**Validates: Requirements 5.3, 5.5**
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


# Hypothesis strategies for generating test data
@st.composite
def account_data(draw):
    """Generate valid account data."""
    return {
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        "type": draw(st.sampled_from([t.value for t in AccountType])),
        "institution": draw(st.one_of(st.none(), st.text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "description": draw(st.one_of(st.none(), st.text(max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
    }


@st.composite
def category_data(draw):
    """Generate valid category data."""
    return {
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
    }


@st.composite
def transaction_data(draw, account_id=None, category_id=None):
    """Generate valid transaction data."""
    return {
        "date_transaction": draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))).isoformat(),
        "description": draw(st.text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        "amount_cents": draw(st.integers(min_value=1, max_value=999999999)),
        "type": draw(st.sampled_from([t.value for t in TransactionType])),
        "note": draw(st.one_of(st.none(), st.text(max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        "account_id": str(account_id) if account_id else str(uuid.uuid4()),
        "category_id": str(category_id) if category_id else None,
    }


def create_test_account(db: Session, name: str = "Test Account") -> Account:
    """Helper to create a test account."""
    account = Account(
        name=name,
        type=AccountType.CHEQUING,
        institution="Test Bank"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_test_category(db: Session, name: str) -> Category:
    """Helper to create a test category."""
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def cleanup_test_data(db: Session, transactions: list, categories: list, accounts: list):
    """Helper to cleanup test data."""
    for t in transactions:
        db.delete(t)
    db.commit()
    for c in categories:
        db.delete(c)
    db.commit()
    for a in accounts:
        db.delete(a)
    db.commit()


class TestCrossAccountDataIntegrity:
    """
    Property 24: Cross-Account Data Integrity
    For any operations involving multiple accounts, all referential relationships 
    should remain valid and consistent.
    
    Feature: personal-finance-tracker, Property 24: Cross-account data integrity
    **Validates: Requirements 5.3**
    """

    @given(
        account1_data=account_data(),
        account2_data=account_data(),
        transaction1_data=transaction_data(),
        transaction2_data=transaction_data()
    )
    @hypothesis_settings(max_examples=100)
    def test_cross_account_referential_integrity(
        self, 
        client: TestClient, 
        db: Session,
        account1_data: dict,
        account2_data: dict,
        transaction1_data: dict,
        transaction2_data: dict
    ):
        """
        Test that transactions maintain valid references to their accounts
        across multiple account operations.
        """
        # Create two accounts via API
        response1 = client.post(f"{settings.API_V1_STR}/accounts/", json=account1_data)
        assert response1.status_code == 200
        account1 = response1.json()
        
        response2 = client.post(f"{settings.API_V1_STR}/accounts/", json=account2_data)
        assert response2.status_code == 200
        account2 = response2.json()
        
        # Create category for transactions
        category_name = f"Test Category {uuid.uuid4().hex[:8]}"
        category_response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json={"name": category_name}
        )
        assert category_response.status_code == 200
        category = category_response.json()
        
        # Create transactions for each account
        transaction1_data["account_id"] = account1["id"]
        transaction1_data["category_id"] = category["id"]
        
        transaction2_data["account_id"] = account2["id"]
        transaction2_data["category_id"] = category["id"]
        
        t1_response = client.post(f"{settings.API_V1_STR}/transactions/", json=transaction1_data)
        assert t1_response.status_code == 200
        t1 = t1_response.json()
        
        t2_response = client.post(f"{settings.API_V1_STR}/transactions/", json=transaction2_data)
        assert t2_response.status_code == 200
        t2 = t2_response.json()
        
        # Verify referential integrity - each transaction points to correct account
        assert t1["account_id"] == account1["id"]
        assert t2["account_id"] == account2["id"]
        
        # Verify both transactions reference the same category
        assert t1["category_id"] == category["id"]
        assert t2["category_id"] == category["id"]
        
        # Update account1 and verify transaction relationship is preserved
        update_response = client.put(
            f"{settings.API_V1_STR}/accounts/{account1['id']}",
            json={"name": f"Updated {account1_data['name']}"}
        )
        assert update_response.status_code == 200
        
        # Retrieve transaction1 and verify account relationship is intact
        t1_retrieved = client.get(f"{settings.API_V1_STR}/transactions/{t1['id']}")
        assert t1_retrieved.status_code == 200
        assert t1_retrieved.json()["account_id"] == account1["id"]
        
        # Verify account deletion is blocked when transactions exist
        delete_response = client.delete(f"{settings.API_V1_STR}/accounts/{account1['id']}")
        assert delete_response.status_code == 400
        assert "Cannot delete account with existing transactions" in delete_response.json()["detail"]
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{t1['id']}")
        client.delete(f"{settings.API_V1_STR}/transactions/{t2['id']}")
        client.delete(f"{settings.API_V1_STR}/categories/{category['id']}")
        client.delete(f"{settings.API_V1_STR}/accounts/{account1['id']}")
        client.delete(f"{settings.API_V1_STR}/accounts/{account2['id']}")


    @given(
        num_accounts=st.integers(min_value=2, max_value=4),
        num_transactions_per_account=st.integers(min_value=1, max_value=3)
    )
    @hypothesis_settings(max_examples=100)
    def test_multi_account_transaction_isolation(
        self,
        client: TestClient,
        db: Session,
        num_accounts: int,
        num_transactions_per_account: int
    ):
        """
        Test that transactions are properly isolated to their respective accounts
        and filtering by account returns only that account's transactions.
        """
        accounts = []
        transactions = []
        
        # Create multiple accounts
        for i in range(num_accounts):
            account_data = {
                "name": f"Account {i} {uuid.uuid4().hex[:8]}",
                "type": "chequing",
                "institution": f"Bank {i}"
            }
            response = client.post(f"{settings.API_V1_STR}/accounts/", json=account_data)
            assert response.status_code == 200
            accounts.append(response.json())
        
        # Create transactions for each account
        for account in accounts:
            for j in range(num_transactions_per_account):
                tx_data = {
                    "date_transaction": "2024-06-15",
                    "description": f"Transaction {j} for {account['name']} {uuid.uuid4().hex[:8]}",
                    "amount_cents": 1000 * (j + 1),
                    "type": "expense",
                    "account_id": account["id"]
                }
                response = client.post(f"{settings.API_V1_STR}/transactions/", json=tx_data)
                assert response.status_code == 200
                transactions.append(response.json())
        
        # Verify filtering by account returns only that account's transactions
        for account in accounts:
            response = client.get(
                f"{settings.API_V1_STR}/transactions/",
                params={"account_id": account["id"]}
            )
            assert response.status_code == 200
            data = response.json()
            
            # All returned transactions should belong to this account
            for tx in data["data"]:
                assert tx["account_id"] == account["id"]
            
            # Count should match expected
            assert data["count"] == num_transactions_per_account
        
        # Cleanup
        for tx in transactions:
            client.delete(f"{settings.API_V1_STR}/transactions/{tx['id']}")
        for account in accounts:
            client.delete(f"{settings.API_V1_STR}/accounts/{account['id']}")


class TestDataRetrievalConsistency:
    """
    Property 25: Data Retrieval Consistency
    For any stored financial data, retrieving it should return exactly the same 
    values that were originally stored without corruption or loss.
    
    Feature: personal-finance-tracker, Property 25: Data retrieval consistency
    **Validates: Requirements 5.5**
    """

    @given(
        account_data=account_data(),
        category_name=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        transaction_data=transaction_data()
    )
    @hypothesis_settings(max_examples=100)
    def test_complete_workflow_data_consistency(
        self,
        client: TestClient,
        db: Session,
        account_data: dict,
        category_name: str,
        transaction_data: dict
    ):
        """
        Test complete user workflow: create account → add transactions → categorize → analyze
        Verify data consistency at each step.
        """
        # Step 1: Create account
        account_response = client.post(f"{settings.API_V1_STR}/accounts/", json=account_data)
        assert account_response.status_code == 200
        created_account = account_response.json()
        
        # Verify account data consistency
        retrieved_account = client.get(f"{settings.API_V1_STR}/accounts/{created_account['id']}")
        assert retrieved_account.status_code == 200
        assert retrieved_account.json()["name"] == account_data["name"]
        assert retrieved_account.json()["type"] == account_data["type"]
        assert retrieved_account.json()["institution"] == account_data["institution"]
        assert retrieved_account.json()["description"] == account_data["description"]
        
        # Step 2: Create category
        unique_category_name = f"{category_name} {uuid.uuid4().hex[:8]}"
        category_response = client.post(
            f"{settings.API_V1_STR}/categories/",
            json={"name": unique_category_name}
        )
        assert category_response.status_code == 200
        created_category = category_response.json()
        
        # Verify category data consistency
        retrieved_category = client.get(f"{settings.API_V1_STR}/categories/{created_category['id']}")
        assert retrieved_category.status_code == 200
        assert retrieved_category.json()["name"] == unique_category_name
        
        # Step 3: Create transaction
        transaction_data["account_id"] = created_account["id"]
        transaction_data["category_id"] = None  # Start uncategorized
        
        tx_response = client.post(f"{settings.API_V1_STR}/transactions/", json=transaction_data)
        assert tx_response.status_code == 200
        created_tx = tx_response.json()
        
        # Verify transaction data consistency
        retrieved_tx = client.get(f"{settings.API_V1_STR}/transactions/{created_tx['id']}")
        assert retrieved_tx.status_code == 200
        tx_data = retrieved_tx.json()
        assert tx_data["date_transaction"] == transaction_data["date_transaction"]
        assert tx_data["description"] == transaction_data["description"]
        assert tx_data["amount_cents"] == transaction_data["amount_cents"]
        assert tx_data["type"] == transaction_data["type"]
        assert tx_data["account_id"] == created_account["id"]
        
        # Step 4: Categorize transaction
        categorize_response = client.put(
            f"{settings.API_V1_STR}/transactions/{created_tx['id']}/categorize",
            params={"category_id": created_category["id"]}
        )
        assert categorize_response.status_code == 200
        
        # Verify categorization data consistency
        categorized_tx = client.get(f"{settings.API_V1_STR}/transactions/{created_tx['id']}")
        assert categorized_tx.status_code == 200
        assert categorized_tx.json()["category_id"] == created_category["id"]
        assert categorized_tx.json()["status"] == "manual"
        
        # Original data should be preserved
        assert categorized_tx.json()["date_transaction"] == transaction_data["date_transaction"]
        assert categorized_tx.json()["description"] == transaction_data["description"]
        assert categorized_tx.json()["amount_cents"] == transaction_data["amount_cents"]
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{created_tx['id']}")
        client.delete(f"{settings.API_V1_STR}/categories/{created_category['id']}")
        client.delete(f"{settings.API_V1_STR}/accounts/{created_account['id']}")


    @given(
        amounts=st.lists(st.integers(min_value=1, max_value=100000), min_size=1, max_size=5)
    )
    @hypothesis_settings(max_examples=100)
    def test_analysis_data_consistency(
        self,
        client: TestClient,
        db: Session,
        amounts: list[int]
    ):
        """
        Test that analysis endpoints return data consistent with stored transactions.
        """
        # Setup
        account = create_test_account(db, f"Analysis Test {uuid.uuid4().hex[:8]}")
        category = create_test_category(db, f"Analysis Category {uuid.uuid4().hex[:8]}")
        transactions = []
        
        expected_total = 0
        for i, amount in enumerate(amounts):
            tx_data = {
                "date_transaction": "2024-06-15",
                "description": f"Analysis tx {i} {uuid.uuid4().hex[:8]}",
                "amount_cents": amount,
                "type": "expense",
                "account_id": str(account.id),
                "category_id": str(category.id)
            }
            response = client.post(f"{settings.API_V1_STR}/transactions/", json=tx_data)
            assert response.status_code == 200
            transactions.append(response.json())
            expected_total += amount
        
        # Verify spending by category analysis
        analysis_response = client.get(
            f"{settings.API_V1_STR}/analysis/spending-by-category",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        # Find our category in results
        category_result = next(
            (c for c in analysis_data["data"] if c["category_id"] == str(category.id)),
            None
        )
        assert category_result is not None
        assert category_result["total_cents"] == expected_total
        assert category_result["transaction_count"] == len(amounts)
        
        # Verify account summary analysis
        summary_response = client.get(
            f"{settings.API_V1_STR}/analysis/account-summary",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        # Find our account in results
        account_result = next(
            (a for a in summary_data["accounts"] if a["account_id"] == str(account.id)),
            None
        )
        assert account_result is not None
        assert account_result["total_expense_cents"] == expected_total
        
        # Cleanup
        for tx in transactions:
            client.delete(f"{settings.API_V1_STR}/transactions/{tx['id']}")
        cleanup_test_data(db, [], [category], [account])


    @given(
        original_amount=st.integers(min_value=1, max_value=100000),
        updated_amount=st.integers(min_value=1, max_value=100000)
    )
    @hypothesis_settings(max_examples=100)
    def test_update_data_consistency(
        self,
        client: TestClient,
        db: Session,
        original_amount: int,
        updated_amount: int
    ):
        """
        Test that updates are persisted correctly and retrievable.
        """
        # Create account and transaction
        account = create_test_account(db, f"Update Test {uuid.uuid4().hex[:8]}")
        
        tx_data = {
            "date_transaction": "2024-06-15",
            "description": f"Original description {uuid.uuid4().hex[:8]}",
            "amount_cents": original_amount,
            "type": "expense",
            "account_id": str(account.id)
        }
        
        create_response = client.post(f"{settings.API_V1_STR}/transactions/", json=tx_data)
        assert create_response.status_code == 200
        created_tx = create_response.json()
        
        # Update transaction
        update_data = {
            "amount_cents": updated_amount,
            "description": f"Updated description {uuid.uuid4().hex[:8]}"
        }
        
        update_response = client.put(
            f"{settings.API_V1_STR}/transactions/{created_tx['id']}",
            json=update_data
        )
        assert update_response.status_code == 200
        
        # Retrieve and verify update was persisted
        retrieved_tx = client.get(f"{settings.API_V1_STR}/transactions/{created_tx['id']}")
        assert retrieved_tx.status_code == 200
        tx_data = retrieved_tx.json()
        
        assert tx_data["amount_cents"] == updated_amount
        assert tx_data["description"] == update_data["description"]
        
        # Original unchanged fields should be preserved
        assert tx_data["date_transaction"] == "2024-06-15"
        assert tx_data["type"] == "expense"
        assert tx_data["account_id"] == str(account.id)
        
        # Cleanup
        client.delete(f"{settings.API_V1_STR}/transactions/{created_tx['id']}")
        cleanup_test_data(db, [], [], [account])


# Unit tests for complete workflow scenarios
def test_complete_user_workflow(client: TestClient, db: Session):
    """
    Test complete user workflow: create account → add transactions → categorize → analyze
    This is a comprehensive integration test covering the full user journey.
    """
    # Step 1: Create account
    account_data = {
        "name": f"My Checking Account {uuid.uuid4().hex[:8]}",
        "type": "chequing",
        "institution": "My Bank",
        "description": "Primary checking account"
    }
    account_response = client.post(f"{settings.API_V1_STR}/accounts/", json=account_data)
    assert account_response.status_code == 200
    account = account_response.json()
    
    # Step 2: Create categories
    categories = []
    for cat_name in ["Groceries", "Entertainment", "Utilities"]:
        unique_name = f"{cat_name} {uuid.uuid4().hex[:8]}"
        cat_response = client.post(f"{settings.API_V1_STR}/categories/", json={"name": unique_name})
        assert cat_response.status_code == 200
        categories.append(cat_response.json())
    
    # Step 3: Add transactions
    transactions = []
    tx_data_list = [
        {"description": f"Grocery Store {uuid.uuid4().hex[:8]}", "amount_cents": 5000, "type": "expense", "date": "2024-06-01"},
        {"description": f"Movie Theater {uuid.uuid4().hex[:8]}", "amount_cents": 2500, "type": "expense", "date": "2024-06-05"},
        {"description": f"Electric Bill {uuid.uuid4().hex[:8]}", "amount_cents": 15000, "type": "expense", "date": "2024-06-10"},
        {"description": f"Salary {uuid.uuid4().hex[:8]}", "amount_cents": 300000, "type": "income", "date": "2024-06-15"},
    ]
    
    for tx_info in tx_data_list:
        tx_data = {
            "date_transaction": tx_info["date"],
            "description": tx_info["description"],
            "amount_cents": tx_info["amount_cents"],
            "type": tx_info["type"],
            "account_id": account["id"]
        }
        tx_response = client.post(f"{settings.API_V1_STR}/transactions/", json=tx_data)
        assert tx_response.status_code == 200
        transactions.append(tx_response.json())
    
    # Step 4: Categorize transactions
    # Groceries
    cat_response = client.put(
        f"{settings.API_V1_STR}/transactions/{transactions[0]['id']}/categorize",
        params={"category_id": categories[0]["id"]}
    )
    assert cat_response.status_code == 200
    
    # Entertainment
    cat_response = client.put(
        f"{settings.API_V1_STR}/transactions/{transactions[1]['id']}/categorize",
        params={"category_id": categories[1]["id"]}
    )
    assert cat_response.status_code == 200
    
    # Utilities
    cat_response = client.put(
        f"{settings.API_V1_STR}/transactions/{transactions[2]['id']}/categorize",
        params={"category_id": categories[2]["id"]}
    )
    assert cat_response.status_code == 200
    
    # Step 5: Verify analysis
    # Spending by category
    analysis_response = client.get(
        f"{settings.API_V1_STR}/analysis/spending-by-category",
        params={"date_from": "2024-06-01", "date_to": "2024-06-30"}
    )
    assert analysis_response.status_code == 200
    analysis_data = analysis_response.json()
    
    # Verify total spending (expenses only)
    expected_expense_total = 5000 + 2500 + 15000
    assert analysis_data["total_spending_cents"] >= expected_expense_total
    
    # Account summary
    summary_response = client.get(
        f"{settings.API_V1_STR}/analysis/account-summary",
        params={"date_from": "2024-06-01", "date_to": "2024-06-30"}
    )
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    
    # Find our account
    account_summary = next(
        (a for a in summary_data["accounts"] if a["account_id"] == account["id"]),
        None
    )
    assert account_summary is not None
    assert account_summary["total_expense_cents"] == expected_expense_total
    assert account_summary["total_income_cents"] == 300000
    
    # Cleanup
    for tx in transactions:
        client.delete(f"{settings.API_V1_STR}/transactions/{tx['id']}")
    for cat in categories:
        client.delete(f"{settings.API_V1_STR}/categories/{cat['id']}")
    client.delete(f"{settings.API_V1_STR}/accounts/{account['id']}")
