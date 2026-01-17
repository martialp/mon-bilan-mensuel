"""PDF Extractor Service for Desjardins Mastercard statements."""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pdfplumber


@dataclass
class RawTransaction:
    """Raw transaction data extracted from PDF before validation."""

    date_str: str
    description: str
    amount_str: str


@dataclass
class ExtractionResult:
    """Result of PDF extraction."""

    statement_date: date | None = None
    statement_total_cents: int | None = None
    transactions: list[RawTransaction] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = False


class PDFExtractor:
    """Extracts transaction data from Desjardins Mastercard PDF statements."""

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

    # French month abbreviations used by Desjardins
    MONTH_MAP = {
        "JAN": 1,
        "JANV": 1,
        "FÉV": 2,
        "FEVR": 2,
        "FEV": 2,
        "MAR": 3,
        "MARS": 3,
        "AVR": 4,
        "AVRI": 4,
        "MAI": 5,
        "JUN": 6,
        "JUIN": 6,
        "JUL": 7,
        "JUIL": 7,
        "AOÛ": 8,
        "AOUT": 8,
        "AOU": 8,
        "SEP": 9,
        "SEPT": 9,
        "OCT": 10,
        "NOV": 11,
        "DÉC": 12,
        "DEC": 12,
    }

    def validate_file(self, file_path: Path) -> tuple[bool, str | None]:
        """
        Validate PDF file format and size.
        Returns (is_valid, error_message).
        """
        if not file_path.exists():
            return False, "File does not exist"

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            return False, f"File exceeds {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB limit"

        # Check file extension
        if file_path.suffix.lower() != ".pdf":
            return False, "Only PDF files are supported"

        # Try to open as PDF to validate format
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    return False, "PDF file has no pages"
        except Exception:
            return False, "Unable to read PDF file"

        return True, None

    def _parse_statement_date(self, text: str) -> date | None:
        """Extract statement date from PDF header text."""
        # Look for patterns like "RELEVÉ DU 15 JANVIER 2025" or "15 JANVIER 2025"
        # Also handles abbreviated months like "15 JANV 2025"
        pattern = r"(\d{1,2})\s+([A-ZÉÛÔ]+)\s+(\d{4})"
        match = re.search(pattern, text.upper())
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3))

            # Try to match month
            for abbrev, month_num in self.MONTH_MAP.items():
                if month_str.startswith(abbrev):
                    try:
                        return date(year, month_num, day)
                    except ValueError:
                        continue
        return None

    def _parse_statement_total(self, text: str) -> int | None:
        """Extract statement total from PDF text."""
        # Look for patterns like "NOUVEAU SOLDE 1 234,56 $" or "SOLDE 1234,56$"
        patterns = [
            r"NOUVEAU\s+SOLDE\s*[:\s]*([0-9\s]+[,\.]\d{2})\s*\$?",
            r"SOLDE\s+(?:AU|DU|COURANT)[^0-9]*([0-9\s]+[,\.]\d{2})\s*\$?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                amount_str = match.group(1)
                # Remove spaces and convert comma to dot
                amount_str = amount_str.replace(" ", "").replace(",", ".")
                try:
                    return int(float(amount_str) * 100)
                except ValueError:
                    continue
        return None

    def _extract_transactions_from_table(
        self, table: list[list[str | None]]
    ) -> list[RawTransaction]:
        """Extract transactions from a pdfplumber table.
        
        Handles two formats:
        1. Standard format: each row is a separate transaction
        2. Desjardins format: columns contain newline-separated values for multiple transactions
        """
        transactions = []

        for row in table:
            if not row or len(row) < 3:
                continue

            # Skip header rows
            first_cell = str(row[0] or "").strip().upper()
            if any(header in first_cell for header in ("DATE", "TRANSACTION", "J M")):
                continue
            
            # Skip rows that start with card holder info
            if "CARTE" in first_cell or "TRANSACTIONS" in first_cell:
                continue

            # Get the raw cell values
            date_col = str(row[0] or "").strip()
            
            # For Desjardins format, description is in column index 2 (after date d'inscription)
            # and amount is in the last column
            if len(row) >= 5:
                # Desjardins format: [date_transaction, date_inscription, description, bonidollars, montant]
                description_col = str(row[2] or "").strip()
                amount_col = str(row[-1] or "").strip()
            else:
                # Standard format: [date, description, amount]
                description_col = str(row[1] or "").strip() if len(row) > 1 else ""
                amount_col = str(row[-1] or "").strip()

            # Validate date format (should start with digits)
            if not date_col or not date_col[0].isdigit():
                continue

            # Skip if no amount
            if not amount_col:
                continue

            # Check if this is a multi-line cell (Desjardins format)
            # where each column contains newline-separated values
            date_lines = date_col.split("\n")
            description_lines = description_col.split("\n")
            amount_lines = amount_col.split("\n")

            # If we have multiple lines, extract each transaction
            if len(date_lines) > 1 and len(amount_lines) > 1:
                # Desjardins multi-line format
                num_transactions = min(len(date_lines), len(amount_lines))
                
                for i in range(num_transactions):
                    date_str = date_lines[i].strip() if i < len(date_lines) else ""
                    description = description_lines[i].strip() if i < len(description_lines) else ""
                    amount_str = amount_lines[i].strip() if i < len(amount_lines) else ""
                    
                    # Skip empty entries
                    if not date_str or not amount_str:
                        continue
                    
                    # Validate date format
                    if not date_str[0].isdigit():
                        continue
                    
                    transactions.append(
                        RawTransaction(
                            date_str=date_str,
                            description=description,
                            amount_str=amount_str,
                        )
                    )
            else:
                # Single transaction per row
                transactions.append(
                    RawTransaction(
                        date_str=date_col,
                        description=description_col,
                        amount_str=amount_col,
                    )
                )

        return transactions

    def _extract_transactions_from_text(self, text: str) -> list[RawTransaction]:
        """Fallback: extract transactions from raw text using regex."""
        transactions = []

        # Pattern for transaction lines: "15 JAN Description 123,45" or "15 JAN Description 123,45-"
        pattern = r"(\d{1,2}\s+[A-ZÉÛÔ]+)\s+(.+?)\s+([0-9\s]+[,\.]\d{2}[\-]?)\s*\$?"

        for match in re.finditer(pattern, text.upper()):
            date_str = match.group(1).strip()
            description = match.group(2).strip()
            amount_str = match.group(3).strip()

            transactions.append(
                RawTransaction(
                    date_str=date_str,
                    description=description,
                    amount_str=amount_str,
                )
            )

        return transactions

    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract transaction data from a Desjardins Mastercard PDF.
        Uses pdfplumber's table extraction to identify transactions.
        """
        result = ExtractionResult()

        # Validate file first
        is_valid, error = self.validate_file(file_path)
        if not is_valid:
            result.errors.append(error or "Unknown validation error")
            return result

        try:
            with pdfplumber.open(file_path) as pdf:
                all_text = ""
                all_transactions: list[RawTransaction] = []

                for page in pdf.pages:
                    # Extract text for statement date and total
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n"

                    # Try table extraction first
                    tables = page.extract_tables()
                    for table in tables:
                        transactions = self._extract_transactions_from_table(table)
                        all_transactions.extend(transactions)

                # Parse statement date from first page text
                result.statement_date = self._parse_statement_date(all_text)

                # Parse statement total
                result.statement_total_cents = self._parse_statement_total(all_text)

                # If no transactions from tables, try text extraction
                if not all_transactions:
                    all_transactions = self._extract_transactions_from_text(all_text)

                result.transactions = all_transactions

                if not all_transactions:
                    result.errors.append(
                        "No transactions found in PDF. "
                        "Please ensure this is a valid Desjardins Mastercard statement."
                    )
                else:
                    result.success = True

        except Exception as e:
            result.errors.append(f"Failed to extract data from PDF: {str(e)}")

        return result
