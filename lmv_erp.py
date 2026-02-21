import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. MODERN UI CONFIGURATION ---
def apply_modern_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 800; }
        .stMetric { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
        .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. IDENTITY & SETTINGS ---
COMPANY_NAME = "LOG MASTER VENTURES"
MASTER_PASS = st.secrets.get("ADMIN_PASSWORD", "master77")
st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="⚖️")
apply_modern_ui()

FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR, BACKUP_DIR = "product_images", "backups"

# --- 3. CORE FUNCTIONS ---
def get_data(key):
    try:
        df = pd.read_csv(FILES[key])
        return df
    except:
        return pd.DataFrame()

def init_system():
    for folder in [IMG_DIR, BACKUP_DIR]:
        if not os.path.exists(folder): os.makedirs(folder)
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=["username", "password", "role"] if key=="users" else []).to_csv(path, index=False)
    
    u_df = get_data("users")
    if u_df.empty or "ADMIN" not in u_df['username'].values:
        pd.DataFrame([{"username": "ADMIN", "password": MASTER_PASS, "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_system()

# --- 4. LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    with st.form("login"):
        u = st.text_input("User ID").upper().strip()
        p = st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN"):
            udb = get_data("users")
            match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
            if not match.empty:
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                st.rerun()
    st.stop()

# --- 5. MODULES ---
users_df = get_data("users")
menu = st.sidebar.radio("Navigation", ["📊 Insights", "⚙️ Admin"])

if menu == "📊 Insights":
    st.title(f"Welcome, {st.session_state.user}")

elif menu == "⚙️ Admin":
    st.title("⚙️ System Administration")
    t1, t2 = st.tabs(["👥 Staff Management", "🛡️ Database"])
    
    with t1:
        st.subheader("Current Staff List")
        st.dataframe(users_df[['username', 'role']], use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔑 Change User Password")
            # Deep check: Select user from the existing list
            user_to_change = st.selectbox("Select User", users_df['username'].tolist())
            new_pass = st.text_input("Enter New Password", type="password")
            if st.button("Update Password"):
                if new_pass:
                    # Absolute Index Update
                    users_df.loc[users_df['username'] == user_to_change, 'password'] = new_pass
                    users_df.to_csv(FILES["users"], index=False)
                    st.success(f"Password for {user_to_change} updated successfully!")
                else:
                    st.warning("Please enter a password.")

        with col2:
            st.markdown("### ➕ Register New Staff")
            with st.form("new_user"):
                nu = st.text_input("New Username").upper().strip()
                np = st.text_input("Initial Password")
                nr = st.selectbox("Role", ["STAFF", "OWNER"])
                if st.form_submit_button("Create Account"):
                    if nu and np:
                        new_row = pd.DataFrame([{"username": nu, "password": np, "role": nr}])
                        pd.concat([users_df, new_row], ignore_index=True).to_csv(FILES["users"], index=False)
                        st.success(f"User {nu} created!")
                        st.rerun()