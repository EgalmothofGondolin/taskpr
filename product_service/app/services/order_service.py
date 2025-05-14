# app/services/order_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.db.models.order import Order as OrderModel, OrderItem as OrderItemModel, OrderStatus
from app.db.models.product import Product as ProductModel
from app.db.models.cart import CartItem as CartItemModel

from . import cart_service 
from . import product_service 

def create_order_from_cart(db: Session, user_id: str) -> OrderModel:
    cart_items = cart_service.get_user_cart_items(db=db, user_id=user_id)

    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shopping cart is empty")

    try:
        total_amount = 0.0
        product_stock_updates = {} 

        for item in cart_items:
            product = item.product 
            if not product: 
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item.product_id} associated with cart item ID {item.id} no longer exists."
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is not available for purchase."
                )
            if item.quantity > product.stock:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product '{product.name}'. Requested: {item.quantity}, Available: {product.stock}"
                )

            total_amount += product.price * item.quantity
            product_stock_updates[product.id] = item.quantity

        db_order = OrderModel(
            user_id=user_id,
            total_amount=round(total_amount, 2),
            status=OrderStatus.PENDING 
        )
        db.add(db_order)
        db.flush() 

        order_items_to_add = []
        for item in cart_items:
            order_item = OrderItemModel(
                order_id=db_order.id, 
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.product.price 
            )
            order_items_to_add.append(order_item)

        db.add_all(order_items_to_add) 

        for product_id, quantity_to_decrease in product_stock_updates.items():
            db.query(ProductModel).filter(ProductModel.id == product_id).update(
                {ProductModel.stock: ProductModel.stock - quantity_to_decrease},
                synchronize_session=False 
            )

        cart_service.clear_cart(db=db, user_id=user_id)

        db.commit()

        db.refresh(db_order) 
        _ = db_order.items 

        return db_order

    except Exception as e:
        db.rollback()
        print(f"Error creating order: {e}") # Loglama
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the order."
        )


def get_user_orders(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[OrderModel]:
    return db.query(OrderModel).filter(OrderModel.user_id == user_id)\
             .order_by(OrderModel.created_at.desc())\
             .offset(skip).limit(limit).all()

def get_order_details(db: Session, order_id: int, user_id: str) -> Optional[OrderModel]:
    order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == user_id 
    ).first()

    if order:
        _ = order.items 
        for item in order.items:
            _ = item.product 

    return order