# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta, timezone
import time

from app.core.config import settings
from app.schemas.token import TokenData
from app.core.security import create_access_token 


def test_login_success_admin(client: TestClient):
    """A1: Geçerli kullanıcı bilgileriyle login -> 200 + JWT token döner"""
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"
    payload = jwt.decode(token["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == settings.FIRST_SUPERUSER_USERNAME
    assert payload["role"] == "admin"
    assert "jti" in payload
    assert "exp" in payload

def test_login_failure_wrong_password(client: TestClient):
    """A2: Geçersiz şifre ile login -> 401 Unauthorized"""
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": "wrong_password"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_failure_wrong_username(client: TestClient):
    """A2 variant: Geçersiz kullanıcı adı ile login -> 401 Unauthorized"""
    login_data = {
        "username": "non_existent_user",
        "password": "password123"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401


def test_access_protected_endpoint_no_token(client: TestClient):
    """A3: Login olmadan korumalı bir endpoint'e erişim -> 401 Unauthorized"""
    response = client.get("/users/me") # Token olmadan
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_get_me_success(client: TestClient, normal_user_token_headers: tuple):
    """A6 variant: JWT token ile kullanıcı bilgilerini çeken servis testi (/users/me)"""
    headers, username = normal_user_token_headers
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username

def test_check_role_admin(client: TestClient, admin_token_headers: dict):
    """A7 variant: Kullanıcı bu role sahip mi? (Admin için ADMIN)"""
    response = client.get("/authz/has-role/ADMIN", headers=admin_token_headers)
    assert response.status_code == 200
    assert response.json() is True
    response = client.get("/authz/has-role/USER", headers=admin_token_headers)
    assert response.status_code == 200
    assert response.json() is False 

def test_check_role_user(client: TestClient, normal_user_token_headers: tuple):
    """A7 variant: Kullanıcı bu role sahip mi? (User için USER)"""
    headers, _ = normal_user_token_headers
    response = client.get("/authz/has-role/USER", headers=headers)
    assert response.status_code == 200
    assert response.json() is True
    response = client.get("/authz/has-role/ADMIN", headers=headers)
    assert response.status_code == 200
    assert response.json() is False 

def test_check_permission_admin(client: TestClient, admin_token_headers: dict):
    """A7 variant: Kullanıcı bu izne sahip mi? (Admin için users:delete_any)"""
    response = client.get("/authz/has-permission/users:delete_any", headers=admin_token_headers)
    assert response.status_code == 200
    assert response.json() is True

def test_check_permission_user_has(client: TestClient, normal_user_token_headers: tuple):
    """A7 variant: Kullanıcı bu izne sahip mi? (User için addresses:create_own)"""
    headers, _ = normal_user_token_headers
    response = client.get("/authz/has-permission/addresses:create_own", headers=headers)
    assert response.status_code == 200
    assert response.json() is True

def test_check_permission_user_does_not_have(client: TestClient, normal_user_token_headers: tuple):
    """A7 variant: Kullanıcı bu izne sahip mi? (User için users:delete_any)"""
    headers, _ = normal_user_token_headers
    response = client.get("/authz/has-permission/users:delete_any", headers=headers)
    assert response.status_code == 200
    assert response.json() is False

def test_check_login_valid_token(client: TestClient, normal_user_token_headers: tuple):
    """A4 variant: Token geçerli mi kontrolü (/checkLogin) - Başarılı"""
    headers, username = normal_user_token_headers
    response = client.get("/auth/checkLogin", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Token is valid"
    assert data["username"] == username

def test_check_login_invalid_token(client: TestClient):
    """A4 variant: Token geçerli mi kontrolü - Geçersiz token"""
    headers = {"Authorization": "Bearer invalidtokenstring"}
    response = client.get("/auth/checkLogin", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_token_expiration_and_check_login(client: TestClient, db_session): 
    """
    A4: Token süresi dolmuş kullanıcı -> /checkLogin -> 401 Unauthorized
    Ayrıca korumalı bir endpoint'e erişmeye çalışıldığında da 401 alınmalı.
    """
    username_for_test = settings.FIRST_SUPERUSER_USERNAME
    role_for_test = "admin" 

    short_expires_delta = timedelta(seconds=2)
    token_payload_data = {"sub": username_for_test, "role": role_for_test}
    expired_token_value = create_access_token(
        payload_data=token_payload_data,
        expires_delta=short_expires_delta
    )
    expired_headers = {"Authorization": f"Bearer {expired_token_value}"}

    response_before_expiry_check = client.get("/auth/checkLogin", headers=expired_headers)
    assert response_before_expiry_check.status_code == 200, \
        f"checkLogin with short-lived token (before expiry) failed: {response_before_expiry_check.text}"

    response_before_expiry_me = client.get("/users/me", headers=expired_headers)
    assert response_before_expiry_me.status_code == 200, \
        f"/users/me with short-lived token (before expiry) failed: {response_before_expiry_me.text}"
    assert response_before_expiry_me.json()["username"] == username_for_test

    time.sleep(short_expires_delta.total_seconds() + 1)

    response_after_expiry_check = client.get("/auth/checkLogin", headers=expired_headers)
    assert response_after_expiry_check.status_code == 401, \
        f"checkLogin with expired token did not return 401: {response_after_expiry_check.text}"
    error_detail_check = response_after_expiry_check.json().get("detail", "").lower()
    assert "expired" in error_detail_check or "not authenticated" in error_detail_check or "could not validate credentials" in error_detail_check, \
        f"Unexpected error detail for expired token on /checkLogin: {response_after_expiry_check.json()}"


    response_after_expiry_me = client.get("/users/me", headers=expired_headers)
    assert response_after_expiry_me.status_code == 401, \
        f"/users/me with expired token did not return 401: {response_after_expiry_me.text}"
    error_detail_me = response_after_expiry_me.json().get("detail", "").lower()
    assert "expired" in error_detail_me or "not authenticated" in error_detail_me or "could not validate credentials" in error_detail_me, \
        f"Unexpected error detail for expired token on /users/me: {response_after_expiry_me.json()}"
    
    
@pytest.mark.asyncio # Logout async olduğu için
async def test_logout_invalidates_token(client: TestClient, normal_user_token_headers: tuple):
    """A5: Logout sonrası token geçersiz olmalı -> 401 dönmeli"""
    headers, username = normal_user_token_headers
    token_to_invalidate = headers["Authorization"].split(" ")[1]

    response_before = client.get("/users/me", headers=headers)
    assert response_before.status_code == 200

    response_logout = client.post("/auth/logout", headers=headers)
    assert response_logout.status_code == 204


    response_after = client.get("/users/me", headers=headers)
    assert response_after.status_code == 401
    assert "Could not validate credentials" in response_after.json()["detail"]


def test_user_update_own_password_success(client: TestClient, normal_user_token_headers: tuple):
    """U3: Kullanıcı kendi şifresini doğru eski şifre ile değiştirir -> 204 OK"""
    headers, username = normal_user_token_headers
    password_data = {
        "current_password": "password123", 
        "new_password": "newSecurePassword456"
    }
    response = client.put("/users/me/password", headers=headers, json=password_data)
    assert response.status_code == 204

    login_data = {"username": username, "password": "newSecurePassword456"}
    response_login = client.post("/auth/login", data=login_data)
    assert response_login.status_code == 200

def test_user_update_own_password_fail_wrong_current(client: TestClient, normal_user_token_headers: tuple):
    """U4: Kullanıcı şifre değiştirirken eski şifre yanlışsa -> 400 Bad Request"""
    headers, username = normal_user_token_headers
    password_data = {
        "current_password": "wrong_old_password", 
        "new_password": "newSecurePassword456"
    }
    response = client.put("/users/me/password", headers=headers, json=password_data)
    assert response.status_code == 400
    assert "Incorrect current password" in response.json()["detail"]

def test_user_deactivate_self(client: TestClient, normal_user_token_headers: tuple):
    """U7: Kullanıcı kendi kullanıcısını iptal eder (pasife alır) -> 204 OK"""
    headers, username = normal_user_token_headers
    response = client.delete("/users/me", headers=headers)
    assert response.status_code == 204

    login_data = {"username": username, "password": "password123"}
    response_login = client.post("/auth/login", data=login_data)
    assert response_login.status_code == 401 