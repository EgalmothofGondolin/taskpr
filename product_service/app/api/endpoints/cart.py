# app/api/endpoints/cart.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from app.schemas import cart as cart_schema 
from app.services import cart_service          
from app.db.database import get_db
from app.core.auth import get_current_user_subject 

router = APIRouter()

@router.post(
    "/items",
    response_model=cart_schema.CartItem,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart or update quantity"
)
def add_or_update_cart_item(
    item_in: cart_schema.CartItemCreateUpdate, 
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject) 
):
    try:
        cart_item = cart_service.add_item_to_cart(db=db, user_id=current_user_sub, item_in=item_in)
        return cart_item
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error adding item to cart: {e}") # Loglama
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not add item to cart")


@router.get(
    "/",
    response_model=cart_schema.Cart,
    summary="Get current user's shopping cart"
)
def read_cart(
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject)
):
    cart_items = cart_service.get_user_cart_items(db=db, user_id=current_user_sub)

    total_items_count = sum(item.quantity for item in cart_items)
    total_cart_price = sum(item.product.price * item.quantity for item in cart_items)

    return cart_schema.Cart(
        items=cart_items,
        total_items=total_items_count,
        total_price=round(total_cart_price, 2)
    )

@router.put(
    "/items/{product_id}", 
    response_model=cart_schema.CartItem,
    summary="Update item quantity in cart",
    responses={404: {"description": "Item not found in cart"}}
)
def update_cart_item(
    product_id: int,
    item_update: cart_schema.CartItemCreateUpdate, 
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject)
):
    item_update.product_id = product_id

    try:
        updated_item = cart_service.update_cart_item_quantity(db=db, user_id=current_user_sub, item_update=item_update)
        if updated_item is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart for this user")
        return updated_item
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error updating cart item: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update cart item")

@router.delete(
    "/items/{product_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
    responses={404: {"description": "Item not found in cart"}}
)
def remove_cart_item(
    product_id: int,
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject)
):
    deleted_item = cart_service.remove_item_from_cart(db=db, user_id=current_user_sub, product_id=product_id)
    if deleted_item is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart for this user")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear the entire cart"
)
def clear_user_cart(
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject)
):
    cart_service.clear_cart(db=db, user_id=current_user_sub)
    return Response(status_code=status.HTTP_204_NO_CONTENT)