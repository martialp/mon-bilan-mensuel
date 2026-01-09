# Design Document: Personal Finance MVP

## Overview

This design document outlines the architecture for a personal finance application MVP that enables manual transaction entry, categorization, and analysis. The system builds upon the existing FastAPI + React + PostgreSQL stack, adding new models and endpoints for financial data management.

The MVP focuses on core functionality: account management, manual transaction entry, basic categorization, and financial reporting. This provides a solid foundation for future enhancements like PDF extraction and AI-powered categorization.

## Architecture

The application follows a three-tier architecture:

### Backend (FastAPI + SQLModel + PostgreSQL)
- **API Layer**: RESTful endpoints for CRUD operations on financial entities
- **Business Logic**: Transaction processing, categorization logic, and analysis calculations
- **Data Layer**: PostgreSQL database with SQLModel ORM for type-safe database operations

### Frontend (React + TypeScript + TanStack)
- **UI Components**: Reusable components built with Radix UI and Tailwind CSS
- **State Management**: TanStack Query for server state and React hooks for local state
- **Routing**: TanStack Router for type-safe navigation
- **Forms**: React Hook Form with Zod validation

### Database (PostgreSQL)
- Uses existing Alembic migration system for schema management
- New tables will be created via Alembic migrations following existing patterns
- Maintains referential integrity with foreign key constraints
- Uses UUIDs for primary keys following existing User/Item model patterns

## Components and Interfaces

### Backend Models

#### Account Model
```python
class AccountBase(SQLModel):
    name: str = Field(max_length=255)
    type: Literal["credit_card", "chequing", "savings", "investment", "other"]
    institution: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)

class Account(AccountBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transactions: list["Transaction"] = Relationship(back_populates="account")

class AccountCreate(AccountBase):
    pass

class AccountUpdate(AccountBase):
    name: str | None = Field(default=None, max_length=255)
    type: Literal["credit_card", "chequing", "savings", "investment", "other"] | None = None
    institution: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)

class AccountPublic(AccountBase):
    id: uuid.UUID
    created_at: datetime
```

#### Category Model
```python
class CategoryBase(SQLModel):
    name: str = Field(max_length=255, unique=True)

class Category(CategoryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transactions: list["Transaction"] = Relationship(back_populates="category")

class CategoryCreate(CategoryBase):
    pass

class CategoryPublic(CategoryBase):
    id: uuid.UUID
    created_at: datetime
```

#### Transaction Model
```python
class TransactionBase(SQLModel):
    date_transaction: date
    date_inscription: date | None = None
    description: str = Field(max_length=500)
    amount_cents: int = Field(gt=0)  # Positive integer, sign determined by type
    type: Literal["expense", "income", "transfer"]
    note: str | None = Field(default=None, max_length=1000)
    source_file: str | None = Field(default=None, max_length=255)
    statement_date: date | None = None

class Transaction(TransactionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_id: uuid.UUID = Field(foreign_key="account.id", nullable=False)
    category_id: uuid.UUID | None = Field(foreign_key="category.id", nullable=True)
    status: Literal["auto", "confirmed", "manual"] = Field(default="manual")
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

class TransactionCreate(TransactionBase):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None

class TransactionUpdate(TransactionBase):
    date_transaction: date | None = None
    description: str | None = Field(default=None, max_length=500)
    amount_cents: int | None = Field(default=None, gt=0)
    type: Literal["expense", "income", "transfer"] | None = None
    category_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=1000)

class TransactionPublic(TransactionBase):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    status: Literal["auto", "confirmed", "manual"]
    created_at: datetime
    account: AccountPublic
    category: CategoryPublic | None
```

### API Endpoints

#### Account Management
- `GET /api/v1/accounts/` - List all accounts
- `POST /api/v1/accounts/` - Create new account
- `GET /api/v1/accounts/{account_id}` - Get account details
- `PUT /api/v1/accounts/{account_id}` - Update account
- `DELETE /api/v1/accounts/{account_id}` - Delete account (if no transactions)

#### Category Management
- `GET /api/v1/categories/` - List all categories
- `POST /api/v1/categories/` - Create new category
- `GET /api/v1/categories/{category_id}` - Get category details
- `PUT /api/v1/categories/{category_id}` - Update category
- `DELETE /api/v1/categories/{category_id}` - Delete category (if no transactions)

#### Transaction Management
- `GET /api/v1/transactions/` - List transactions with filtering (by account, category, status, date range)
- `GET /api/v1/transactions/uncategorized` - List transactions needing categorization (category_id NULL)
- `GET /api/v1/transactions/pending-confirmation` - List transactions needing confirmation (status 'auto')
- `POST /api/v1/transactions/` - Create new transaction
- `GET /api/v1/transactions/{transaction_id}` - Get transaction details
- `PUT /api/v1/transactions/{transaction_id}` - Update transaction
- `DELETE /api/v1/transactions/{transaction_id}` - Delete transaction
- `PUT /api/v1/transactions/{transaction_id}/categorize` - Manually categorize transaction
- `PUT /api/v1/transactions/{transaction_id}/confirm` - Confirm auto-categorized transaction

#### Analysis Endpoints
- `GET /api/v1/analysis/spending-by-category` - Category spending analysis
- `GET /api/v1/analysis/spending-trends` - Monthly spending trends
- `GET /api/v1/analysis/account-summary` - Per-account financial summary

### Frontend Components

#### Account Management
- `AccountList` - Display all accounts with basic info
- `AccountForm` - Create/edit account form
- `AccountCard` - Individual account display component

#### Transaction Management
- `TransactionList` - Paginated transaction list with filtering
- `TransactionForm` - Create/edit transaction form
- `TransactionRow` - Individual transaction display with status indicators
- `CategorySelector` - Dropdown for category selection
- `TransactionFilters` - Date range, account, category filters

#### Analysis Dashboard
- `SpendingByCategory` - Pie/bar chart of category spending
- `SpendingTrends` - Line chart of monthly trends
- `AccountSummary` - Cards showing account balances and totals
- `DateRangePicker` - Date range selection for analysis

## Data Models

### Database Schema
The application will create new tables using Alembic migrations, following the existing project patterns. The schema will be based on the conception design in `docs/schema.sql` but implemented through proper migrations:

**Migration 1: Create accounts table**
```python
def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum('credit_card', 'chequing', 'savings', 'investment', 'other', name='account_type'), nullable=False),
        sa.Column('institution', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
```

**Migration 2: Create categories table**
```python
def upgrade() -> None:
    op.create_table(
        'categories',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
```

**Migration 3: Create transactions table**
```python
def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('account_id', sa.UUID(), nullable=False),
        sa.Column('date_transaction', sa.Date(), nullable=False),
        sa.Column('date_inscription', sa.Date(), nullable=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('expense', 'income', 'transfer', name='transaction_type'), nullable=False),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.Enum('auto', 'confirmed', 'manual', name='transaction_status'), nullable=False, server_default='manual'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('source_file', sa.String(255), nullable=True),
        sa.Column('statement_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.UniqueConstraint('account_id', 'date_transaction', 'description', 'amount_cents', 'statement_date', name='unique_transaction'),
        sa.CheckConstraint('amount_cents > 0', name='positive_amount')
    )
```

### Data Relationships
- **Account → Transactions**: One-to-many relationship
- **Category → Transactions**: One-to-many relationship (nullable)
- **Unique Constraint**: Prevents duplicate transactions based on key fields

### Amount Handling
- All monetary amounts stored as positive integers in cents
- Transaction type (expense/income/transfer) determines the semantic meaning
- Frontend displays amounts in currency format (e.g., $123.45)
- Business logic handles sign conversion based on transaction type

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Now I need to use the prework tool to analyze the acceptance criteria before writing the correctness properties:
Based on the prework analysis, I've identified the following testable properties while eliminating redundancy:

### Property 1: Transaction Creation and Persistence
*For any* valid transaction data with required fields (date_transaction, description, amount_cents, type, account_id), creating the transaction should result in it being immediately persisted to the database with all fields intact.
**Validates: Requirements 1.1, 5.1**

### Property 2: Currency Conversion Accuracy
*For any* valid currency amount, converting to cents and back to currency should preserve the original value with proper precision.
**Validates: Requirements 1.2**

### Property 3: Transaction Type Validation
*For any* transaction creation attempt, only valid transaction types (expense, income, transfer) should be accepted, and invalid types should be rejected with appropriate error messages.
**Validates: Requirements 1.3**

### Property 4: Duplicate Transaction Prevention
*For any* transaction that already exists in the database, attempting to create an identical transaction (same account_id, date_transaction, description, amount_cents, statement_date) should be prevented and return a clear conflict explanation.
**Validates: Requirements 1.4, 5.2, 7.3**

### Property 5: Comprehensive Input Validation
*For any* invalid transaction data (negative amounts, missing required fields, invalid types), the system should validate input before database persistence and provide specific error messages.
**Validates: Requirements 1.5, 7.1, 7.4**

### Property 6: Transaction Update Integrity
*For any* existing transaction, updating its fields should preserve data integrity and maintain all relationships while persisting the changes.
**Validates: Requirements 1.6**

### Property 7: Manual Categorization Workflow
*For any* transaction that is manually assigned a category, the category_id should be updated and the status should be set to 'manual' and never changed automatically.
**Validates: Requirements 2.1, 2.5**

### Property 8: Transaction Status Filtering
*For any* set of transactions, filtering for uncategorized transactions should return only those with category_id NULL, and filtering for transactions needing confirmation should return only those with status 'auto'.
**Validates: Requirements 2.2**

### Property 9: Category Creation and Uniqueness
*For any* new category name, the system should create the category successfully, but attempting to create a category with an existing name should be rejected.
**Validates: Requirements 2.3, 5.4**

### Property 10: Category Update Flexibility
*For any* transaction, the category assignment should be changeable at any time while preserving the transaction's other properties.
**Validates: Requirements 2.4**

### Property 11: Transaction Status Rendering
*For any* transaction with status 'auto', the rendering function should produce output that visually distinguishes it from transactions with other statuses.
**Validates: Requirements 2.6**

### Property 12: Status Transition Confirmation
*For any* transaction with status 'auto', confirming it should change the status to 'confirmed' while preserving all other transaction properties.
**Validates: Requirements 2.7**

### Property 13: Account Creation and Storage
*For any* valid account data with required fields (name, type), creating the account should store all provided fields including optional institution and description.
**Validates: Requirements 3.1**

### Property 14: Account Type Validation
*For any* account creation attempt, only valid account types (credit_card, chequing, savings, investment, other) should be accepted.
**Validates: Requirements 3.2**

### Property 15: Account Data Retrieval
*For any* stored account, retrieving it should return all required fields (name, type, institution) for identification.
**Validates: Requirements 3.3**

### Property 16: Account Deletion Protection
*For any* account that has associated transactions, deletion attempts should be prevented while maintaining referential integrity.
**Validates: Requirements 3.4**

### Property 17: Account Update Preservation
*For any* account with associated transactions, updating account details should preserve all transaction relationships.
**Validates: Requirements 3.5**

### Property 18: Category Spending Calculation
*For any* set of categorized transactions within a time period, the total spending per category should equal the sum of all transaction amounts in that category and period.
**Validates: Requirements 4.1**

### Property 19: Monthly Trend Accuracy
*For any* set of transactions across multiple months, the monthly breakdown should accurately group transactions by month with correct totals.
**Validates: Requirements 4.2**

### Property 20: Percentage Calculation Accuracy
*For any* category spending summary, the percentage values should be mathematically correct relative to the total spending amount.
**Validates: Requirements 4.3**

### Property 21: Date Range Filtering
*For any* date range query, the returned transactions should include only those with transaction dates within the specified range (inclusive).
**Validates: Requirements 4.4**

### Property 22: Category Ranking Accuracy
*For any* spending analysis period, the top spending categories should be correctly ranked by total amount in descending order.
**Validates: Requirements 4.5**

### Property 23: Multi-Account Analysis Consistency
*For any* analysis across multiple accounts, the consolidated totals should equal the sum of individual account totals.
**Validates: Requirements 4.6**

### Property 24: Cross-Account Data Integrity
*For any* operations involving multiple accounts, all referential relationships should remain valid and consistent.
**Validates: Requirements 5.3**

### Property 25: Data Retrieval Consistency
*For any* stored financial data, retrieving it should return exactly the same values that were originally stored without corruption or loss.
**Validates: Requirements 5.5**

### Property 26: Form Validation Feedback
*For any* form submission with missing or invalid required fields, the system should return specific validation messages identifying the problematic fields.
**Validates: Requirements 6.2**

### Property 27: Transaction Display Completeness
*For any* transaction retrieval, the response should include all required fields (category, date, description, amount) in a structured format.
**Validates: Requirements 6.3**

### Property 28: Error Message Specificity
*For any* error condition during data entry, the system should return user-friendly error messages with specific details about the problem.
**Validates: Requirements 6.5**

### Property 29: Comprehensive Error Handling
*For any* system error or database failure, the system should maintain data consistency, log detailed debugging information, and provide meaningful user feedback.
**Validates: Requirements 7.2, 7.5**

## Error Handling

The application implements comprehensive error handling at multiple levels:

### Input Validation
- **Client-side**: React Hook Form with Zod schemas for immediate feedback
- **Server-side**: Pydantic/SQLModel validation for data integrity
- **Database-level**: Constraints and foreign key validation

### Error Response Format
```python
class ErrorResponse(SQLModel):
    detail: str
    error_code: str
    field_errors: dict[str, list[str]] | None = None
```

### Common Error Scenarios
- **Duplicate Transaction**: HTTP 409 with specific conflict details
- **Invalid Account Type**: HTTP 422 with validation details
- **Missing Required Fields**: HTTP 422 with field-specific messages
- **Referential Integrity Violations**: HTTP 400 with relationship details
- **Database Connection Issues**: HTTP 503 with retry guidance

### Logging Strategy
- **Application Logs**: Structured JSON logs with correlation IDs
- **Error Tracking**: Integration with existing Sentry setup

## Testing Strategy

The testing approach combines unit tests for specific scenarios with property-based tests for comprehensive validation:

### Unit Testing
- **Specific Examples**: Test concrete scenarios like creating a transaction with specific values
- **Edge Cases**: Test boundary conditions like zero amounts, maximum string lengths
- **Error Conditions**: Test specific error scenarios like duplicate creation attempts
- **Integration Points**: Test API endpoints with realistic data

### Property-Based Testing
- **Library**: Use Hypothesis for Python backend testing
- **Configuration**: Minimum 20 iterations per property test
- **Universal Properties**: Test properties that should hold for all valid inputs
- **Data Generation**: Smart generators that create realistic financial data within valid constraints

### Test Organization
- **Backend Tests**: Located in `backend/tests/` following existing patterns
- **API Tests**: Test endpoints with various input combinations
- **Model Tests**: Test SQLModel validation and database operations
- **Business Logic Tests**: Test financial calculations and categorization logic

### Property Test Examples
```python
# Example property test structure
@given(transaction_data=transaction_strategy())
def test_transaction_creation_persistence(transaction_data):
    """Property 1: Transaction Creation and Persistence"""
    # Feature: personal-finance-tracker, Property 1: Transaction creation and persistence
    created_transaction = create_transaction(transaction_data)
    retrieved_transaction = get_transaction(created_transaction.id)
    assert retrieved_transaction == created_transaction

@given(currency_amount=st.decimals(min_value=0.01, max_value=999999.99, places=2))
def test_currency_conversion_accuracy(currency_amount):
    """Property 2: Currency Conversion Accuracy"""
    # Feature: personal-finance-tracker, Property 2: Currency conversion accuracy
    cents = currency_to_cents(currency_amount)
    converted_back = cents_to_currency(cents)
    assert converted_back == currency_amount
```

Each property test will be tagged with the format: **Feature: personal-finance-tracker, Property {number}: {property_text}** to maintain traceability to the design document.