import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import SessionDep
from app.models import Account, AccountCreate, AccountPublic, AccountsPublic, AccountUpdate, Message, Transaction

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=AccountsPublic)
def read_accounts(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve accounts.
    """
    count_statement = select(func.count()).select_from(Account)
    count = session.exec(count_statement).one()
    statement = select(Account).offset(skip).limit(limit)
    accounts = session.exec(statement).all()
    return AccountsPublic(data=accounts, count=count)


@router.get("/{id}", response_model=AccountPublic)
def read_account(session: SessionDep, id: uuid.UUID) -> Any:
    """
    Get account by ID.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=AccountPublic)
def create_account(
    *, session: SessionDep, account_in: AccountCreate
) -> Any:
    """
    Create new account.
    """
    account = Account.model_validate(account_in)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.put("/{id}", response_model=AccountPublic)
def update_account(
    *,
    session: SessionDep,
    id: uuid.UUID,
    account_in: AccountUpdate,
) -> Any:
    """
    Update an account.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    update_dict = account_in.model_dump(exclude_unset=True)
    account.sqlmodel_update(update_dict)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{id}")
def delete_account(
    session: SessionDep, id: uuid.UUID
) -> Message:
    """
    Delete an account.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if account has transactions - implement referential integrity protection
    statement = select(Transaction).where(Transaction.account_id == id)
    existing_transaction = session.exec(statement).first()
    if existing_transaction:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete account with existing transactions"
        )
    
    session.delete(account)
    session.commit()
    return Message(message="Account deleted successfully")