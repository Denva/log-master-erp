import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. MODERN UI CONFIG ---
st.set_page_config(page_title="LOG MASTER VENTURES", layout="wide", page_icon="⚖️")

def apply_modern_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stMetric { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
        .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; width: 100%; }
        </style>
    """, unsafe_allow_html=True)

apply_modern_ui()

# --- 2. IDENTITY & DB ARCHITECTURE ---
COMPANY_NAME = "LOG MASTER VENTURES"
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR, BACKUP_DIR = "product_images", "backups"

HEADERS = {
    "sales": ["Timestamp", "Type", "Item", "Qty", "Price", "Total", "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

# --- 3. SYSTEM INITIALIZATION ---
def init_system():
    for folder in [IMG_DIR, BACKUP_DIR]:
        if not os.path.exists(folder): os.makedirs(folder)
    
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            # Fix missing columns automatically
            missing = [c for c in HEADERS[key] if c not in df.columns]
            if missing:
                for col in missing:
                    df[col] = 0.0 if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"] else ""
                df.to_csv(path, index=False)

    # Initial Admin Setup
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty:
        pd.DataFrame([{"username": "ADMIN", "password": "master77", "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_system()

# --- 4. DATA LOADING (NUMERIC ENFORCEMENT) ---
def load_data(key):
    df = pd.read_csv(FILES[key])
    if key == "inventory":
        for col in ["Cost Price", "Selling Price", "Stock"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    elif key == "sales":
        for col in ["Total", "Cost", "Profit", "Price", "Qty"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 5. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title(f"⚖️ {COMPANY_NAME}")
        with st.form("login_form"):
            u = st.text_input("Username").upper().strip()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN"):
                udb = load_data("users")
                match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                    st.rerun()
                else: st.error("Access Denied")
    st.stop()

# --- 6. GLOBAL REFRESH ---
stock_df = load_data("inventory")
sales_df = load_data("sales")
users_df = load_data("users")

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    nav = ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"]
    if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
    menu = st.radio("Navigation", nav)
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 8. MODULES ---

if menu == "📊 Insights":
    st.title("📊 Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Asset Value", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        c3.metric("Profit", f"GHS {sales_df['Profit'].sum():,.2f}")
    st.dataframe(sales_df.tail(10), use_container_width=True)

elif menu == "📦 Inventory":
    st.title("📦 Inventory & Stock Adjust")
    tab1, tab2, tab3 = st.tabs(["Stock List", "Quick Adjustment", "Add New Product"])
    
    with tab1:
        st.dataframe(stock_df, use_container_width=True)

    with tab2:
        if stock_df.empty:
            st.info("Please add a product first.")
        else:
            with st.form("adj_form"):
                target = st.selectbox("Select Product", stock_df['Product Name'].tolist())
                # CRASH FIX: Ensure we only get values if the product exists
                current_q = stock_df[stock_df['Product Name'] == target]['Stock'].values[0]
                st.write(f"Current Stock: **{current_q}**")
                
                mode = st.radio("Action", ["Add Stock (+)", "Subtract Stock (-)"])
                amt = st.number_input("Amount", min_value=1, step=1)
                
                if st.form_submit_button("APPLY ADJUSTMENT"):
                    new_q = current_q + amt if mode == "Add Stock (+)" else current_q - amt
                    if new_q < 0:
                        st.error("Cannot have negative stock!")
                    else:
                        stock_df.loc[stock_df['Product Name'] == target, 'Stock'] = new_q
                        stock_df.to_csv(FILES["inventory"], index=False)
                        st.success(f"Updated {target} to {new_q}")
                        st.rerun()

    with tab3:
        with st.form("add_prod_form"):
            n = st.text_input("Product Name")
            b = st.text_input("Brand")
            cp = st.number_input("Cost Price", 0.0)
            sp = st.number_input("Selling Price", 0.0)
            s = st.number_input("Opening Stock", 0)
            if st.form_submit_button("SAVE PRODUCT"):
                new_data = pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": 2, "Image_Path": ""}])
                pd.concat([stock_df, new_data], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.success("Product Added!")
                st.rerun()

elif menu == "🛒 Sales POS":
    st.title("🛒 Sales Terminal")
    if stock_df.empty:
        st.warning("Inventory is empty. Add products first.")
    else:
        with st.form("sale_form"):
            col1, col2 = st.columns(2)
            with col1:
                cn = st.text_input("Customer Name")
                items = stock_df[stock_df['Stock'] > 0]['Product Name'].tolist()
                item = st.selectbox("Item", items if items else ["OUT OF STOCK"])
            with col2:
                q = st.number_input("Qty", 1)
                p = st.number_input("Price", 0.0)
            
            if st.form_submit_button("COMPLETE SALE"):
                if item != "OUT OF STOCK":
                    cost = float(stock_df[stock_df['Product Name'] == item]['Cost Price'].iloc[0])
                    new_sale = {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT", "Item": item,
                        "Qty": q, "Price": p, "Total": q*p, "Cost": cost*q, "Profit": (q*p)-(cost*q),
                        "Staff": st.session_state.user, "Cust_Name": cn, "Status": "Sold"
                    }
                    pd.concat([sales_df, pd.DataFrame([new_sale])], ignore_index=True).to_csv(FILES["sales"], index=False)
                    stock_df.loc[stock_df['Product Name'] == item, 'Stock'] -= q
                    stock_df.to_csv(FILES["inventory"], index=False)
                    st.success("Sale Recorded!")
                    st.rerun()

# Repair and Admin modules follow the same "st.form_submit_button" logic...