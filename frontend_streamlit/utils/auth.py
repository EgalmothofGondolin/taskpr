# frontend_streamlit/utils/auth.py
import streamlit as st
# API Client importları (güncel halleriyle)
from .api_client import login_user_api, get_current_user_api, USER_SERVICE_BASE_URL
import requests # Logout için

def initialize_session_state():
    """Streamlit session state'i gerekli anahtarlarla başlatır."""
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "force_password_change" not in st.session_state:
        st.session_state.force_password_change = False 

# --- Login Fonksiyonu ---
def login(username, password):
    """Kullanıcı girişi yapar, token ve kullanıcı bilgilerini session state'e kaydeder."""
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.user_role = None
    st.session_state.force_password_change = False

    token_data = login_user_api(username, password)
    if token_data and "access_token" in token_data:
        st.session_state.access_token = token_data["access_token"]
        user_details = get_current_user_api() # /users/me çağrısı
        if user_details:
            st.session_state.user_info = user_details
            st.session_state.force_password_change = user_details.get('force_password_change', False)

            user_roles = user_details.get("roles", [])
            is_admin = False
            if user_roles:
                if isinstance(user_roles[0], dict): 
                    is_admin = any(r.get("name", "").lower() == "admin" for r in user_roles)
                elif isinstance(user_roles[0], str): 
                    is_admin = "admin" in [r.lower() for r in user_roles]

            st.session_state.user_role = "admin" if is_admin else "user"
            return True 
        else: 
            st.session_state.access_token = None 
            st.error("Kullanıcı bilgileri alınamadı veya token geçersiz.")
            return False
    return False

def logout():
    """Kullanıcı oturumunu sonlandırır ve session state'i temizler."""
    token = st.session_state.get("access_token")
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
        except requests.exceptions.RequestException:
            st.warning("Logout sırasında sunucuya ulaşılamadı.") 

    # Session state'i temizle
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.user_role = None
    st.session_state.force_password_change = False 
    st.success("Başarıyla çıkış yapıldı.")
    st.rerun() 

def is_logged_in():
    """Kullanıcının giriş yapıp yapmadığını kontrol eder."""
    return st.session_state.get("access_token") is not None and st.session_state.get("user_info") is not None

def get_current_user():
    """Mevcut giriş yapmış kullanıcının bilgilerini döndürür."""
    return st.session_state.get("user_info")

def get_user_role():
    """Mevcut giriş yapmış kullanıcının rolünü döndürür."""
    return st.session_state.get("user_role")

def must_force_password_change():
    """Kullanıcının şifre değiştirmeye zorlanıp zorlanmadığını kontrol eder."""
    return is_logged_in() and st.session_state.get("force_password_change", False)