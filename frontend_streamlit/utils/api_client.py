# frontend_streamlit/utils/api_client.py
import requests
import streamlit as st
import os
from typing import Optional, List

USER_SERVICE_BASE_URL = os.getenv("USER_SERVICE_BASE_URL", "http://localhost:8000")
PRODUCT_SERVICE_BASE_URL = os.getenv("PRODUCT_SERVICE_BASE_URL", "http://localhost:8001")

def get_auth_headers():
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def login_user_api(username, password):
    try:
        response = requests.post(
            f"{USER_SERVICE_BASE_URL}/auth/login", 
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Giriş hatası: {error_detail}")
        return None

def register_user_api(username, email, password): 
    payload = {"username": username, "email": email, "password": password, "is_active": True, "roles": []} 
    try:
        response = requests.post(f"{USER_SERVICE_BASE_URL}/users/", json=payload) # path: /user
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Kayıt hatası: {error_detail}")
        return None

def get_current_user_api():
    headers = get_auth_headers()
    if not headers:
        return None
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/users/me", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def change_password_api(old_password, new_password, confirm_new_password):
    headers = get_auth_headers()
    if not headers: return False
    payload = {"current_password": old_password, "new_password": new_password}
    try:
        response = requests.put(f"{USER_SERVICE_BASE_URL}/users/me/password", headers=headers, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Şifre değiştirilirken hata: {error_detail}")
        return False

def deactivate_my_account_api(): 
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{USER_SERVICE_BASE_URL}/users/me", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Hesap silinirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

def get_my_addresses_api():
    headers = get_auth_headers()
    if not headers: return []
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/addresses", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Adresler getirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return []

def add_address_api(address_data):
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.post(f"{USER_SERVICE_BASE_URL}/addresses", headers=headers, json=address_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Adres eklenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def update_address_api(address_id: int, address_data):
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.put(f"{USER_SERVICE_BASE_URL}/address/{address_id}", headers=headers, json=address_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Adres güncellenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def delete_address_api(address_id: int):
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{USER_SERVICE_BASE_URL}/addresses/{address_id}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Adres silinirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

def get_my_contacts_api():
    headers = get_auth_headers()
    if not headers: return []
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/contacts/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"İletişim bilgileri getirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return []

def add_contact_api(contact_data):
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.post(f"{USER_SERVICE_BASE_URL}/contacts/", headers=headers, json=contact_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"İletişim bilgisi eklenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def update_contact_api(contact_id: int, contact_data):
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.put(f"{USER_SERVICE_BASE_URL}/contacts/{contact_id}", headers=headers, json=contact_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"İletişim bilgisi güncellenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def delete_contact_api(contact_id: int):
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{USER_SERVICE_BASE_URL}/contacts/{contact_id}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"İletişim bilgisi silinirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False


def get_products_api(skip=0, limit=100, active_status: Optional[str] = None): 
    """
    Ürünleri API'den çeker.
    active_status: "active", "inactive", "all" (Sadece admin için anlamlı olabilir)
    """
    try:
        headers = get_auth_headers() 
        if not headers: 
            st.error("Ürünleri getirmek için yetkilendirme token'ı bulunamadı.")
            return []

        params = {"skip": skip, "limit": limit}
        if active_status: 
            params["active_status"] = active_status

        response = requests.get(
            f"{PRODUCT_SERVICE_BASE_URL}/products/",
            headers=headers,
            params=params 
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e.response.text))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Ürünler getirilirken hata: {error_detail} (Status: {e.response.status_code if e.response else 'N/A'})")
        return []

def get_product_details_api(product_id: int):
    try:
        headers = get_auth_headers() 
        response = requests.get(f"{PRODUCT_SERVICE_BASE_URL}/products/{product_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Ürün detayı getirilirken hata: {error_detail}")
        return None

def add_to_cart_api(product_id: int, quantity: int):
    headers = get_auth_headers()
    if not headers:
        st.error("Sepete eklemek için giriş yapmalısınız.")
        return None
    payload = {"product_id": product_id, "quantity": quantity}
    try:
        response = requests.post(f"{PRODUCT_SERVICE_BASE_URL}/cart/items", headers=headers, json=payload) 
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Sepete eklenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def get_cart_api():
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.get(f"{PRODUCT_SERVICE_BASE_URL}/cart/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Sepet getirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def update_cart_item_api(product_id: int, quantity: int):
    headers = get_auth_headers()
    if not headers: return False
    payload = {"product_id": product_id, "quantity": quantity} 
    try:
        response = requests.put(f"{PRODUCT_SERVICE_BASE_URL}/cart/items/{product_id}", headers=headers, json=payload)
        response.raise_for_status()
        st.toast("Sepet güncellendi.", icon="✔️")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Sepet güncellenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

def remove_cart_item_api(product_id: int):
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{PRODUCT_SERVICE_BASE_URL}/cart/items/{product_id}", headers=headers) 
        response.raise_for_status()
        st.toast("Ürün sepetten çıkarıldı.", icon="🗑️")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Ürün sepetten çıkarılırken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

def clear_cart_api():
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{PRODUCT_SERVICE_BASE_URL}/cart/", headers=headers)
        response.raise_for_status()
        st.toast("Sepet temizlendi.", icon="✨")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Sepet temizlenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

def create_order_api(shipping_address_id: int, billing_contact_id: Optional[int] = None): 
    """
    Kullanıcının sepetindeki ürünlerle yeni bir sipariş oluşturur.
    Teslimat adresi ID'si zorunludur. Fatura iletişim ID'si opsiyoneldir.
    """
    headers = get_auth_headers()
    if not headers:
        st.error("Sipariş oluşturmak için giriş yapmalısınız.")
        return None

    payload = {
        "shipping_address_id": shipping_address_id
    }
    if billing_contact_id is not None:
        payload["billing_contact_id"] = billing_contact_id 

    st.write("DEBUG: create_order_api - Payload:", payload) 

    try:
        response = requests.post(
            f"{PRODUCT_SERVICE_BASE_URL}/orders/",
            headers=headers,
            json=payload 
        )
        st.write(f"DEBUG: create_order_api - Status Code: {response.status_code}")
        st.write(f"DEBUG: create_order_api - Response Text: {response.text[:500]}")
        response.raise_for_status()
        return response.json() 
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e.response.text))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Sipariş oluşturulurken hata: {error_detail} (Status: {e.response.status_code if e.response else 'N/A'})")
        return None

def get_my_orders_api():
    headers = get_auth_headers()
    if not headers: return []
    try:
        response = requests.get(f"{PRODUCT_SERVICE_BASE_URL}/orders/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Siparişler getirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return []



def get_all_users_api(skip=0, limit=100): 
    headers = get_auth_headers()
    if not headers: return []
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/users/?skip={skip}&limit={limit}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Kullanıcılar getirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return []

def get_user_details_admin_api(user_id: int): 
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/users/{user_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Kullanıcı detayı getirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def update_user_admin_api(user_id: int, user_data: dict): 
    """Admin tarafından bir kullanıcının bilgilerini (örn: is_active, roller) günceller."""
    headers = get_auth_headers()
    if not headers:
        st.error("Yetkilendirme başlığı alınamadı.")
        return None
    try:
        st.write(f"DEBUG: update_user_admin_api - Payload for user {user_id}:", user_data) 
        response = requests.put(f"{USER_SERVICE_BASE_URL}/users/{user_id}", headers=headers, json=user_data)
        st.write(f"DEBUG: update_user_admin_api - Status Code: {response.status_code}") 
        st.write(f"DEBUG: update_user_admin_api - Response: {response.text[:200]}") 
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e.response.text))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Kullanıcı güncellenirken hata (Admin): {error_detail} (Status: {e.response.status_code if e.response else 'N/A'})")
        return None
    

def create_user_admin_api(username: str, email: str, password: str, roles: List[str], is_active: bool = True):
    """Admin tarafından yeni bir kullanıcı oluşturur."""
    headers = get_auth_headers()
    if not headers:
        st.error("Yetkilendirme başlığı alınamadı.")
        return None


    payload = {
        "username": username,
        "email": email,
        "password": password,
        "is_active": is_active,
        "roles": roles 
    }
    st.write("DEBUG: create_user_admin_api - Payload:", payload) # DEBUG

    try:
        response = requests.post(f"{USER_SERVICE_BASE_URL}/users/", headers=headers, json=payload)
        st.write(f"DEBUG: create_user_admin_api - Status Code: {response.status_code}") # DEBUG
        st.write(f"DEBUG: create_user_admin_api - Response: {response.text[:200]}") # DEBUG
        response.raise_for_status()
        return response.json() 
    except requests.exceptions.RequestException as e:
        error_detail = "Bilinmeyen bir hata oluştu."
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e.response.text))
            except ValueError:
                error_detail = e.response.text
        st.error(f"Yeni kullanıcı oluşturulurken hata (Admin): {error_detail} (Status: {e.response.status_code if e.response else 'N/A'})")
        return None

def deactivate_user_admin_api(user_id: int): 
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{USER_SERVICE_BASE_URL}/users/{user_id}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Kullanıcı pasifleştirilirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

def reset_user_password_admin_api(user_id: int): 
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.post(f"{USER_SERVICE_BASE_URL}/users/{user_id}/reset-password", headers=headers)
        response.raise_for_status()
        st.success(f"{user_id} ID'li kullanıcının şifresi sıfırlandı.")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Şifre sıfırlanırken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False
    
def get_roles_api():
    headers = get_auth_headers()
    if not headers: return []
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/roles/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Roller getirilirken hata: {e.response.json().get('detail') if e.response and e.response.content else str(e)}")
        return []

def create_role_api(role_name: str, role_description: Optional[str]):
    headers = get_auth_headers()
    if not headers: return None
    payload = {"name": role_name, "description": role_description}
    try:
        response = requests.post(f"{USER_SERVICE_BASE_URL}/roles/", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Rol oluşturulurken hata: {e.response.json().get('detail') if e.response and e.response.content else str(e)}")
        return None

def update_role_details_api(role_id: int, role_name: Optional[str], role_description: Optional[str]):
    headers = get_auth_headers()
    if not headers: return None
    payload = {}
    if role_name is not None:
        payload["name"] = role_name
    if role_description is not None: 
        payload["description"] = role_description

    if not payload: 
        st.info("Güncellenecek bir rol detayı belirtilmedi.")
        return None 

    try:
        response = requests.put(f"{USER_SERVICE_BASE_URL}/roles/{role_id}", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Rol güncellenirken hata: {e.response.json().get('detail') if e.response and e.response.content else str(e)}")
        return None

def update_role_permissions_api(role_id: int, permission_ids: List[int]):
    headers = get_auth_headers()
    if not headers: return None
    payload = {"permission_ids": permission_ids}
    try:
        response = requests.put(f"{USER_SERVICE_BASE_URL}/roles/{role_id}/permissions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Rol izinleri güncellenirken hata: {e.response.json().get('detail') if e.response and e.response.content else str(e)}")
        return None

def get_permissions_api():
    headers = get_auth_headers()
    if not headers: return []
    try:
        response = requests.get(f"{USER_SERVICE_BASE_URL}/permissions/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"İzinler getirilirken hata: {e.response.json().get('detail') if e.response and e.response.content else str(e)}")
        return []


def create_product_api(product_data: dict): 
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.post(f"{PRODUCT_SERVICE_BASE_URL}/products/", headers=headers, json=product_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ürün oluşturulurken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def update_product_api(product_id: int, product_data: dict): 
    headers = get_auth_headers()
    if not headers: return None
    try:
        response = requests.put(f"{PRODUCT_SERVICE_BASE_URL}/products/{product_id}", headers=headers, json=product_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ürün güncellenirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return None

def delete_product_api(product_id: int): 
    headers = get_auth_headers()
    if not headers: return False
    try:
        response = requests.delete(f"{PRODUCT_SERVICE_BASE_URL}/products/{product_id}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Ürün silinirken hata: {e.response.json().get('detail') if e.response else str(e)}")
        return False

