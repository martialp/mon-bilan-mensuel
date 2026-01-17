"""Statement Parser Service for Desjardins Mastercard statements."""

import re
from dataclasses import dataclass, field
from datetime import date

from app.models import TransactionType
from app.services.pdf_extractor import RawTransaction


@dataclass
class ParsedTransaction:
    """Parsed and validated transaction ready for import."""

    date_transaction: date
    description: str
    amount_cents: int
    transaction_type: TransactionType


@dataclass
class ParseResult:
    """Result of parsing transactions with partial failure support."""

    transactions: list[ParsedTransaction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failed_count: int = 0


class StatementParser:
    """Parses raw PDF data into structured transactions."""

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

    def parse_date(self, date_str: str, statement_year: int) -> date:
        """
        Parse Desjardins date format to ISO date.
        
        Supports two formats:
        - "DD MMM" (e.g., "15 JAN", "15 JANV") - month as text
        - "DD MM" (e.g., "17 12", "03 01") - month as number
        
        Uses statement_year to determine the full year.

        Args:
            date_str: Date string in format "DD MMM" or "DD MM"
            statement_year: The year from the statement to use for the date

        Returns:
            A date object representing the parsed date

        Raises:
            ValueError: If the date string cannot be parsed
        """
        # Normalize the string: uppercase and strip whitespace
        normalized = date_str.strip().upper()

        # First try: numeric format "DD MM" (e.g., "17 12")
        numeric_pattern = r"^(\d{1,2})\s+(\d{1,2})$"
        numeric_match = re.match(numeric_pattern, normalized)
        
        if numeric_match:
            day = int(numeric_match.group(1))
            month = int(numeric_match.group(2))
            
            # Validate month range
            if month < 1 or month > 12:
                raise ValueError(f"Invalid month number: {month}")
            
            try:
                return date(statement_year, month, day)
            except ValueError as e:
                raise ValueError(f"Invalid date: {date_str} for year {statement_year}") from e

        # Second try: text format "DD MMM" (e.g., "15 JAN")
        text_pattern = r"(\d{1,2})\s+([A-ZÉÛÔ]+)"
        text_match = re.match(text_pattern, normalized)

        if not text_match:
            raise ValueError(f"Invalid date format: {date_str}")

        day = int(text_match.group(1))
        month_str = text_match.group(2)

        # Find the month number
        month = None
        for abbrev, month_num in self.MONTH_MAP.items():
            if month_str.startswith(abbrev):
                month = month_num
                break

        if month is None:
            raise ValueError(f"Unknown month abbreviation: {month_str}")

        try:
            return date(statement_year, month, day)
        except ValueError as e:
            raise ValueError(f"Invalid date: {date_str} for year {statement_year}") from e

    def parse_amount(self, amount_str: str) -> tuple[int, TransactionType]:
        """
        Parse amount string to cents and determine transaction type.

        Args:
            amount_str: Amount string (e.g., "123,45", "1 234,56", "123.45-", "-123,45", "100,00CR")

        Returns:
            Tuple of (amount_cents, transaction_type).
            - Credits (CR suffix or positive) -> income
            - Debits (no CR suffix, regular amounts) -> expense

        Raises:
            ValueError: If the amount string cannot be parsed
        """
        # Normalize the string
        normalized = amount_str.strip().upper()

        # Check for credit indicator (CR suffix means it's a credit/payment)
        is_credit = False
        if normalized.endswith("CR"):
            is_credit = True
            normalized = normalized[:-2].strip()

        # Check for negative indicator (trailing minus or leading minus)
        is_negative = False
        if normalized.endswith("-"):
            is_negative = True
            normalized = normalized[:-1]
        elif normalized.startswith("-"):
            is_negative = True
            normalized = normalized[1:]

        # Remove currency symbols and spaces
        normalized = normalized.replace("$", "").replace(" ", "").strip()

        # Handle both comma and dot as decimal separator
        # French format uses comma, but we might encounter dots
        if "," in normalized and "." in normalized:
            # Both present: assume comma is thousands separator, dot is decimal
            normalized = normalized.replace(",", "")
        elif "," in normalized:
            # Only comma: assume it's the decimal separator (French format)
            normalized = normalized.replace(",", ".")

        try:
            amount_decimal = float(normalized)
        except ValueError as e:
            raise ValueError(f"Invalid amount format: {amount_str}") from e

        # Convert to cents (integer)
        amount_cents = abs(int(round(amount_decimal * 100)))

        # Determine transaction type based on indicators
        # In Desjardins statements:
        # - CR suffix means credit/payment (income)
        # - Regular amounts are purchases/debits (expense)
        # - Negative sign also indicates expense
        if is_credit:
            transaction_type = TransactionType.INCOME
        elif is_negative:
            transaction_type = TransactionType.EXPENSE
        else:
            # Default: regular amounts without CR are expenses (purchases)
            transaction_type = TransactionType.EXPENSE

        return amount_cents, transaction_type

    def normalize_description(self, description: str) -> str:
        """
        Trim whitespace and normalize text formatting.

        This operation is idempotent: normalizing twice produces the same result.

        Args:
            description: Raw description string from PDF

        Returns:
            Normalized description string
        """
        if not description:
            return ""

        # Remove any control characters first
        normalized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", description)

        # Collapse multiple spaces into single space
        normalized = re.sub(r"\s+", " ", normalized)

        # Strip leading/trailing whitespace (must be last for idempotence)
        normalized = normalized.strip()

        return normalized

    def parse_transactions(
        self,
        raw_transactions: list[RawTransaction],
        statement_date: date,
    ) -> list[ParsedTransaction]:
        """
        Parse all raw transactions into structured format.

        Args:
            raw_transactions: List of raw transactions from PDF extraction
            statement_date: The statement date to use for year inference

        Returns:
            List of parsed transactions ready for import

        Raises:
            ValueError: If any transaction cannot be parsed
        """
        parsed: list[ParsedTransaction] = []
        statement_year = statement_date.year

        for raw in raw_transactions:
            # Parse date
            transaction_date = self.parse_date(raw.date_str, statement_year)

            # Parse amount and determine type
            amount_cents, transaction_type = self.parse_amount(raw.amount_str)

            # Normalize description
            description = self.normalize_description(raw.description)

            parsed.append(
                ParsedTransaction(
                    date_transaction=transaction_date,
                    description=description,
                    amount_cents=amount_cents,
                    transaction_type=transaction_type,
                )
            )

        return parsed

    def parse_transactions_partial(
        self,
        raw_transactions: list[RawTransaction],
        statement_date: date,
    ) -> ParseResult:
        """
        Parse all raw transactions with partial failure support.

        Unlike parse_transactions(), this method continues processing
        even when individual transactions fail to parse, returning
        successfully parsed transactions along with warnings.

        Args:
            raw_transactions: List of raw transactions from PDF extraction
            statement_date: The statement date to use for year inference

        Returns:
            ParseResult containing successfully parsed transactions,
            warnings for failed transactions, and count of failures.
        """
        result = ParseResult()
        statement_year = statement_date.year

        for i, raw in enumerate(raw_transactions):
            try:
                # Parse date
                transaction_date = self.parse_date(raw.date_str, statement_year)

                # Parse amount and determine type
                amount_cents, transaction_type = self.parse_amount(raw.amount_str)

                # Normalize description
                description = self.normalize_description(raw.description)

                result.transactions.append(
                    ParsedTransaction(
                        date_transaction=transaction_date,
                        description=description,
                        amount_cents=amount_cents,
                        transaction_type=transaction_type,
                    )
                )
            except ValueError as e:
                result.failed_count += 1
                # Create a truncated description for the warning
                desc_preview = raw.description[:30] + "..." if len(raw.description) > 30 else raw.description
                result.warnings.append(
                    f"Transaction {i + 1} could not be parsed: {str(e)} "
                    f"(date: '{raw.date_str}', desc: '{desc_preview}')"
                )

        return result
