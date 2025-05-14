# app/schemas/token.py
from pydantic import BaseModel
from typing import Union, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None 
    jti: Optional[str] = None 
    role: Optional[str] = None 