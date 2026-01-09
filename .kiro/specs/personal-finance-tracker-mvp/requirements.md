# Requirements Document

## Introduction

A personal finance application MVP for analyzing bank transactions from Desjardins statements. The system provides manual transaction entry, basic categorization, and financial analysis across multiple account types. This MVP focuses on core transaction management and analysis features, with PDF extraction and AI-powered categorization planned for future releases.

## Glossary

- **Transaction_Manager**: Component for manual entry and management of transaction records
- **Transaction**: A financial transaction record with date, description, amount, type, and account association
- **Account**: A financial account (credit card, chequing, savings, investment) tracked in the system
- **Category**: A classification label for transactions stored in the categories table
- **Manual_Categorization**: User-driven process to assign categories to transactions
- **Analysis_Engine**: Component that generates financial insights and reports from categorized transactions
- **Account_Manager**: Component for creating and managing different account types

## Requirements

### Requirement 1: Manual Transaction Entry

**User Story:** As a user, I want to manually enter my bank transactions, so that I can track my financial activity in the system.

#### Acceptance Criteria

1. WHEN a user creates a new transaction, THE Transaction_Manager SHALL store it with date_transaction, description, amount_cents, type, and account_id
2. WHEN entering transaction amounts, THE System SHALL convert currency values to integer cents for precise storage
3. WHEN creating a transaction, THE User SHALL specify the transaction type as expense, income, or transfer
4. WHEN a user enters duplicate transaction data, THE System SHALL prevent duplicate entries based on the unique constraint (account_id, date_transaction, description, amount_cents, statement_date)
5. THE System SHALL validate that amount_cents is positive and transaction type is valid before saving
6. WHEN a user edits an existing transaction, THE System SHALL update the record while maintaining data integrity

### Requirement 2: Manual Transaction Categorization

**User Story:** As a user, I want to manually assign categories to my transactions, so that I can organize my spending for analysis.

#### Acceptance Criteria

1. WHEN a user assigns a category to a transaction, THE System SHALL update the category_id field and set status to 'manual'
2. WHEN displaying transactions, THE System SHALL show uncategorized transactions (category_id NULL) prominently for user attention
3. WHEN a user creates a new category, THE System SHALL add it to the categories table with a unique name
4. THE System SHALL allow users to change transaction categories at any time
5. WHEN a transaction is manually categorized, THE System SHALL preserve the user's choice with status 'manual' and never change it automatically
6. WHEN displaying transaction lists, THE System SHALL visually distinguish transactions with status 'auto' to indicate they need user confirmation
7. WHEN a user confirms an auto-categorized transaction, THE System SHALL change the status from 'auto' to 'confirmed'

### Requirement 3: Account Management

**User Story:** As a user, I want to create and manage different types of financial accounts, so that I can track transactions across my various accounts.

#### Acceptance Criteria

1. WHEN a user creates a new account, THE Account_Manager SHALL store it with name, type, institution, and optional description
2. THE System SHALL support account types: credit_card, chequing, savings, investment, and other
3. WHEN displaying accounts, THE System SHALL show account name, type, and institution for easy identification
4. WHEN a user deletes an account, THE System SHALL prevent deletion if transactions exist for that account
5. THE System SHALL allow users to edit account details while preserving associated transaction history

### Requirement 4: Financial Analysis and Reporting

**User Story:** As a user, I want to see analysis of my spending patterns, so that I can make informed financial decisions.

#### Acceptance Criteria

1. WHEN transactions are categorized, THE Analysis_Engine SHALL calculate total spending per category for specified time periods
2. WHEN generating reports, THE Analysis_Engine SHALL show spending trends over time with monthly breakdowns
3. WHEN displaying category summaries, THE System SHALL show both absolute amounts and percentages of total spending
4. WHEN a user requests analysis for a date range, THE System SHALL filter transactions within that period accurately
5. THE System SHALL identify and highlight the top spending categories for any given period
6. WHEN analyzing across multiple accounts, THE System SHALL provide consolidated views and per-account breakdowns

### Requirement 5: Data Persistence and Management

**User Story:** As a user, I want my transaction data and account information to be saved reliably, so that I can build a comprehensive financial history.

#### Acceptance Criteria

1. WHEN transactions are entered and categorized, THE System SHALL persist them to the PostgreSQL database immediately
2. WHEN storing transaction data, THE System SHALL enforce the unique constraint to prevent duplicate transactions
3. WHEN a user manages multiple accounts, THE System SHALL maintain data integrity across all account relationships
4. THE System SHALL store categories persistently and allow reuse across different transactions
5. WHEN retrieving historical data, THE System SHALL maintain data consistency and provide accurate financial records

### Requirement 6: User Interface and Experience

**User Story:** As a user, I want an intuitive interface to manage my accounts, enter transactions, and view financial analysis, so that I can easily track my finances.

#### Acceptance Criteria

1. WHEN a user accesses the application, THE System SHALL display a clear interface for managing accounts and transactions
2. WHEN entering new transactions, THE System SHALL provide form validation and clear feedback on required fields
3. WHEN displaying transaction lists, THE System SHALL show transactions with their categories, dates, descriptions, and amounts in a readable format
4. WHEN showing analysis results, THE System SHALL present data using charts and tables for easy comprehension
5. WHEN errors occur during data entry, THE System SHALL display user-friendly error messages with suggested corrections
6. THE System SHALL provide clear navigation between account management, transaction entry, and analysis views

### Requirement 7: Data Validation and Error Handling

**User Story:** As a system administrator, I want robust error handling and data validation, so that the application remains stable and reliable.

#### Acceptance Criteria

1. WHEN invalid data is entered during transaction creation, THE System SHALL validate input and provide specific error messages
2. WHEN database operations fail, THE System SHALL maintain data consistency and provide meaningful error feedback
3. WHEN users attempt to create duplicate transactions, THE System SHALL prevent creation and explain the conflict
4. THE System SHALL validate transaction data integrity before persisting to the database
5. WHEN system errors occur, THE System SHALL log detailed information for debugging while showing user-friendly messages