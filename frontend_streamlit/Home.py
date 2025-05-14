# frontend_streamlit/Home.py
import streamlit as st
from utils.auth import initialize_session_state, login, logout, is_logged_in, get_current_user, get_user_role
from utils.ui_helpers import render_top_user_section 


st.set_page_config(
    page_title="E-Ticaret Platformu",
    page_icon="🛒",
    layout="wide",              
    initial_sidebar_state="expanded" 
)

initialize_session_state() 

render_top_user_section()


st.sidebar.success("Yukarıdaki menüden bir sayfa seçin.")

if is_logged_in():
    if get_user_role() == "admin":
        st.sidebar.page_link("pages/90_Admin_Paneli.py", label="👑 Admin Paneli")

else:
    st.sidebar.header("Kullanıcı İşlemleri") 
    with st.sidebar.form("login_form_sidebar"): 
        st.write("Giriş Yap")
        username = st.text_input("Kullanıcı Adı", key="login_username_sidebar")
        password = st.text_input("Şifre", type="password", key="login_password_sidebar")
        submitted = st.form_submit_button("Giriş")
        if submitted:
            if login(username, password):
                pass 
    st.sidebar.markdown("---") 
    st.sidebar.page_link("pages/05_Kayıt_Ol.py", label="Hesabınız yok mu? Kayıt Olun")


st.title("🛒 E-Ticaret Platformumuza Hoş Geldiniz!")

st.markdown(
    """
    Bu platform, kullanıcı dostu bir alışveriş deneyimi sunmak üzere geliştirilmiştir.
    Ürünlerimizi inceleyebilir, sepetinize ekleyebilir ve kolayca sipariş verebilirsiniz.

    **👈 Sol taraftaki menüden istediğiniz sayfaya gidebilirsiniz.**

    ### Hızlı Başlangıç
    - **Ürünler:** Mevcut ürünlerimizi listeleyin ve detaylarını inceleyin.
    - **Sepetim:** Sepetinizdeki ürünleri yönetin ve siparişinizi tamamlayın.
    - **Siparişlerim:** Geçmiş siparişlerinizi görüntüleyin.
    - **Hesabım:** Profil bilgilerinizi, adreslerinizi ve şifrenizi yönetin.
    """
)


st.markdown("---")
st.markdown("© 2024 E-Ticaret Projesi - Tüm Hakları Saklıdır.")