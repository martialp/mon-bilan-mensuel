# Implementation Plan: PDF Currency Line Fix

## Overview

This plan implements the fix for PDF import misalignment caused by foreign currency conversion lines in Desjardins Mastercard statements. The approach is test-driven: write failing tests first, then implement the fix.

## Tasks

- [ ] 1. Create failing tests for currency conversion line detection
  - [x] 1.1 Add unit tests that verify specific currency conversion lines are detected
    - Test lines like "2,18 EURO TX: 1.527522" and "15,00 USD TX: 1.345678"
    - Test that non-currency lines are NOT detected
    - Test edge cases: empty lines, partial matches, substring matches
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 1.2 Add property test for currency line detection
    - **Property 1: Currency Conversion Line Detection Accuracy**
    - Generate valid currency lines with Hypothesis → assert detected
    - Generate invalid lines → assert not detected
    - **Validates: Requirements 1.1, 1.2, 1.3**

- [ ] 2. Implement currency conversion line detection
  - [x] 2.1 Add `_is_currency_conversion_line` method to PDFExtractor
    - Implement regex pattern `^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$`
    - Return True only for exact full-line matches
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Checkpoint - Verify detection tests pass
  - Run `docker compose exec backend pytest tests/services/test_pdf_extractor.py -v -k "currency"` 
  - Ensure all detection tests pass before proceeding

- [ ] 4. Create failing tests for filtering and alignment
  - [x] 4.1 Add unit tests for filtering behavior
    - Test that currency lines are removed from description lists
    - Test that non-currency lines are preserved in order
    - _Requirements: 2.1, 2.2_
  
  - [x] 4.2 Add property test for filtering preservation
    - **Property 2: Currency Line Filtering Preserves Non-Currency Lines**
    - Generate mixed lists → assert non-currency lines preserved
    - **Validates: Requirements 2.1, 2.2**

  - [x] 4.3 Add fixture-based tests for correct extraction
    - Test MUSIC-A STOCKHOLM AB has amount 20.57
    - Test Serv-A Paris FR has amount 3.33
    - Test RESTAURANT AAA___ VILLE-D QC has amount 41.40
    - Test total expense transactions = 83
    - Test no description contains "EURO TX:" or "USD TX:"
    - _Requirements: 3.2, 3.3, 4.2, 4.3, 3.4_

- [ ] 5. Implement filtering and fix alignment
  - [x] 5.1 Add `_filter_currency_conversion_lines` method to PDFExtractor
    - Filter out lines where `_is_currency_conversion_line` returns True
    - Preserve order of remaining lines
    - _Requirements: 2.1, 2.2_
  
  - [x] 5.2 Modify `_extract_transactions_from_table` to use filtering
    - Call `_filter_currency_conversion_lines` on description_lines before alignment
    - Ensure filtered descriptions align correctly with amounts
    - _Requirements: 3.1, 4.1_

- [x] 6. Checkpoint - Verify all tests pass
  - Run `docker compose exec backend pytest tests/services/test_pdf_extractor.py -v`
  - Ensure all tests pass including fixture-based assertions

- [ ] 7. Add backward compatibility property test
  - [x] 7.1 Add property test for backward compatibility
    - **Property 4: Backward Compatibility for Domestic Transactions**
    - Generate lists with no currency lines → assert output equals input
    - **Validates: Requirements 5.1, 5.2**

- [x] 8. Final checkpoint - Run full test suite
  - Run `docker compose exec backend pytest tests/services/test_pdf_extractor.py -v`
  - Ensure all tests pass
  - Run `docker compose exec backend bash scripts/lint.sh` to verify code quality

## Notes

- The test-driven approach ensures we verify the bug exists before fixing it
- Fixture PDF is at `backend/tests/fixtures/desjardins_mastercard_statement.pdf`
- All tests go in `backend/tests/services/test_pdf_extractor.py`
