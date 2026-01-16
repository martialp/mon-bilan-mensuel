# Requirements Document

## Introduction

This feature enables importing transactions from Mastercard PDF statements downloaded from Desjardins (AccèsD) platform. The system extracts transaction data from PDF files and integrates them into the existing transaction management workflow. This builds upon the existing MVP's manual transaction entry capabilities.

**Reference PDF**: A sample Desjardins Mastercard statement is available at `#[[file:############8000-janvier-2025.pdf]]` for testing and validation purposes.

## Glossary

- **PDF_Extractor**: Component that extracts transaction data from Mastercard PDF statements using pdfplumber library
- **Mastercard_Statement**: A PDF document downloaded from Desjardins AccèsD containing credit card transactions
- **Statement_Parser**: Component that parses PDFs into structured transaction data using pdfplumber's table extraction
- **Transaction_Importer**: Component that validates and imports extracted transactions into the database
- **Import_Session**: A record tracking a single PDF import operation including file metadata and results
- **Extraction_Result**: Structured data containing all transactions extracted from a single PDF statement
- **pdfplumber**: Python library for extracting text and tables from PDF files

## Requirements

### Requirement 1: PDF File Upload and Validation

**User Story:** As a user, I want to upload Mastercard PDF statements from Desjardins, so that I can import my credit card transactions automatically.

#### Acceptance Criteria

1. WHEN a user uploads a file, THE System SHALL validate that the file is a PDF format before processing
2. WHEN a user uploads a PDF, THE System SHALL validate the file size does not exceed 10MB
3. WHEN a user uploads a valid PDF, THE System SHALL store the file temporarily for processing
4. WHEN a user uploads an invalid file type, THE System SHALL reject the upload with a clear error message
5. WHEN a user uploads a PDF, THE System SHALL require the user to select a target account for the transactions
6. IF the uploaded PDF is corrupted or unreadable, THEN THE System SHALL return an error indicating the file cannot be processed

### Requirement 2: Transaction Extraction from PDF

**User Story:** As a user, I want the system to automatically extract transaction data from my PDF statements, so that I don't have to manually enter each transaction.

#### Acceptance Criteria

1. WHEN a valid PDF is uploaded, THE PDF_Extractor SHALL use pdfplumber to process the PDF and extract transaction data
2. WHEN processing the PDF, THE Statement_Parser SHALL use pdfplumber's table extraction to identify transaction date, description, and amount for each transaction
3. WHEN extracting transactions, THE Statement_Parser SHALL identify the statement date from the PDF header text
4. WHEN extracting amounts, THE Statement_Parser SHALL correctly identify positive amounts (payments/credits) and negative amounts (purchases/debits)
5. WHEN extracting dates, THE Statement_Parser SHALL parse dates in the Desjardins format (e.g., "15 JAN", "15 JANV") and convert to ISO date format
6. IF the PDF_Extractor cannot extract data from the PDF using pdfplumber, THEN THE System SHALL return an error with details about the extraction failure
7. WHEN extraction completes, THE System SHALL return a structured list of all extracted transactions for user review

### Requirement 3: Transaction Data Validation and Transformation

**User Story:** As a user, I want extracted transactions to be validated and properly formatted, so that my financial data is accurate and consistent.

#### Acceptance Criteria

1. WHEN transactions are extracted, THE Transaction_Importer SHALL validate that each transaction has required fields (date, description, amount)
2. WHEN processing amounts, THE System SHALL convert currency values to integer cents for storage
3. WHEN processing transaction types, THE System SHALL classify transactions as expense (purchases) or income (payments/credits) based on amount sign
4. WHEN a transaction has missing required fields, THE System SHALL fail the import with a clear error message
5. WHEN processing descriptions, THE System SHALL trim whitespace and normalize text formatting
6. THE System SHALL associate the statement_date with all transactions from the same PDF

### Requirement 4: Import Preview and Confirmation

**User Story:** As a user, I want to preview extracted transactions before importing, so that I can verify the data is correct before accepting it.

#### Acceptance Criteria

1. WHEN extraction completes, THE System SHALL display a preview of all extracted transactions before importing
2. WHEN displaying the preview, THE System SHALL show transaction date, description, amount, and detected type for each transaction
3. WHEN displaying the preview, THE System SHALL calculate and display the total of all extracted transactions
4. WHEN displaying the preview, THE System SHALL extract and display the statement total from the PDF
5. WHEN the totals match, THE System SHALL indicate validation passed
6. WHEN the totals do not match, THE System SHALL warn the user of the discrepancy and show both totals
7. THE System SHALL allow the user to accept or reject the entire import
8. WHEN the user accepts the import, THE System SHALL persist all extracted transactions
9. WHEN the user rejects the import, THE System SHALL discard all extracted data without persisting any transactions

### Requirement 5: Import Session Tracking

**User Story:** As a user, I want to track my import history, so that I can see which statements I've already imported and review past imports.

#### Acceptance Criteria

1. WHEN an import is completed, THE System SHALL create an Import_Session record with file name, import date, and transaction count
2. WHEN displaying import history, THE System SHALL show all past imports with their status and statistics
3. WHEN a user views an import session, THE System SHALL show all transactions that were imported in that session
4. THE System SHALL store the source_file field on each transaction to link it to its import session
5. WHEN an import fails, THE System SHALL record the failure reason in the import session

### Requirement 6: Error Handling and Recovery

**User Story:** As a user, I want clear error messages and the ability to retry failed imports, so that I can successfully import my statements even when issues occur.

#### Acceptance Criteria

1. IF the extraction service is unavailable, THEN THE System SHALL return a clear error message and suggest retrying later
2. IF the PDF format is not recognized as a Desjardins Mastercard statement, THEN THE System SHALL inform the user the format is not supported
3. WHEN an error occurs during import, THE System SHALL not persist partial data and maintain data consistency
4. WHEN extraction partially fails, THE System SHALL return successfully extracted transactions and report which parts failed
5. THE System SHALL provide detailed error messages that help users understand and resolve issues
6. WHEN a network timeout occurs during extraction, THE System SHALL allow the user to retry the extraction

