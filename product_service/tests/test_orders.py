# tests/test_orders.py (product_service)
import pytest
from fastapi.testclient import TestClient
import os

def create_product_for_order_test(client: TestClient, admin_headers: dict, name_suffix: str = "", price: float = 10.0, stock: int = 5) -> dict:
    product_name = f"Order Test Ürün {name_suffix} {os.urandom(2).hex()}"
    product_data = {"name": product_name, "price": price, "stock": stock, "is_active": True}
    response = client.post("/products/", headers=admin_headers, json=product_data)
    assert response.status_code == 201
    return response.json()

def test_create_order_from_cart(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    admin_headers = admin_product_token_headers

    product1 = create_product_for_order_test(client, admin_headers, price=25.0, stock=10)
    product2 = create_product_for_order_test(client, admin_headers, price=15.0, stock=5)

    client.post("/cart/items", headers=headers, json={"product_id": product1["id"], "quantity": 2}) 
    client.post("/cart/items", headers=headers, json={"product_id": product2["id"], "quantity": 1}) 

    response_order = client.post("/orders/", headers=headers)
    assert response_order.status_code == 201, response_order.text
    order_data = response_order.json()
    assert order_data["user_id"] == username
    assert order_data["total_amount"] == 65.0
    assert order_data["status"] == "PENDING"
    assert len(order_data["items"]) == 2
    order_id = order_data["id"]

    response_cart = client.get("/cart/", headers=headers)
    assert response_cart.json()["total_items"] == 0

    response_p1 = client.get(f"/products/{product1['id']}", headers=headers) # Token ile
    assert response_p1.json()["stock"] == 10 - 2 # 8
    response_p2 = client.get(f"/products/{product2['id']}", headers=headers) # Token ile
    assert response_p2.json()["stock"] == 5 - 1 # 4

    response_get_order = client.get(f"/orders/{order_id}", headers=headers)
    assert response_get_order.status_code == 200
    assert response_get_order.json()["id"] == order_id

def test_create_order_empty_cart(client: TestClient, normal_user_product_token_headers: tuple):
    headers, _ = normal_user_product_token_headers
    response_order = client.post("/orders/", headers=headers)
    assert response_order.status_code == 400 # Sepet boş hatası
    assert "Shopping cart is empty" in response_order.json()["detail"]

def test_list_user_orders(client: TestClient, normal_user_product_token_headers: tuple, admin_product_token_headers: dict):
    headers, username = normal_user_product_token_headers
    admin_headers = admin_product_token_headers

    product1 = create_product_for_order_test(client, admin_headers, "OrderList1")
    client.post("/cart/items", headers=headers, json={"product_id": product1["id"], "quantity": 1})
    client.post("/orders/", headers=headers) 
    client.post("/cart/items", headers=headers, json={"product_id": product1["id"], "quantity": 1}) 
    client.post("/orders/", headers=headers) 

    response_list = client.get("/orders/", headers=headers)
    assert response_list.status_code == 200
    orders = response_list.json()
    assert isinstance(orders, list)
    assert len(orders) >= 2
    for order in orders:
        assert order["user_id"] == username

def test_unauthorized_user_cannot_list_other_user_orders(
    client: TestClient,
    admin_product_token_headers: dict,
):
    admin_headers = admin_product_token_headers

    username_a = f"ordertest_user_a_{os.urandom(2).hex()}"
    from .conftest import create_test_access_token 
    token_a = create_test_access_token(subject=username_a, role="user")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    product_a = create_product_for_order_test(client, admin_headers, name_suffix="ForUserA")
    client.post("/cart/items", headers=headers_a, json={"product_id": product_a["id"], "quantity": 1})
    response_order_a = client.post("/orders/", headers=headers_a)
    assert response_order_a.status_code == 201
    order_a_id = response_order_a.json()["id"]

    username_b = f"ordertest_user_b_{os.urandom(2).hex()}"
    token_b = create_test_access_token(subject=username_b, role="user")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    response_b_tries_a_list = client.get("/orders/", headers=headers_b)
    assert response_b_tries_a_list.status_code == 200
    orders_for_b = response_b_tries_a_list.json()
    assert not any(order["id"] == order_a_id for order in orders_for_b), \
        f"User B should not see User A's order (ID: {order_a_id}) in their order list."


    response_b_tries_a_specific_order = client.get(f"/orders/{order_a_id}", headers=headers_b)
    assert response_b_tries_a_specific_order.status_code in [403, 404], \
        f"User B trying to access User A's specific order (ID: {order_a_id}) " \
        f"should result in 403 or 404. Got: {response_b_tries_a_specific_order.status_code}. Response: {response_b_tries_a_specific_order.text}"