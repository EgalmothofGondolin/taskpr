# tests/test_categories.py (product_service)
import pytest
from fastapi.testclient import TestClient
import os


def test_create_category_admin(client: TestClient, admin_product_token_headers: dict):
    category_name = f"Test Kategori {os.urandom(2).hex()}"
    category_data = {"name": category_name, "description": "Admin tarafından oluşturuldu"}
    response = client.post("/categories/", headers=admin_product_token_headers, json=category_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == category_name
    assert "id" in data

def test_create_category_normal_user_forbidden(client: TestClient, normal_user_product_token_headers: tuple):
    headers, _ = normal_user_product_token_headers
    category_data = {"name": "Normal Kullanıcı Kategori Denemesi", "description": "Bu olmamalı"}
    response = client.post("/categories/", headers=headers, json=category_data)
    assert response.status_code == 403

def test_read_categories_public(client: TestClient, admin_product_token_headers: dict):
    cat1_name = f"Genel Kategori 1 {os.urandom(2).hex()}"
    client.post("/categories/", headers=admin_product_token_headers, json={"name": cat1_name})
    cat2_name = f"Genel Kategori 2 {os.urandom(2).hex()}"
    client.post("/categories/", headers=admin_product_token_headers, json={"name": cat2_name})

    response = client.get("/categories/") 
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    category_names = [c["name"] for c in data]
    assert cat1_name in category_names
    assert cat2_name in category_names

def test_read_one_category_public(client: TestClient, admin_product_token_headers: dict):
    category_name = f"Özel Kategori {os.urandom(2).hex()}"
    response_create = client.post("/categories/", headers=admin_product_token_headers, json={"name": category_name})
    assert response_create.status_code == 201
    category_id = response_create.json()["id"]

    response_get = client.get(f"/categories/{category_id}") 
    assert response_get.status_code == 200
    assert response_get.json()["id"] == category_id
    assert response_get.json()["name"] == category_name

    response_not_found = client.get("/categories/999999")
    assert response_not_found.status_code == 404

def test_update_category_admin(client: TestClient, admin_product_token_headers: dict):
    category_name_old = f"Eski Kategori Adı {os.urandom(2).hex()}"
    response_create = client.post("/categories/", headers=admin_product_token_headers, json={"name": category_name_old, "description": "Eski Açıklama"})
    assert response_create.status_code == 201
    category_id = response_create.json()["id"]

    category_name_new = f"Yeni Kategori Adı {os.urandom(2).hex()}"
    update_data = {"name": category_name_new, "description": "Yeni Açıklama"}
    response_update = client.put(f"/categories/{category_id}", headers=admin_product_token_headers, json=update_data)
    assert response_update.status_code == 200, response_update.text
    assert response_update.json()["name"] == category_name_new
    assert response_update.json()["description"] == "Yeni Açıklama"

def test_delete_category_admin(client: TestClient, admin_product_token_headers: dict):
    category_name = f"Silinecek Kategori {os.urandom(2).hex()}"
    response_create = client.post("/categories/", headers=admin_product_token_headers, json={"name": category_name})
    assert response_create.status_code == 201
    category_id = response_create.json()["id"]

    response_delete = client.delete(f"/categories/{category_id}", headers=admin_product_token_headers)
    assert response_delete.status_code == 204

    response_get_deleted = client.get(f"/categories/{category_id}")
    assert response_get_deleted.status_code == 404