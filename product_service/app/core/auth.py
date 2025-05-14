# product_service/app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class TokenData(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

def verify_access_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role") 

        if subject is None:
            print("DEBUG: Subject (sub) is missing in token payload!")
            raise credentials_exception
        if role is None:
             print("DEBUG: Role (role) is missing or None in token payload!")
             raise credentials_exception 

        token_data = TokenData(sub=subject, role=role)

    except KeyError as e:
        print(f"DEBUG: KeyError accessing payload: {e}")
        raise credentials_exception from e
    except JWTError as e:
        print(f"DEBUG: JWTError decoding token: {e}")
        raise credentials_exception from e
    except Exception as e:
        print(f"DEBUG: Unexpected error in verify_access_token: {e}")
        raise credentials_exception from e


    print(f"DEBUG: Decoded token data in verify_access_token: {token_data}")
    return token_data

async def require_admin(token_data: TokenData = Depends(verify_access_token)):
    if not token_data.role or token_data.role.lower() != "admin":
        logger.warning(f"Admin privilege check failed for subject: {token_data.sub}, role: {token_data.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    logger.debug(f"Admin access granted for subject: {token_data.sub}")

def get_current_user_subject(token_data: TokenData = Depends(verify_access_token)) -> str:
    return token_data.sub