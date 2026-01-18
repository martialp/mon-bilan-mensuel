# Implementation Plan: PDF Import UI

## Overview

This implementation plan breaks down the PDF Import UI feature into incremental coding tasks. The implementation uses TypeScript with React 19, TanStack Router, TanStack Query, shadcn/ui components, and React Hook Form with Zod validation. All tasks build on the existing frontend patterns and integrate with the already-implemented backend API.

## Tasks

- [x] 1. Set up route and page structure
  - [x] 1.1 Create the imports route file at `frontend/src/routes/_layout/imports.tsx`
    - Define route with `createFileRoute("/_layout/imports")`
    - Add page head meta with title "Import Statements - Personal Finance Tracker"
    - Create basic page component with header "Import Statements" and description
    - _Requirements: 1.3_
  
  - [x] 1.2 Update sidebar navigation in `frontend/src/components/Sidebar/AppSidebar.tsx`
    - Import `Upload` icon from lucide-react
    - Add Import menu item between Transactions and Categories
    - Set path to "/imports"
    - _Requirements: 1.1, 1.2_

- [x] 2. Implement upload dialog component
  - [x] 2.1 Create `frontend/src/components/Imports/UploadDialog.tsx`
    - Create Zod schema for file (PDF only) and accountId validation
    - Implement dialog with file input and account selector
    - Use React Hook Form for form state management
    - Fetch accounts using useSuspenseQuery
    - Call ImportsService.uploadPdf on submit
    - Handle loading state with LoadingButton
    - Pass preview data to parent on success
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 3. Implement transaction preview component
  - [x] 3.1 Create column definitions at `frontend/src/components/Imports/columns.tsx`
    - Define previewColumns for TransactionPreview table (Date, Description, Amount, Type)
    - Add currency formatting for amount_cents
    - Add type badge rendering (expense/income/transfer)
    - _Requirements: 3.3_
  
  - [x] 3.2 Create `frontend/src/components/Imports/ImportPreview.tsx`
    - Display file name and statement date
    - Display transaction table using DataTable with previewColumns
    - Show statement total and calculated total
    - Display warning alert when totals don't match
    - Display each warning from warnings array
    - Show transaction count
    - Add Confirm Import and Cancel buttons
    - Handle loading states for both actions
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.8_

- [x] 4. Implement import confirmation and rejection
  - [x] 4.1 Add confirmation mutation to ImportPreview
    - Call ImportsService.confirmImport with import_id
    - Show success toast with transaction count on success
    - Call onConfirm callback to close preview and refresh history
    - Handle errors with toast, keep preview open
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 4.2 Add rejection mutation to ImportPreview
    - Call ImportsService.rejectImport with import_id
    - Show info toast "Import cancelled" on success
    - Call onReject callback to close preview and refresh history
    - Handle errors with toast, keep preview open
    - _Requirements: 4.5, 4.6, 4.7_

- [x] 5. Implement import history component
  - [x] 5.1 Add history column definitions to `frontend/src/components/Imports/columns.tsx`
    - Define historyColumns for ImportSessionPublic table
    - Add columns: File Name, Account, Status, Transactions, Date
    - Implement status badge with correct variants (default/success/secondary/destructive)
    - Add date formatting for created_at
    - _Requirements: 5.2, 5.4_
  
  - [x] 5.2 Create `frontend/src/components/Imports/ImportHistory.tsx`
    - Fetch import history using useSuspenseQuery with ImportsService.listImports
    - Render DataTable with historyColumns
    - Show empty state "No imports yet" when data is empty
    - Support pagination through DataTable
    - _Requirements: 5.1, 5.3, 5.5, 5.6_

- [x] 6. Wire components together in imports page
  - [x] 6.1 Complete the imports route component
    - Add state for previewData (ImportPreviewPublic | null)
    - Render UploadDialog with onUploadSuccess handler
    - Conditionally render ImportPreview when previewData exists
    - Render ImportHistory wrapped in Suspense with loading fallback
    - Handle confirm/reject callbacks to clear preview and invalidate queries
    - _Requirements: 3.1, 4.4, 4.7_

- [x] 7. Implement error handling
  - [x] 7.1 Add error handling to UploadDialog
    - Use extractErrorMessage and getErrorCode from utils
    - Show specific error for invalid file type
    - Show specific error for no transactions found
    - Show network error with retry option
    - Show API error messages for other failures
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_
  
  - [x] 7.2 Add error handling to ImportPreview
    - Handle confirmation errors with toast, keep preview open
    - Handle rejection errors with toast, keep preview open
    - Use existing error utilities for consistent messaging
    - _Requirements: 6.4_

- [x] 8. Checkpoint - Ensure all components work together
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Write E2E tests
  - [x] 9.1 Create `frontend/tests/imports.spec.ts` with navigation tests
    - Test Import page is accessible from sidebar
    - Test page displays header and description
    - Test Add Import button is visible
    - _Requirements: 1.1, 1.2, 1.3, 2.1_
  
  - [x] 9.2 Add upload dialog tests
    - Test dialog opens with required fields
    - Test file input accepts only PDF
    - Test account selector is populated
    - Test form validation errors
    - _Requirements: 2.2, 2.3, 2.4, 2.5_
  
  - [x] 9.3 Add history table tests
    - Test history table displays past imports
    - Test status badges have correct styling
    - Test empty state when no imports
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 10. Final checkpoint - Verify complete implementation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- The implementation follows existing patterns from Accounts, Transactions, and Categories pages
- All API calls use the auto-generated client from `@/client`
- Error handling uses existing utilities from `@/utils`
