# app/api/endpoints/categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from app.schemas import category as category_schema
from app.services import category_service
from app.db.database import get_db
from app.core.auth import require_admin

router = APIRouter()

@router.post(
    "/",
    response_model=category_schema.Category,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (Admin only)",
    dependencies=[Depends(require_admin)]
)
def create_new_category(
    category_in: category_schema.CategoryCreate,
    db: Session = Depends(get_db)
):
    try:
        return category_service.create_category(db=db, category_in=category_in)
    except HTTPException as e:
        raise e

@router.get(
    "/",
    response_model=List[category_schema.Category],
    summary="List all categories"
)
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return category_service.get_categories(db=db, skip=skip, limit=limit)

@router.get(
    "/{category_id}",
    response_model=category_schema.Category,
    summary="Get a specific category",
    responses={404: {"description": "Category not found"}}
)
def read_category(category_id: int, db: Session = Depends(get_db)):
    db_category = category_service.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category

@router.put(
    "/{category_id}",
    response_model=category_schema.Category,
    summary="Update a category (Admin only)",
    dependencies=[Depends(require_admin)],
    responses={404: {"description": "Category not found"}, 409: {"description": "Category name already exists"}}
)
def update_existing_category(
    category_id: int,
    category_in: category_schema.CategoryUpdate,
    db: Session = Depends(get_db)
):
    try:
        updated_category = category_service.update_category(db, category_id=category_id, category_in=category_in)
        if updated_category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return updated_category
    except HTTPException as e:
        raise e

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category (Admin only)",
    dependencies=[Depends(require_admin)],
    responses={404: {"description": "Category not found"}, 400: {"description": "Category has associated products"}}
)
def delete_existing_category(category_id: int, db: Session = Depends(get_db)):
    try:
        deleted = category_service.delete_category(db, category_id=category_id)
        if deleted is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as e:
        raise e