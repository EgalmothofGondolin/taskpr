# tests/test_roles_permissions.py
import pytest
from fastapi.testclient import TestClient
import os

from app.schemas.user import UserRoleUpdate
from app.schemas.role import RolePermissionUpdate, RoleCreate, RoleUpdate 


def get_role_id(client: TestClient, headers: dict, role_name: str) -> int:
    response = client.get("/roles/", headers=headers) 
    assert response.status_code == 200, f"Failed to list roles: {response.text}"
    roles = response.json()
    for role in roles:
        if role["name"].upper() == role_name.upper():
            return role["id"]
    pytest.fail(f"Role '{role_name}' not found in response: {roles}")

def get_permission_id(client: TestClient, headers: dict, perm_name: str) -> int:
    response = client.get("/permissions/", headers=headers) 
    assert response.status_code == 200, f"Failed to list permissions: {response.text}"
    permissions = response.json()
    for perm in permissions:
        if perm["name"] == perm_name:
            return perm["id"]
    pytest.fail(f"Permission '{perm_name}' not found in response: {permissions}")


def test_admin_creates_new_role(client: TestClient, admin_token_headers: dict):
    """R1: Admin yeni rol tanımlar -> 201"""
    role_name = f"TestRole_{os.urandom(3).hex()}"
    role_description = "Bu bir test rolüdür."
    role_create_data = RoleCreate(name=role_name, description=role_description)

    response = client.post("/roles/", headers=admin_token_headers, json=role_create_data.model_dump())
    assert response.status_code == 201, response.text
    created_role = response.json()
    assert created_role["name"] == role_name
    assert created_role["description"] == role_description
    assert "id" in created_role
    assert "permissions" in created_role 
    assert len(created_role["permissions"]) == 0

    response_conflict = client.post("/roles/", headers=admin_token_headers, json=role_create_data.model_dump())
    assert response_conflict.status_code == 409

def test_admin_updates_role_details(client: TestClient, admin_token_headers: dict):
    """R2: Admin rol detaylarını günceller -> 200"""
    role_name_orig = f"RoleToUpdate_{os.urandom(3).hex()}"
    role_desc_orig = "Orijinal açıklama."
    role_create_data = RoleCreate(name=role_name_orig, description=role_desc_orig)
    response_create = client.post("/roles/", headers=admin_token_headers, json=role_create_data.model_dump())
    assert response_create.status_code == 201
    created_role_id = response_create.json()["id"]

    new_role_name = f"UpdatedRole_{os.urandom(3).hex()}"
    new_role_desc = "Güncellenmiş açıklama."
    role_update_data = RoleUpdate(name=new_role_name, description=new_role_desc)

    response_update = client.put(
        f"/roles/{created_role_id}",
        headers=admin_token_headers,
        json=role_update_data.model_dump(exclude_unset=True) 
    )
    assert response_update.status_code == 200, response_update.text
    updated_role = response_update.json()
    assert updated_role["id"] == created_role_id
    assert updated_role["name"] == new_role_name
    assert updated_role["description"] == new_role_desc

    role_update_desc_only = RoleUpdate(description="Sadece açıklama güncel.")
    response_desc_update = client.put(
        f"/roles/{created_role_id}",
        headers=admin_token_headers,
        json=role_update_desc_only.model_dump(exclude_unset=True)
    )
    assert response_desc_update.status_code == 200
    assert response_desc_update.json()["name"] == new_role_name 
    assert response_desc_update.json()["description"] == "Sadece açıklama güncel."

    response_not_found = client.put(
        "/roles/999999",
        headers=admin_token_headers,
        json=RoleUpdate(name="NotFoundUpdate").model_dump()
    )
    assert response_not_found.status_code == 404


def test_admin_updates_user_roles(client: TestClient, admin_token_headers: dict, normal_user_for_admin_test: dict):
    """R3: Kullanıcı rolü admin tarafından değiştirilir -> 200"""
    user_to_update_id = normal_user_for_admin_test["id"] 

    admin_role_id = get_role_id(client, admin_token_headers, "ADMIN")
    user_role_id = get_role_id(client, admin_token_headers, "USER")

    roles_payload_user = UserRoleUpdate(role_ids=[user_role_id])
    response_set_user = client.put(
        f"/users/{user_to_update_id}/roles",
        headers=admin_token_headers,
        json=roles_payload_user.model_dump() 
    )
    assert response_set_user.status_code == 200, response_set_user.text
    response_data_user = response_set_user.json()
    assert "roles" in response_data_user, "Response JSON should contain 'roles' key"
    assert any(r["name"].upper() == "USER" for r in response_data_user["roles"])
    assert not any(r["name"].upper() == "ADMIN" for r in response_data_user["roles"])

    roles_payload_admin = UserRoleUpdate(role_ids=[admin_role_id])
    response_set_admin = client.put(
        f"/users/{user_to_update_id}/roles",
        headers=admin_token_headers,
        json=roles_payload_admin.model_dump()
    )
    assert response_set_admin.status_code == 200, response_set_admin.text
    response_data_admin = response_set_admin.json()
    assert "roles" in response_data_admin
    assert any(r["name"].upper() == "ADMIN" for r in response_data_admin["roles"])


def test_admin_assign_role_non_existent_user(client: TestClient, admin_token_headers: dict):
    """R4: Kullanıcı olmayan birine rol atanırsa -> 404"""
    user_role_id = get_role_id(client, admin_token_headers, "USER")
    roles_payload = UserRoleUpdate(role_ids=[user_role_id])
    response = client.put(
        "/users/999999/roles", 
        headers=admin_token_headers,
        json=roles_payload.model_dump()
    )
    assert response.status_code == 404 

def test_admin_assign_permission_to_role(client: TestClient, admin_token_headers: dict):
    """R5: Admin role permission atar -> 200"""
    user_role_id = get_role_id(client, admin_token_headers, "USER") 

    perm_read_self_id = get_permission_id(client, admin_token_headers, "users:read_self")
    perm_update_self_id = get_permission_id(client, admin_token_headers, "users:update_self")

    permissions_payload = RolePermissionUpdate(permission_ids=[perm_read_self_id, perm_update_self_id])
    response = client.put(
        f"/roles/{user_role_id}/permissions", 
        headers=admin_token_headers,
        json=permissions_payload.model_dump()
    )
    assert response.status_code == 200, response.text
    updated_role = response.json()
    assert "permissions" in updated_role, "Response JSON should contain 'permissions' key"
    assigned_perm_names = {p["name"] for p in updated_role["permissions"]}
    assert assigned_perm_names == {"users:read_self", "users:update_self"}