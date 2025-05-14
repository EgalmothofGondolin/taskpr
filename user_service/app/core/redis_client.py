# app/core/redis_client.py (user_service - Temizlenmiş)
import logging
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

_blacklist_redis_pool: Optional[redis.ConnectionPool] = None

def get_redis_pool() -> redis.ConnectionPool:
    """Initializes and returns the Redis connection pool."""
    global _blacklist_redis_pool
    if _blacklist_redis_pool is None:
        logger.info(f"Initializing Redis connection pool: {settings.REDIS_HOST}:{settings.REDIS_PORT} DB: {settings.REDIS_BLACKLIST_DB}")
        try:
             _blacklist_redis_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_BLACKLIST_DB,
                decode_responses=True, 
                max_connections=10 
            )
        except Exception as e:
            logger.critical(f"Failed to initialize Redis connection pool: {e}", exc_info=True)
            raise 
    return _blacklist_redis_pool

async def get_redis_blacklist_client() -> redis.Redis:
    """FastAPI dependency to get an async Redis client from the pool."""
    pool = get_redis_pool()
    try:
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        logger.debug("Redis connection successful (ping).")
        return client
    except RedisConnectionError as conn_err:
        logger.error(f"Could not connect to Redis: {conn_err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to backend services (Redis)."
        )
    except Exception as e:
        logger.error(f"Unexpected error getting Redis client: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred with backend services."
        )


async def add_token_to_blacklist(redis_client: redis.Redis, jti: str, expires_in: int):
    """
    Adds a token JTI to the Redis blacklist with an expiration time (in seconds).
    `expires_in` should be the remaining validity time of the token.
    """
    if expires_in <= 0:
        logger.debug(f"Token JTI {jti} already expired, not adding to blacklist.")
        return

    redis_key = f"blacklist:{jti}"
    try:
        await redis_client.set(redis_key, "blacklisted", ex=expires_in)
        logger.info(f"Token JTI {jti} added to blacklist, expires in {expires_in} seconds.")
    except RedisConnectionError as conn_err:
        logger.error(f"Redis connection error adding JTI {jti} to blacklist: {conn_err}")
    except Exception as e:
        logger.error(f"Error adding token JTI {jti} to blacklist: {e}", exc_info=True)


async def is_token_blacklisted(redis_client: redis.Redis, jti: str) -> bool:
    """Checks if a token JTI exists in the Redis blacklist."""
    redis_key = f"blacklist:{jti}"
    try:
        result = await redis_client.exists(redis_key)
        is_blacklisted = result > 0
        if is_blacklisted:
            logger.debug(f"Token JTI {jti} found in blacklist.")
        return is_blacklisted
    except RedisConnectionError as conn_err:
        logger.error(f"Redis connection error checking blacklist for JTI {jti}: {conn_err}")
        return True
    except Exception as e:
        logger.error(f"Error checking blacklist for JTI {jti}: {e}", exc_info=True)
        return True


async def close_redis_pool():
    """Closes the Redis connection pool gracefully."""
    global _blacklist_redis_pool
    if _blacklist_redis_pool:
        logger.info("Closing Redis connection pool...")
        try:
            await _blacklist_redis_pool.disconnect(inuse_connections=True)
            logger.info("Redis connection pool closed.")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}", exc_info=True)
        finally:
             _blacklist_redis_pool = None 