"""
Error handling utilities for the API.

Provides consistent error responses and validation helpers.
"""

from typing import Any
from fastapi import HTTPException, status


class ErrorMessages:
    """Centralized error messages for consistent user feedback."""
    
    # Resource not found errors
    ACCOUNT_NOT_FOUND = "Account not found"
    CATEGORY_NOT_FOUND = "Category not found"
    TRANSACTION_NOT_FOUND = "Transaction not found"
    IMPORT_SESSION_NOT_FOUND = "Import session not found"
    
    # Validation errors
    INVALID_ACCOUNT_TYPE = "Invalid account type. Must be one of: credit_card, chequing, savings, investment, other"
    INVALID_TRANSACTION_TYPE = "Invalid transaction type. Must be one of: expense, income, transfer"
    INVALID_AMOUNT = "Amount must be a positive integer representing cents"
    MISSING_REQUIRED_FIELD = "Missing required field: {field}"
    
    # Duplicate/conflict errors
    DUPLICATE_TRANSACTION = "A transaction with the same account, date, description, amount, and statement date already exists"
    DUPLICATE_CATEGORY = "Category with name '{name}' already exists"
    
    # Referential integrity errors
    ACCOUNT_HAS_TRANSACTIONS = "Cannot delete account with existing transactions. Delete or reassign transactions first."
    CATEGORY_HAS_TRANSACTIONS = "Cannot delete category with existing transactions. Delete or reassign transactions first."
    
    # Status transition errors
    ONLY_AUTO_CAN_CONFIRM = "Only auto-categorized transactions can be confirmed. This transaction has status '{status}'."
    
    # Database errors
    DATABASE_ERROR = "A database error occurred. Please try again."
    INTEGRITY_ERROR = "Data integrity error. The operation could not be completed."
    
    # Import-specific errors (Requirements 6.1, 6.2, 6.4, 6.5)
    IMPORT_INVALID_FILE_TYPE = "Only PDF files are supported"
    IMPORT_FILE_TOO_LARGE = "File exceeds {max_size}MB limit"
    IMPORT_CORRUPTED_PDF = "Unable to read PDF file"
    IMPORT_UNSUPPORTED_FORMAT = "PDF format not recognized as Desjardins Mastercard statement"
    IMPORT_MISSING_FIELDS = "Transaction missing required data: {fields}"
    IMPORT_ALREADY_PROCESSED = "Import has already been {status}"
    IMPORT_PREVIEW_EXPIRED = "Import preview has expired. Please upload the PDF again."
    IMPORT_FAILED = "Failed to save transactions. Please try again."
    IMPORT_EXTRACTION_FAILED = "Failed to extract transactions from PDF: {details}"
    IMPORT_PARTIAL_EXTRACTION = "Some transactions could not be extracted. {count} transactions extracted successfully."
    IMPORT_NO_TRANSACTIONS = "No valid transactions found in PDF"
    IMPORT_SERVICE_UNAVAILABLE = "Import service is temporarily unavailable. Please try again later."
    IMPORT_NETWORK_TIMEOUT = "Request timed out. Please try again."


def raise_not_found(resource: str) -> None:
    """Raise a 404 HTTPException for a resource not found."""
    messages = {
        "account": ErrorMessages.ACCOUNT_NOT_FOUND,
        "category": ErrorMessages.CATEGORY_NOT_FOUND,
        "transaction": ErrorMessages.TRANSACTION_NOT_FOUND,
    }
    detail = messages.get(resource.lower(), f"{resource.capitalize()} not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_duplicate_transaction() -> None:
    """Raise a 409 HTTPException for duplicate transaction."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorMessages.DUPLICATE_TRANSACTION
    )


def raise_duplicate_category(name: str) -> None:
    """Raise a 400 HTTPException for duplicate category."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorMessages.DUPLICATE_CATEGORY.format(name=name)
    )


def raise_referential_integrity_error(resource: str) -> None:
    """Raise a 400 HTTPException for referential integrity violation."""
    messages = {
        "account": ErrorMessages.ACCOUNT_HAS_TRANSACTIONS,
        "category": ErrorMessages.CATEGORY_HAS_TRANSACTIONS,
    }
    detail = messages.get(resource.lower(), f"Cannot delete {resource} with existing references")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_invalid_status_transition(current_status: str) -> None:
    """Raise a 400 HTTPException for invalid status transition."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorMessages.ONLY_AUTO_CAN_CONFIRM.format(status=current_status)
    )


def raise_database_error(detail: str | None = None) -> None:
    """Raise a 400 HTTPException for database errors."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail or ErrorMessages.DATABASE_ERROR
    )


def is_duplicate_key_error(error: Exception) -> bool:
    """Check if an exception is a duplicate key/unique constraint violation."""
    error_str = str(error).lower()
    return (
        "unique_transaction" in error_str or
        "ix_unique_transaction" in error_str or
        "duplicate key" in error_str or
        "unique constraint" in error_str or
        "uniqueviolation" in error_str
    )


# Import-specific error helpers (Requirements 6.1, 6.2, 6.4, 6.5)

def raise_import_invalid_file_type() -> None:
    """Raise a 400 HTTPException for invalid file type during import."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorMessages.IMPORT_INVALID_FILE_TYPE
    )


def raise_import_file_too_large(max_size_mb: int = 10) -> None:
    """Raise a 400 HTTPException for file exceeding size limit."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorMessages.IMPORT_FILE_TOO_LARGE.format(max_size=max_size_mb)
    )


def raise_import_corrupted_pdf() -> None:
    """Raise a 422 HTTPException for corrupted or unreadable PDF."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=ErrorMessages.IMPORT_CORRUPTED_PDF
    )


def raise_import_unsupported_format() -> None:
    """Raise a 422 HTTPException for unsupported PDF format."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=ErrorMessages.IMPORT_UNSUPPORTED_FORMAT
    )


def raise_import_missing_fields(fields: list[str]) -> None:
    """Raise a 422 HTTPException for missing required transaction fields."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=ErrorMessages.IMPORT_MISSING_FIELDS.format(fields=", ".join(fields))
    )


def raise_import_already_processed(current_status: str) -> None:
    """Raise a 409 HTTPException for already processed import."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorMessages.IMPORT_ALREADY_PROCESSED.format(status=current_status)
    )


def raise_import_preview_expired() -> None:
    """Raise a 410 HTTPException for expired import preview."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=ErrorMessages.IMPORT_PREVIEW_EXPIRED
    )


def raise_import_failed(detail: str | None = None) -> None:
    """Raise a 500 HTTPException for import failure."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail or ErrorMessages.IMPORT_FAILED
    )


def raise_import_extraction_failed(details: str) -> None:
    """Raise a 422 HTTPException for extraction failure."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=ErrorMessages.IMPORT_EXTRACTION_FAILED.format(details=details)
    )


def raise_import_no_transactions() -> None:
    """Raise a 422 HTTPException when no transactions found in PDF."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=ErrorMessages.IMPORT_NO_TRANSACTIONS
    )


def raise_import_service_unavailable() -> None:
    """Raise a 503 HTTPException when import service is unavailable."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=ErrorMessages.IMPORT_SERVICE_UNAVAILABLE
    )


class ImportError:
    """Structured error response for import operations."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: list[str] | None = None,
        recoverable: bool = True,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.recoverable = recoverable
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


# Import error codes for structured error responses
class ImportErrorCodes:
    """Error codes for import operations."""
    INVALID_FILE_TYPE = "IMPORT_INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "IMPORT_FILE_TOO_LARGE"
    CORRUPTED_PDF = "IMPORT_CORRUPTED_PDF"
    UNSUPPORTED_FORMAT = "IMPORT_UNSUPPORTED_FORMAT"
    MISSING_FIELDS = "IMPORT_MISSING_FIELDS"
    ALREADY_PROCESSED = "IMPORT_ALREADY_PROCESSED"
    PREVIEW_EXPIRED = "IMPORT_PREVIEW_EXPIRED"
    EXTRACTION_FAILED = "IMPORT_EXTRACTION_FAILED"
    NO_TRANSACTIONS = "IMPORT_NO_TRANSACTIONS"
    IMPORT_FAILED = "IMPORT_FAILED"
    SERVICE_UNAVAILABLE = "IMPORT_SERVICE_UNAVAILABLE"
    PARTIAL_EXTRACTION = "IMPORT_PARTIAL_EXTRACTION"


def create_import_error(
    error_code: str,
    message: str,
    details: list[str] | None = None,
    recoverable: bool = True,
) -> ImportError:
    """Create a structured import error."""
    return ImportError(
        error_code=error_code,
        message=message,
        details=details,
        recoverable=recoverable,
    )
