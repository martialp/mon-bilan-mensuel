"""Import API routes for Mastercard PDF statement imports."""

import atexit
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlmodel import func, select

from app.api.deps import SessionDep
from app.api.errors import raise_not_found
from app.models import (
    Account,
    ImportPreviewPublic,
    ImportResultPublic,
    ImportSession,
    ImportSessionCreate,
    ImportSessionPublic,
    ImportSessionsPublic,
    ImportStatus,
    Message,
    Transaction,
    TransactionCreate,
    TransactionPreview,
    TransactionStatus,
    TransactionType,
)
from app.services.pdf_extractor import PDFExtractor
from app.services.statement_parser import StatementParser

router = APIRouter(prefix="/imports", tags=["imports"])

# In-memory storage for pending imports (preview data)
# In production, this should be stored in Redis or database
_pending_imports: dict[uuid.UUID, dict[str, Any]] = {}


def _cleanup_temp_file(import_id: uuid.UUID) -> None:
    """Clean up temporary PDF file for a given import session."""
    pending_data = _pending_imports.get(import_id)
    if pending_data and "temp_file_path" in pending_data:
        temp_path = pending_data["temp_file_path"]
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass  # Best effort cleanup


def _cleanup_all_temp_files() -> None:
    """Clean up all temporary files on application shutdown."""
    for import_id in list(_pending_imports.keys()):
        _cleanup_temp_file(import_id)


# Register cleanup function for application shutdown
atexit.register(_cleanup_all_temp_files)


@router.post("/upload", response_model=ImportPreviewPublic)
async def upload_pdf(
    session: SessionDep,
    file: UploadFile = File(...),
    account_id: uuid.UUID = Query(..., description="Target account ID for imported transactions"),
) -> ImportPreviewPublic:
    """
    Upload a Mastercard PDF statement for extraction.
    Returns preview of extracted transactions for user review.
    
    Requirements: 1.3, 1.5, 4.1
    """
    # Verify that the account exists
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not found"
        )
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file to temporary location (kept during preview phase)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    try:
        # Extract data from PDF
        extractor = PDFExtractor()
        
        # Validate file
        is_valid, error_msg = extractor.validate_file(tmp_path)
        if not is_valid:
            # Clean up temp file on validation failure
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Invalid PDF file"
            )
        
        # Extract transactions
        extraction_result = extractor.extract(tmp_path)
        
        if not extraction_result.success:
            # Clean up temp file on extraction failure
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="; ".join(extraction_result.errors) or "Failed to extract transactions from PDF"
            )
        
        # Parse extracted transactions
        parser = StatementParser()
        warnings: list[str] = []
        
        # Use statement date from extraction or default to today
        statement_date = extraction_result.statement_date
        if not statement_date:
            statement_date = datetime.utcnow().date()
            warnings.append("Could not extract statement date from PDF, using current date")
        
        try:
            parsed_transactions = parser.parse_transactions(
                extraction_result.transactions,
                statement_date
            )
        except ValueError as e:
            # Clean up temp file on parse failure
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse transactions: {str(e)}"
            )
        
        if not parsed_transactions:
            # Clean up temp file when no transactions found
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No valid transactions found in PDF"
            )
        
        # Calculate total from parsed transactions
        calculated_total_cents = sum(
            txn.amount_cents if txn.transaction_type == TransactionType.INCOME else -txn.amount_cents
            for txn in parsed_transactions
        )
        
        # Check if totals match
        statement_total_cents = extraction_result.statement_total_cents
        totals_match = (
            statement_total_cents is not None and
            statement_total_cents == calculated_total_cents
        )
        
        if statement_total_cents is not None and not totals_match:
            warnings.append(
                f"Statement total ({statement_total_cents / 100:.2f}) does not match "
                f"calculated total ({calculated_total_cents / 100:.2f})"
            )
        
        # Create import session in PENDING status
        import_session_data = ImportSessionCreate(
            file_name=file.filename or "unknown.pdf",
            account_id=account_id,
            statement_date=statement_date,
            statement_total_cents=statement_total_cents,
            calculated_total_cents=calculated_total_cents,
        )
        import_session = ImportSession.model_validate(import_session_data.model_dump())
        import_session.transaction_count = len(parsed_transactions)
        import_session.status = ImportStatus.PENDING
        session.add(import_session)
        session.commit()
        session.refresh(import_session)
        
        # Store parsed transactions and temp file path for later confirmation
        _pending_imports[import_session.id] = {
            "transactions": parsed_transactions,
            "account_id": account_id,
            "source_file": file.filename or "unknown.pdf",
            "statement_date": statement_date,
            "temp_file_path": str(tmp_path),  # Store temp file path for cleanup
        }
        
        # Build preview response
        transaction_previews = [
            TransactionPreview(
                date_transaction=txn.date_transaction,
                description=txn.description,
                amount_cents=txn.amount_cents,
                type=txn.transaction_type,
            )
            for txn in parsed_transactions
        ]
        
        return ImportPreviewPublic(
            import_id=import_session.id,
            file_name=file.filename or "unknown.pdf",
            statement_date=statement_date,
            statement_total_cents=statement_total_cents,
            calculated_total_cents=calculated_total_cents,
            totals_match=totals_match,
            transactions=transaction_previews,
            warnings=warnings,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already handled cleanup above)
        raise
    except Exception as e:
        # Clean up temp file on unexpected error
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during PDF processing: {str(e)}"
        )


@router.post("/{import_id}/confirm", response_model=ImportResultPublic)
def confirm_import(
    import_id: uuid.UUID,
    session: SessionDep,
) -> ImportResultPublic:
    """
    Confirm and persist extracted transactions.
    
    Requirements: 4.7, 4.8
    """
    # Get import session
    import_session = session.get(ImportSession, import_id)
    if not import_session:
        raise_not_found("import session")
    
    # Check status
    if import_session.status != ImportStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Import has already been {import_session.status.value}"
        )
    
    # Get pending import data
    pending_data = _pending_imports.get(import_id)
    if not pending_data:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Import preview has expired. Please upload the PDF again."
        )
    
    try:
        # Create all transactions
        transactions_created = 0
        for txn in pending_data["transactions"]:
            transaction_create = TransactionCreate(
                date_transaction=txn.date_transaction,
                description=txn.description,
                amount_cents=txn.amount_cents,
                type=txn.transaction_type,
                account_id=pending_data["account_id"],
                source_file=pending_data["source_file"],
                statement_date=pending_data["statement_date"],
            )
            db_transaction = Transaction.model_validate(transaction_create.model_dump())
            db_transaction.status = TransactionStatus.AUTO
            session.add(db_transaction)
            transactions_created += 1
        
        # Update import session
        import_session.status = ImportStatus.COMPLETED
        import_session.completed_at = datetime.utcnow()
        import_session.transaction_count = transactions_created
        session.add(import_session)
        
        # Commit all changes atomically
        session.commit()
        
        # Clean up temporary file after successful import
        _cleanup_temp_file(import_id)
        
        # Clean up pending data
        del _pending_imports[import_id]
        
        return ImportResultPublic(
            import_session_id=import_id,
            transactions_imported=transactions_created,
            success=True,
        )
        
    except Exception as e:
        session.rollback()
        
        # Update import session with error
        import_session.status = ImportStatus.FAILED
        import_session.error_message = str(e)[:1000]
        import_session.completed_at = datetime.utcnow()
        session.add(import_session)
        session.commit()
        
        # Clean up temporary file on failure
        _cleanup_temp_file(import_id)
        
        # Clean up pending data on failure
        if import_id in _pending_imports:
            del _pending_imports[import_id]
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import transactions: {str(e)}"
        )


@router.post("/{import_id}/reject", response_model=Message)
def reject_import(
    import_id: uuid.UUID,
    session: SessionDep,
) -> Message:
    """
    Reject import and discard extracted data.
    
    Requirements: 4.7, 4.9
    """
    # Get import session
    import_session = session.get(ImportSession, import_id)
    if not import_session:
        raise_not_found("import session")
    
    # Check status
    if import_session.status != ImportStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Import has already been {import_session.status.value}"
        )
    
    # Update import session
    import_session.status = ImportStatus.REJECTED
    import_session.completed_at = datetime.utcnow()
    session.add(import_session)
    session.commit()
    
    # Clean up temporary file after rejection
    _cleanup_temp_file(import_id)
    
    # Clean up pending data
    if import_id in _pending_imports:
        del _pending_imports[import_id]
    
    return Message(message="Import rejected successfully")


@router.get("/", response_model=ImportSessionsPublic)
def list_imports(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    account_id: uuid.UUID | None = Query(None, description="Filter by account ID"),
    status_filter: ImportStatus | None = Query(None, alias="status", description="Filter by import status"),
) -> ImportSessionsPublic:
    """
    List all import sessions with status and statistics.
    
    Requirements: 5.2
    """
    # Build query
    statement = select(ImportSession)
    
    # Apply filters
    if account_id:
        statement = statement.where(ImportSession.account_id == account_id)
    if status_filter:
        statement = statement.where(ImportSession.status == status_filter)
    
    # Get count
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()
    
    # Apply pagination and ordering
    statement = statement.order_by(ImportSession.created_at.desc()).offset(skip).limit(limit)
    import_sessions = session.exec(statement).all()
    
    return ImportSessionsPublic(data=list(import_sessions), count=count)


@router.get("/{import_id}", response_model=ImportSessionPublic)
def get_import(
    import_id: uuid.UUID,
    session: SessionDep,
) -> ImportSessionPublic:
    """
    Get import session details.
    
    Requirements: 5.3
    """
    import_session = session.get(ImportSession, import_id)
    if not import_session:
        raise_not_found("import session")
    
    return import_session
