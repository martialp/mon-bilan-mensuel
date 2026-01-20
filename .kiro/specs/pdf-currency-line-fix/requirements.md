# Requirements Document

## Introduction

This document specifies the requirements for fixing PDF import misalignment caused by foreign currency conversion lines in Desjardins Mastercard statements. When importing transactions, foreign currency transactions include an extra line in the description column (e.g., "2,18 EURO TX: 1.527522") that shows the original currency amount and exchange rate. This line has no corresponding amount in the amount column, causing all subsequent transactions to be misaligned and the last transaction to be missing.

## Glossary

- **PDF_Extractor**: The service component responsible for extracting transaction data from Desjardins Mastercard PDF statements
- **Currency_Conversion_Line**: An extra description line in foreign currency transactions showing the original currency amount and exchange rate (e.g., "2,18 EURO TX: 1.527522")
- **Raw_Transaction**: A data structure containing date, description, and amount extracted from the PDF before validation
- **Multi_Line_Cell**: A table cell in the PDF that contains newline-separated values for multiple transactions

## Requirements

### Requirement 1: Currency Conversion Line Detection

**User Story:** As a user importing Mastercard statements, I want the system to detect currency conversion lines, so that they don't cause transaction misalignment.

#### Acceptance Criteria

1. WHEN the PDF_Extractor processes a description column containing a Currency_Conversion_Line, THE PDF_Extractor SHALL identify lines matching the strict pattern: a line that consists ONLY of `<amount> <currency> TX: <exchange_rate>` where amount is a decimal number, currency is a currency code, and exchange_rate is a decimal number
2. THE PDF_Extractor SHALL use the pattern `^\s*\d+[,\.]\d{2}\s+[A-Z]{2,4}\s+TX:\s*\d+[,\.]\d+\s*$` to match Currency_Conversion_Lines, ensuring the entire line matches (not just a substring)
3. THE PDF_Extractor SHALL NOT match lines where the currency conversion pattern appears as part of a longer merchant description

### Requirement 2: Currency Conversion Line Filtering

**User Story:** As a user importing Mastercard statements, I want currency conversion lines to be filtered out before alignment, so that transaction amounts are correctly matched to their descriptions.

#### Acceptance Criteria

1. WHEN the PDF_Extractor encounters a Currency_Conversion_Line in the description column, THE PDF_Extractor SHALL remove that line before aligning descriptions with amounts
2. WHEN filtering Currency_Conversion_Lines, THE PDF_Extractor SHALL preserve all other description lines unchanged
3. WHEN a foreign currency transaction is processed, THE PDF_Extractor SHALL retain the merchant description and correctly associate it with the CAD amount

### Requirement 3: Transaction Alignment Correctness

**User Story:** As a user importing Mastercard statements, I want all transactions to have correct amounts after filtering, so that my financial data is accurate.

#### Acceptance Criteria

1. WHEN the PDF_Extractor processes a statement with foreign currency transactions, THE PDF_Extractor SHALL correctly align each description with its corresponding amount
2. WHEN the PDF_Extractor processes the test fixture statement, THE PDF_Extractor SHALL extract "MUSIC-A STOCKHOLM AB" with amount 20.57
3. WHEN the PDF_Extractor processes the test fixture statement, THE PDF_Extractor SHALL extract "Serv-A Paris FR" with amount 3.33
4. IF a transaction description contains "EURO TX:" or "USD TX:" or similar currency conversion text, THEN THE PDF_Extractor SHALL NOT include that text in the final transaction description

### Requirement 4: Complete Transaction Extraction

**User Story:** As a user importing Mastercard statements, I want all transactions to be extracted including the last one, so that no financial data is lost.

#### Acceptance Criteria

1. WHEN the PDF_Extractor processes a statement, THE PDF_Extractor SHALL extract all transactions including the last expense transaction
2. WHEN the PDF_Extractor processes the test fixture statement, THE PDF_Extractor SHALL extract "RESTAURANT AAA___ VILLE-D QC" with amount 41.40
3. WHEN the PDF_Extractor processes the test fixture statement, THE PDF_Extractor SHALL extract exactly 83 expense transactions

### Requirement 5: Backward Compatibility

**User Story:** As a user importing Mastercard statements, I want the fix to not break extraction of statements without foreign currency transactions, so that existing functionality is preserved.

#### Acceptance Criteria

1. WHEN the PDF_Extractor processes a statement without Currency_Conversion_Lines, THE PDF_Extractor SHALL extract transactions using the existing logic unchanged
2. WHEN the PDF_Extractor processes a statement with only domestic transactions, THE PDF_Extractor SHALL produce identical results to the previous implementation
