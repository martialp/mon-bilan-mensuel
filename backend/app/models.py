import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


# Enums for the new models
class AccountType(str, Enum):
    CREDIT_CARD = "credit_card"
    CHEQUING = "chequing"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    OTHER = "other"


class TransactionType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    AUTO = "auto"
    CONFIRMED = "confirmed"
    MANUAL = "manual"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# Account models
class AccountBase(SQLModel):
    name: str = Field(max_length=255)
    type: AccountType
    institution: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(AccountBase):
    name: str | None = Field(default=None, max_length=255)
    type: AccountType | None = None
    institution: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class Account(AccountBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transactions: list["Transaction"] = Relationship(back_populates="account", cascade_delete=True)


class AccountPublic(AccountBase):
    id: uuid.UUID
    created_at: datetime


class AccountsPublic(SQLModel):
    data: list[AccountPublic]
    count: int


# Category models
class CategoryBase(SQLModel):
    name: str = Field(max_length=255, unique=True)


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transactions: list["Transaction"] = Relationship(back_populates="category")


class CategoryPublic(CategoryBase):
    id: uuid.UUID
    created_at: datetime


class CategoriesPublic(SQLModel):
    data: list[CategoryPublic]
    count: int


# Transaction models
class TransactionBase(SQLModel):
    date_transaction: date
    date_inscription: date | None = None
    description: str = Field(max_length=500)
    amount_cents: int = Field(gt=0)  # Positive integer, sign determined by type
    type: TransactionType
    note: str | None = Field(default=None, max_length=1000)
    source_file: str | None = Field(default=None, max_length=255)
    statement_date: date | None = None


class TransactionCreate(TransactionBase):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None


class TransactionUpdate(TransactionBase):
    date_transaction: date | None = None
    description: str | None = Field(default=None, max_length=500)
    amount_cents: int | None = Field(default=None, gt=0)
    type: TransactionType | None = None
    category_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=1000)


class Transaction(TransactionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_id: uuid.UUID = Field(foreign_key="account.id", nullable=False)
    category_id: uuid.UUID | None = Field(foreign_key="category.id", nullable=True)
    status: TransactionStatus = Field(default=TransactionStatus.MANUAL)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    account: Account = Relationship(back_populates="transactions")
    category: Category | None = Relationship(back_populates="transactions")
    
    __table_args__ = (
        UniqueConstraint(
            "account_id", "date_transaction", "description", 
            "amount_cents", "statement_date", 
            name="unique_transaction"
        ),
    )


class TransactionPublic(TransactionBase):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    status: TransactionStatus
    created_at: datetime
    account: AccountPublic
    category: CategoryPublic | None


class TransactionsPublic(SQLModel):
    data: list[TransactionPublic]
    count: int
