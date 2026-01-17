# Implementation Plan: Mastercard PDF Import

## Overview

This plan implements the Mastercard PDF import feature following the existing FastAPI patterns. Tasks are ordered to build incrementally, with core extraction logic first, then API endpoints, and finally integration.

## Tasks

- [x] 1. Create data models for import functionality
  - Add `ImportStatus` enum and `ImportSession` model to `backend/app/models.py`
  - Add `ImportSessionCreate`, `ImportSessionPublic`, `ImportSessionsPublic` schemas
  - Add `TransactionPreview`, `ImportPreviewPublic`, `ImportResultPublic` schemas
  - _Requirements: 5.1, 5.2, 5.3, 4.1, 4.2_

- [x] 2. Create database migration for ImportSession table
  - Run `alembic revision --autogenerate -m "Add ImportSession model"`
  - Apply migration with `alembic upgrade head`
  - _Requirements: 5.1_

- [x] 3. Implement PDF Extractor Service
  - [x] 3.1 Create `backend/app/services/__init__.py` and `backend/app/services/pdf_extractor.py`
    - Implement `RawTransaction` and `ExtractionResult` dataclasses
    - Implement `PDFExtractor.validate_file()` for PDF format and size validation
    - Implement `PDFExtractor.extract()` using pdfplumber table extraction
    - _Requirements: 1.1, 1.2, 1.6, 2.1, 2.3_

  - [x] 3.2 Write property test for file validation
    - **Property 1: File Validation Boundary**
    - **Validates: Requirements 1.1, 1.2, 1.4**

- [x] 4. Implement Statement Parser Service
  - [x] 4.1 Create `backend/app/services/statement_parser.py`
    - Implement `ParsedTransaction` dataclass
    - Implement `StatementParser.parse_date()` for Desjardins French date formats
    - Implement `StatementParser.parse_amount()` for amount and type detection
    - Implement `StatementParser.normalize_description()` for text cleanup
    - Implement `StatementParser.parse_transactions()` to process all raw transactions
    - _Requirements: 2.2, 2.4, 2.5, 3.2, 3.3, 3.5_

  - [x] 4.2 Write property test for date parsing round-trip
    - **Property 4: Date Parsing Round-Trip**
    - **Validates: Requirements 2.5**

  - [x] 4.3 Write property test for currency conversion round-trip
    - **Property 5: Currency Conversion Round-Trip**
    - **Validates: Requirements 3.2**

  - [x] 4.4 Write property test for amount sign classification
    - **Property 3: Amount Sign Classification**
    - **Validates: Requirements 2.4, 3.3**

  - [x] 4.5 Write property test for description normalization idempotence
    - **Property 6: Description Normalization Idempotence**
    - **Validates: Requirements 3.5**

- [x] 5. Implement Transaction Importer Service
  - [x] 5.1 Create `backend/app/services/transaction_importer.py`
    - Implement `ImportResult` dataclass
    - Implement `TransactionImporter.validate_transaction()` for field validation
    - Implement `TransactionImporter.import_transactions()` with atomic persistence
    - _Requirements: 3.1, 3.4, 3.6, 4.8, 5.1, 5.4, 6.3_

  - [x] 5.2 Write property test for transaction field completeness
    - **Property 2: Transaction Field Completeness**
    - **Validates: Requirements 2.2, 3.1**

  - [x] 5.3 Write property test for statement date association
    - **Property 7: Statement Date Association**
    - **Validates: Requirements 3.6**

  - [x] 5.4 Write property test for data consistency on failure
    - **Property 12: Data Consistency on Failure**
    - **Validates: Requirements 6.3**

- [x] 6. Checkpoint - Ensure all service tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Import CRUD operations
  - Add import session CRUD functions to `backend/app/crud.py`
    - `create_import_session()`
    - `get_import_session()`
    - `get_import_sessions()`
    - `update_import_session()`
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [x] 8. Implement Import API routes
  - [x] 8.1 Create `backend/app/api/routes/imports.py`
    - Implement `POST /imports/upload` endpoint for PDF upload and extraction
    - Implement `POST /imports/{id}/confirm` endpoint for import confirmation
    - Implement `POST /imports/{id}/reject` endpoint for import rejection
    - Implement `GET /imports` endpoint for import history
    - Implement `GET /imports/{id}` endpoint for import details
    - _Requirements: 1.3, 1.5, 4.1, 4.4, 4.7, 5.2, 5.3_

  - [x] 8.2 Register import routes in `backend/app/api/main.py`
    - Add `from app.api.routes import imports`
    - Add `api_router.include_router(imports.router)`
    - _Requirements: All API requirements_

  - [x] 8.3 Write property test for preview data completeness
    - **Property 8: Preview Data Completeness**
    - **Validates: Requirements 4.2, 4.3**

  - [x] 8.4 Write property test for total validation consistency
    - **Property 9: Total Validation Consistency**
    - **Validates: Requirements 4.5, 4.6**

- [x] 9. Implement import persistence logic
  - [x] 9.1 Add temporary file storage handling in upload endpoint
    - Store uploaded PDF temporarily during preview phase
    - Clean up temporary files after confirm/reject
    - _Requirements: 1.3, 4.9_

  - [x] 9.2 Write property test for import persistence atomicity
    - **Property 10: Import Persistence Atomicity**
    - **Validates: Requirements 4.8, 4.9**

  - [x] 9.3 Write property test for import session tracking
    - **Property 11: Import Session Tracking**
    - **Validates: Requirements 5.1, 5.3, 5.4**

- [ ] 10. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Add error handling and edge cases
  - [ ] 11.1 Add error classes to `backend/app/api/errors.py`
    - Add import-specific error messages and helper functions
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ] 11.2 Implement partial extraction handling
    - Return successfully extracted transactions when some fail
    - Include warnings in preview response
    - _Requirements: 6.4_

- [ ] 12. Regenerate frontend API client
  - Run `npm run generate-client` in frontend directory
  - Verify new import endpoints are available in generated client
  - _Requirements: All frontend integration_

- [ ] 13. Final checkpoint - Full integration test
  - Ensure all tests pass, ask the user if questions arise.
  - Test full flow: upload → preview → confirm
  - Test rejection flow: upload → preview → reject
  - Verify import history displays correctly

## Notes

- All property-based tests are required for comprehensive coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- The existing `source_file` and `statement_date` fields on Transaction model will be used for linking
