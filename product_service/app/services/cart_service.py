# app/services/cart_service.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.cart import CartItem as CartItemModel
from app.db.models.product import Product as ProductModel
from app.schemas.cart import CartItemCreateUpdate
from fastapi import HTTPException, status


def _get_cart_item(db: Session, user_id: str, product_id: int) -> Optional[CartItemModel]:
    return db.query(CartItemModel).filter(
        CartItemModel.user_id == user_id,
        CartItemModel.product_id == product_id
    ).first()


def add_item_to_cart(db: Session, user_id: str, item_in: CartItemCreateUpdate) -> CartItemModel:
    product = db.query(ProductModel).filter(ProductModel.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if not product.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is not available")

    db_cart_item = _get_cart_item(db, user_id=user_id, product_id=item_in.product_id)

    if db_cart_item:
        new_quantity = db_cart_item.quantity + item_in.quantity
        if new_quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product '{product.name}'. Available: {product.stock}"
            )
        db_cart_item.quantity = new_quantity
    else:
        if item_in.quantity > product.stock:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product '{product.name}'. Available: {product.stock}"
            )
        db_cart_item = CartItemModel(
            user_id=user_id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(db_cart_item)

    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def get_user_cart_items(db: Session, user_id: str) -> List[CartItemModel]:
    return db.query(CartItemModel).filter(CartItemModel.user_id == user_id).all()

def update_cart_item_quantity(db: Session, user_id: str, item_update: CartItemCreateUpdate) -> Optional[CartItemModel]:
    db_cart_item = _get_cart_item(db, user_id=user_id, product_id=item_update.product_id)
    if not db_cart_item:
        return None 

    product = db_cart_item.product 
    if item_update.quantity > product.stock:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough stock for product '{product.name}'. Available: {product.stock}"
        )

    db_cart_item.quantity = item_update.quantity
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def remove_item_from_cart(db: Session, user_id: str, product_id: int) -> Optional[CartItemModel]:
    db_cart_item = _get_cart_item(db, user_id=user_id, product_id=product_id)
    if not db_cart_item:
        return None 

    db.delete(db_cart_item)
    db.commit()
    return db_cart_item 

def clear_cart(db: Session, user_id: str) -> int:
    deleted_count = db.query(CartItemModel).filter(CartItemModel.user_id == user_id).delete()
    db.commit()
    return deleted_count