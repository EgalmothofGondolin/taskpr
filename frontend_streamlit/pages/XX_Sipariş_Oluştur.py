# frontend_streamlit/pages/XX_Sipariş_Oluştur.py
import streamlit as st
from utils.api_client import create_order_api, get_my_addresses_api, get_my_contacts_api
from utils.auth import initialize_session_state, is_logged_in, get_current_user
from typing import List, Dict, Any, Optional # Tip ipuçları için

initialize_session_state()

st.set_page_config(page_title="Sipariş Oluştur", layout="centered")
st.title("📦 Siparişi Tamamla")

if not is_logged_in():
    st.warning("Sipariş oluşturmak için lütfen giriş yapınız.")
    if st.button("Giriş Sayfasına Git"):
        st.switch_page("Home.py")
    st.stop()

addresses: List[Dict[str, Any]] = get_my_addresses_api()
contacts: List[Dict[str, Any]] = get_my_contacts_api()

if not addresses:
    st.error("Sipariş verebilmek için kayıtlı bir teslimat adresiniz bulunmalıdır.")
    st.warning("Lütfen 'Hesabım' sayfasından bir adres ekleyin.")
    if st.button("Hesabım Sayfasına Git"):
        st.switch_page("pages/04_Hesabım.py")
    st.stop() # Adres yoksa devam etme

user = get_current_user()
if user:
    st.write(f"Sipariş veren: {user.get('username')}")
st.divider()

st.subheader("Teslimat Adresi Seçin")

address_options_display = []
address_id_map = {} 
for addr in addresses:
    display_text = (
        f"{addr.get('address_type', 'Bilinmeyen').capitalize()}: "
        f"{addr.get('street', '')}, {addr.get('city', '')} "
        f"({addr.get('postal_code', '')})"
    )
    address_options_display.append(display_text)
    address_id_map[display_text] = addr.get('id')

selected_address_display = st.selectbox(
    "Kayıtlı Adresleriniz:",
    options=address_options_display,
    index=None,
    placeholder="Teslimat adresi seçiniz..."
)

selected_address_id: Optional[int] = None
if selected_address_display:
    selected_address_id = address_id_map.get(selected_address_display)
    selected_address_details = next((addr for addr in addresses if addr.get('id') == selected_address_id), None)
    if selected_address_details:
        with st.expander("Seçilen Adres Detayı"):
            st.write(f"**Tip:** {selected_address_details.get('address_type', '').capitalize()}")
            st.write(f"**Sokak/Cadde:** {selected_address_details.get('street', '')}")
            st.write(f"**Şehir:** {selected_address_details.get('city', '')}")
            st.write(f"**Posta Kodu:** {selected_address_details.get('postal_code', '')}")

st.divider()

st.subheader("Fatura İletişim Bilgisi (Opsiyonel)")

selected_contact_id: Optional[int] = None 

if not contacts:
    st.info("Kayıtlı iletişim bilginiz bulunmuyor. Bu alan opsiyoneldir.")
else:
    contact_options_display = ["Seçme"]
    contact_id_map = {} 
    for contact in contacts:
        display_text = (
            f"{contact.get('contact_type', 'Bilinmeyen').capitalize()}: "
            f"{contact.get('value', '')}"
        )
        contact_options_display.append(display_text)
        contact_id_map[display_text] = contact.get('id')

    selected_contact_display = st.selectbox(
        "Kayıtlı İletişim Bilgileriniz:",
        options=contact_options_display,
        index=0, 
        placeholder="Fatura için iletişim bilgisi seçin..."
    )

    if selected_contact_display and selected_contact_display != "Seçme":
        selected_contact_id = contact_id_map.get(selected_contact_display)
        selected_contact_details = next((c for c in contacts if c.get('id') == selected_contact_id), None)
        if selected_contact_details:
             with st.expander("Seçilen İletişim Bilgisi"):
                 st.write(f"**Tip:** {selected_contact_details.get('contact_type', '').capitalize()}")
                 st.write(f"**Değer:** {selected_contact_details.get('value', '')}")


st.divider()

st.markdown("Siparişinizi onaylamak üzeresiniz.")


order_button_disabled = selected_address_id is None
order_button_tooltip = "Lütfen bir teslimat adresi seçin." if order_button_disabled else "Siparişi oluşturmak için tıklayın"

if st.button("Siparişi Onayla ve Oluştur", type="primary", disabled=order_button_disabled, help=order_button_tooltip):
    if selected_address_id is None:
        st.error("Teslimat adresi seçilmeden sipariş oluşturulamaz.")
    else:
        with st.spinner("Siparişiniz oluşturuluyor..."):
            order_details = create_order_api(
                shipping_address_id=selected_address_id,
                billing_contact_id=selected_contact_id # None olabilir
            )

        if order_details:
            st.balloons()
            st.success(f"Siparişiniz #{order_details.get('id')} başarıyla oluşturuldu!")
            st.write("Sipariş Detaylarınız:")
            st.json(order_details) 
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Siparişlerim Sayfasına Git", use_container_width=True):
                    st.switch_page("pages/03_Siparişlerim.py")
            with col2:
                if st.button("Alışverişe Devam Et", use_container_width=True):
                    st.switch_page("pages/01_Ürünler.py")
        else:
            st.error("Sipariş oluşturulamadı. Lütfen bilgileri kontrol edin veya daha sonra tekrar deneyin.")

st.divider()
if st.button("Sepete Geri Dön"):
    st.switch_page("pages/02_Sepetim.py")