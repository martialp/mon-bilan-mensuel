"""
Property-based tests for analysis API endpoints.

These tests validate universal properties that should hold for all valid inputs
using Hypothesis for property-based testing.
"""

import uuid
from datetime import date, timedelta
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
def transaction_list_data(draw, min_transactions=1, max_transactions=10):
    """Generate a list of valid transaction data for testing."""
    num_transactions = draw(st.integers(min_value=min_transactions, max_value=max_transactions))
    transactions = []
    
    for i in range(num_transactions):
        transactions.append({
            "date_transaction": draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))),
            "description": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
            "amount_cents": draw(st.integers(min_value=1, max_value=1000000)),
            "type": draw(st.sampled_from([t.value for t in TransactionType])),
        })
    
    return transactions


@st.composite
def date_range_data(draw):
    """Generate valid date range data."""
    start_date = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)))
    # End date is at least the same as start date
    end_date = draw(st.dates(min_value=start_date, max_value=date(2025, 12, 31)))
    return {"date_from": start_date, "date_to": end_date}


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


def create_test_transaction(
    db: Session,
    account_id: uuid.UUID,
    amount_cents: int,
    transaction_type: TransactionType,
    transaction_date: date,
    category_id: uuid.UUID | None = None,
    description: str = "Test transaction"
) -> Transaction:
    """Helper to create a test transaction."""
    transaction = Transaction(
        date_transaction=transaction_date,
        description=description,
        amount_cents=amount_cents,
        type=transaction_type,
        account_id=account_id,
        category_id=category_id,
        status=TransactionStatus.MANUAL,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


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


class TestCategorySpendingProperties:
    """Property-based tests for category spending analysis."""

    @given(amounts=st.lists(st.integers(min_value=1, max_value=100000), min_size=1, max_size=10))
    @hypothesis_settings(max_examples=100)
    def test_category_spending_calculation(self, client: TestClient, db: Session, amounts: list[int]):
        """
        Property 18: Category Spending Calculation
        For any set of categorized transactions within a time period, the total spending 
        per category should equal the sum of all transaction amounts in that category and period.
        
        Feature: personal-finance-tracker, Property 18: Category spending calculation
        **Validates: Requirements 4.1**
        """
        # Setup test data
        account = create_test_account(db, f"Test Account {uuid.uuid4().hex[:8]}")
        category = create_test_category(db, f"Test Category {uuid.uuid4().hex[:8]}")
        
        transactions = []
        expected_total = 0
        
        for i, amount in enumerate(amounts):
            t = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=amount,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=date(2024, 1, 15),
                category_id=category.id,
                description=f"Test transaction {i} {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t)
            expected_total += amount
        
        # Call the API
        response = client.get(
            f"{settings.API_V1_STR}/analysis/spending-by-category",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find our category in the results
        category_result = next(
            (c for c in data["data"] if c["category_id"] == str(category.id)),
            None
        )
        
        # Verify the total matches
        assert category_result is not None
        assert category_result["total_cents"] == expected_total
        assert category_result["transaction_count"] == len(amounts)
        
        # Cleanup
        cleanup_test_data(db, transactions, [category], [account])

    @given(amounts=st.lists(st.integers(min_value=1, max_value=100000), min_size=2, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_percentage_calculation_accuracy(self, client: TestClient, db: Session, amounts: list[int]):
        """
        Property 20: Percentage Calculation Accuracy
        For any category spending summary, the percentage values should be mathematically 
        correct relative to the total spending amount.
        
        Feature: personal-finance-tracker, Property 20: Percentage calculation accuracy
        **Validates: Requirements 4.3**
        """
        # Setup test data with multiple categories
        account = create_test_account(db, f"Test Account {uuid.uuid4().hex[:8]}")
        categories = []
        transactions = []
        
        for i, amount in enumerate(amounts):
            category = create_test_category(db, f"Category {i} {uuid.uuid4().hex[:8]}")
            categories.append(category)
            
            t = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=amount,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=date(2024, 1, 15),
                category_id=category.id,
                description=f"Test transaction {i} {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t)
        
        # Call the API
        response = client.get(
            f"{settings.API_V1_STR}/analysis/spending-by-category",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        
        total_spending = data["total_spending_cents"]
        
        # Verify percentages sum to approximately 100% for our test categories
        our_category_ids = {str(c.id) for c in categories}
        our_results = [c for c in data["data"] if c["category_id"] in our_category_ids]
        
        # Verify each percentage is mathematically correct
        for result in our_results:
            expected_percentage = (result["total_cents"] / total_spending * 100) if total_spending > 0 else 0
            assert abs(result["percentage"] - round(expected_percentage, 2)) < 0.01
        
        # Cleanup
        cleanup_test_data(db, transactions, categories, [account])

    @given(amounts=st.lists(st.integers(min_value=1, max_value=100000), min_size=2, max_size=5))
    @hypothesis_settings(max_examples=100)
    def test_category_ranking_accuracy(self, client: TestClient, db: Session, amounts: list[int]):
        """
        Property 22: Category Ranking Accuracy
        For any spending analysis period, the top spending categories should be correctly 
        ranked by total amount in descending order.
        
        Feature: personal-finance-tracker, Property 22: Category ranking accuracy
        **Validates: Requirements 4.5**
        """
        # Setup test data with multiple categories
        account = create_test_account(db, f"Test Account {uuid.uuid4().hex[:8]}")
        categories = []
        transactions = []
        
        for i, amount in enumerate(amounts):
            category = create_test_category(db, f"Category {i} {uuid.uuid4().hex[:8]}")
            categories.append(category)
            
            t = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=amount,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=date(2024, 1, 15),
                category_id=category.id,
                description=f"Test transaction {i} {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t)
        
        # Call the API
        response = client.get(
            f"{settings.API_V1_STR}/analysis/spending-by-category",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify results are sorted by total_cents in descending order
        results = data["data"]
        for i in range(len(results) - 1):
            assert results[i]["total_cents"] >= results[i + 1]["total_cents"]
        
        # Cleanup
        cleanup_test_data(db, transactions, categories, [account])


class TestMonthlyTrendProperties:
    """Property-based tests for monthly spending trends."""

    @given(
        months_data=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=12),
                st.integers(min_value=1, max_value=100000)
            ),
            min_size=1,
            max_size=6
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_monthly_trend_accuracy(self, client: TestClient, db: Session, months_data: list[tuple[int, int]]):
        """
        Property 19: Monthly Trend Accuracy
        For any set of transactions across multiple months, the monthly breakdown should 
        accurately group transactions by month with correct totals.
        
        Feature: personal-finance-tracker, Property 19: Monthly trend accuracy
        **Validates: Requirements 4.2**
        """
        # Setup test data
        account = create_test_account(db, f"Test Account {uuid.uuid4().hex[:8]}")
        transactions = []
        expected_by_month = {}
        
        for i, (month, amount) in enumerate(months_data):
            transaction_date = date(2024, month, 15)
            t = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=amount,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=transaction_date,
                description=f"Test transaction {i} {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t)
            
            # Track expected totals by month
            key = (2024, month)
            expected_by_month[key] = expected_by_month.get(key, 0) + amount
        
        # Call the API
        response = client.get(
            f"{settings.API_V1_STR}/analysis/spending-trends",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify monthly totals match expected
        for result in data["data"]:
            key = (result["year"], result["month"])
            if key in expected_by_month:
                assert result["total_cents"] >= expected_by_month[key]
        
        # Cleanup
        cleanup_test_data(db, transactions, [], [account])


class TestDateRangeFilteringProperties:
    """Property-based tests for date range filtering."""

    @given(date_range=date_range_data())
    @hypothesis_settings(max_examples=100)
    def test_date_range_filtering(self, client: TestClient, db: Session, date_range: dict):
        """
        Property 21: Date Range Filtering
        For any date range query, the returned transactions should include only those 
        with transaction dates within the specified range (inclusive).
        
        Feature: personal-finance-tracker, Property 21: Date range filtering
        **Validates: Requirements 4.4**
        """
        # Setup test data with transactions inside and outside the date range
        account = create_test_account(db, f"Test Account {uuid.uuid4().hex[:8]}")
        category = create_test_category(db, f"Test Category {uuid.uuid4().hex[:8]}")
        transactions = []
        
        date_from = date_range["date_from"]
        date_to = date_range["date_to"]
        
        # Create transaction inside the range
        inside_date = date_from + timedelta(days=1) if date_from < date_to else date_from
        t_inside = create_test_transaction(
            db=db,
            account_id=account.id,
            amount_cents=1000,
            transaction_type=TransactionType.EXPENSE,
            transaction_date=inside_date,
            category_id=category.id,
            description=f"Inside range {uuid.uuid4().hex[:8]}"
        )
        transactions.append(t_inside)
        
        # Create transaction outside the range (before)
        if date_from > date(2020, 1, 2):
            outside_before = date_from - timedelta(days=30)
            t_before = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=2000,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=outside_before,
                category_id=category.id,
                description=f"Before range {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t_before)
        
        # Create transaction outside the range (after)
        if date_to < date(2025, 12, 30):
            outside_after = date_to + timedelta(days=30)
            t_after = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=3000,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=outside_after,
                category_id=category.id,
                description=f"After range {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t_after)
        
        # Call the API with date range
        response = client.get(
            f"{settings.API_V1_STR}/analysis/spending-by-category",
            params={
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify the period dates in response
        assert data["period_start"] == date_from.isoformat()
        assert data["period_end"] == date_to.isoformat()
        
        # Cleanup
        cleanup_test_data(db, transactions, [category], [account])


class TestMultiAccountAnalysisProperties:
    """Property-based tests for multi-account analysis."""

    @given(
        account_amounts=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=100000),  # expense
                st.integers(min_value=1, max_value=100000)   # income
            ),
            min_size=2,
            max_size=4
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_multi_account_analysis_consistency(self, client: TestClient, db: Session, account_amounts: list[tuple[int, int]]):
        """
        Property 23: Multi-Account Analysis Consistency
        For any analysis across multiple accounts, the consolidated totals should equal 
        the sum of individual account totals.
        
        Feature: personal-finance-tracker, Property 23: Multi-account analysis consistency
        **Validates: Requirements 4.6**
        """
        # Setup test data with multiple accounts
        accounts = []
        transactions = []
        expected_total_expense = 0
        expected_total_income = 0
        
        for i, (expense_amount, income_amount) in enumerate(account_amounts):
            account = create_test_account(db, f"Account {i} {uuid.uuid4().hex[:8]}")
            accounts.append(account)
            
            # Create expense transaction
            t_expense = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=expense_amount,
                transaction_type=TransactionType.EXPENSE,
                transaction_date=date(2024, 1, 15),
                description=f"Expense {i} {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t_expense)
            expected_total_expense += expense_amount
            
            # Create income transaction
            t_income = create_test_transaction(
                db=db,
                account_id=account.id,
                amount_cents=income_amount,
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2024, 1, 15),
                description=f"Income {i} {uuid.uuid4().hex[:8]}"
            )
            transactions.append(t_income)
            expected_total_income += income_amount
        
        # Call the API
        response = client.get(
            f"{settings.API_V1_STR}/analysis/account-summary",
            params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Calculate sum of individual account totals
        our_account_ids = {str(a.id) for a in accounts}
        our_accounts = [a for a in data["accounts"] if a["account_id"] in our_account_ids]
        
        sum_expense = sum(a["total_expense_cents"] for a in our_accounts)
        sum_income = sum(a["total_income_cents"] for a in our_accounts)
        
        # Verify individual account totals match expected
        assert sum_expense == expected_total_expense
        assert sum_income == expected_total_income
        
        # Verify consolidated totals include our accounts' data
        assert data["consolidated_expense_cents"] >= expected_total_expense
        assert data["consolidated_income_cents"] >= expected_total_income
        
        # Cleanup
        cleanup_test_data(db, transactions, [], accounts)


# Unit tests for edge cases and specific scenarios
def test_spending_by_category_empty(client: TestClient, db: Session):
    """Test spending by category with no transactions."""
    response = client.get(
        f"{settings.API_V1_STR}/analysis/spending-by-category",
        params={"date_from": "2099-01-01", "date_to": "2099-12-31"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total_spending_cents"] == 0


def test_spending_trends_empty(client: TestClient, db: Session):
    """Test spending trends with no transactions."""
    response = client.get(
        f"{settings.API_V1_STR}/analysis/spending-trends",
        params={"date_from": "2099-01-01", "date_to": "2099-12-31"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total_spending_cents"] == 0


def test_account_summary_empty(client: TestClient, db: Session):
    """Test account summary with no transactions."""
    response = client.get(
        f"{settings.API_V1_STR}/analysis/account-summary",
        params={"date_from": "2099-01-01", "date_to": "2099-12-31"}
    )
    assert response.status_code == 200
    data = response.json()
    # Should still return accounts but with zero totals for the date range
    assert "accounts" in data
    assert data["consolidated_expense_cents"] == 0
    assert data["consolidated_income_cents"] == 0


def test_spending_by_category_with_account_filter(client: TestClient, db: Session):
    """Test spending by category filtered by specific account."""
    # Create two accounts
    account1 = create_test_account(db, f"Account 1 {uuid.uuid4().hex[:8]}")
    account2 = create_test_account(db, f"Account 2 {uuid.uuid4().hex[:8]}")
    category = create_test_category(db, f"Test Category {uuid.uuid4().hex[:8]}")
    
    # Create transactions for each account
    t1 = create_test_transaction(
        db=db,
        account_id=account1.id,
        amount_cents=1000,
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2024, 1, 15),
        category_id=category.id,
        description=f"Account 1 transaction {uuid.uuid4().hex[:8]}"
    )
    
    t2 = create_test_transaction(
        db=db,
        account_id=account2.id,
        amount_cents=2000,
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2024, 1, 15),
        category_id=category.id,
        description=f"Account 2 transaction {uuid.uuid4().hex[:8]}"
    )
    
    # Query with account filter
    response = client.get(
        f"{settings.API_V1_STR}/analysis/spending-by-category",
        params={
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "account_id": str(account1.id)
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should only include account1's transaction
    category_result = next(
        (c for c in data["data"] if c["category_id"] == str(category.id)),
        None
    )
    assert category_result is not None
    assert category_result["total_cents"] == 1000
    
    # Cleanup
    cleanup_test_data(db, [t1, t2], [category], [account1, account2])


def test_uncategorized_transactions_in_analysis(client: TestClient, db: Session):
    """Test that uncategorized transactions appear with null category in analysis."""
    account = create_test_account(db, f"Test Account {uuid.uuid4().hex[:8]}")
    
    # Create uncategorized transaction
    t = create_test_transaction(
        db=db,
        account_id=account.id,
        amount_cents=1000,
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2024, 1, 15),
        category_id=None,
        description=f"Uncategorized {uuid.uuid4().hex[:8]}"
    )
    
    response = client.get(
        f"{settings.API_V1_STR}/analysis/spending-by-category",
        params={"date_from": "2024-01-01", "date_to": "2024-12-31"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should include uncategorized transactions
    uncategorized = next(
        (c for c in data["data"] if c["category_id"] is None),
        None
    )
    assert uncategorized is not None
    assert uncategorized["total_cents"] >= 1000
    
    # Cleanup
    cleanup_test_data(db, [t], [], [account])
