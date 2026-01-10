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
        "duplicate key" in error_str or
        "unique constraint" in error_str or
        "uniqueviolation" in error_str
    )
