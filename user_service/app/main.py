# app/main.py 
import logging
from fastapi import FastAPI
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional 

from app.api.endpoints import users, auth, addresses, contacts, roles, permissions, authorization
from app.db.database import engine, Base, SessionLocal
from app.db.models import user, address, contact, role, permission 
from app.initial_data import init_db 
from app.core.redis_client import close_redis_pool 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup sequence initiated...")

    logger.info("Step 1: Checking/Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables check/creation complete.")
    except Exception as e:
        logger.error(f"CRITICAL: Error creating database tables: {e}", exc_info=True)

    logger.info("Step 2: Initializing initial data (roles, permissions, superuser)...")
    db: Optional[Session] = None 
    try:
        db = SessionLocal() 
        init_db(db)         
        logger.info("Initial data initialization process finished successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: An error occurred during initial data initialization: {e}", exc_info=True)
        if db and db.is_active: 
             db.rollback()
    finally:
        if db: 
            db.close()
            logger.info("Database session for initial data closed.")

    logger.info("Application startup complete. Ready to accept requests.")
    yield 

    logger.info("Application shutdown sequence initiated...")
    await close_redis_pool() 
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="User Service API",
    description="API for managing users, authentication, addresses, and contacts.",
    version="0.1.0",
    lifespan=lifespan 
)

# --- Root Endpoint ---
@app.get("/", tags=["Root"], summary="Check service status")
async def read_root():
    return {"message": "User Service is running!"}

# --- Router'ları Dahil Etme ---
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication & Authorization"]) 
app.include_router(addresses.router, prefix="/addresses", tags=["User Addresses"])      
app.include_router(contacts.router, prefix="/contacts", tags=["User Contacts"])        
app.include_router(roles.router, prefix="/roles", tags=["Roles Management (Admin)"])     
app.include_router(permissions.router, prefix="/permissions", tags=["Permissions Management (Admin)"]) 
app.include_router(authorization.router, prefix="/authz", tags=["Authorization Checks"]) 
