import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select, and_, or_
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep
from app.models import (
    Transaction, TransactionCreate, TransactionPublic, TransactionsPublic, 
    TransactionUpdate, Message, Account, Category, TransactionStatus
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=TransactionsPublic)
def read_transactions(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    account_id: uuid.UUID | None = Query(None, description="Filter by account ID"),
    category_id: uuid.UUID | None = Query(None, description="Filter by category ID"),
    status: TransactionStatus | None = Query(None, description="Filter by transaction status"),
    date_from: date | None = Query(None, description="Filter transactions from this date (inclusive)"),
    date_to: date | None = Query(None, description="Filter transactions to this date (inclusive)"),
) -> Any:
    """
    Retrieve transactions with optional filtering by account, category, status, and date range.
    """
    # Build the base query
    statement = select(Transaction)
    
    # Apply filters
    filters = []
    if account_id:
        filters.append(Transaction.account_id == account_id)
    if category_id:
        filters.append(Transaction.category_id == category_id)
    if status:
        filters.append(Transaction.status == status)
    if date_from:
        filters.append(Transaction.date_transaction >= date_from)
    if date_to:
        filters.append(Transaction.date_transaction <= date_to)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    # Get count for pagination
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()
    
    # Apply pagination and execute
    statement = statement.offset(skip).limit(limit).order_by(Transaction.date_transaction.desc())
    transactions = session.exec(statement).all()
    
    return TransactionsPublic(data=transactions, count=count)


@router.get("/uncategorized", response_model=TransactionsPublic)
def read_uncategorized_transactions(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve transactions that need categorization (category_id is NULL).
    """
    count_statement = select(func.count()).select_from(Transaction).where(Transaction.category_id.is_(None))
    count = session.exec(count_statement).one()
    
    statement = (
        select(Transaction)
        .where(Transaction.category_id.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(Transaction.date_transaction.desc())
    )
    transactions = session.exec(statement).all()
    
    return TransactionsPublic(data=transactions, count=count)


@router.get("/pending-confirmation", response_model=TransactionsPublic)
def read_pending_confirmation_transactions(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve transactions that need confirmation (status is 'auto').
    """
    count_statement = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.status == TransactionStatus.AUTO)
    )
    count = session.exec(count_statement).one()
    
    statement = (
        select(Transaction)
        .where(Transaction.status == TransactionStatus.AUTO)
        .offset(skip)
        .limit(limit)
        .order_by(Transaction.date_transaction.desc())
    )
    transactions = session.exec(statement).all()
    
    return TransactionsPublic(data=transactions, count=count)


@router.get("/{id}", response_model=TransactionPublic)
def read_transaction(session: SessionDep, id: uuid.UUID) -> Any:
    """
    Get transaction by ID.
    """
    transaction = session.get(Transaction, id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.post("/", response_model=TransactionPublic)
def create_transaction(
    *, session: SessionDep, transaction_in: TransactionCreate
) -> Any:
    """
    Create new transaction with duplicate prevention.
    """
    # Verify that the account exists
    account = session.get(Account, transaction_in.account_id)
    if not account:
        raise HTTPException(status_code=400, detail="Account not found")
    
    # Verify that the category exists if provided
    if transaction_in.category_id:
        category = session.get(Category, transaction_in.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    try:
        transaction = Transaction.model_validate(transaction_in)
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction
    except IntegrityError as e:
        session.rollback()
        if "unique_transaction" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="A transaction with the same account, date, description, amount, and statement date already exists"
            )
        raise HTTPException(status_code=400, detail="Database error occurred")


@router.put("/{id}", response_model=TransactionPublic)
def update_transaction(
    *,
    session: SessionDep,
    id: uuid.UUID,
    transaction_in: TransactionUpdate,
) -> Any:
    """
    Update a transaction while maintaining data integrity.
    """
    transaction = session.get(Transaction, id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Verify that the category exists if provided
    if transaction_in.category_id:
        category = session.get(Category, transaction_in.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    try:
        update_dict = transaction_in.model_dump(exclude_unset=True)
        transaction.sqlmodel_update(update_dict)
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction
    except IntegrityError as e:
        session.rollback()
        if "unique_transaction" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="A transaction with the same account, date, description, amount, and statement date already exists"
            )
        raise HTTPException(status_code=400, detail="Database error occurred")


@router.put("/{id}/categorize", response_model=TransactionPublic)
def categorize_transaction(
    *,
    session: SessionDep,
    id: uuid.UUID,
    category_id: uuid.UUID,
) -> Any:
    """
    Manually categorize a transaction (sets status to 'manual').
    """
    transaction = session.get(Transaction, id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Verify that the category exists
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    # Update the transaction with manual categorization
    transaction.category_id = category_id
    transaction.status = TransactionStatus.MANUAL
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


@router.put("/{id}/confirm", response_model=TransactionPublic)
def confirm_transaction(
    *,
    session: SessionDep,
    id: uuid.UUID,
) -> Any:
    """
    Confirm an auto-categorized transaction (changes status from 'auto' to 'confirmed').
    """
    transaction = session.get(Transaction, id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.AUTO:
        raise HTTPException(
            status_code=400, 
            detail="Only auto-categorized transactions can be confirmed"
        )
    
    # Update the status to confirmed
    transaction.status = TransactionStatus.CONFIRMED
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


@router.delete("/{id}")
def delete_transaction(
    session: SessionDep, id: uuid.UUID
) -> Message:
    """
    Delete a transaction.
    """
    transaction = session.get(Transaction, id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    session.delete(transaction)
    session.commit()
    return Message(message="Transaction deleted successfully")