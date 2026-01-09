import uuid
from typing import Any
from decimal import Decimal

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item, ItemCreate, User, UserCreate, UserUpdate,
    Account, AccountCreate, AccountUpdate,
    Category, CategoryCreate,
    Transaction, TransactionCreate, TransactionUpdate,
    AccountType, TransactionType
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# Currency conversion utilities
def currency_to_cents(amount: Decimal) -> int:
    """Convert currency amount to cents (integer)."""
    return int(amount * 100)


def cents_to_currency(cents: int) -> Decimal:
    """Convert cents (integer) to currency amount."""
    return Decimal(cents) / 100


# Validation utilities
def validate_transaction_type(transaction_type: str) -> bool:
    """Validate that transaction type is one of the allowed values."""
    try:
        TransactionType(transaction_type)
        return True
    except ValueError:
        return False


def validate_account_type(account_type: str) -> bool:
    """Validate that account type is one of the allowed values."""
    try:
        AccountType(account_type)
        return True
    except ValueError:
        return False


# Account CRUD operations
def create_account(*, session: Session, account_in: AccountCreate) -> Account:
    """Create a new account."""
    db_account = Account.model_validate(account_in)
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    return db_account


def get_account(*, session: Session, account_id: uuid.UUID) -> Account | None:
    """Get account by ID."""
    statement = select(Account).where(Account.id == account_id)
    return session.exec(statement).first()


def get_accounts(*, session: Session, skip: int = 0, limit: int = 100) -> list[Account]:
    """Get all accounts with pagination."""
    statement = select(Account).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_account(*, session: Session, db_account: Account, account_in: AccountUpdate) -> Account:
    """Update an existing account."""
    account_data = account_in.model_dump(exclude_unset=True)
    db_account.sqlmodel_update(account_data)
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    return db_account


def delete_account(*, session: Session, account_id: uuid.UUID) -> bool:
    """Delete an account if it has no transactions."""
    account = get_account(session=session, account_id=account_id)
    if not account:
        return False
    
    # Check if account has transactions
    statement = select(Transaction).where(Transaction.account_id == account_id)
    transactions = session.exec(statement).first()
    if transactions:
        raise ValueError("Cannot delete account with existing transactions")
    
    session.delete(account)
    session.commit()
    return True


# Category CRUD operations
def create_category(*, session: Session, category_in: CategoryCreate) -> Category:
    """Create a new category."""
    db_category = Category.model_validate(category_in)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


def get_category(*, session: Session, category_id: uuid.UUID) -> Category | None:
    """Get category by ID."""
    statement = select(Category).where(Category.id == category_id)
    return session.exec(statement).first()


def get_category_by_name(*, session: Session, name: str) -> Category | None:
    """Get category by name."""
    statement = select(Category).where(Category.name == name)
    return session.exec(statement).first()


def get_categories(*, session: Session, skip: int = 0, limit: int = 100) -> list[Category]:
    """Get all categories with pagination."""
    statement = select(Category).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def delete_category(*, session: Session, category_id: uuid.UUID) -> bool:
    """Delete a category if it has no transactions."""
    category = get_category(session=session, category_id=category_id)
    if not category:
        return False
    
    # Check if category has transactions
    statement = select(Transaction).where(Transaction.category_id == category_id)
    transactions = session.exec(statement).first()
    if transactions:
        raise ValueError("Cannot delete category with existing transactions")
    
    session.delete(category)
    session.commit()
    return True


# Transaction CRUD operations
def create_transaction(*, session: Session, transaction_in: TransactionCreate) -> Transaction:
    """Create a new transaction."""
    db_transaction = Transaction.model_validate(transaction_in)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


def get_transaction(*, session: Session, transaction_id: uuid.UUID) -> Transaction | None:
    """Get transaction by ID."""
    statement = select(Transaction).where(Transaction.id == transaction_id)
    return session.exec(statement).first()


def get_transactions(*, session: Session, skip: int = 0, limit: int = 100) -> list[Transaction]:
    """Get all transactions with pagination."""
    statement = select(Transaction).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_transactions_by_account(*, session: Session, account_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Transaction]:
    """Get transactions for a specific account."""
    statement = select(Transaction).where(Transaction.account_id == account_id).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_transactions_by_category(*, session: Session, category_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Transaction]:
    """Get transactions for a specific category."""
    statement = select(Transaction).where(Transaction.category_id == category_id).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_uncategorized_transactions(*, session: Session, skip: int = 0, limit: int = 100) -> list[Transaction]:
    """Get transactions that need categorization (category_id is NULL)."""
    statement = select(Transaction).where(Transaction.category_id.is_(None)).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_transaction(*, session: Session, db_transaction: Transaction, transaction_in: TransactionUpdate) -> Transaction:
    """Update an existing transaction."""
    transaction_data = transaction_in.model_dump(exclude_unset=True)
    db_transaction.sqlmodel_update(transaction_data)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction


def delete_transaction(*, session: Session, transaction_id: uuid.UUID) -> bool:
    """Delete a transaction."""
    transaction = get_transaction(session=session, transaction_id=transaction_id)
    if not transaction:
        return False
    
    session.delete(transaction)
    session.commit()
    return True
