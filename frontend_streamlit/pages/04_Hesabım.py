# frontend_streamlit/pages/04_Hesabım.py
import streamlit as st
from utils.auth import initialize_session_state, is_logged_in, get_current_user, logout
from utils.api_client import (
    change_password_api, deactivate_my_account_api,
    get_my_addresses_api, add_address_api, update_address_api, delete_address_api,
    get_my_contacts_api, add_contact_api, update_contact_api, delete_contact_api
)
from utils.ui_helpers import render_top_user_section 

st.set_page_config(page_title="Hesabım", layout="wide")

initialize_session_state()
render_top_user_section()

st.title("👤 Hesabım")

if not is_logged_in():
    st.warning("Hesap bilgilerinizi görmek için lütfen giriş yapınız.")
    if st.button("Giriş Sayfasına Git"):
        st.switch_page("Home.py")
    st.stop()

user = get_current_user()
if not user:
    st.error("Kullanıcı bilgileri alınamadı. Lütfen tekrar giriş yapın.")
    logout() 
    st.stop()


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📜 Profil Bilgileri", "🏠 Adreslerim", "📞 İletişim Bilgilerim", "🔑 Şifre Değiştir", "⚙️ Hesap Ayarları"
])

with tab1:
    st.subheader("Profil Bilgileriniz")
    st.write(f"**Kullanıcı Adı:** {user.get('username')}")
    st.write(f"**E-posta:** {user.get('email')}")
    first_name = user.get('first_name', '')
    last_name = user.get('last_name', '')
    if first_name or last_name:
        st.write(f"**Ad Soyad:** {first_name} {last_name}".strip())
    roles_data = user.get('roles', [])
    roles_display = []
    if roles_data:
            if isinstance(roles_data[0], dict):
                roles_display = [r.get('name', 'Bilinmiyor') for r in roles_data]
            elif isinstance(roles_data[0], str):
                roles_display = roles_data
    st.write(f"**Roller:** {', '.join(roles_display) if roles_display else 'Tanımsız'}")
    st.write(f"**Hesap Durumu:** {'Aktif' if user.get('is_active') else 'Pasif'}")


with tab2: 
    st.subheader("Adreslerim")

    def render_addresses():
        addresses = get_my_addresses_api()
        if addresses:
            for address_item in addresses:
                display_address_type = address_item.get('address_type', 'Belirtilmemiş')
                if display_address_type == "HOME":
                    display_address_type = "Ev"
                elif display_address_type == "WORK":
                    display_address_type = "İş"
                elif display_address_type == "OTHER":
                    display_address_type = "Diğer"

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**Tip:** {display_address_type}")
                    st.write(f"{address_item.get('street', '')}, {address_item.get('city', '')}, {address_item.get('postal_code', '')}")
                    st.write(f"**Ülke:** {address_item.get('country', 'Türkiye')}")
                    if address_item.get('state'):
                        st.write(f"**İl/Bölge:** {address_item.get('state')}")
                    st.caption(f"ID: {address_item.get('id')}")
                with col2:
                    if st.button("Düzenle", key=f"edit_addr_{address_item.get('id')}"):
                        st.session_state.edit_address_id = address_item.get('id')
                        st.session_state.edit_address_data = address_item 
                with col3:
                    if st.button("Sil", key=f"delete_addr_{address_item.get('id')}", type="secondary"):
                        if delete_address_api(address_item.get('id')):
                            st.success("Adres başarıyla silindi.")
                            st.rerun()
                st.markdown("---")
        else:
            st.info("Kayıtlı adresiniz bulunmamaktadır.")

    render_addresses()

    st.subheader("Yeni Adres Ekle / Düzenle")
    edit_mode_address = "edit_address_id" in st.session_state and st.session_state.edit_address_id is not None
    default_address_data = st.session_state.get("edit_address_data", {}) if edit_mode_address else {}

    ADDRESS_TYPE_OPTIONS_DISPLAY = ["Ev", "İş", "Diğer"]
    ADDRESS_TYPE_API_VALUES = ["HOME", "WORK", "OTHER"] 

    default_address_type_index = 0
    if edit_mode_address and default_address_data.get("address_type") in ADDRESS_TYPE_API_VALUES:
        default_address_type_index = ADDRESS_TYPE_API_VALUES.index(default_address_data.get("address_type"))

    with st.form(key="address_form_hesabim", clear_on_submit=not edit_mode_address): 
        selected_address_type_display = st.selectbox(
            "Adres Tipi*",
            options=ADDRESS_TYPE_OPTIONS_DISPLAY,
            index=default_address_type_index
        )
        street = st.text_input("Sokak/Cadde*", value=default_address_data.get("street", ""))
        city = st.text_input("Şehir*", value=default_address_data.get("city", ""))
        state = st.text_input("İl/Bölge (Opsiyonel)", value=default_address_data.get("state", ""))
        postal_code = st.text_input("Posta Kodu*", value=default_address_data.get("postal_code", ""))
        country = st.text_input("Ülke", value=default_address_data.get("country", "Türkiye")) 

        submit_text = "Adresi Güncelle" if edit_mode_address else "Yeni Adres Ekle"
        submitted_address_form = st.form_submit_button(submit_text)

        if submitted_address_form:
            if not all([street, city, postal_code, selected_address_type_display, country]):
                st.warning("Lütfen yıldızlı (*) alanları doldurun.")
            else:
                api_address_type_value = ADDRESS_TYPE_API_VALUES[ADDRESS_TYPE_OPTIONS_DISPLAY.index(selected_address_type_display)]

                address_payload = {
                    "street": street,
                    "city": city,
                    "state": state if state else None, 
                    "postal_code": postal_code,
                    "country": country,
                    "address_type": api_address_type_value 
                }

                if edit_mode_address:
                    if update_address_api(st.session_state.edit_address_id, address_payload):
                        st.success("Adres başarıyla güncellendi.")
                        del st.session_state.edit_address_id
                        del st.session_state.edit_address_data
                        st.rerun()
                else:
                    if add_address_api(address_payload):
                        st.success("Yeni adres başarıyla eklendi.")
                        st.rerun()
    if edit_mode_address:
        if st.button("Adres Düzenlemeyi İptal Et"):
            del st.session_state.edit_address_id
            del st.session_state.edit_address_data
            st.rerun()


with tab3: 
    st.subheader("İletişim Bilgilerim")

    CONTACT_TYPE_MAP = {
        "PHONE": "Ev Telefonu",
        "MOBILE": "Cep Telefonu",
        "EMAIL": "E-posta",
        "FAX": "Faks",
        "WORK_PHONE": "İş Telefonu",
        "OTHER": "Diğer"
    }
    CONTACT_TYPE_API_VALUES = list(CONTACT_TYPE_MAP.keys()) 

    def render_contacts():
        contacts = get_my_contacts_api()
        if contacts:
            for contact_item in contacts: 
                display_contact_type = CONTACT_TYPE_MAP.get(contact_item.get('contact_type'), contact_item.get('contact_type', 'Bilinmeyen'))

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**Tip:** {display_contact_type}")
                    st.write(f"**Değer:** {contact_item.get('value', '')}")
                    if contact_item.get('description'):
                        st.write(f"**Açıklama:** {contact_item.get('description')}")
                    st.caption(f"ID: {contact_item.get('id')}")
                with col2:
                    if st.button("Düzenle", key=f"edit_contact_{contact_item.get('id')}"):
                        st.session_state.edit_contact_id = contact_item.get('id')
                        st.session_state.edit_contact_data = contact_item
                with col3:
                    if st.button("Sil", key=f"delete_contact_{contact_item.get('id')}", type="secondary"):
                        if delete_contact_api(contact_item.get('id')):
                            st.success("İletişim bilgisi silindi.")
                            st.rerun()
                st.markdown("---")
        else:
            st.info("Kayıtlı iletişim bilginiz bulunmamaktadır.")

    render_contacts()

    st.subheader("Yeni İletişim Bilgisi Ekle / Düzenle")
    edit_contact_mode = "edit_contact_id" in st.session_state and st.session_state.edit_contact_id is not None
    default_contact_data = st.session_state.get("edit_contact_data", {}) if edit_contact_mode else {}

    default_contact_type_api_value = default_contact_data.get("contact_type", CONTACT_TYPE_API_VALUES[0]) 

    with st.form(key="contact_form_hesabim", clear_on_submit=not edit_contact_mode):
        selected_contact_type_api_value = st.selectbox(
            "İletişim Tipi*",
            options=CONTACT_TYPE_API_VALUES, 
            format_func=lambda api_val: CONTACT_TYPE_MAP.get(api_val, api_val), 
            index=CONTACT_TYPE_API_VALUES.index(default_contact_type_api_value) if default_contact_type_api_value in CONTACT_TYPE_API_VALUES else 0
        )
        contact_value = st.text_input("Değer* (Numara, E-posta Adresi vb.)", value=default_contact_data.get("value", ""))
        contact_description = st.text_area("Açıklama (Opsiyonel)", value=default_contact_data.get("description", ""))

        submit_contact_text = "Bilgiyi Güncelle" if edit_contact_mode else "Yeni Bilgi Ekle"
        submitted_contact_form = st.form_submit_button(submit_contact_text)

        if submitted_contact_form:
            if not all([contact_value, selected_contact_type_api_value]):
                st.warning("Lütfen yıldızlı (*) alanları doldurun.")
            else:
                contact_payload = {
                    "contact_type": selected_contact_type_api_value,
                    "value": contact_value,
                    "description": contact_description if contact_description else None
                }

                if edit_contact_mode:
                    if update_contact_api(st.session_state.edit_contact_id, contact_payload):
                        st.success("İletişim bilgisi güncellendi.")
                        del st.session_state.edit_contact_id
                        del st.session_state.edit_contact_data
                        st.rerun()
                else:
                    if add_contact_api(contact_payload):
                        st.success("Yeni iletişim bilgisi eklendi.")
                        st.rerun()
    if edit_contact_mode:
        if st.button("İletişim Düzenlemeyi İptal Et"):
            del st.session_state.edit_contact_id
            del st.session_state.edit_contact_data
            st.rerun()


with tab4:
    st.subheader("Şifre Değiştir")
    with st.form("change_password_form"):
        current_password = st.text_input("Mevcut Şifreniz", type="password")
        new_password = st.text_input("Yeni Şifreniz", type="password")
        confirm_new_password = st.text_input("Yeni Şifreniz (Tekrar)", type="password")
        submitted_password = st.form_submit_button("Şifreyi Değiştir")

        if submitted_password:
            if not all([current_password, new_password, confirm_new_password]):
                st.warning("Lütfen tüm şifre alanlarını doldurun.")
            elif new_password != confirm_new_password:
                st.error("Yeni şifreler eşleşmiyor.")
            elif len(new_password) < 8:
                st.error("Yeni şifre en az 8 karakter olmalıdır.")
            else:
                if change_password_api(current_password, new_password, confirm_new_password):
                    st.success("Şifreniz başarıyla değiştirildi!")
                    if "force_password_change" in st.session_state:
                         st.session_state.force_password_change = False
                    st.info("Güvenlik nedeniyle çıkış yapıldı. Lütfen yeni şifrenizle tekrar giriş yapın.")
                    logout() 

with tab5:
    st.subheader("Hesap Ayarları")
    st.warning("Bu işlem geri alınamaz!")
    if st.checkbox("Hesabımı kalıcı olarak silmek/pasifleştirmek istediğimi onaylıyorum.", key="deactivate_account_confirm"):
        if st.button("Hesabımı Sil/Pasifleştir", type="primary", key="deactivate_account_btn"):
            if deactivate_my_account_api():
                st.success("Hesabınız başarıyla silindi/pasifleştirildi.")
                st.info("Çıkış yapılıyor...")
                logout()
