# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Set
from datetime import datetime
from .role import Role
from .permission import Permission


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username (3-50 chars)")
    email: EmailStr = Field(..., description="Valid and unique email address")
    first_name: Optional[str] = Field(None, max_length=50, description="User's first name (optional)")
    last_name: Optional[str] = Field(None, max_length=50, description="User's last name (optional)")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password (min 8 chars)")

class User(UserBase):
    id: int = Field(..., description="Unique user ID")
    is_active: bool = Field(True, description="Is the user account active?")
    is_superuser: bool = Field(False, description="Is the user an administrator?")
    created_at: datetime = Field(..., description="Timestamp when the user was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp of the last update")

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=8, description="New password (if changing)")

    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    roles: List[Role] = []
    permissions: Set[str] = set() 

    class Config:
        from_attributes = True

class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8, description="The new password for the user (min 8 chars)")

class UserInDB(User):
    hashed_password: str

class UserRoleUpdate(BaseModel):
    role_ids: List[int] = Field(..., description="List of Role IDs to assign to the user")

class UserPasswordUpdate(BaseModel):
    current_password: str = Field(..., description="User's current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")

