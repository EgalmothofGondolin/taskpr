# app/api/endpoints/authorization.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Set

from app.schemas import permission as permission_schema 
from app.db.database import get_db
from app.core.auth import get_current_active_user 
from app.db.models.user import User as UserModel 

router = APIRouter()


@router.get(
    "/", 
    response_model=Set[str], # İzin isimlerinin seti
    summary="Get all permissions for the current user",
    description="Retrieves a distinct set of all permission names assigned to the currently authenticated user via their roles."
)
async def read_my_all_permissions( 
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user.permissions

@router.get(
    "/has-role/{role_name}",
    response_model=bool,
    summary="Check if current user has a specific role",
    description="Checks if the currently authenticated user is assigned the specified role (case-insensitive)."
)
async def check_if_user_has_role( 
    role_name: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    return any(role.name.upper() == role_name.upper() for role in current_user.roles)

@router.get(
    "/has-permission/{permission_name}",
    response_model=bool,
    summary="Check if current user has a specific permission",
    description="Checks if the currently authenticated user has the specified permission assigned through any of their roles."
)
async def check_if_user_has_permission(
    permission_name: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user.has_permission(permission_name)