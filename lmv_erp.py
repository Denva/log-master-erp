import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import urllib.parse

# --- 1. SETTINGS & BRANDING ---
COMPANY = "LOG MASTER VENTURES"
MASTER_KEY = "Premium@1233"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"
LOGO_FILE = "logo.png"
BACKUP_DIR = "LMV_BACKUPS"

# Precise file mapping
FILES = {
    "stock": "lmv_stock.csv",
    "sales": "lmv_sales.csv",
    "repairs": "lmv_repairs.csv",
    "users": "lmv_users.csv"
}

# --- 2. THE DATA GUARDIAN (Stops Column Mixing) ---
def final_integrity_check():
    """Forces every file to have the correct columns and no other data."""
    BLUEPRINTS = {
        "stock": ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock"],
        "sales": ["Invoice_ID", "Timestamp", "Item", "Total", "Staff", "Payment"],
        "repairs": ["Repair_ID", "Cust_Phone", "Device", "Issue", "Status", "Price"],
        "users": ["username", "password", "role"]
    }
    
    for key, cols in BLUEPRINTS.items():
        path = FILES[key]
        if not os.path.exists(path):
            df = pd.DataFrame(columns=cols)
            if key == "users":
                df = pd.DataFrame([{"username": ADMIN_USER, "password": ADMIN_PASS, "role": "ADMIN"}])
            df.to_csv(path, index=False)
        else:
            # Deep clean the file structure
            df = pd.read_csv(path)
            # Remove any columns that don't belong (Stops 'different things together')
            valid_cols = [c for c in df.columns if c in cols]
            df = df[valid_cols]
            # Add missing columns
            missing = [c for c in cols if c not in df.columns]
            for c in missing:
                df[c] = 0.0 if c in ["Selling Price", "Total", "Price", "Stock", "Min_Stock"] else "N/A"
            df.to_csv(path, index=False)

# Run integrity check on startup
final_integrity_check()

# --- 3. SECURITY GATE ---
st.set_page_config(page_title=COMPANY, layout="wide")

if os.path.exists(LOGO_FILE):
    st.sidebar.image(LOGO_FILE, use_container_width=True)
else:
    st.sidebar.title(COMPANY)

if 'm_ok' not in st.session_state: st.session_state.m_ok = False
if 's_ok' not in st.session_state: st.session_state.s_ok = False

if not st.session_state.m_ok:
    st.title("🔐 Master Gate")
    if st.text_input("Master Key", type="password") == MASTER_KEY:
        if st.button("Unlock"): 
            st.session_state.m_ok = True
            st.rerun()
    st.stop()

if not st.session_state.s_ok:
    st.subheader("👤 Staff Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u.upper() == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.s_ok, st.session_state.user = True, u.upper()
            st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
nav = st.sidebar.radio("Menu", ["🛒 POS", "📦 Inventory", "🔧 Repairs", "📊 Dashboard"])

if st.sidebar.button("Logout"):
    st.session_state.m_ok = st.session_state.s_ok = False
    st.rerun()

# --- 5. ISOLATED MODULES ---

# --- POS (SALES ONLY) ---
if nav == "🛒 POS":
    st.header("Point of Sale")
    # Load ONLY stock for POS
    pos_stock = pd.read_csv(FILES["stock"])
    if 'cart' not in st.session_state: st.session_state.cart = []

    def scan_item():
        code = st.session_state.pos_scan
        match = pos_stock[pos_stock['Barcode'].astype(str) == str(code)]
        if not match.empty:
            st.session_state.cart.append(match.iloc[0].to_dict())
        st.session_state.pos_scan = ""

    st.text_input("Scan Barcode", key="pos_scan", on_change=scan_item)
    
    if st.session_state.cart:
        c_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(c_df[["Product Name", "Selling Price"]], use_container_width=True)
        total = c_df["Selling Price"].sum()
        if st.button(f"Complete Sale (GHS {total})"):
            sales_db = pd.read_csv(FILES["sales"])
            new_s = pd.DataFrame([{"Invoice_ID": f"INV-{datetime.now().strftime('%M%S')}", "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": "Retail", "Total": total, "Staff": st.session_state.user, "Payment": "Cash"}])
            pd.concat([sales_db, new_s], ignore_index=True).to_csv(FILES["sales"], index=False)
            st.session_state.cart = []
            st.success("Sale Recorded!")
            st.rerun()

# --- INVENTORY (STOCK ONLY) ---
elif nav == "📦 Inventory":
    st.header("Inventory Management")
    # Load ONLY stock
    inv_df = pd.read_csv(FILES["stock"])
    
    # Check for empty data
    if inv_df.empty:
        st.info("Inventory is currently empty. Add your first item below.")
    
    st.dataframe(inv_df, use_container_width=True)
    
    with st.expander("➕ Add New Stock Item"):
        with st.form("stock_form"):
            b, n, p, s = st.text_input("Barcode"), st.text_input("Name"), st.number_input("Price"), st.number_input("Qty")
            if st.form_submit_button("Save Product"):
                new_p = pd.DataFrame([{"Barcode": b, "Product Name": n, "Selling Price": p, "Stock": s, "Min_Stock": 5}])
                pd.concat([inv_df, new_p], ignore_index=True).to_csv(FILES["stock"], index=False)
                st.success("Product Added!")
                st.rerun()

# --- REPAIRS (REPAIRS ONLY) ---
elif nav == "🔧 Repairs":
    st.header("Repair Tracker")
    # Load ONLY repairs
    rep_df = pd.read_csv(FILES["repairs"])
    
    st.dataframe(rep_df, use_container_width=True)
    
    with st.expander("➕ Log New Repair"):
        with st.form("rep_form"):
            ph, dv, is_ = st.text_input("Phone"), st.text_input("Device"), st.text_area("Issue")
            if st.form_submit_button("Save Repair"):
                rid = f"REP-{datetime.now().strftime('%M%S')}"
                new_r = pd.DataFrame([{"Repair_ID": rid, "Cust_Phone": ph, "Device": dv, "Issue": is_, "Status": "Received", "Price": 0.0}])
                pd.concat([rep_df, new_r], ignore_index=True).to_csv(FILES["repairs"], index=False)
                st.success("Repair Logged!")
                st.rerun()

    # WhatsApp Notifications
    for i, row in rep_df.iterrows():
        msg = f"Hello! Your {row['Device']} status is: {row['Status']}."
        st.link_button(f"📲 WhatsApp {row['Cust_Phone']}", f"https://wa.me/{row['Cust_Phone']}?text={urllib.parse.quote(msg)}")

# --- DASHBOARD (SALES DATA) ---
elif nav == "📊 Dashboard":
    st.header("Business Reports")
    final_sales = pd.read_csv(FILES["sales"])
    st.metric("Total Sales", f"GHS {final_sales['Total'].sum():,.2f}")
    st.dataframe(final_sales, use_container_width=True)