# frontend_streamlit/pages/05_Kayıt_Ol.py
import streamlit as st
from utils.auth import initialize_session_state, login
from utils.api_client import register_user_api
import re 

st.set_page_config(page_title="Kayıt Ol", layout="centered")
initialize_session_state()

st.title("📝 Yeni Kullanıcı Kaydı")

with st.form("registration_form"):
    username = st.text_input("Kullanıcı Adı")
    email = st.text_input("E-posta Adresi")
    password = st.text_input("Şifre (en az 8 karakter)", type="password")
    password_confirm = st.text_input("Şifre (Tekrar)", type="password")
    
    submitted = st.form_submit_button("Kayıt Ol")

    if submitted:
        if not all([username, email, password, password_confirm]):
            st.warning("Lütfen tüm alanları doldurun.")
        elif password != password_confirm:
            st.error("Şifreler eşleşmiyor.")
        elif len(password) < 8: 
            st.error("Şifre en az 8 karakter olmalıdır.")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email): 
            st.error("Lütfen geçerli bir e-posta adresi girin.")
        else:
            user_data = register_user_api(username, email, password)
            if user_data:
                st.success(f"Hoş geldin {username}! Kaydınız başarıyla oluşturuldu.")
                st.info("Giriş yapılıyor...")
                if login(username, password):
                    st.switch_page("Home.py") 
                else:
                    st.info("Lütfen giriş sayfasından manuel olarak giriş yapın.")
                    st.page_link("Home.py", label="Giriş Sayfasına Git")

st.markdown("---")
st.page_link("Home.py", label="Zaten bir hesabınız var mı? Giriş Yapın")