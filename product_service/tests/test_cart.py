# tests/test_cart.py (product_service)
import pytest
from fastapi.testclient import TestClient
import os

# Helper: Admin ile ürün oluşturup ID'sini döndür
def create_product_for_cart_test(client: TestClient, admin_headers: dict, price: float = 10.0, stock: int = 5) -> int:
    product_name = f"Cart Test Ürün {os.urandom(2).hex()}"
    product_data = {"name": product_name, "price": price, "stock": stock, "is_active": True}
    response = client.post("/products/", headers=admin_headers, json=product_data)
    assert response.status_code == 201
    return response.json()["id"]

def test_add_item_to_cart(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    prod_id = create_product_for_cart_test(client, admin_product_token_headers)

    cart_item_data = {"product_id": prod_id, "quantity": 2}
    response_add = client.post("/cart/items", headers=headers, json=cart_item_data)
    assert response_add.status_code == 201, response_add.text
    item = response_add.json()
    assert item["product_id"] == prod_id
    assert item["quantity"] == 2

    response_add_again = client.post("/cart/items", headers=headers, json={"product_id": prod_id, "quantity": 1})
    assert response_add_again.status_code == 201 # Veya 200 OK
    item_updated = response_add_again.json()
    assert item_updated["quantity"] == 3 # 2 + 1

    response_no_stock = client.post("/cart/items", headers=headers, json={"product_id": prod_id, "quantity": 10}) # Stok 5'ti
    assert response_no_stock.status_code == 400
    assert "Not enough stock" in response_no_stock.json()["detail"]

def test_get_cart(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    prod1_id = create_product_for_cart_test(client, admin_product_token_headers, price=10.0, stock=3)
    prod2_id = create_product_for_cart_test(client, admin_product_token_headers, price=20.0, stock=2)

    client.post("/cart/items", headers=headers, json={"product_id": prod1_id, "quantity": 2})
    client.post("/cart/items", headers=headers, json={"product_id": prod2_id, "quantity": 1})

    response_cart = client.get("/cart/", headers=headers)
    assert response_cart.status_code == 200
    cart_data = response_cart.json()
    assert cart_data["total_items"] == 3 # 2 + 1
    assert cart_data["total_price"] == (10.0 * 2) + (20.0 * 1) # 40.0
    assert len(cart_data["items"]) == 2

def test_update_cart_item_quantity(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    prod_id = create_product_for_cart_test(client, admin_product_token_headers, stock=10)
    client.post("/cart/items", headers=headers, json={"product_id": prod_id, "quantity": 1})

    update_data = {"product_id": prod_id, "quantity": 5} # Şema bunu bekliyor
    response_update = client.put(f"/cart/items/{prod_id}", headers=headers, json=update_data)
    assert response_update.status_code == 200, response_update.text
    assert response_update.json()["quantity"] == 5

    update_data_no_stock = {"product_id": prod_id, "quantity": 15}
    response_update_no_stock = client.put(f"/cart/items/{prod_id}", headers=headers, json=update_data_no_stock)
    assert response_update_no_stock.status_code == 400

def test_remove_item_from_cart(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    prod_id = create_product_for_cart_test(client, admin_product_token_headers)
    client.post("/cart/items", headers=headers, json={"product_id": prod_id, "quantity": 1})

    response_delete = client.delete(f"/cart/items/{prod_id}", headers=headers)
    assert response_delete.status_code == 204

    response_cart = client.get("/cart/", headers=headers)
    cart_data = response_cart.json()
    assert not any(item["product_id"] == prod_id for item in cart_data["items"])

def test_clear_cart(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    prod1_id = create_product_for_cart_test(client, admin_product_token_headers)
    prod2_id = create_product_for_cart_test(client, admin_product_token_headers)
    client.post("/cart/items", headers=headers, json={"product_id": prod1_id, "quantity": 1})
    client.post("/cart/items", headers=headers, json={"product_id": prod2_id, "quantity": 1})

    response_clear = client.delete("/cart/", headers=headers)
    assert response_clear.status_code == 204

    response_cart = client.get("/cart/", headers=headers)
    assert response_cart.json()["items"] == []
    assert response_cart.json()["total_items"] == 0


def test_add_item_to_cart_no_token(client: TestClient, admin_product_token_headers: dict):
    """S7: User not logged in tries to add to cart -> 401 Unauthorized."""
    prod_id = create_product_for_cart_test(client, admin_product_token_headers)

    cart_item_data = {"product_id": prod_id, "quantity": 1}
    response_add_no_token = client.post("/cart/items", json=cart_item_data)

    assert response_add_no_token.status_code == 401, \
        f"Expected 401 Unauthorized, got {response_add_no_token.status_code}. Response: {response_add_no_token.text}"
    error_detail = response_add_no_token.json().get("detail", "").lower()
    assert "not authenticated" in error_detail