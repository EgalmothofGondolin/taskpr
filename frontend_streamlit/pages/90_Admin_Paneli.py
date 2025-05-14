# frontend_streamlit/pages/90_Admin_Paneli.py
import streamlit as st
from utils.api_client import (
    get_all_users_api, update_user_admin_api, create_user_admin_api,
    reset_user_password_admin_api,
    get_products_api, create_product_api, update_product_api, delete_product_api,
    get_roles_api, create_role_api, update_role_details_api,
    update_role_permissions_api, get_permissions_api    
)
from utils.auth import initialize_session_state, is_logged_in, get_user_role, get_current_user

import pandas as pd
from typing import List, Dict, Any

from utils.ui_helpers import render_top_user_section

st.set_page_config(page_title="Admin Paneli", layout="wide")
initialize_session_state()
render_top_user_section()


st.title("👑 Admin Paneli")

if not is_logged_in():
    st.warning("Bu sayfayı görüntülemek için lütfen giriş yapınız.")
    st.switch_page("Home.py")
    st.stop()

if get_user_role() != "admin":
    st.error("Bu sayfaya erişim yetkiniz bulunmamaktadır.")
    st.switch_page("Home.py")
    st.stop()

AVAILABLE_ROLES = ["admin", "user"] 

tab_user_management, tab_role_perm_management, tab_product_management = st.tabs(["👥 Kullanıcı Yönetimi", "📜 Rol ve İzin Yönetimi", "📦 Ürün Yönetimi"])

# Kullanıcı Yönetimi Sekmesi
with tab_user_management:
    st.header("Kullanıcı Yönetimi")

    st.subheader("Mevcut Kullanıcılar")
    users_list: List[Dict[str, Any]] = get_all_users_api()
    user_objects_map = {}

    if users_list:
        user_data_for_display = []
        for u_obj in users_list:
            current_roles_from_api = []
            roles_data_from_api = u_obj.get('roles', [])
            if roles_data_from_api:
                if roles_data_from_api and isinstance(roles_data_from_api[0], dict):
                    current_roles_from_api = [r.get('name', '').lower() for r in roles_data_from_api if r.get('name')]
                elif roles_data_from_api and isinstance(roles_data_from_api[0], str):
                    current_roles_from_api = [r.lower() for r in roles_data_from_api]

            display_roles = ", ".join(current_roles_from_api) if current_roles_from_api else "Tanımsız"

            user_data_for_display.append({
                "ID": u_obj.get('id'),
                "Kullanıcı Adı": u_obj.get('username'),
                "E-posta": u_obj.get('email'),
                "Roller": display_roles,
                "Aktif": "✅ Evet" if u_obj.get('is_active') else "❌ Hayır",
            })
            u_obj['extracted_roles_for_multiselect'] = current_roles_from_api
            user_objects_map[u_obj.get('id')] = u_obj

        df_users_display = pd.DataFrame(user_data_for_display)
        st.dataframe(df_users_display, use_container_width=True, hide_index=True)
    else:
        st.info("Sistemde kayıtlı kullanıcı bulunmamaktadır.")

    st.divider()

    st.subheader("Kullanıcıyı Düzenle / İşlemler")
    if users_list:
        user_ids_options = [u['ID'] for u in user_data_for_display]
        selected_user_id_for_edit = st.selectbox(
            "Düzenlenecek Kullanıcı ID:",
            options=user_ids_options,
            index=None,
            placeholder="Kullanıcı seçin..."
        )

        if selected_user_id_for_edit:
            user_to_edit_details = user_objects_map.get(selected_user_id_for_edit)
            if user_to_edit_details:
                st.markdown(f"#### Seçili Kullanıcı: **{user_to_edit_details.get('username')}** (ID: {user_to_edit_details.get('id')})")

                with st.form(key=f"admin_update_user_form_{user_to_edit_details.get('id')}"):
                    st.write("**Kullanıcı Durumu ve Rolleri:**")
                    updated_is_active = st.checkbox(
                        "Hesap Aktif mi?",
                        value=user_to_edit_details.get('is_active', True),
                        key=f"user_active_chk_{user_to_edit_details.get('id')}"
                    )

                    default_roles = user_to_edit_details.get('extracted_roles_for_multiselect', [])
                    valid_default_roles = [role for role in default_roles if role in AVAILABLE_ROLES]

                    updated_roles_selection = st.multiselect(
                        "Kullanıcı Rolleri:",
                        options=AVAILABLE_ROLES, 
                        default=valid_default_roles, 
                        key=f"user_roles_ms_{user_to_edit_details.get('id')}"
                    )

                    submit_user_update_btn = st.form_submit_button("🔄 Bilgileri Güncelle")
                    if submit_user_update_btn:
                        user_update_payload = {
                            "is_active": updated_is_active,
                            "roles": updated_roles_selection,
                        }
                        if update_user_admin_api(user_to_edit_details.get('id'), user_update_payload):
                            st.success(f"Kullanıcı '{user_to_edit_details.get('username')}' başarıyla güncellendi.")
                            st.rerun()

                st.markdown("---")
                st.write("**Kullanıcı Şifre İşlemleri:**")
                with st.expander("🔑 Kullanıcı Şifresini Sıfırla"):
                    with st.form(key=f"admin_reset_pass_form_{user_to_edit_details.get('id')}"):
                        new_temp_password = st.text_input("Yeni Geçici Şifre Belirle*", type="password", help="Kullanıcı ilk girişte bu şifreyi değiştirmelidir.")
                        confirm_reset = st.checkbox("Bu işlemi onaylıyorum.", key=f"confirm_reset_chk_{user_to_edit_details.get('id')}")
                        submit_reset_pass_btn = st.form_submit_button("Şifreyi Sıfırla")

                        if submit_reset_pass_btn:
                            if not new_temp_password:
                                st.warning("Lütfen yeni bir geçici şifre girin.")
                            elif not confirm_reset:
                                st.warning("Lütfen şifre sıfırlama işlemini onaylayın.")
                            else:
                                reset_payload = {"new_password": new_temp_password}
                                if reset_user_password_admin_api(user_to_edit_details.get('id'), reset_payload):
                                    st.success(f"'{user_to_edit_details.get('username')}' kullanıcısının şifresi sıfırlandı.")
                                    st.info(f"Belirlenen geçici şifre: {new_temp_password} (Lütfen kullanıcıya iletin!)")
            else:
                st.warning(f"ID: {selected_user_id_for_edit} olan kullanıcı bulunamadı.")

    st.divider()

    st.subheader("➕ Yeni Kullanıcı Oluştur")
    with st.form("admin_new_user_form", clear_on_submit=True):
        new_username = st.text_input("Yeni Kullanıcı Adı*")
        new_email = st.text_input("Yeni Kullanıcı E-posta Adresi*")
        new_password = st.text_input("Başlangıç Şifresi* (en az 8 karakter)", type="password")
        new_roles_selection = st.multiselect(
            "Kullanıcı Rolleri:",
            options=AVAILABLE_ROLES,
            default=["user"]
        )
        new_is_active_selection = st.checkbox("Hesap Hemen Aktif Olsun", value=True)
        submit_new_user_btn = st.form_submit_button("Yeni Kullanıcıyı Kaydet")

        if submit_new_user_btn:
            if not all([new_username, new_email, new_password]):
                st.warning("Lütfen zorunlu (*) alanları (Kullanıcı Adı, E-posta, Şifre) doldurun.")
            elif len(new_password) < 8:
                st.error("Başlangıç şifresi en az 8 karakter olmalıdır.")
            elif not new_roles_selection:
                st.warning("Lütfen en az bir rol seçin.")
            else:
                created_user = create_user_admin_api(
                    username=new_username,
                    email=new_email,
                    password=new_password,
                    roles=new_roles_selection,
                    is_active=new_is_active_selection
                )
                if created_user:
                    st.success(f"Yeni kullanıcı '{created_user.get('username')}' başarıyla oluşturuldu!")
                    st.rerun()


# Rol ve İzin Yönetimi Sekmesi (YENİ)
with tab_role_perm_management:
    st.header("Rol ve İzin Yönetimi")

    col_roles, col_permissions = st.columns(2)

    with col_roles:
        st.subheader("Roller")
        roles_list = get_roles_api()
        permissions_list = get_permissions_api() 

        if roles_list:
            role_df_data = [{"ID": r.get('id'), "Rol Adı": r.get('name'), "Açıklama": r.get('description', '-'), "İzin Sayısı": len(r.get('permissions',[]))} for r in roles_list]
            st.dataframe(pd.DataFrame(role_df_data), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.write("**Rol Düzenle / İzin Ata:**")
            selected_role_id_for_edit = st.selectbox(
                "Düzenlenecek Rol:",
                options=[(r.get('name'), r.get('id')) for r in roles_list], 
                format_func=lambda x: x[0], 
                index=None,
                placeholder="Rol seçin...",
                key="role_edit_select"
            )

            if selected_role_id_for_edit:
                role_id = selected_role_id_for_edit[1] 
                role_name_for_display = selected_role_id_for_edit[0]
                selected_role_obj = next((r for r in roles_list if r.get('id') == role_id), None)

                if selected_role_obj:
                    st.markdown(f"#### Seçili Rol: **{role_name_for_display}**")
                    with st.form(key=f"edit_role_form_{role_id}"):
                        new_role_name = st.text_input("Yeni Rol Adı (Opsiyonel)", value=selected_role_obj.get('name',''))
                        new_role_desc = st.text_area("Yeni Rol Açıklaması (Opsiyonel)", value=selected_role_obj.get('description',''))

                        st.write("**Bu Role Atanacak İzinler:**")
                        if permissions_list:
                            permission_options = {p.get('name'): p.get('id') for p in permissions_list}
                            current_permission_ids = {p.get('id') for p in selected_role_obj.get('permissions', [])}
                            default_perms_for_ms = [name for name, id_val in permission_options.items() if id_val in current_permission_ids]

                            selected_perm_names_for_role = st.multiselect(
                                "İzinler:",
                                options=list(permission_options.keys()),
                                default=default_perms_for_ms,
                                key=f"role_perms_ms_{role_id}"
                            )
                            selected_perm_ids_for_role = [permission_options[name] for name in selected_perm_names_for_role]
                        else:
                            st.info("Sistemde tanımlı izin bulunmuyor.")
                            selected_perm_ids_for_role = []


                        submit_role_update_btn = st.form_submit_button("💾 Rolü ve İzinleri Güncelle")
                        if submit_role_update_btn:
                            if new_role_name != selected_role_obj.get('name','') or \
                               new_role_desc != selected_role_obj.get('description',''):
                                update_role_details_api(role_id, new_role_name or None, new_role_desc or None)

                            if update_role_permissions_api(role_id, selected_perm_ids_for_role):
                                st.success(f"Rol '{new_role_name or role_name_for_display}' ve izinleri güncellendi.")
                                st.rerun()
        else:
            st.info("Sistemde tanımlı rol bulunmamaktadır.")


        st.markdown("---")
        st.write("**Yeni Rol Oluştur:**")
        with st.form("new_role_form", clear_on_submit=True):
            new_role_create_name = st.text_input("Yeni Rol Adı*")
            new_role_create_desc = st.text_area("Rol Açıklaması (Opsiyonel)")
            submit_new_role_btn = st.form_submit_button("➕ Rol Oluştur")
            if submit_new_role_btn:
                if not new_role_create_name:
                    st.warning("Rol adı boş olamaz.")
                else:
                    if create_role_api(new_role_create_name, new_role_create_desc):
                        st.success(f"Rol '{new_role_create_name}' oluşturuldu.")
                        st.rerun()

    with col_permissions:
        st.subheader("İzinler (Permissions)")
        if permissions_list:
            perm_df_data = [{"ID": p.get('id'), "İzin Adı": p.get('name'), "Açıklama": p.get('description', '-')} for p in permissions_list]
            st.dataframe(pd.DataFrame(perm_df_data), use_container_width=True, hide_index=True)
            st.caption("İzinler genellikle `init_db` ile sabit olarak oluşturulur ve API üzerinden CRUD'u yapılmaz.")
        else:
            st.info("Sistemde tanımlı izin bulunmamaktadır.")


# Ürün Yönetimi Sekmesi
with tab_product_management:
    st.header("Ürün Yönetimi")

    st.subheader("Mevcut Ürünler")
    admin_product_filter_options = {
        "all": "Tümü",
        "active": "Sadece Aktif",
        "inactive": "Sadece Pasif"
    }
    selected_filter_key = st.selectbox(
        "Ürünleri Filtrele:",
        options=list(admin_product_filter_options.keys()), # ['all', 'active', 'inactive']
        format_func=lambda key: admin_product_filter_options[key], # "Tümü", "Sadece Aktif" vs. göster
        index=0, 
        key="admin_prod_filter_select"
    )

    products_admin_list: List[Dict[str, Any]] = get_products_api(active_status=selected_filter_key)

    if products_admin_list:
        product_df_data = []
        product_map = {}
        for p_obj in products_admin_list:
            product_df_data.append({
                "ID": p_obj.get('id'),
                "Ürün Adı": p_obj.get('name'),
                "Fiyat (TL)": p_obj.get('price'),
                "Stok": p_obj.get('stock'),
                "Kategori": p_obj.get('category_name', '-'),
                "Aktif": "✅ Evet" if p_obj.get('is_active', True) else "❌ Hayır"
            })
            product_map[p_obj.get('id')] = p_obj
        st.dataframe(pd.DataFrame(product_df_data), use_container_width=True, hide_index=True)
    else:
        st.info(f"'{admin_product_filter_options[selected_filter_key]}' filtre kriterine uygun ürün bulunmamaktadır.")

    st.divider()

    st.subheader("Ürün İşlemleri")

    product_action_options = ["Yeni Ürün Ekle"]
    if products_admin_list: 
        product_action_options.append("Mevcut Ürünü Düzenle/Sil")

    product_action = st.radio(
        "Yapmak istediğiniz işlem:",
        options=product_action_options,
        index=0 if not products_admin_list and "Yeni Ürün Ekle" in product_action_options else None, 
        horizontal=True,
        key="product_action_radio_admin" 
    )

    if product_action == "Yeni Ürün Ekle":
        st.markdown("#### Yeni Ürün Bilgileri")
        with st.form("admin_new_product_form", clear_on_submit=True): 
            prod_name = st.text_input("Ürün Adı*")
            prod_desc = st.text_area("Açıklama")
            prod_price = st.number_input("Fiyat (TL)*", min_value=0.01, value=1.0, format="%.2f") 
            prod_stock = st.number_input("Stok Adedi*", min_value=0, value=0) 
            prod_category = st.text_input("Kategori Adı (Opsiyonel)")
            prod_is_active = st.checkbox("Ürün Aktif Olsun", value=True, key="admin_new_prod_active")
            submitted_new_prod = st.form_submit_button("➕ Yeni Ürünü Kaydet") 

            if submitted_new_prod:
                if not all([prod_name, prod_price is not None, prod_stock is not None]):
                    st.warning("Lütfen zorunlu (*) alanları (Ürün Adı, Fiyat, Stok) doldurun.")
                else:
                    new_prod_payload = {
                        "name": prod_name, "description": prod_desc, "price": prod_price,
                        "stock": prod_stock, "category_name": prod_category or None, 
                        "is_active": prod_is_active
                    }
                    if create_product_api(new_prod_payload):
                        st.success(f"'{prod_name}' ürünü başarıyla eklendi.")
                        st.rerun()

    elif product_action == "Mevcut Ürünü Düzenle/Sil":
        if not products_admin_list: 
            st.warning("Düzenlenecek/silinecek ürün bulunmamaktadır. Lütfen önce ürün ekleyin.")
        else:
            product_ids_options = [p['ID'] for p in product_df_data]
            selected_product_id_for_prod_edit = st.selectbox(
                "Düzenlenecek/Silinecek Ürün ID:",
                options=product_ids_options,
                index=None,
                placeholder="Ürün seçin...",
                key="admin_edit_prod_select" 
            )
            if selected_product_id_for_prod_edit:
                product_to_edit_details = product_map.get(selected_product_id_for_prod_edit)
                if product_to_edit_details:
                    st.markdown(f"#### Seçili Ürün: **{product_to_edit_details.get('name')}**")
                    with st.form(key=f"admin_edit_product_form_{product_to_edit_details.get('id')}"):
                        edit_prod_name = st.text_input("Ürün Adı*", value=product_to_edit_details.get('name', ''))
                        edit_prod_desc = st.text_area("Açıklama", value=product_to_edit_details.get('description',''))
                        edit_prod_price = st.number_input("Fiyat (TL)*", value=float(product_to_edit_details.get('price',0.0)), min_value=0.01, format="%.2f")
                        edit_prod_stock = st.number_input("Stok Adedi*", value=int(product_to_edit_details.get('stock',0)), min_value=0)
                        edit_prod_category = st.text_input("Kategori Adı", value=product_to_edit_details.get('category_name',''))
                        edit_prod_is_active = st.checkbox("Ürün Aktif", value=product_to_edit_details.get('is_active', True), key=f"admin_edit_prod_active_{product_to_edit_details.get('id')}")

                        submitted_edit_prod = st.form_submit_button("🔄 Ürünü Güncelle")
                        if submitted_edit_prod:
                            if not edit_prod_name:
                                st.warning("Ürün adı boş olamaz.")
                            else:
                                update_payload = {
                                    "name": edit_prod_name,
                                    "description": edit_prod_desc,
                                    "price": edit_prod_price,
                                    "stock": edit_prod_stock,
                                    "category_name": edit_prod_category or None,
                                    "is_active": edit_prod_is_active
                                }
                                if update_product_api(product_to_edit_details.get('id'), update_payload):
                                    st.success(f"Ürün '{edit_prod_name}' güncellendi.")
                                    st.rerun()

                    st.markdown("---")
                    if st.button(f"🗑️ '{product_to_edit_details.get('name')}' Ürününü Sil", type="secondary", key=f"admin_delete_prod_btn_{product_to_edit_details.get('id')}"):
                        if st.checkbox(f"Onaylıyorum: '{product_to_edit_details.get('name')}' ürününü sil.", key=f"admin_confirm_del_prod_{product_to_edit_details.get('id')}"):
                            if delete_product_api(product_to_edit_details.get('id')):
                                st.success(f"Ürün '{product_to_edit_details.get('name')}' silindi.")
                                st.rerun()
    else:
        st.info("Sistemde ürün bulunmamaktadır.")