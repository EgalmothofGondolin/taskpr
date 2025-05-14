# app/services/category_service.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from fastapi import HTTPException, status

from app.db.models.category import Category as CategoryModel
from app.schemas.category import CategoryCreate, CategoryUpdate

def create_category(db: Session, category_in: CategoryCreate) -> CategoryModel:
    existing_category = db.query(CategoryModel).filter(CategoryModel.name == category_in.name).first()
    if existing_category:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
    db_category = CategoryModel(**category_in.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_category(db: Session, category_id: int) -> Optional[CategoryModel]:
    return db.query(CategoryModel).filter(CategoryModel.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[CategoryModel]:
    return db.query(CategoryModel).offset(skip).limit(limit).all()

def update_category(db: Session, category_id: int, category_in: CategoryUpdate) -> Optional[CategoryModel]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    update_data = category_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != db_category.name:
         existing = db.query(CategoryModel).filter(CategoryModel.name == update_data["name"]).first()
         if existing:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")

    for field, value in update_data.items():
        setattr(db_category, field, value)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> Optional[CategoryModel]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    if db_category.products: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{db_category.name}' as it has associated products. Please reassign products first."
         )

    db.delete(db_category)
    db.commit()
    return db_category