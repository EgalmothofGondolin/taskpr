# app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from datetime import timedelta 
from typing import Set

from app.schemas import token as token_schema 
from app.schemas import user as user_schema
from app.schemas.auth import CheckLoginResponse
from app.schemas.token import TokenData
from app.services import auth_service
from app.core.security import create_access_token 
from app.db.database import get_db
from app.core.config import settings
from app.core.auth import get_current_active_user
from app.core.auth import verify_token
from app.db.models.user import User as UserModel
from app.core.security import create_access_token 
from app.core.auth import oauth2_scheme 

router = APIRouter()

@router.post(
    "/login",
    response_model=token_schema.Token, # Başarılı yanıtta Token şeması dönecek
    summary="User Login",
    description="Authenticate user with username and password, returns JWT token."
)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = auth_service.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    user_is_admin = any(role.name == "ADMIN" for role in user.roles)
    user_role = "admin" if user_is_admin else "user"

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_payload = {
        "sub": user.username, 
        "role": user_role,    
    }

    access_token = create_access_token(
        payload_data=token_payload, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Adds the current user's token to the blacklist, effectively logging them out."
)
async def logout( 
    token: str = Depends(oauth2_scheme), 
):
    await auth_service.blacklist_token(token=token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

router.get(
    "/me/permissions",
    response_model= Set[str], 
    summary="Get current user's permissions",
    description="Retrieves a distinct set of permission names assigned to the currently authenticated user via their roles."
)
def read_my_permissions(
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user.permissions

@router.get(
    "/checkLogin",
    response_model=CheckLoginResponse, 
    summary="Check if the current token is valid",
    description="Verifies the access token provided in the Authorization header. Checks signature, expiration, and blacklist."
)
async def check_token_validity(
    token_data: TokenData = Depends(verify_token)
):
    return CheckLoginResponse(username=token_data.username)


