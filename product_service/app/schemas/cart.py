# app/schemas/cart.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from .product import Product as ProductSchema 

class CartItemCreateUpdate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantity must be positive") 

class CartItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    added_at: datetime
    product: ProductSchema 

    class Config:
        from_attributes = True

class Cart(BaseModel):
    items: list[CartItem] = [] 
    total_items: int = 0      
    total_price: float = 0.0  