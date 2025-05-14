# app/core/auth.py (user_service - Temizlenmiş)
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis_client import get_redis_blacklist_client, is_token_blacklisted
from app.db.database import get_db
from app.db.models.user import User as UserModel
from app.schemas.token import TokenData
from app.services import user_service

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def verify_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    redis_client: Optional[redis.Redis] = None

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        jti: Optional[str] = payload.get("jti") 
        role: Optional[str] = payload.get("role") 

        if username is None or jti is None:
            logger.warning("Token missing required claims (sub or jti).")
            raise credentials_exception

        try:
            redis_client = await get_redis_blacklist_client()
            if await is_token_blacklisted(redis_client, jti):
                logger.warning(f"Attempt to use blacklisted token JTI: {jti} for user: {username}")
                raise credentials_exception
        except ConnectionError as redis_conn_err:
             logger.error(f"Redis connection error during token verification: {redis_conn_err}")
             raise credentials_exception

        token_data = TokenData(username=username, jti=jti, role=role)

    except JWTError as jwt_err: 
        logger.warning(f"JWT Error decoding token: {jwt_err}")
        raise credentials_exception
    except ValidationError as pydantic_err: 
         logger.error(f"Token payload validation error: {pydantic_err}")
         raise credentials_exception

    return token_data


async def get_current_active_user(
    token_data: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
) -> UserModel:
    user = user_service.get_user_by_username(db, username=token_data.username)

    if user is None:
        logger.warning(f"User '{token_data.username}' from valid token not found in DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"Inactive user '{token_data.username}' attempted access.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # 400 yerine 401 daha uygun olabilir
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_superuser(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    is_admin = any(role.name.upper() == "ADMIN" for role in current_user.roles)
    if not is_admin:
        logger.warning(f"User '{current_user.username}' attempted admin action without privileges.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user