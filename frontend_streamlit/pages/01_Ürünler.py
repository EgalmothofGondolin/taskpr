# frontend_streamlit/pages/01_Ürünler.py
import streamlit as st
from utils.api_client import get_products_api, add_to_cart_api
from utils.auth import initialize_session_state, is_logged_in 
from utils.ui_helpers import render_top_user_section

initialize_session_state()

render_top_user_section()

st.title("🛍️ Ürünler")

if not is_logged_in(): 
    st.warning("Ürünleri görmek için lütfen giriş yapınız.")
    if st.button("Giriş Sayfasına Git"):
        st.switch_page("Home.py") 
    st.stop()

products = get_products_api()

if products:
    cols = st.columns(3) 
    for i, product in enumerate(products):
        with cols[i % 3]:
            st.subheader(product.get("name"))
            st.write(f"Fiyat: {product.get('price'):.2f} TL")
            st.write(f"Stok: {product.get('stock')}")
            st.caption(product.get("description", "")[:100] + "...") 
            if st.button("Detaylar", key=f"detail_{product.get('id')}"):
                st.session_state.selected_product_id = product.get('id')
                st.info(f"{product.get('name')} için detaylar gösterilecek...")
            if st.button("Sepete Ekle", key=f"add_{product.get('id')}", type="primary", use_container_width=True):
                if add_to_cart_api(product.get('id'), 1):
                    st.toast(f"{product.get('name')} sepete eklendi!", icon="🎉")
                else: 
                    pass
else:
    st.write("Gösterilecek ürün bulunamadı.")