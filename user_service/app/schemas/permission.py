# app/schemas/permission.py
from pydantic import BaseModel, Field
from typing import Optional

class PermissionBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100) 
    description: Optional[str] = Field(None, max_length=255)

class PermissionCreate(PermissionBase):
    pass


class Permission(PermissionBase):
    id: int

    class Config:
        from_attributes = True