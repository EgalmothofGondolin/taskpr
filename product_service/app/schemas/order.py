# app/schemas/order.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.db.models.order import OrderStatus
from .product import Product as ProductSchema

class OrderItem(BaseModel):
    id: int
    product_id: Optional[int] 
    quantity: int
    price_at_purchase: float
    product: Optional[ProductSchema] = None 

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    pass 

class Order(BaseModel):
    id: int
    user_id: str 
    total_amount: float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItem] = [] 

    class Config:
        from_attributes = True