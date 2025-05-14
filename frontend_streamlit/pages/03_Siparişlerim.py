# frontend_streamlit/pages/03_Siparişlerim.py
import streamlit as st
from utils.api_client import get_my_orders_api
from utils.auth import initialize_session_state, is_logged_in
import pandas as pd
from utils.ui_helpers import render_top_user_section


st.set_page_config(page_title="Siparişlerim", layout="wide")
initialize_session_state()
render_top_user_section()

st.title("📋 Siparişlerim")

if not is_logged_in():
    st.warning("Siparişlerinizi görmek için lütfen giriş yapınız.")
    if st.button("Giriş Sayfasına Git"):
        st.switch_page("Home.py")
    st.stop()

orders = get_my_orders_api()

if orders:
    st.subheader("Geçmiş Siparişleriniz")
    

    for order in reversed(orders): 
        with st.expander(f"Sipariş ID: #{order.get('id')} - Tarih: {pd.to_datetime(order.get('created_at')).strftime('%d.%m.%Y %H:%M')} - Toplam: {order.get('total_price', 0.0):.2f} TL"):
            st.write(f"**Sipariş Durumu:** {order.get('status', 'Bilinmiyor').capitalize()}")
            
            st.markdown("**Sipariş Edilen Ürünler:**")
            if order.get("items"):
                items_data = []
                for item in order["items"]:
                    product_info = item.get("product", {}) 
                    items_data.append({
                        "Ürün Adı": product_info.get("name", item.get("product_name", "Bilinmeyen Ürün")), 
                        "Miktar": item.get("quantity"),
                        "Birim Fiyat (TL)": item.get("price_at_purchase", product_info.get("price", 0.0)), 
                        "Toplam Fiyat (TL)": item.get("quantity",0) * item.get("price_at_purchase", product_info.get("price", 0.0))
                    })
                
                if items_data:
                    df_items = pd.DataFrame(items_data)
                    st.dataframe(df_items, use_container_width=True, hide_index=True)
                else:
                    st.write("Bu siparişte ürün bulunmuyor.")
            else:
                st.write("Bu siparişte ürün detayı bulunmuyor.")

elif isinstance(orders, list) and not orders:
    st.info("Henüz hiç sipariş vermediniz.")
    if st.button("Alışverişe Başla"):
        st.switch_page("pages/01_Ürünler.py")
else:
    st.error("Sipariş bilgileri alınamadı.")