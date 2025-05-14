# app/schemas/auth.py
from pydantic import BaseModel

class CheckLoginResponse(BaseModel):
    message: str = "Token is valid"
    username: str
