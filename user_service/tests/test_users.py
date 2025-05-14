# tests/test_users.py
import os
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.schemas.user import UserCreate, UserUpdate, UserPasswordReset, UserRoleUpdate
from app.db.models.user import User as UserModel

def test_admin_create_user_success(client: TestClient, admin_token_headers: dict):
    """U1: Admin kullanıcı yeni kullanıcı oluşturur -> 201 Created"""
    username = f"created_by_admin_{os.urandom(4).hex()}"
    email = f"admin_create_{os.urandom(4).hex()}@example.com"
    user_data = {"username": username, "email": email, "password": "password123"}

    response = client.post("/users/", headers=admin_token_headers, json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email

def test_admin_create_user_conflict(client: TestClient, admin_token_headers: dict):
    """U2: Aynı kullanıcı adıyla tekrar kayıt -> 409 Conflict"""
    username = f"conflict_user_{os.urandom(4).hex()}"
    email1 = f"conflict1_{os.urandom(4).hex()}@example.com"
    email2 = f"conflict2_{os.urandom(4).hex()}@example.com"
    user_data1 = {"username": username, "email": email1, "password": "password123"}
    user_data2 = {"username": username, "email": email2, "password": "password123"}

    response1 = client.post("/users/", headers=admin_token_headers, json=user_data1)
    assert response1.status_code == 201

    response2 = client.post("/users/", headers=admin_token_headers, json=user_data2)
    assert response2.status_code == 409
    assert "Username already registered" in response2.json()["detail"]


def test_admin_reset_password_any(client: TestClient, admin_token_headers: dict, normal_user_for_admin_test: dict):
    """U5: Admin başka bir kullanıcının şifresini sıfırlar -> 200 OK"""
    user_id_to_reset = normal_user_for_admin_test["id"]
    new_password_data = {"new_password": "newPasswordByAdmin"}
    response = client.post(f"/users/{user_id_to_reset}/reset-password", headers=admin_token_headers, json=new_password_data)
    assert response.status_code == 200

    login_data = {"username": normal_user_for_admin_test["username"], "password": "newPasswordByAdmin"}
    response_login = client.post("/auth/login", data=login_data)
    assert response_login.status_code == 200, f"Login with reset password failed: {response_login.text}"


def test_admin_update_user_status(client: TestClient, admin_token_headers: dict, normal_user_for_admin_test: dict):
    """U6: Kullanıcı durumu güncellenir (Admin tarafından) -> 200 OK"""
    user_id_to_update = normal_user_for_admin_test["id"]
    update_data = {"is_active": False}
    response = client.put(f"/users/{user_id_to_update}", headers=admin_token_headers, json=update_data)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    login_data = {"username": normal_user_for_admin_test["username"], "password": "password123"} 
    response_login = client.post("/auth/login", data=login_data)
    assert response_login.status_code == 401, "Login should fail for inactive user"


def test_admin_get_user_by_id_success(client: TestClient, admin_token_headers: dict, normal_user_for_admin_test: dict):
    """U8: Kullanıcı bilgisi doğru id ile çekilir (Admin) -> 200 OK"""
    user_id_to_get = normal_user_for_admin_test["id"]
    response = client.get(f"/users/{user_id_to_get}", headers=admin_token_headers)
    assert response.status_code == 200
    assert response.json()["id"] == user_id_to_get
    assert response.json()["username"] == normal_user_for_admin_test["username"]

def test_admin_get_user_by_id_not_found(client: TestClient, admin_token_headers: dict):
    """U9: Kullanıcı olmayan bir ID ile sorgulanır (Admin) -> 404 Not Found"""
    non_existent_id = 99999
    response = client.get(f"/users/{non_existent_id}", headers=admin_token_headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]



def test_normal_user_cannot_list_all_users(client: TestClient, normal_user_token_headers: tuple):
    """Normal kullanıcı tüm kullanıcıları listeleyememeli -> 403 Forbidden veya 401"""
    headers, _ = normal_user_token_headers
    response = client.get("/users/", headers=headers)
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}. Response: {response.text}"
    error_detail = response.json().get("detail", "").lower() 
    expected_messages = [
        "not enough permissions",
        "forbidden",
        "administrator privileges required" 
    ]
    assert any(msg in error_detail for msg in expected_messages), \
        f"Unexpected error detail: '{response.json().get('detail')}'"


def test_normal_user_cannot_get_other_user_by_id(
    client: TestClient,
    normal_user_token_headers: tuple,
    admin_token_headers: dict 
):
    """Normal kullanıcı başka bir kullanıcının detaylarını ID ile alamasın -> 403 veya 401"""
    normal_headers, _ = normal_user_token_headers

    admin_user_response = client.get("/users/me", headers=admin_token_headers)
    assert admin_user_response.status_code == 200
    admin_user_id = admin_user_response.json()["id"]

    response = client.get(f"/users/{admin_user_id}", headers=normal_headers)
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}. Response: {response.text}"


def test_normal_user_cannot_update_other_user(
    client: TestClient,
    normal_user_token_headers: tuple,
    admin_token_headers: dict 
):
    """Normal kullanıcı başka bir kullanıcıyı güncelleyemesin -> 403 veya 401"""
    normal_headers, _ = normal_user_token_headers
    admin_user_response = client.get("/users/me", headers=admin_token_headers)
    admin_user_id = admin_user_response.json()["id"]

    update_data = {"first_name": "AttemptedUpdate"}
    response = client.put(f"/users/{admin_user_id}", headers=normal_headers, json=update_data)
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}. Response: {response.text}"


def test_normal_user_cannot_deactivate_other_user(
    client: TestClient,
    normal_user_token_headers: tuple,
    admin_token_headers: dict 
):
    """Normal kullanıcı başka bir kullanıcıyı pasifleştiremesin -> 403 veya 401"""
    normal_headers, _ = normal_user_token_headers
    admin_user_response = client.get("/users/me", headers=admin_token_headers)
    admin_user_id = admin_user_response.json()["id"]

    response = client.delete(f"/users/{admin_user_id}", headers=normal_headers)
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}. Response: {response.text}"


def test_normal_user_cannot_reset_other_user_password(
    client: TestClient,
    normal_user_token_headers: tuple,
    admin_token_headers: dict 
):
    """Normal kullanıcı başka bir kullanıcının şifresini sıfırlayamasın -> 403 veya 401"""
    normal_headers, _ = normal_user_token_headers
    admin_user_response = client.get("/users/me", headers=admin_token_headers)
    admin_user_id = admin_user_response.json()["id"]

    password_data = {"new_password": "attemptedReset"}
    response = client.post(f"/users/{admin_user_id}/reset-password", headers=normal_headers, json=password_data)
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}. Response: {response.text}"


def test_normal_user_cannot_update_other_user_roles(
    client: TestClient,
    normal_user_token_headers: tuple,
    admin_token_headers: dict 
):
    """Normal kullanıcı başka bir kullanıcının rollerini güncelleyemesin -> 403 veya 401"""
    normal_headers, _ = normal_user_token_headers
    admin_user_response = client.get("/users/me", headers=admin_token_headers)
    admin_user_id = admin_user_response.json()["id"]

    roles_payload = UserRoleUpdate(role_ids=[1]) 

    response = client.put(f"/users/{admin_user_id}/roles", headers=normal_headers, json=roles_payload.model_dump())
    assert response.status_code in [403, 401], f"Expected 403 or 401, got {response.status_code}. Response: {response.text}"


def test_create_user_invalid_email_format(client: TestClient):
    username = f"badmail_{os.urandom(4).hex()}"
    response = client.post(
        "/users/",
        json={"username": username, "email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422
    data = response.json()
    assert any(err["type"] == "value_error" and "valid email address" in err["msg"].lower() and err["loc"] == ["body", "email"] for err in data["detail"])


def test_create_user_invalid_password_too_short(client: TestClient):
    username = f"shortpass_{os.urandom(4).hex()}"
    email = f"shortpass_{os.urandom(4).hex()}@example.com"
    response = client.post(
        "/users/",
        json={"username": username, "email": email, "password": "short"}, 
    )
    assert response.status_code == 422 
    data = response.json()
    assert any(err["type"] == "string_too_short" and err["loc"] == ["body", "password"] for err in data["detail"])

def test_update_my_password_new_too_short(client: TestClient, normal_user_token_headers: tuple):
    headers, _ = normal_user_token_headers
    password_data = {
        "current_password": "password123", 
        "new_password": "new" 
    }
    response = client.put("/users/me/password", headers=headers, json=password_data)
    assert response.status_code == 422
    data = response.json()
    assert any(err["type"] == "string_too_short" and err["loc"] == ["body", "new_password"] for err in data["detail"])

def test_admin_update_user_invalid_email(
    client: TestClient,
    admin_token_headers: dict
):
    normal_username = f"update_target_{os.urandom(4).hex()}"
    normal_email = f"updatetarget_{os.urandom(4).hex()}@example.com"
    normal_password = "password123"
    create_data = {
        "username": normal_username,
        "email": normal_email,
        "password": normal_password
    }
    response_create = client.post("/users/", headers=admin_token_headers, json=create_data)
    assert response_create.status_code == 201, f"Failed to create user for update test: {response_create.text}"
    user_to_update_id = response_create.json()["id"]

    update_data = {"email": "invalid-email-format"} 
    response = client.put(f"/users/{user_to_update_id}", headers=admin_token_headers, json=update_data)
    assert response.status_code == 422
    data = response.json()
    assert any(
        (err["type"] == "value_error" and "valid email address" in err["msg"].lower() and err["loc"] == ["body", "email"]) or \
        (err["type"] == "email_parsing" and err["loc"] == ["body", "email"])
        for err in data["detail"]
    )

def test_create_user_missing_fields(client: TestClient):
    response_no_pass = client.post(
        "/users/",
        json={"username": "missingpass", "email": "mp@example.com"},
    )
    assert response_no_pass.status_code == 422
    data_no_pass = response_no_pass.json()
    assert any(err["type"] == "missing" and err["loc"] == ["body", "password"] for err in data_no_pass["detail"])

    response_no_user = client.post(
        "/users/",
        json={"email": "nu@example.com", "password": "password123"},
    )
    assert response_no_user.status_code == 422
    data_no_user = response_no_user.json()
    assert any(err["type"] == "missing" and err["loc"] == ["body", "username"] for err in data_no_user["detail"])