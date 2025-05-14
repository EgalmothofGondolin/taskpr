# product_service/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database, drop_database
from typing import Generator, Any
import sys
import os
import logging
from datetime import timedelta, datetime, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import settings 
from app.db.database import Base, get_db
from app.main import app 
from jose import jwt 

logger = logging.getLogger("pytest_conftest_product")
logging.basicConfig(level=logging.INFO)

TEST_DATABASE_URL = settings.DATABASE_URL.replace("/user_db", "/product_db_test") 

logger.info(f"Using Product Service Test Database URL: {TEST_DATABASE_URL}")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_db_product(): 
    logger.info("--- Setting up Product Service Test Database ---")
    if database_exists(engine.url):
        logger.warning(f"Dropping existing product test database: {engine.url.database}")
        drop_database(engine.url)
    logger.info(f"Creating product test database: {engine.url.database}")
    create_database(engine.url)
    logger.info("Creating tables in product test database...")
    Base.metadata.create_all(bind=engine) 
    logger.info("--- Product Service Test Database Setup Complete ---")
    yield
    logger.info("\n--- Tearing down Product Service Test Database ---")
    logger.info(f"Dropping product test database: {engine.url.database}")
    try:
        engine.dispose()
        drop_database(engine.url)
        logger.info("Product test database dropped.")
    except Exception as e:
        logger.error(f"Error dropping product test database: {e}", exc_info=True)
    logger.info("--- Product Service Test Database Teardown Complete ---")

@pytest.fixture(scope="function")
def db_session_product() -> Generator[Session, None, None]: 
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    logger.debug(f"Product DB Session {id(db)} created for test.")
    try:
        yield db
    finally:
        logger.debug(f"Rolling back Product DB Session {id(db)}.")
        if transaction.is_active:
            transaction.rollback()
        db.close()
        connection.close()

@pytest.fixture(autouse=True)
def override_get_db_product(db_session_product: Session): 
    def _override_get_db():
        yield db_session_product
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    logger.info("Creating TestClient for Product Service module.")
    with TestClient(app) as c:
        yield c
    logger.info("TestClient for Product Service module finished.")


def create_test_access_token(subject: str, role: str) -> str:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires
    to_encode = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "jti": os.urandom(16).hex() # Basit bir jti
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

@pytest.fixture(scope="function")
def admin_product_token_headers() -> dict:
    admin_username = os.getenv("FIRST_SUPERUSER_USERNAME_FOR_TEST", "admin_test_user") 
    token = create_test_access_token(subject=admin_username, role="admin")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def normal_user_product_token_headers() -> tuple[dict, str]:
    """Generates a header with a token for a 'user' role and the username."""
    username = f"testproduser_{os.urandom(4).hex()}"
    token = create_test_access_token(subject=username, role="user")
    headers = {"Authorization": f"Bearer {token}"}
    return headers, username