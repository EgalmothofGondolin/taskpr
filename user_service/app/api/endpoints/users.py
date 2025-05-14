# app/api/endpoints/users.py (Temizlenmiş ve Sıralanmış)

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas import user as user_schema
from app.services import user_service
from app.db.database import get_db
from app.core.auth import get_current_active_user, get_current_active_superuser
from app.db.models.user import User as UserModel

router = APIRouter()

@router.post(
    "/",
    response_model=user_schema.User,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account. This endpoint is typically public.",
)
def create_new_user(
    *, 
    db: Session = Depends(get_db),
    user_in: user_schema.UserCreate 
):
    try:
        created_user = user_service.create_user(db=db, user_in=user_in)
        return created_user
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        print(f"Unexpected error creating user: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user creation.",
        )

@router.get(
    "/me",
    response_model=user_schema.User,
    summary="Get current user's profile",
    description="Retrieves the full profile information for the currently authenticated user.",
    responses={401: {"description": "Authentication required"}}
)
def read_me(
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update current user's password",
    description="Allows the currently authenticated user to change their own password by providing the current one.",
    responses={
        400: {"description": "Incorrect current password"},
        401: {"description": "Authentication required"},
    }
)
def update_my_password(
    password_update: user_schema.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    success = user_service.update_user_password(
        db=db, user=current_user, password_update=password_update
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate current user's account",
    description="Allows the currently authenticated user to deactivate their own account (soft delete).",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "User not found (should not happen here)"}
    }
)
def deactivate_me(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    deleted_user = user_service.delete_user(db=db, user_id=current_user.id)
    if deleted_user is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") 

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "/",
    response_model=List[user_schema.User],
    summary="List all users (Admin only)",
    description="Retrieves a list of all users with pagination. Requires admin privileges.",
    dependencies=[Depends(get_current_active_superuser)] # Sadece Admin
)
def read_all_users( 
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records")
):
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get(
    "/{user_id}",
    response_model=user_schema.User,
    summary="Get user by ID (Admin only)",
    description="Gets the details of a specific user by their unique ID. Requires admin privileges.",
    dependencies=[Depends(get_current_active_superuser)], 
    responses={404: {"description": "User not found"}}
)
def read_user( 
    user_id: int,
    db: Session = Depends(get_db)
):
    db_user = user_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put(
    "/{user_id}",
    response_model=user_schema.User,
    summary="Update user by ID (Admin only)",
    description="Updates user details for a specific user. Requires admin privileges.",
    dependencies=[Depends(get_current_active_superuser)], # Sadece Admin
    responses={
        404: {"description": "User not found"},
        409: {"description": "Username or Email already exists"}
    }
)
def update_user(
    user_id: int,
    user_in: user_schema.UserUpdate,
    db: Session = Depends(get_db)
):
    updated_user = user_service.update_user(db=db, user_id=user_id, user_in=user_in)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.post(
    "/{user_id}/reset-password",
    response_model=user_schema.User,
    summary="Reset user's password (Admin only)",
    description="Allows an administrator to set a new password for a specific user.",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_active_superuser)],
    responses={
        404: {"description": "User not found"},
        400: {"description": "Admin cannot reset own password here"}
    }
)
def admin_reset_password(
    user_id: int,
    password_in: user_schema.UserPasswordReset,
    db: Session = Depends(get_db),
    current_admin_user: UserModel = Depends(get_current_active_superuser)
):
    if current_admin_user.id == user_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins should reset their own password via the /users/me/password endpoint")
    updated_user = user_service.reset_user_password(db=db, user_id=user_id, password_in=password_in)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user by ID (Admin only)",
    description="Deactivates a specific user account (soft delete). Requires admin privileges.",
    dependencies=[Depends(get_current_active_superuser)],
    responses={
        404: {"description": "User not found"},
        400: {"description": "Admin cannot deactivate themselves"}
    }
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin_user: UserModel = Depends(get_current_active_superuser) 
):
    if current_admin_user.id == user_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot deactivate their own account via this endpoint.")
    deleted_user = user_service.delete_user(db=db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{user_id}/roles",
    response_model=user_schema.User,
    summary="Update user roles (Admin only)",
    description="Assigns or updates the list of roles for a specific user. Replaces all existing roles.",
    dependencies=[Depends(get_current_active_superuser)], 
    responses={
        404: {"description": "User or one or more Roles not found"},
    }
)
def admin_update_user_roles(
    user_id: int,
    roles_in: user_schema.UserRoleUpdate,
    db: Session = Depends(get_db),
):
    updated_user = user_service.update_user_roles(db=db, user_id=user_id, role_update_in=roles_in)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user