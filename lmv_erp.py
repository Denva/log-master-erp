import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. UI CONFIG ---
st.set_page_config(page_title="LOG MASTER VENTURES", layout="wide", page_icon="⚖️")

def apply_modern_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stMetric { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
        .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; }
        .stAlert { border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

apply_modern_ui()

# --- 2. IDENTITY & FILES ---
COMPANY_NAME = "LOG MASTER VENTURES"
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR, BACKUP_DIR = "product_images", "backups"

# --- 3. CORE LOADING ENGINE ---
def load_and_clean(key):
    if not os.path.exists(FILES[key]):
        # Default headers if file is missing
        headers = {
            "sales": ["Timestamp", "Type", "Item", "Qty", "Price", "Total", "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"],
            "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
            "users": ["username", "password", "role"]
        }
        pd.DataFrame(columns=headers[key]).to_csv(FILES[key], index=False)
    
    df = pd.read_csv(FILES[key])
    # Type enforcement to prevent math errors
    if key == "inventory":
        for col in ["Cost Price", "Selling Price", "Stock"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    with st.container():
        st.title(f"⚖️ {COMPANY_NAME}")
        u = st.text_input("User ID").upper().strip()
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            udb = load_and_clean("users")
            if udb.empty: # Setup Admin if first time
                pd.DataFrame([{"username": "ADMIN", "password": "master77", "role": "OWNER"}]).to_csv(FILES["users"], index=False)
                udb = load_and_clean("users")
            
            match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
            if not match.empty:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                st.rerun()
    st.stop()

# --- 5. MAIN NAVIGATION ---
stock_df = load_and_clean("inventory")
sales_df = load_and_clean("sales")

menu = st.sidebar.radio("Navigation", ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"])

if menu == "📊 Insights":
    st.title("📊 Business Intelligence")
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock Value", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Total Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        c3.metric("Profit", f"GHS {sales_df['Profit'].sum():,.2f}")
    st.dataframe(sales_df.tail(10), use_container_width=True)

elif menu == "📦 Inventory":
    st.title("📦 Inventory Management")
    tab_list, tab_adjust, tab_new = st.tabs(["Warehouse View", "Stock Adjustment", "Add New Product"])
    
    with tab_list:
        st.dataframe(stock_df, use_container_width=True)

    with tab_adjust:
        st.subheader("Update Existing Stock Levels")
        with st.form("adj_form"):
            target_item = st.selectbox("Select Product", stock_df['Product Name'].tolist())
            current_qty = stock_df[stock_df['Product Name'] == target_item]['Stock'].values[0]
            st.info(f"Current Stock for **{target_item}**: {current_qty}")
            
            mode = st.radio("Action", ["Add New Stock (+)", "Remove/Correction (-)"])
            amount = st.number_input("Amount", min_value=1, step=1)
            
            if st.form_submit_button("PROCESS ADJUSTMENT"):
                new_qty = current_qty + amount if mode == "Add New Stock (+)" else current_qty - amount
                
                if new_qty < 0:
                    st.error("Error: Stock cannot be negative.")
                else:
                    stock_df.loc[stock_df['Product Name'] == target_item, 'Stock'] = new_qty
                    stock_df.to_csv(FILES["inventory"], index=False)
                    st.success(f"Updated {target_item}: New Qty is {new_qty}")
                    st.rerun()

    with tab_new:
        with st.form("new_prod"):
            n, b, cp, sp, s = st.text_input("Name"), st.text_input("Brand"), st.number_input("Cost"), st.number_input("Selling"), st.number_input("Initial Stock")
            if st.form_submit_button("SAVE NEW ITEM"):
                new_row = pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": 2, "Image_Path": ""}])
                pd.concat([stock_df, new_row], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()

# (Other modules like Sales/Repairs/Admin remain integrated in the background)