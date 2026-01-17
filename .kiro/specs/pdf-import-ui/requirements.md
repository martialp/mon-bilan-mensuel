# Requirements Document

## Introduction

This document defines the requirements for a frontend UI that enables users to import transactions from Mastercard PDF statements. The UI will integrate with the existing backend import API endpoints to provide a complete workflow for uploading PDFs, previewing extracted transactions, and confirming or rejecting imports. The feature will follow existing frontend patterns using React, TypeScript, TanStack Router, TanStack Query, and shadcn/ui components.

## Glossary

- **Import_UI**: The frontend user interface for PDF import functionality
- **Import_Page**: The main page component accessible via sidebar navigation
- **Upload_Dialog**: A modal dialog for selecting a PDF file and target account
- **Preview_View**: A view displaying extracted transactions before confirmation
- **History_Table**: A table displaying past import sessions with their status
- **Import_Service**: The auto-generated API client service for import endpoints
- **Account_Selector**: A dropdown component for selecting the target account

## Requirements

### Requirement 1: Navigation and Page Access

**User Story:** As a user, I want to access the PDF import feature from the sidebar navigation, so that I can easily find and use the import functionality.

#### Acceptance Criteria

1. THE Import_UI SHALL add an "Import" menu item to the sidebar navigation between "Transactions" and "Categories"
2. WHEN a user clicks the "Import" menu item, THE Import_UI SHALL navigate to the `/imports` route
3. THE Import_Page SHALL display a page header with title "Import Statements" and description "Import transactions from PDF statements"

### Requirement 2: PDF Upload

**User Story:** As a user, I want to upload a PDF file and select a target account, so that I can import transactions from my bank statement.

#### Acceptance Criteria

1. THE Import_Page SHALL display an "Import PDF" button that opens the Upload_Dialog
2. WHEN the Upload_Dialog opens, THE Import_UI SHALL display a file input that accepts only PDF files
3. THE Upload_Dialog SHALL display an Account_Selector dropdown populated with the user's accounts
4. WHEN a user selects a file that is not a PDF, THE Import_UI SHALL display an error message "Please select a PDF file"
5. WHEN a user attempts to upload without selecting an account, THE Import_UI SHALL display an error message "Please select an account"
6. WHEN a user submits a valid PDF and account selection, THE Import_UI SHALL call the Import_Service.uploadPdf endpoint
7. WHILE the upload is in progress, THE Import_UI SHALL display a loading indicator and disable the submit button

### Requirement 3: Transaction Preview

**User Story:** As a user, I want to preview extracted transactions before confirming the import, so that I can verify the data is correct.

#### Acceptance Criteria

1. WHEN the upload succeeds, THE Import_UI SHALL display the Preview_View with extracted transactions
2. THE Preview_View SHALL display the file name and statement date from the import preview
3. THE Preview_View SHALL display a table of extracted transactions with columns: Date, Description, Amount, Type
4. THE Preview_View SHALL display the statement total and calculated total from extracted transactions
5. IF the totals do not match, THEN THE Preview_View SHALL display a warning alert with the mismatch details
6. IF the import preview contains warnings, THEN THE Preview_View SHALL display each warning in an alert
7. THE Preview_View SHALL display the total count of extracted transactions

### Requirement 4: Import Confirmation

**User Story:** As a user, I want to confirm or reject an import after reviewing the preview, so that I can control which transactions are added to my account.

#### Acceptance Criteria

1. THE Preview_View SHALL display "Confirm Import" and "Cancel" buttons
2. WHEN a user clicks "Confirm Import", THE Import_UI SHALL call the Import_Service.confirmImport endpoint
3. WHEN the confirmation succeeds, THE Import_UI SHALL display a success toast with the number of transactions imported
4. WHEN the confirmation succeeds, THE Import_UI SHALL close the preview and refresh the import history
5. WHEN a user clicks "Cancel", THE Import_UI SHALL call the Import_Service.rejectImport endpoint
6. WHEN the rejection succeeds, THE Import_UI SHALL display an info toast "Import cancelled"
7. WHEN the rejection succeeds, THE Import_UI SHALL close the preview and refresh the import history
8. WHILE confirmation or rejection is in progress, THE Import_UI SHALL display a loading indicator and disable both buttons

### Requirement 5: Import History

**User Story:** As a user, I want to see a history of my past imports, so that I can track what statements I have already imported.

#### Acceptance Criteria

1. THE Import_Page SHALL display the History_Table showing past import sessions
2. THE History_Table SHALL display columns: File Name, Account, Status, Transactions, Date
3. THE History_Table SHALL fetch data using the Import_Service.listImports endpoint
4. THE History_Table SHALL display the import status with appropriate visual indicators (badge colors)
5. WHEN no import history exists, THE Import_Page SHALL display an empty state message "No imports yet"
6. THE History_Table SHALL support pagination for large datasets

### Requirement 6: Error Handling

**User Story:** As a user, I want to see clear error messages when something goes wrong, so that I can understand and resolve issues.

#### Acceptance Criteria

1. IF the PDF upload fails due to invalid file type, THEN THE Import_UI SHALL display the error "Invalid file type. Please upload a PDF file."
2. IF the PDF upload fails due to extraction errors, THEN THE Import_UI SHALL display the specific error message from the API
3. IF the PDF contains no transactions, THEN THE Import_UI SHALL display "No transactions found in the PDF"
4. IF the import confirmation fails, THEN THE Import_UI SHALL display the error message and keep the preview open
5. IF a network error occurs, THEN THE Import_UI SHALL display "Unable to connect to the server. Please check your internet connection."
6. WHEN an error occurs, THE Import_UI SHALL provide a way to retry the operation where applicable
