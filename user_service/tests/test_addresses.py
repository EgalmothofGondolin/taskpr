# tests/test_addresses.py
import pytest
from fastapi.testclient import TestClient
from typing import List, Dict, Any
import os

def test_create_address_for_current_user(client: TestClient, normal_user_token_headers: tuple):
    """C1 variant: Kullanıcı yeni bir adres ekler -> 201"""
    headers, username = normal_user_token_headers
    address_data_home = {
        "street": f"Ev Adresi {os.urandom(2).hex()}",
        "city": "Ankara",
        "postal_code": "06500",
        "country": "Türkiye",
        "address_type": "HOME" 
    }
    response_home = client.post("/addresses/", headers=headers, json=address_data_home)
    assert response_home.status_code == 201, f"Home address creation failed: {response_home.text}"
    created_home = response_home.json()
    assert created_home["street"] == address_data_home["street"]
    assert created_home["address_type"] == "HOME"
    assert "id" in created_home
    home_address_id = created_home["id"]

    address_data_work = {
        "street": f"İş Adresi {os.urandom(2).hex()}",
        "city": "İstanbul",
        "state": "Beşiktaş",
        "postal_code": "34350",
        "country": "Türkiye",
        "address_type": "WORK"
    }
    response_work = client.post("/addresses/", headers=headers, json=address_data_work)
    assert response_work.status_code == 201, f"Work address creation failed: {response_work.text}"
    created_work = response_work.json()
    assert created_work["address_type"] == "WORK"

    invalid_address_data = {**address_data_home, "address_type": "INVALID_TYPE"}
    response_invalid_type = client.post("/addresses/", headers=headers, json=invalid_address_data)
    assert response_invalid_type.status_code == 422 

def test_read_addresses_for_current_user(client: TestClient, normal_user_token_headers: tuple):
    headers, username = normal_user_token_headers
    client.post("/addresses/", headers=headers, json={"street": "Test Sokak 1", "city": "TestŞehir", "postal_code": "12345", "address_type": "HOME"})
    client.post("/addresses/", headers=headers, json={"street": "Test Sokak 2", "city": "TestŞehir", "postal_code": "12346", "address_type": "WORK"})

    response = client.get("/addresses/", headers=headers)
    assert response.status_code == 200
    addresses = response.json()
    assert isinstance(addresses, list)
    assert len(addresses) >= 2 
    for addr in addresses:
        assert addr["owner_id"] is not None 

def test_read_specific_address(client: TestClient, normal_user_token_headers: tuple):
    headers, username = normal_user_token_headers
    address_data = {"street": "Özel Sokak", "city": "İzmir", "postal_code": "35000", "address_type": "HOME"}
    response_create = client.post("/addresses/", headers=headers, json=address_data)
    assert response_create.status_code == 201
    created_address_id = response_create.json()["id"]

    response_get = client.get(f"/addresses/{created_address_id}", headers=headers)
    assert response_get.status_code == 200
    assert response_get.json()["id"] == created_address_id
    assert response_get.json()["street"] == "Özel Sokak"

    response_not_found = client.get("/addresses/999999", headers=headers)
    assert response_not_found.status_code == 404

def test_update_address(client: TestClient, normal_user_token_headers: tuple):
    """C2: Kullanıcı adresini günceller -> 200"""
    headers, username = normal_user_token_headers
    address_data = {"street": "Eski Sokak", "city": "Bursa", "postal_code": "16000", "address_type": "WORK"}
    response_create = client.post("/addresses/", headers=headers, json=address_data)
    assert response_create.status_code == 201
    address_id = response_create.json()["id"]

    update_payload = {"street": "Yeni Güncel Sokak", "city": "BURSA"}
    response_update = client.put(f"/addresses/{address_id}", headers=headers, json=update_payload)
    assert response_update.status_code == 200, response_update.text
    updated_data = response_update.json()
    assert updated_data["street"] == "Yeni Güncel Sokak"
    assert updated_data["city"] == "BURSA"
    assert updated_data["address_type"] == "WORK" # Değişmeyen alan aynı kalmalı

    response_update_not_found = client.put("/addresses/999999", headers=headers, json=update_payload)
    assert response_update_not_found.status_code == 404

def test_delete_address(client: TestClient, normal_user_token_headers: tuple):
    headers, username = normal_user_token_headers
    address_data = {"street": "Silinecek Sokak", "city": "Antalya", "postal_code": "07000", "address_type": "HOME"}
    response_create = client.post("/addresses/", headers=headers, json=address_data)
    assert response_create.status_code == 201
    address_id = response_create.json()["id"]

    response_delete_invalid = client.delete("/addresses/999999", headers=headers)
    assert response_delete_invalid.status_code == 404

    response_delete = client.delete(f"/addresses/{address_id}", headers=headers)
    assert response_delete.status_code == 204

    response_get_deleted = client.get(f"/addresses/{address_id}", headers=headers)
    assert response_get_deleted.status_code == 404