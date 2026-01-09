import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep
from app.models import Category, CategoryCreate, CategoryPublic, CategoriesPublic, CategoryUpdate, Message, Transaction

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=CategoriesPublic)
def read_categories(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve categories.
    """
    count_statement = select(func.count()).select_from(Category)
    count = session.exec(count_statement).one()
    statement = select(Category).offset(skip).limit(limit)
    categories = session.exec(statement).all()
    return CategoriesPublic(data=categories, count=count)


@router.get("/{id}", response_model=CategoryPublic)
def read_category(session: SessionDep, id: uuid.UUID) -> Any:
    """
    Get category by ID.
    """
    category = session.get(Category, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=CategoryPublic)
def create_category(
    *, session: SessionDep, category_in: CategoryCreate
) -> Any:
    """
    Create new category.
    """
    try:
        category = Category.model_validate(category_in)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    except IntegrityError as e:
        session.rollback()
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail=f"Category with name '{category_in.name}' already exists"
            )
        raise HTTPException(status_code=400, detail="Database error occurred")


@router.put("/{id}", response_model=CategoryPublic)
def update_category(
    *,
    session: SessionDep,
    id: uuid.UUID,
    category_in: CategoryUpdate,
) -> Any:
    """
    Update a category.
    """
    category = session.get(Category, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    try:
        update_dict = category_in.model_dump(exclude_unset=True)
        category.sqlmodel_update(update_dict)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    except IntegrityError as e:
        session.rollback()
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail=f"Category with name '{category_in.name}' already exists"
            )
        raise HTTPException(status_code=400, detail="Database error occurred")


@router.delete("/{id}")
def delete_category(
    session: SessionDep, id: uuid.UUID
) -> Message:
    """
    Delete a category.
    """
    category = session.get(Category, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has transactions - implement referential integrity protection
    statement = select(Transaction).where(Transaction.category_id == id)
    existing_transaction = session.exec(statement).first()
    if existing_transaction:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category with existing transactions"
        )
    
    session.delete(category)
    session.commit()
    return Message(message="Category deleted successfully")