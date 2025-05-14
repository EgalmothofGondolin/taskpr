# app/schemas/product.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

from .category import Category as CategorySchema

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be positive") 
    stock: int = Field(..., ge=0, description="Stock cannot be negative") 
    is_active: bool = True
    category_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass 

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategorySchema] = None

    class Config:
        from_attributes = True

class ProductBulkUpdateItem(BaseModel):
    id: int 
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    category_id: Optional[int] = None

class ProductBulkUpdateRequest(BaseModel):
    updates: List[ProductBulkUpdateItem] = Field(..., min_length=1) 

class ProductBulkUpdateResponse(BaseModel):
    updated_count: int