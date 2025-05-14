# app/schemas/address.py
from pydantic import BaseModel, Field
from typing import Optional
from app.db.models.address import AddressType

class AddressBase(BaseModel):
    street: str = Field(..., max_length=100)
    city: str = Field(..., max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: str = Field(..., max_length=20)
    country: str = Field("Türkiye", max_length=50)
    address_type: AddressType # Enum tipini kullanıyoruz

class AddressCreate(AddressBase):
    pass 

class AddressUpdate(BaseModel):
    street: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)
    address_type: Optional[AddressType] = None


class Address(AddressBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True