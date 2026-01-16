"""Statement Parser Service for Desjardins Mastercard statements."""

import re
from dataclasses import dataclass
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
        Parse Desjardins date format (e.g., "15 JAN", "15 JANV") to ISO date.
        Uses statement_year to determine the full year.

        Args:
            date_str: Date string in format "DD MMM" (e.g., "15 JAN", "15 JANV")
            statement_year: The year from the statement to use for the date

        Returns:
            A date object representing the parsed date

        Raises:
            ValueError: If the date string cannot be parsed
        """
        # Normalize the string: uppercase and strip whitespace
        normalized = date_str.strip().upper()

        # Pattern: day followed by month abbreviation
        pattern = r"(\d{1,2})\s+([A-ZÉÛÔ]+)"
        match = re.match(pattern, normalized)

        if not match:
            raise ValueError(f"Invalid date format: {date_str}")

        day = int(match.group(1))
        month_str = match.group(2)

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
            amount_str: Amount string (e.g., "123,45", "1 234,56", "123.45-", "-123,45")

        Returns:
            Tuple of (amount_cents, transaction_type).
            - Positive amounts (credits/payments) -> income
            - Negative amounts (purchases/debits) -> expense

        Raises:
            ValueError: If the amount string cannot be parsed
        """
        # Normalize the string
        normalized = amount_str.strip()

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

        # Determine transaction type based on sign
        # In Desjardins statements:
        # - Negative amounts (purchases/debits) are expenses
        # - Positive amounts (payments/credits) are income
        if is_negative:
            transaction_type = TransactionType.EXPENSE
        else:
            transaction_type = TransactionType.INCOME

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
