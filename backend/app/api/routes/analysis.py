"""
Analysis and reporting endpoints for financial data.

Provides spending analysis by category, monthly trends, and multi-account summaries.
"""

import uuid
from datetime import date
from typing import Any
from decimal import Decimal

from fastapi import APIRouter, Query
from sqlmodel import func, select, and_
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.models import Transaction, TransactionType, Category, Account


router = APIRouter(prefix="/analysis", tags=["analysis"])


# Response models for analysis endpoints
class CategorySpending(BaseModel):
    """Spending data for a single category."""
    category_id: uuid.UUID | None
    category_name: str | None
    total_cents: int
    percentage: float
    transaction_count: int


class SpendingByCategoryResponse(BaseModel):
    """Response for spending by category analysis."""
    data: list[CategorySpending]
    total_spending_cents: int
    period_start: date | None
    period_end: date | None


class MonthlySpending(BaseModel):
    """Spending data for a single month."""
    year: int
    month: int
    total_cents: int
    transaction_count: int


class SpendingTrendsResponse(BaseModel):
    """Response for monthly spending trends."""
    data: list[MonthlySpending]
    total_spending_cents: int
    period_start: date | None
    period_end: date | None


class AccountSpending(BaseModel):
    """Spending summary for a single account."""
    account_id: uuid.UUID
    account_name: str
    account_type: str
    total_expense_cents: int
    total_income_cents: int
    net_cents: int
    transaction_count: int


class AccountSummaryResponse(BaseModel):
    """Response for account summary analysis."""
    accounts: list[AccountSpending]
    consolidated_expense_cents: int
    consolidated_income_cents: int
    consolidated_net_cents: int
    total_transaction_count: int
    period_start: date | None
    period_end: date | None


@router.get("/spending-by-category", response_model=SpendingByCategoryResponse)
def get_spending_by_category(
    session: SessionDep,
    date_from: date | None = Query(None, description="Start date for analysis (inclusive)"),
    date_to: date | None = Query(None, description="End date for analysis (inclusive)"),
    account_id: uuid.UUID | None = Query(None, description="Filter by specific account"),
) -> Any:
    """
    Get spending analysis by category for a specified time period.
    
    Returns total spending per category with percentages and transaction counts.
    Only includes expense transactions in the analysis.
    """
    # Build base query for expense transactions
    filters = [Transaction.type == TransactionType.EXPENSE]
    
    if date_from:
        filters.append(Transaction.date_transaction >= date_from)
    if date_to:
        filters.append(Transaction.date_transaction <= date_to)
    if account_id:
        filters.append(Transaction.account_id == account_id)
    
    # Query for category spending with aggregation
    statement = (
        select(
            Transaction.category_id,
            Category.name.label("category_name"),
            func.sum(Transaction.amount_cents).label("total_cents"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(and_(*filters))
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount_cents).desc())
    )
    
    results = session.exec(statement).all()
    
    # Calculate total spending for percentage calculation
    total_spending = sum(row.total_cents for row in results) if results else 0
    
    # Build response data with percentages
    category_spending = []
    for row in results:
        percentage = (row.total_cents / total_spending * 100) if total_spending > 0 else 0.0
        category_spending.append(
            CategorySpending(
                category_id=row.category_id,
                category_name=row.category_name,
                total_cents=row.total_cents,
                percentage=round(percentage, 2),
                transaction_count=row.transaction_count,
            )
        )
    
    return SpendingByCategoryResponse(
        data=category_spending,
        total_spending_cents=total_spending,
        period_start=date_from,
        period_end=date_to,
    )


@router.get("/spending-trends", response_model=SpendingTrendsResponse)
def get_spending_trends(
    session: SessionDep,
    date_from: date | None = Query(None, description="Start date for analysis (inclusive)"),
    date_to: date | None = Query(None, description="End date for analysis (inclusive)"),
    account_id: uuid.UUID | None = Query(None, description="Filter by specific account"),
) -> Any:
    """
    Get monthly spending trends for a specified time period.
    
    Returns total spending per month with transaction counts.
    Only includes expense transactions in the analysis.
    """
    # Build base query for expense transactions
    filters = [Transaction.type == TransactionType.EXPENSE]
    
    if date_from:
        filters.append(Transaction.date_transaction >= date_from)
    if date_to:
        filters.append(Transaction.date_transaction <= date_to)
    if account_id:
        filters.append(Transaction.account_id == account_id)
    
    # Query for monthly spending with aggregation
    statement = (
        select(
            func.extract("year", Transaction.date_transaction).label("year"),
            func.extract("month", Transaction.date_transaction).label("month"),
            func.sum(Transaction.amount_cents).label("total_cents"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .where(and_(*filters))
        .group_by(
            func.extract("year", Transaction.date_transaction),
            func.extract("month", Transaction.date_transaction),
        )
        .order_by(
            func.extract("year", Transaction.date_transaction),
            func.extract("month", Transaction.date_transaction),
        )
    )
    
    results = session.exec(statement).all()
    
    # Calculate total spending
    total_spending = sum(row.total_cents for row in results) if results else 0
    
    # Build response data
    monthly_spending = [
        MonthlySpending(
            year=int(row.year),
            month=int(row.month),
            total_cents=row.total_cents,
            transaction_count=row.transaction_count,
        )
        for row in results
    ]
    
    return SpendingTrendsResponse(
        data=monthly_spending,
        total_spending_cents=total_spending,
        period_start=date_from,
        period_end=date_to,
    )


@router.get("/account-summary", response_model=AccountSummaryResponse)
def get_account_summary(
    session: SessionDep,
    date_from: date | None = Query(None, description="Start date for analysis (inclusive)"),
    date_to: date | None = Query(None, description="End date for analysis (inclusive)"),
) -> Any:
    """
    Get financial summary per account and consolidated totals.
    
    Returns expense, income, and net amounts for each account,
    plus consolidated totals across all accounts.
    """
    # Build date filters
    date_filters = []
    if date_from:
        date_filters.append(Transaction.date_transaction >= date_from)
    if date_to:
        date_filters.append(Transaction.date_transaction <= date_to)
    
    # Get all accounts
    accounts_statement = select(Account)
    accounts = session.exec(accounts_statement).all()
    
    account_summaries = []
    consolidated_expense = 0
    consolidated_income = 0
    total_transaction_count = 0
    
    for account in accounts:
        # Build filters for this account
        account_filters = [Transaction.account_id == account.id] + date_filters
        
        # Get expense total for this account
        expense_statement = (
            select(func.coalesce(func.sum(Transaction.amount_cents), 0))
            .where(and_(*account_filters, Transaction.type == TransactionType.EXPENSE))
        )
        expense_total = session.exec(expense_statement).one()
        
        # Get income total for this account
        income_statement = (
            select(func.coalesce(func.sum(Transaction.amount_cents), 0))
            .where(and_(*account_filters, Transaction.type == TransactionType.INCOME))
        )
        income_total = session.exec(income_statement).one()
        
        # Get transaction count for this account
        count_statement = (
            select(func.count(Transaction.id))
            .where(and_(*account_filters))
        )
        transaction_count = session.exec(count_statement).one()
        
        # Calculate net (income - expense)
        net = income_total - expense_total
        
        account_summaries.append(
            AccountSpending(
                account_id=account.id,
                account_name=account.name,
                account_type=account.type.value,
                total_expense_cents=expense_total,
                total_income_cents=income_total,
                net_cents=net,
                transaction_count=transaction_count,
            )
        )
        
        # Accumulate consolidated totals
        consolidated_expense += expense_total
        consolidated_income += income_total
        total_transaction_count += transaction_count
    
    return AccountSummaryResponse(
        accounts=account_summaries,
        consolidated_expense_cents=consolidated_expense,
        consolidated_income_cents=consolidated_income,
        consolidated_net_cents=consolidated_income - consolidated_expense,
        total_transaction_count=total_transaction_count,
        period_start=date_from,
        period_end=date_to,
    )
