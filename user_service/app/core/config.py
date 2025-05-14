# app/core/config.py (user_service - Temizlenmiş)
import os
import logging
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    FIRST_SUPERUSER_EMAIL: str
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_USERNAME: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_BLACKLIST_DB: int = 1 

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore' 

@lru_cache()
def get_settings():
    logger.debug("Loading application settings...")
    try:
        settings = Settings()
        logger.debug("Application settings loaded successfully.")
        return settings
    except Exception as e:
        logger.critical(f"FATAL ERROR: Could not load settings from .env file or environment variables: {e}", exc_info=True)
        raise e

settings = get_settings()