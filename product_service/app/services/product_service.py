# app/services/product_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
import logging

from app.db.models.product import Product as ProductModel
from app.schemas.product import ProductCreate, ProductUpdate, ProductBulkUpdateItem
from app.services import category_service

logger = logging.getLogger(__name__)

def create_product(db: Session, product_in: ProductCreate) -> ProductModel:
    existing_product = db.query(ProductModel).filter(ProductModel.name == product_in.name).first()
    if existing_product:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product name already exists")

    if product_in.category_id:
        category = category_service.get_category(db, category_id=product_in.category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {product_in.category_id} not found")

    product_data = product_in.model_dump()
    db_product = ProductModel(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int) -> Optional[ProductModel]:
    return db.query(ProductModel).filter(ProductModel.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, *, is_active_filter: Optional[bool] = None):
    query = db.query(ProductModel)
    if is_active_filter is not None: 
        query = query.filter(ProductModel.is_active == is_active_filter)
    return query.offset(skip).limit(limit).all()

def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Optional[ProductModel]:
    db_product = get_product(db, product_id=product_id)
    if not db_product:
        return None

    update_data = product_in.model_dump(exclude_unset=True)

    if "category_id" in update_data and update_data["category_id"] is not None:
        category = category_service.get_category(db, category_id=update_data["category_id"])
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {update_data['category_id']} not found")

    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> Optional[ProductModel]:
    db_product = get_product(db, product_id=product_id)
    if not db_product:
        return None

    db.delete(db_product) 
    db.commit()
    return db_product 

def bulk_update_products(db: Session, updates: List[ProductBulkUpdateItem]) -> int:
    updated_count = 0
    product_ids_to_update = [item.id for item in updates]

    if not product_ids_to_update:
        return 0

    products_to_update = db.query(ProductModel).filter(ProductModel.id.in_(product_ids_to_update)).all()
    products_map = {product.id: product for product in products_to_update} 

    try:
        for item_update in updates:
            db_product = products_map.get(item_update.id)
            if not db_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {item_update.id} not found for bulk update."
                )

            update_data_with_values = {
                k: v for k, v in item_update.model_dump(exclude={'id'}).items() if v is not None
            }

            if not update_data_with_values:
                continue
            
            if "category_id" in update_data_with_values and update_data_with_values["category_id"] is not None:
                category = category_service.get_category(db, category_id=update_data_with_values["category_id"])
                if not category:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {update_data_with_values['category_id']} not found")

            for field, value in update_data_with_values.items():
                setattr(db_product, field, value)

            db.add(db_product) 
            updated_count += 1

        db.commit() 

    except Exception as e:
        db.rollback() 
        logger.error(f"Error during bulk product update: {e}", exc_info=True) 
        if isinstance(e, HTTPException): 
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Bulk update failed.")

    return updated_count