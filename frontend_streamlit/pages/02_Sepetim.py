# frontend_streamlit/pages/02_Sepetim.py
import streamlit as st
from utils.api_client import (
    get_cart_api, 
    update_cart_item_api, 
    remove_cart_item_api, 
    clear_cart_api 
)

st.set_page_config(page_title="Sepetim", layout="wide")

from utils.auth import initialize_session_state, is_logged_in
from utils.ui_helpers import render_top_user_section

initialize_session_state()

render_top_user_section()

st.title("🛒 Sepetim")

if not is_logged_in():
    st.warning("Sepetinizi görmek için lütfen giriş yapınız.")
    if st.button("Giriş Sayfasına Git"):
        st.switch_page("Home.py") 
    st.stop()


cart_data = get_cart_api()

if cart_data and cart_data.get("items"):
    st.subheader("Sepetinizdeki Ürünler")

    total_price_calculated = 0.0

    for item in cart_data["items"]:
        product = item.get("product", {}) 
        item_id = item.get("id")
        product_id = product.get("id")
        product_name = product.get("name", "Bilinmeyen Ürün")
        quantity = item.get("quantity")
        price = product.get("price", 0.0)
        item_total_price = price * quantity
        total_price_calculated += item_total_price

        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 1, 1, 1])
        with col1:
            st.write(product_name)
            st.caption(f"Birim Fiyat: {price:.2f} TL")
        with col2:
            st.write(f"Adet: {quantity}")

        with col3:
            if st.button("Miktarı Güncelle (-/+)", key=f"update_qty_btn_{product_id}"):
                st.info("Miktar güncelleme özelliği eklenecek.")

            with st.popover("Miktarı Ayarla", use_container_width=True):
                new_quantity_val = st.number_input(
                    "Yeni Adet",
                    min_value=1,
                    max_value=product.get("stock", quantity), 
                    value=quantity,
                    step=1,
                    key=f"num_input_update_{product_id}"
                )
                if st.button("Onayla", key=f"confirm_update_{product_id}"):
                    if new_quantity_val != quantity:
                        if update_cart_item_api(product_id, new_quantity_val):
                            st.rerun() 

        with col4:
            st.write(f"Toplam: {item_total_price:.2f} TL")
        with col5:
            if st.button("🗑️ Çıkar", key=f"remove_{product_id}", type="primary", use_container_width=True):
                if remove_cart_item_api(product_id):
                    st.rerun() # Sayfayı yeniden yükle

        st.markdown("---")

    st.subheader("Sepet Özeti")
    st.metric(label="Toplam Ürün Adedi", value=cart_data.get("total_items", 0))
    st.metric(label="Sepet Toplamı", value=f"{cart_data.get('total_price', 0.0):.2f} TL")

    col_clear, col_order = st.columns(2)
    with col_clear:
        if st.button("Sepeti Temizle", use_container_width=True, type="secondary"):
            if clear_cart_api():
                st.rerun()
    with col_order:
        if st.button("Siparişi Tamamla", type="primary", use_container_width=True):
            st.session_state.nav_to_order_creation = True 
            st.switch_page("pages/XX_Sipariş_Oluştur.py") 

elif cart_data and not cart_data.get("items"):
    st.info("Sepetiniz şu anda boş.")
    if st.button("Alışverişe Başla"):
        st.switch_page("pages/01_Ürünler.py")
else:
    st.error("Sepet bilgileri alınamadı veya bir hata oluştu.")