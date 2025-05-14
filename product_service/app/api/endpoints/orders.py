# app/api/endpoints/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas import order as order_schema 
from app.services import order_service          
from app.db.database import get_db
from app.core.auth import get_current_user_subject 

router = APIRouter()

@router.post(
    "/",
    response_model=order_schema.Order, 
    status_code=status.HTTP_201_CREATED,
    summary="Create an order from the shopping cart",
    description="Creates a new order using the items currently in the user's shopping cart. Clears the cart afterwards."
)
def create_order(
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject) 
):
    try:
        created_order = order_service.create_order_from_cart(db=db, user_id=current_user_sub)
        return created_order
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error creating order via API: {e}") 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create order")

@router.get(
    "/",
    response_model=List[order_schema.Order],
    summary="List user's orders",
    description="Retrieves a list of past orders for the currently authenticated user."
)
def read_user_orders(
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject),
    skip: int = 0,
    limit: int = 20 
):
    orders = order_service.get_user_orders(db=db, user_id=current_user_sub, skip=skip, limit=limit)
    return orders

@router.get(
    "/{order_id}",
    response_model=order_schema.Order,
    summary="Get specific order details",
    description="Retrieves the details of a specific order, including items. Ensures the order belongs to the current user.",
    responses={404: {"description": "Order not found"}} 
)
def read_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user_sub: str = Depends(get_current_user_subject)
):
    order = order_service.get_order_details(db=db, order_id=order_id, user_id=current_user_sub)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or not authorized")
    return order