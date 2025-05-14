# app/api/endpoints/roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.schemas import role as role_schema
from app.services import role_permission_service
from app.db.database import get_db
from app.core.auth import get_current_active_superuser

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=role_schema.Role,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role (Admin only)",
    dependencies=[Depends(get_current_active_superuser)]
)
def create_new_role(
    role_in: role_schema.RoleCreate,
    db: Session = Depends(get_db)
):
    try:
        return role_permission_service.create_role(db=db, role_in=role_in)
    except HTTPException as e:
        raise e 
    except Exception as e:
        logger.error(f"Error creating role: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create role")

@router.get(
    "/",
    response_model=List[role_schema.Role],
    summary="List all roles (Admin only)",
    dependencies=[Depends(get_current_active_superuser)]
)
def read_roles(db: Session = Depends(get_db)):
    roles = role_permission_service.get_roles(db=db)
    return roles

@router.get(
    "/{role_id}",
    response_model=role_schema.Role,
    summary="Get a specific role by ID (Admin only)",
    dependencies=[Depends(get_current_active_superuser)],
    responses={404: {"description": "Role not found"}}
)
def read_specific_role(role_id: int, db: Session = Depends(get_db)):
    db_role = role_permission_service.get_role_by_id(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return db_role

@router.put(
    "/{role_id}",
    response_model=role_schema.Role,
    summary="Update role details (Admin only)",
    description="Updates the name and/or description of a role. Does not affect permissions.",
    dependencies=[Depends(get_current_active_superuser)],
    responses={
        404: {"description": "Role not found"},
        409: {"description": "Role name already exists"}
    }
)
def update_role_name_description( 
    role_id: int,
    role_in: role_schema.RoleUpdate, 
    db: Session = Depends(get_db)
):
    """Updates a role's name and/or description."""
    try:
        updated_role = role_permission_service.update_role_details(db=db, role_id=role_id, role_in=role_in)
        if updated_role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return updated_role
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating role details: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update role details")


@router.put(
    "/{role_id}/permissions",
    response_model=role_schema.Role,
    summary="Update permissions for a role (Admin only)",
    dependencies=[Depends(get_current_active_superuser)],
    responses={404: {"description": "Role or one or more Permissions not found"}}
)
def update_permissions_for_role( 
    role_id: int,
    permissions_in: role_schema.RolePermissionUpdate,
    db: Session = Depends(get_db)
):
    try:
        updated_role = role_permission_service.update_role_permissions(
            db=db, role_id=role_id, permission_ids=permissions_in.permission_ids
        )
        if updated_role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found when updating permissions")
        return updated_role
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating role permissions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update role permissions")

