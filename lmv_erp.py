import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --- 1. CONFIG & SECURITY ---
COMPANY = "LOG MASTER VENTURES"
MASTER_KEY = "LOGMASTER2026"
FILES = {
    "stock": "lmv_stock.csv",
    "sales": "lmv_sales.csv",
    "repairs": "lmv_repairs.csv",
    "users": "lmv_users.csv"
}

# --- 2. DATA INTEGRITY ENGINE (Self-Healing) ---
def check_health():
    for key, path in FILES.items():
        if not os.path.exists(path):
            if key == "stock":
                cols = ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock", "Image_URL"]
            elif key == "sales":
                cols = ["Invoice_ID", "Timestamp", "Item", "Qty", "Total", "Staff", "Payment"]
            elif key == "repairs":
                cols = ["Repair_ID", "Cust_Phone", "Device", "Issue", "Status", "Price"]
            else:
                cols = ["username", "password", "role"]
            pd.DataFrame(columns=cols).to_csv(path, index=False)
            st.toast(f"Fixed missing database: {path}")

st.set_page_config(page_title=f"{COMPANY} ERP", layout="wide")
check_health()

# --- 3. ACCESS CONTROL ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title(f"🔐 {COMPANY} Portal")
    key = st.text_input("Master Business Key", type="password")
    if st.button("Unlock System"):
        if key == MASTER_KEY:
            st.session_state.auth = True
            st.rerun()
        else: st.error("Invalid Key")
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Executive Menu", ["🛒 POS (Barcode)", "📦 Inventory", "🔧 Repairs", "📊 Analytics"])

# --- 5. MODULE: BARCODE POS ---
if menu == "🛒 POS (Barcode)":
    st.header("⚡ Fast-Scan Checkout")
    stock_df = pd.read_csv(FILES["stock"])
    
    if 'cart' not in st.session_state: st.session_state.cart = []

    def scan_item():
        code = st.session_state.barcode_scan
        match = stock_df[stock_df['Barcode'].astype(str) == code]
        if not match.empty:
            st.session_state.cart.append(match.iloc[0].to_dict())
            st.toast(f"Added {match.iloc[0]['Product Name']}")
        st.session_state.barcode_scan = "" # Clear for next beep

    st.text_input("BEEP BARCODE HERE", key="barcode_scan", on_change=scan_item)

    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.table(cart_df[["Product Name", "Selling Price"]])
        total = cart_df["Selling Price"].sum()
        st.subheader(f"Total: GHS {total:,.2f}")
        if st.button("Finalize Sale"):
            # Logic to save to sales.csv goes here
            st.success("Sale Completed!")
            st.session_state.cart = []

# --- 6. MODULE: INVENTORY ---
elif menu == "📦 Inventory":
    st.header("Manage Stock")
    df = pd.read_csv(FILES["stock"])
    st.dataframe(df)
    with st.expander("Add New Product"):
        with st.form("new_item"):
            name = st.text_input("Item Name")
            bcode = st.text_input("Barcode Number")
            price = st.number_input("Price (GHS)")
            if st.form_submit_button("Save Item"):
                # Save logic
                st.success("Item Added")