# tests/conftest.py 
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database, drop_database
from typing import Generator, Any
import sys
import os
import logging
from datetime import timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.initial_data import init_db
from app.core.security import create_access_token, get_password_hash 
from app.db.models.user import User as UserModel
from app.db.models.role import Role as RoleModel
from app.services import user_service # 

logger = logging.getLogger("pytest_conftest")
logging.basicConfig(level=logging.INFO) 

TEST_DATABASE_URL = settings.DATABASE_URL.replace("/user_db", "/user_db_test")

logger.info(f"Using Test Database URL: {TEST_DATABASE_URL}")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_db():
    logger.info("--- Setting up Test Database ---")
    if database_exists(engine.url):
        logger.warning(f"Dropping existing test database: {engine.url.database}")
        drop_database(engine.url)
    logger.info(f"Creating test database: {engine.url.database}")
    create_database(engine.url)
    logger.info("Creating tables in test database...")
    Base.metadata.create_all(bind=engine) # Tabloları oluştur

    db = TestingSessionLocal()
    try:
        logger.info("Initializing base data (roles, perms, admin) for test session...")
        init_db(db) # Bu fonksiyon kendi commit/rollback'ini yapmalı
        logger.info("Base data initialized for test session.")
    except Exception as e:
        logger.error(f"CRITICAL: ERROR loading initial data for test session: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

    logger.info("--- Test Database Setup Complete ---")
    yield 

    logger.info("\n--- Tearing down Test Database ---")
    logger.info(f"Dropping test database: {engine.url.database}")
    try:
        engine.dispose() # Bağlantıları kapat
        drop_database(engine.url)
        logger.info("Test database dropped.")
    except Exception as e:
        logger.error(f"Error dropping test database: {e}", exc_info=True)
    logger.info("--- Test Database Teardown Complete ---")


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    logger.debug(f"DB Session {id(db)} created for test.")
    try:
        yield db 
    finally:
        logger.debug(f"Rolling back DB Session {id(db)}.")
        db.close()
        transaction.rollback() 
        connection.close()

@pytest.fixture(autouse=True)
def override_get_db(db_session: Session): 
    def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    logger.info("Creating TestClient for the module.")
    with TestClient(app) as c:
        yield c
    logger.info("TestClient for the module finished.")


@pytest.fixture(scope="function")
def admin_token_headers(client: TestClient, db_session: Session) -> dict:
    logger.debug("Generating admin token header...")
    user = user_service.get_user_by_username(db_session, username=settings.FIRST_SUPERUSER_USERNAME)
    if not user:
        pytest.fail("Admin user not found in test DB. Check init_db in setup_and_teardown_db fixture.")
    if not user.is_active:
        pytest.fail("Admin user is not active in test DB.")
    is_admin = any(role.name.upper() == "ADMIN" for role in user.roles)
    if not is_admin:
         pytest.fail("Superuser in DB does not have ADMIN role assigned.")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_payload_data = {"sub": user.username, "role": "admin"}
    a_token = create_access_token(payload_data=token_payload_data, expires_delta=access_token_expires)
    headers = {"Authorization": f"Bearer {a_token}"}
    logger.debug("Admin token header generated.")
    return headers

@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db_session: Session) -> tuple[dict, str]:
    logger.debug("Generating normal user token header...")
    suffix = os.urandom(4).hex()
    username = f"testuser_{suffix}"
    email = f"test_{suffix}@example.com"
    password = "password123"

    hashed_password = get_password_hash(password)
    db_user = UserModel(username=username, email=email, hashed_password=hashed_password, is_active=True)
    user_role = db_session.query(RoleModel).filter(RoleModel.name == "USER").first()
    if not user_role:
        pytest.fail("USER role not found in test DB. Check init_db in setup_and_teardown_db fixture.")
    db_user.roles.append(user_role)
    db_session.add(db_user)
    try:
        db_session.commit() 
        db_session.refresh(db_user) 
        logger.debug(f"Normal user '{username}' created and committed in fixture.")
    except Exception as e:
        logger.error(f"ERROR committing normal user in fixture: {e}", exc_info=True)
        db_session.rollback()
        pytest.fail(f"Failed to commit normal user: {e}")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_payload_data = {"sub": username, "role": "user"}
    a_token = create_access_token(payload_data=token_payload_data, expires_delta=access_token_expires)
    headers = {"Authorization": f"Bearer {a_token}"}
    logger.debug(f"Normal user token header generated for '{username}'.")
    return headers, username

@pytest.fixture(scope="function")
def normal_user_for_admin_test(client: TestClient, admin_token_headers: dict, db_session: Session) -> dict:
    logger.debug("Creating 'normal_user_for_admin_test' fixture user...")
    suffix = os.urandom(4).hex()
    username = f"admintest_user_{suffix}"
    email = f"admintest_{suffix}@example.com"
    password = "password123"

    user_create_data = {
        "username": username,
        "email": email,
        "password": password
    }

    response = client.post("/users/", headers=admin_token_headers, json=user_create_data)

    if response.status_code != 201:
        logger.error(f"Failed to create user for admin_test fixture. Status: {response.status_code}, Response: {response.text}")
        pytest.fail(f"Failed to create user for admin_test fixture: {response.text}")

    created_user_data = response.json()
    logger.debug(f"User '{created_user_data['username']}' created for admin_test fixture with ID: {created_user_data['id']}.")

    return created_user_data