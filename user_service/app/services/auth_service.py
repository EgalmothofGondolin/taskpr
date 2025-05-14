# app/services/auth_service.py
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timezone
from fastapi import HTTPException, status
import redis.asyncio as redis 
import logging 

from app.db.models.user import User as UserModel
from app.services import user_service 
from app.core.security import verify_password 
from app.core.redis_client import add_token_to_blacklist, get_redis_blacklist_client
from app.core.config import settings

logger = logging.getLogger(__name__)

def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
    user = user_service.get_user_by_username(db, username=username)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def blacklist_token(token: str):
    redis_client: Optional[redis.Redis] = None 
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            logger.warning("Logout attempt with invalid token structure (missing jti or exp).")
            return 

        now = datetime.now(timezone.utc).timestamp()
        expires_in = int(exp - now)

        if expires_in <= 0:
             logger.info(f"Token JTI {jti} already expired. Not adding to blacklist.")
             return

        try:
            redis_client = await get_redis_blacklist_client()
            await add_token_to_blacklist(redis_client, jti, expires_in)

        except ConnectionError as e:
            pass
        except Exception as e:
            pass

    except JWTError as e:
        logger.warning(f"JWT Error decoding token during logout: {e}")
        pass 
    except ConnectionError as e:
         logger.error(f"Redis connection error during logout: {e}")
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Logout service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}", exc_info=True) 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not process logout")
