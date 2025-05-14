# tests/test_products.py 
import pytest
from fastapi.testclient import TestClient
import os
from decimal import Decimal

from app.schemas.product import (
    ProductCreate, ProductUpdate, Product,
    ProductBulkUpdateRequest, ProductBulkUpdateItem, ProductBulkUpdateResponse 
)
# --- Product CRUD Tests ---

def test_create_product_admin(client: TestClient, admin_product_token_headers: dict):
    """Admin creates a new product successfully."""
    product_data = {
        "name": f"Test Product Admin {os.urandom(2).hex()}",
        "description": "A product created by admin for testing.",
        "price": 19.99,
        "stock": 100,
        "is_active": True
    }
    response = client.post("/products/", headers=admin_product_token_headers, json=product_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == product_data["name"]
    assert "id" in data

def test_create_product_normal_user_forbidden(client: TestClient, normal_user_product_token_headers: tuple):
    """Normal user attempts to create a product, should be forbidden."""
    headers, username = normal_user_product_token_headers
    product_data = {
        "name": "Forbidden Product",
        "price": 9.99,
        "stock": 10
    }
    response = client.post("/products/", headers=headers, json=product_data)
    assert response.status_code == 403

def test_read_products_with_token(client: TestClient, admin_product_token_headers: dict, normal_user_product_token_headers: tuple):
    """Authenticated users can read products."""
    admin_headers = admin_product_token_headers
    normal_headers, _ = normal_user_product_token_headers

    p1_name = f"TokenRead Product 1 {os.urandom(2).hex()}"
    p2_name = f"TokenRead Product 2 {os.urandom(2).hex()}"
    client.post("/products/", headers=admin_headers, json={"name": p1_name, "price": 10, "stock": 5, "is_active": True})
    client.post("/products/", headers=admin_headers, json={"name": p2_name, "price": 20, "stock": 15, "is_active": True})

    response = client.get("/products/", headers=normal_headers)
    assert response.status_code == 200, f"Failed for normal user: {response.text}"
    data = response.json()
    assert isinstance(data, list)
    product_names_in_response = [p["name"] for p in data]
    assert p1_name in product_names_in_response
    assert p2_name in product_names_in_response

    response_no_token = client.get("/products/")
    assert response_no_token.status_code == 401

def test_read_one_product_with_token(client: TestClient, admin_product_token_headers: dict, normal_user_product_token_headers: tuple):
    """Authenticated users can read a specific product."""
    admin_headers = admin_product_token_headers
    normal_headers, _ = normal_user_product_token_headers
    product_name = f"Specific TokenRead Product {os.urandom(2).hex()}"

    product_data = {"name": product_name, "price": 25.50, "stock": 5, "is_active": True}
    response_create = client.post("/products/", headers=admin_headers, json=product_data)
    assert response_create.status_code == 201
    product_id = response_create.json()["id"]

    response_get = client.get(f"/products/{product_id}", headers=normal_headers)
    assert response_get.status_code == 200, f"Failed for normal user: {response_get.text}"
    assert response_get.json()["id"] == product_id
    assert response_get.json()["name"] == product_name

    response_get_no_token = client.get(f"/products/{product_id}")
    assert response_get_no_token.status_code == 401

    response_not_found = client.get("/products/999999", headers=normal_headers)
    assert response_not_found.status_code == 404


def test_update_product_admin(client: TestClient, admin_product_token_headers: dict):
    product_data = {"name": f"Product to Update {os.urandom(2).hex()}", "price": 30.00, "stock": 10, "is_active": True}
    response_create = client.post("/products/", headers=admin_product_token_headers, json=product_data)
    assert response_create.status_code == 201
    product_id = response_create.json()["id"]

    update_data = {"price": 35.50, "stock": 8, "is_active": False}
    response_update = client.put(f"/products/{product_id}", headers=admin_product_token_headers, json=update_data)
    assert response_update.status_code == 200, response_update.text
    updated_product = response_update.json()
    assert updated_product["price"] == 35.50

def test_bulk_update_products_success(client: TestClient, admin_product_token_headers: dict):
    """Admin birden fazla ürünü başarıyla toplu günceller."""
    headers = admin_product_token_headers

    product1_create_data = ProductCreate(name=f"BulkProd1_{os.urandom(2).hex()}", price=10.00, stock=10, is_active=True)
    response1 = client.post("/products/", headers=headers, json=product1_create_data.model_dump())
    assert response1.status_code == 201
    prod1_id = response1.json()["id"]

    product2_create_data = ProductCreate(name=f"BulkProd2_{os.urandom(2).hex()}", price=20.00, stock=20, is_active=True)
    response2 = client.post("/products/", headers=headers, json=product2_create_data.model_dump())
    assert response2.status_code == 201
    prod2_id = response2.json()["id"]

    product3_create_data = ProductCreate(name=f"BulkProd3_{os.urandom(2).hex()}", price=30.00, stock=30, is_active=False) # Pasif ürün
    response3 = client.post("/products/", headers=headers, json=product3_create_data.model_dump())
    assert response3.status_code == 201
    prod3_id = response3.json()["id"]

    bulk_update_payload = ProductBulkUpdateRequest(
        updates=[
            ProductBulkUpdateItem(id=prod1_id, price=12.50, stock=8), 
            ProductBulkUpdateItem(id=prod2_id, description="Yeni Bulk Açıklama", is_active=False),
            ProductBulkUpdateItem(id=prod3_id, is_active=True, name=f"Aktif Edilmiş BulkProd3_{os.urandom(2).hex()}")
        ]
    )

    response_bulk = client.patch("/products/bulk", headers=headers, json=bulk_update_payload.model_dump())
    assert response_bulk.status_code == 200, response_bulk.text
    update_result = response_bulk.json()

    assert "products potentially updated" in update_result.get("message", "")

    res_p1_updated = client.get(f"/products/{prod1_id}", headers=headers)
    assert res_p1_updated.status_code == 200
    p1_updated_data = res_p1_updated.json()
    assert float(p1_updated_data["price"]) == 12.50 # float karşılaştırması
    assert p1_updated_data["stock"] == 8
    assert p1_updated_data["is_active"] is True

    res_p2_updated = client.get(f"/products/{prod2_id}", headers=headers)
    assert res_p2_updated.status_code == 200
    p2_updated_data = res_p2_updated.json()
    assert p2_updated_data["description"] == "Yeni Bulk Açıklama"
    assert p2_updated_data["is_active"] is False

    res_p3_updated = client.get(f"/products/{prod3_id}", headers=headers)
    assert res_p3_updated.status_code == 200
    p3_updated_data = res_p3_updated.json()
    assert p3_updated_data["is_active"] is True
    assert p3_updated_data["name"].startswith("Aktif Edilmiş BulkProd3_")


def test_bulk_update_products_partial_failure_product_not_found(client: TestClient, admin_product_token_headers: dict):
    headers = admin_product_token_headers
    non_existent_id = 999999

    product_to_check_data = ProductCreate(name=f"CheckProd_{os.urandom(2).hex()}", price=5.0, stock=5, is_active=True)
    response_check_create = client.post("/products/", headers=headers, json=product_to_check_data.model_dump())
    assert response_check_create.status_code == 201
    check_prod_id = response_check_create.json()["id"]

    bulk_update_payload_only_invalid = ProductBulkUpdateRequest(
        updates=[
            ProductBulkUpdateItem(id=non_existent_id, price=1.00)
        ]
    )
    response_bulk = client.patch("/products/bulk", headers=headers, json=bulk_update_payload_only_invalid.model_dump())
    assert response_bulk.status_code == 404 # Bu doğru
    assert f"Product with id {non_existent_id} not found for bulk update" in response_bulk.json().get("detail", "")

    res_check_prod_after_failed_bulk = client.get(f"/products/{check_prod_id}", headers=headers)
    assert res_check_prod_after_failed_bulk.status_code == 404, \
        f"Product {check_prod_id} was expected to be NOT FOUND (404) due to transaction rollback " \
        f"in the same test function's session. Got {res_check_prod_after_failed_bulk.status_code}"


def test_bulk_update_products_empty_list(client: TestClient, admin_product_token_headers: dict):
    """Boş bir güncelleme listesi gönderildiğinde 400 veya 422 hata almalı."""
    headers = admin_product_token_headers
    response_bulk = client.patch("/products/bulk", headers=headers, json={"updates": []})
    assert response_bulk.status_code == 422 # Pydantic validasyon hatası


def test_bulk_update_products_normal_user_forbidden(client: TestClient, normal_user_product_token_headers: tuple):
    """Normal kullanıcı toplu güncelleme yapamamalı."""
    headers, _ = normal_user_product_token_headers
    bulk_update_payload = ProductBulkUpdateRequest(
        updates=[ProductBulkUpdateItem(id=1, price=99.00)]
    )
    response_bulk = client.patch("/products/bulk", headers=headers, json=bulk_update_payload.model_dump())
    assert response_bulk.status_code == 403 # Forbidden


def test_delete_product_admin(client: TestClient, admin_product_token_headers: dict):
    """Admin deletes a product. Check if product is accessible after deletion."""
    product_data = {"name": f"Product to Delete {os.urandom(2).hex()}", "price": 40.00, "stock": 20, "is_active": True}
    response_create = client.post("/products/", headers=admin_product_token_headers, json=product_data)
    assert response_create.status_code == 201
    product_id = response_create.json()["id"]

    response_delete = client.delete(f"/products/{product_id}", headers=admin_product_token_headers)
    assert response_delete.status_code == 204

    response_get_deleted = client.get(f"/products/{product_id}", headers=admin_product_token_headers)
    assert response_get_deleted.status_code == 404 


def test_admin_create_product_with_same_name_conflict(client: TestClient, admin_product_token_headers: dict):
    """P3: Admin creates a product with an already existing name -> 409 Conflict (if enforced)."""
    headers = admin_product_token_headers
    product_name = f"UniqueProductName_{os.urandom(3).hex()}"
    product_data1 = ProductCreate(name=product_name, price=10.00, stock=10, is_active=True)

    response1 = client.post("/products/", headers=headers, json=product_data1.model_dump())
    assert response1.status_code == 201, f"First product creation failed: {response1.text}"

    product_data2 = ProductCreate(name=product_name, price=15.00, stock=5, is_active=True) 
    response2 = client.post("/products/", headers=headers, json=product_data2.model_dump())

    assert response2.status_code == 409, \
        f"Expected 409 Conflict for duplicate product name, got {response2.status_code}. Response: {response2.text}"
    if response2.status_code == 409:
        assert "Product name already exists" in response2.json().get("detail", "")


def test_normal_user_cannot_delete_product(client: TestClient, admin_product_token_headers: dict, normal_user_product_token_headers: tuple):
    """P5: Normal user attempts to delete a product -> 403 Forbidden."""
    admin_headers = admin_product_token_headers
    normal_headers, _ = normal_user_product_token_headers

    product_to_delete_data = ProductCreate(name=f"ProductForDeleteTest_{os.urandom(2).hex()}", price=5.0, stock=1, is_active=True)
    response_create = client.post("/products/", headers=admin_headers, json=product_to_delete_data.model_dump())
    assert response_create.status_code == 201
    product_id = response_create.json()["id"]

    response_delete_attempt = client.delete(f"/products/{product_id}", headers=normal_headers)
    assert response_delete_attempt.status_code == 403, \
        f"Expected 403 Forbidden, got {response_delete_attempt.status_code}. Response: {response_delete_attempt.text}"
    assert "Administrator privileges required" in response_delete_attempt.json().get("detail", "")