# tests/test_contacts.py
import pytest
from fastapi.testclient import TestClient
from typing import List, Dict, Any
import os

def test_create_contact_for_current_user(client: TestClient, normal_user_token_headers: tuple):
    """C4 variant: Kullanıcı yeni iletişim bilgisi ekler -> 201"""
    headers, username = normal_user_token_headers
    contact_data_phone = {
        "contact_type": "PHONE", 
        "value": "+905551234567",
        "description": "Kişisel Telefon"
    }
    response_phone = client.post("/contacts/", headers=headers, json=contact_data_phone)
    assert response_phone.status_code == 201, f"Phone contact creation failed: {response_phone.text}"
    created_phone = response_phone.json()
    assert created_phone["value"] == contact_data_phone["value"]
    assert created_phone["contact_type"] == "PHONE"
    assert "id" in created_phone
    phone_contact_id = created_phone["id"]

    contact_data_work = {
        "contact_type": "WORK_PHONE",
        "value": "+902129876543",
        "description": "İş Telefonu"
    }
    response_work = client.post("/contacts/", headers=headers, json=contact_data_work)
    assert response_work.status_code == 201, f"Work contact creation failed: {response_work.text}"
    assert response_work.json()["contact_type"] == "WORK_PHONE"

    invalid_phone_data = {**contact_data_phone, "value": "ABC-DEF-GHI"}
    response_invalid_format = client.post("/contacts/", headers=headers, json=invalid_phone_data)
    assert response_invalid_format.status_code == 422
    assert "Invalid characters in phone number" in response_invalid_format.text

    too_short_phone_data = {**contact_data_phone, "value": "123"}
    response_too_short = client.post("/contacts/", headers=headers, json=too_short_phone_data)
    assert response_too_short.status_code == 422
    assert "Phone number seems too short" in response_too_short.text

def test_read_contacts_for_current_user(client: TestClient, normal_user_token_headers: tuple):
    headers, username = normal_user_token_headers
    client.post("/contacts/", headers=headers, json={"contact_type": "MOBILE", "value": "05001112233"})
    client.post("/contacts/", headers=headers, json={"contact_type": "PHONE", "value": "03124445566"})

    response = client.get("/contacts/", headers=headers)
    assert response.status_code == 200
    contacts = response.json()
    assert isinstance(contacts, list)
    assert len(contacts) >= 2
    for contact_entry in contacts:
        assert contact_entry["owner_id"] is not None

def test_read_specific_contact(client: TestClient, normal_user_token_headers: tuple):
    headers, username = normal_user_token_headers
    contact_data = {"contact_type": "MOBILE", "value": "05337778899", "description": "Acil Durum"}
    response_create = client.post("/contacts/", headers=headers, json=contact_data)
    assert response_create.status_code == 201
    created_contact_id = response_create.json()["id"]

    response_get = client.get(f"/contacts/{created_contact_id}", headers=headers)
    assert response_get.status_code == 200
    assert response_get.json()["id"] == created_contact_id
    assert response_get.json()["value"] == "05337778899"

    response_not_found = client.get("/contacts/999999", headers=headers)
    assert response_not_found.status_code == 404

def test_update_contact(client: TestClient, normal_user_token_headers: tuple):
    """C5 variant: Kullanıcı iletişim bilgisini güncellerken format hatası varsa -> 400 (Pydantic 422)"""
    headers, username = normal_user_token_headers
    contact_data = {"contact_type": "PHONE", "value": "02161234567", "description": "Eski Ev Telefonu"}
    response_create = client.post("/contacts/", headers=headers, json=contact_data)
    assert response_create.status_code == 201
    contact_id = response_create.json()["id"]

    update_payload_valid = {"value": "02167654321", "description": "Yeni Ev Telefonu"}
    response_update = client.put(f"/contacts/{contact_id}", headers=headers, json=update_payload_valid)
    assert response_update.status_code == 200, response_update.text
    updated_data = response_update.json()
    assert updated_data["value"] == "02167654321"
    assert updated_data["description"] == "Yeni Ev Telefonu"

    update_payload_invalid_format = {"value": "INVALID-PHONE-NUMBER"}
    response_update_invalid = client.put(f"/contacts/{contact_id}", headers=headers, json=update_payload_invalid_format)
    assert response_update_invalid.status_code == 422
    assert "Invalid characters in phone number" in response_update_invalid.text

def test_delete_contact(client: TestClient, normal_user_token_headers: tuple):
    headers, username = normal_user_token_headers
    contact_data = {"contact_type": "MOBILE", "value": "05550001122"}
    response_create = client.post("/contacts/", headers=headers, json=contact_data)
    assert response_create.status_code == 201
    contact_id = response_create.json()["id"]

    response_delete_invalid = client.delete("/contacts/999999", headers=headers)
    assert response_delete_invalid.status_code == 404

    response_delete = client.delete(f"/contacts/{contact_id}", headers=headers)
    assert response_delete.status_code == 204

    response_get_deleted = client.get(f"/contacts/{contact_id}", headers=headers)
    assert response_get_deleted.status_code == 404

    