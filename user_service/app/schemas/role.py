# app/schemas/role.py
from pydantic import BaseModel, Field
from typing import List, Optional
from .permission import Permission

class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Unique role name")
    description: Optional[str] = Field(None, max_length=255, description="Description of of the role")

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []

    class Config:
        from_attributes = True

class RolePermissionUpdate(BaseModel):
    permission_ids: List[int] = Field(..., description="List of Permission IDs to assign to the role")