import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. UI & CONFIG ---
st.set_page_config(page_title="LOG MASTER VENTURES", layout="wide", page_icon="⚖️")

def apply_modern_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stButton>button { border-radius: 8px; font-weight: 600; background-color: #3b82f6; color: white; width: 100%; }
        .stAlert { border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

apply_modern_ui()

# --- 2. FILES & HEADERS ---
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
HEADERS = {
    "sales": ["Timestamp", "Type", "Item", "Qty", "Price", "Total", "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

# --- 3. SYSTEM INITIALIZATION ---
def init_system():
    if not os.path.exists("product_images"): os.makedirs("product_images")
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
    
    # Check for Master Admin
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty or "ADMIN" not in u_df['username'].str.upper().values:
        admin_fix = pd.DataFrame([{"username": "ADMIN", "password": "master77", "role": "OWNER"}])
        pd.concat([u_df, admin_fix], ignore_index=True).to_csv(FILES["users"], index=False)

init_system()

# --- 4. DATA LOADER ---
def load_data(key):
    df = pd.read_csv(FILES[key])
    # Force everything to string for the login check to prevent 'Access Denied'
    if key == "users":
        df['username'] = df['username'].astype(str).str.upper().str.strip()
        df['password'] = df['password'].astype(str).str.strip()
    return df

# --- 5. THE FIXED LOGIN LOGIC ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>LOG MASTER ERP ACCESS</h2>", unsafe_allow_html=True)
    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("login_gate"):
                input_u = st.text_input("Username / Staff ID").upper().strip()
                input_p = st.text_input("Password", type="password").strip()
                
                if st.form_submit_button("UNLOCK SYSTEM"):
                    udb = load_data("users")
                    # DEEP CHECK: Compare as strings and ignore case
                    match = udb[(udb['username'] == input_u) & (udb['password'] == input_p)]
                    
                    if not match.empty:
                        st.session_state.auth = True
                        st.session_state.user = input_u
                        st.session_state.role = match.iloc[0]['role']
                        st.success("Access Granted!")
                        st.rerun()
                    else:
                        st.error("Access Denied: Check Username or Password")
    st.stop()

# --- 6. MAIN APP REFRESH ---
stock_df = load_data("inventory")
sales_df = load_data("sales")
users_df = load_data("users")

# --- 7. SIDEBAR ---
with st.sidebar:
    st.title("LOG MASTER")
    st.write(f"Logged in: **{st.session_state.user}**")
    nav = ["📊 Insights", "🛒 Sales POS", "📦 Inventory", "⚙️ Admin"]
    if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
    menu = st.radio("Menu", nav)
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 8. THE MODULES (DASHBOARD & ADMIN) ---
if menu == "📊 Insights":
    st.title("Business Insights")
    st.metric("Total Revenue", f"GHS {sales_df['Total'].astype(float).sum():,.2f}")
    st.dataframe(sales_df.tail(10), use_container_width=True)

elif menu == "⚙️ Admin":
    st.title("Staff & Security")
    t1, t2 = st.tabs(["User Management", "Database"])
    
    with t1:
        st.subheader("Existing Staff")
        st.table(users_df)
        
        with st.form("add_user"):
            st.write("Add New Staff")
            new_u = st.text_input("New Username").upper().strip()
            new_p = st.text_input("New Password")
            new_r = st.selectbox("Role", ["STAFF", "OWNER"])
            if st.form_submit_button("Register User"):
                if new_u and new_p:
                    entry = pd.DataFrame([{"username": new_u, "password": new_p, "role": new_r}])
                    pd.concat([users_df, entry], ignore_index=True).to_csv(FILES["users"], index=False)
                    st.success("User Added!")
                    st.rerun()