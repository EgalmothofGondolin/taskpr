# frontend_streamlit/utils/ui_helpers.py
import streamlit as st
from .auth import is_logged_in, get_current_user, logout, must_force_password_change 

def render_top_user_section():
    """
    Sayfanın en üstüne kullanıcı bilgilerini (Ad Soyad, E-posta)
    ve işlemlerini (Hesabım, Şifre Değiştir, Çıkış Yap) yerleştirir.
    """
    if is_logged_in():
        user = get_current_user() 
        if user:

            col_spacer, col_user_display = st.columns([0.75, 0.25]) 

            with col_user_display:
                first_name = user.get('first_name', '')
                last_name = user.get('last_name', '')
                email = user.get('email', '')

                display_name = f"{first_name} {last_name}".strip()
                if not display_name: 
                    display_name = user.get('username', 'Kullanıcı')

                st.markdown(f"<div style='text-align: right; padding-top: 10px;'>", unsafe_allow_html=True)
                st.markdown(f"Hoş geldin, **{display_name}**!")
                if email:
                    st.markdown(f"<small style='color: grey;'>{email}</small>", unsafe_allow_html=True)

                with st.popover("⚙️ İşlemler", use_container_width=False): 
                    st.page_link("pages/04_Hesabım.py", label="🔑 Şifre Değiştir", icon="🔑") 

                    st.markdown("---")
                    if st.button("🚪 Çıkış Yap", key="top_corner_logout_btn", type="primary", use_container_width=True):
                        logout()
                        # logout() fonksiyonu zaten st.rerun() yapıyor olmalı
                st.markdown(f"</div>", unsafe_allow_html=True)


    st.markdown("---")


# --- YENİ Yönlendirme Fonksiyonu ---
def check_and_force_password_change_redirect():
    if is_logged_in():
        if must_force_password_change():
            st.warning("Güvenlik nedeniyle devam etmeden önce şifrenizi değiştirmeniz gerekmektedir.")
            st.info("Hesabım sayfasına yönlendiriliyorsunuz...")

            try:
                st.switch_page("pages/04_Hesabım.py")
            except Exception as e:
                 st.error(f"Yönlendirme hatası: {e}. Sayfa yenileniyor.")
                 st.rerun()
            st.stop()