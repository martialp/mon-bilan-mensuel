"""Transaction Importer Service for importing parsed transactions into the database."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlmodel import Session

from app.models import (
    ImportSession,
    ImportSessionCreate,
    ImportStatus,
    Transaction,
    TransactionCreate,
    TransactionStatus,
)
from app.services.statement_parser import ParsedTransaction


@dataclass
class ImportResult:
    """Result of import operation."""

    success: bool
    import_session_id: UUID | None
    transactions_imported: int
    errors: list[str]


class TransactionImporter:
    """Imports validated transactions into the database."""

    def validate_transaction(
        self, transaction: ParsedTransaction
    ) -> tuple[bool, str | None]:
        """
        Validate a single transaction has all required fields.

        Args:
            transaction: A parsed transaction to validate

        Returns:
            Tuple of (is_valid, error_message).
            - is_valid: True if the transaction has all required fields
            - error_message: Description of validation failure, or None if valid
        """
        errors: list[str] = []

        # Check date is not None
        if transaction.date_transaction is None:
            errors.append("Transaction date is required")

        # Check description is not empty
        if not transaction.description or not transaction.description.strip():
            errors.append("Transaction description is required and cannot be empty")

        # Check amount is positive (non-zero)
        if transaction.amount_cents is None or transaction.amount_cents <= 0:
            errors.append("Transaction amount must be a positive integer (in cents)")

        # Check transaction type is valid
        if transaction.transaction_type is None:
            errors.append("Transaction type is required")

        if errors:
            return False, "; ".join(errors)

        return True, None

    def import_transactions(
        self,
        session: Session,
        transactions: list[ParsedTransaction],
        account_id: UUID,
        source_file: str,
        statement_date: date,
    ) -> ImportResult:
        """
        Import all transactions atomically.

        Creates ImportSession record and links all transactions.
        Rolls back on any error to maintain data consistency.

        Args:
            session: Database session
            transactions: List of parsed transactions to import
            account_id: Target account ID for all transactions
            source_file: Name of the source PDF file
            statement_date: Statement date to associate with all transactions

        Returns:
            ImportResult with success status, session ID, count, and any errors
        """
        errors: list[str] = []

        # Validate all transactions first
        for i, txn in enumerate(transactions):
            is_valid, error_msg = self.validate_transaction(txn)
            if not is_valid:
                errors.append(f"Transaction {i + 1}: {error_msg}")

        if errors:
            return ImportResult(
                success=False,
                import_session_id=None,
                transactions_imported=0,
                errors=errors,
            )

        try:
            # Calculate total for the import session
            calculated_total_cents = sum(
                txn.amount_cents
                if txn.transaction_type.value == "income"
                else -txn.amount_cents
                for txn in transactions
            )

            # Create import session
            import_session_data = ImportSessionCreate(
                file_name=source_file,
                account_id=account_id,
                statement_date=statement_date,
                calculated_total_cents=calculated_total_cents,
            )
            import_session = ImportSession.model_validate(import_session_data.model_dump())
            session.add(import_session)
            session.flush()  # Get the ID without committing

            # Create all transactions
            created_transactions: list[Transaction] = []
            for txn in transactions:
                transaction_create = TransactionCreate(
                    date_transaction=txn.date_transaction,
                    description=txn.description,
                    amount_cents=txn.amount_cents,
                    type=txn.transaction_type,
                    account_id=account_id,
                    source_file=source_file,
                    statement_date=statement_date,
                )
                db_transaction = Transaction.model_validate(
                    transaction_create.model_dump()
                )
                db_transaction.status = TransactionStatus.AUTO
                session.add(db_transaction)
                created_transactions.append(db_transaction)

            # Update import session with transaction count and status
            import_session.transaction_count = len(created_transactions)
            import_session.status = ImportStatus.COMPLETED
            import_session.completed_at = datetime.utcnow()
            session.add(import_session)

            # Commit all changes atomically
            session.commit()
            session.refresh(import_session)

            return ImportResult(
                success=True,
                import_session_id=import_session.id,
                transactions_imported=len(created_transactions),
                errors=[],
            )

        except Exception as e:
            # Rollback on any error to maintain data consistency
            session.rollback()
            return ImportResult(
                success=False,
                import_session_id=None,
                transactions_imported=0,
                errors=[f"Import failed: {str(e)}"],
            )
