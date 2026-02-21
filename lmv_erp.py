import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIG & HIGH-SECURITY SECRETS ---
COMPANY = "LOG MASTER VENTURES"
MASTER_KEY = "Premium@1233"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"

FILES = {
    "stock": "lmv_stock.csv",
    "sales": "lmv_sales.csv",
    "repairs": "lmv_repairs.csv",
    "users": "lmv_users.csv"
}

# --- 2. THE SCHEMA GUARDIAN (Fixes Deleted Columns Automatically) ---
def schema_enforcement():
    SCHEMAS = {
        "stock": ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock", "Image_URL"],
        "sales": ["Invoice_ID", "Timestamp", "Item", "Total", "Staff", "Payment"],
        "repairs": ["Repair_ID", "Cust_Phone", "Device", "Issue", "Status", "Price"],
        "users": ["username", "password", "role"]
    }

    for key, path in FILES.items():
        if not os.path.exists(path):
            df = pd.DataFrame(columns=SCHEMAS[key])
            if key == "users":
                df = pd.DataFrame([{"username": ADMIN_USER, "password": ADMIN_PASS, "role": "ADMIN"}])
            if key == "stock":
                df = pd.DataFrame([
                    {"Barcode": "LMV001", "Product Name": "iPhone 20W Plug", "Category": "Accessories", "Selling Price": 350.0, "Stock": 10, "Min_Stock": 2, "Image_URL": ""}
                ])
            df.to_csv(path, index=False)
        else:
            # Check for missing columns and restore them without losing data
            df = pd.read_csv(path)
            missing = [col for col in SCHEMAS[key] if col not in df.columns]
            if missing:
                for col in missing:
                    df[col] = 0.0 if col in ["Selling Price", "Total", "Price", "Stock"] else "N/A"
                df.to_csv(path, index=False)
                st.toast(f"System recovered missing columns in {key}!", icon="🛡️")

schema_enforcement()

# --- 3. UI SETUP ---
st.set_page_config(page_title=f"{COMPANY} ERP", layout="wide", page_icon="💼")

# --- 4. ACCESS CONTROL ---
if 'master_ok' not in st.session_state: st.session_state.master_ok = False
if 'staff_ok' not in st.session_state: st.session_state.staff_ok = False

if not st.session_state.master_ok:
    st.title("🔐 LOG MASTER MASTER GATE")
    m_key = st.text_input("Master Business Key", type="password")
    if st.button("Unlock Dashboard"):
        if m_key == MASTER_KEY:
            st.session_state.master_ok = True
            st.rerun()
        else: st.error("Access Denied.")
    st.stop()

if not st.session_state.staff_ok:
    st.subheader("👤 Staff Login")
    u, p = st.text_input("Username").upper(), st.text_input("Password", type="password")
    if st.button("Login"):
        if u == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.staff_ok = True
            st.session_state.user = u
            st.rerun()
        else: st.error("Invalid Credentials.")
    st.stop()

# --- 5. NAVIGATION ---
st.sidebar.title(f"{COMPANY}")
st.sidebar.info(f"User: {st.session_state.user}")
nav = st.sidebar.radio("Main Menu", ["🛒 POS", "📦 Inventory & Bulk", "🛠️ Repairs", "📊 Dashboard"])

if st.sidebar.button("Logout"):
    st.session_state.master_ok = False
    st.session_state.staff_ok = False
    st.rerun()

# --- 6. MODULES ---

if nav == "🛒 POS":
    st.header("Point of Sale")
    stock_df = pd.read_csv(FILES["stock"])
    if 'cart' not in st.session_state: st.session_state.cart = []

    def scan_logic():
        code = st.session_state.scanner_box
        match = stock_df[stock_df['Barcode'].astype(str) == str(code)]
        if not match.empty:
            st.session_state.cart.append(match.iloc[0].to_dict())
            st.toast(f"Added: {match.iloc[0]['Product Name']}")
        st.session_state.scanner_box = ""

    st.text_input("SCAN BARCODE", key="scanner_box", on_change=scan_logic)

    if st.session_state.cart:
        c_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(c_df[["Product Name", "Selling Price"]], use_container_width=True)
        total = c_df["Selling Price"].sum()
        st.subheader(f"Total: GHS {total:,.2f}")
        if st.button("Checkout"):
            sales_df = pd.read_csv(FILES["sales"])
            new_sale = pd.DataFrame([{"Invoice_ID": f"INV{datetime.now().strftime('%M%S')}", "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": "Retail Sale", "Total": total, "Staff": st.session_state.user, "Payment": "Cash/MoMo"}])
            pd.concat([sales_df, new_sale], ignore_index=True).to_csv(FILES["sales"], index=False)
            st.session_state.cart = []
            st.success("Sale Complete!")
            st.rerun()

elif nav == "📦 Inventory & Bulk":
    st.header("Inventory Management")
    inv_df = pd.read_csv(FILES["stock"])
    
    tab1, tab2 = st.tabs(["Single Item", "Bulk Import (Excel/CSV)"])
    
    with tab1:
        with st.form("single_add"):
            b, n, p, s = st.text_input("Barcode"), st.text_input("Name"), st.number_input("Price"), st.number_input("Qty")
            if st.form_submit_button("Add Item"):
                new_row = pd.DataFrame([{"Barcode": b, "Product Name": n, "Selling Price": p, "Stock": s, "Min_Stock": 5}])
                pd.concat([inv_df, new_row], ignore_index=True).to_csv(FILES["stock"], index=False)
                st.success("Added!")
                st.rerun()
    
    with tab2:
        st.write("Upload a file with columns: `Barcode`, `Product Name`, `Selling Price`, `Stock`")
        uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])
        if uploaded_file:
            if uploaded_file.name.endswith('.csv'):
                import_df = pd.read_csv(uploaded_file)
            else:
                import_df = pd.read_excel(uploaded_file)
            
            if st.button("Confirm Bulk Import"):
                pd.concat([inv_df, import_df], ignore_index=True).to_csv(FILES["stock"], index=False)
                st.success(f"Imported {len(import_df)} items!")
                st.rerun()
    
    st.dataframe(inv_df, use_container_width=True)

elif nav == "🛠️ Repairs":
    st.header("Repair Tracker")
    rep_df = pd.read_csv(FILES["repairs"])
    st.dataframe(rep_df, use_container_width=True)
    with st.form("rep_form"):
        ph, dv, is_ = st.text_input("Customer Phone"), st.text_input("Device"), st.text_area("Issue")
        if st.form_submit_button("Log Repair"):
            rid = f"REP{datetime.now().strftime('%M%S')}"
            new_rep = pd.DataFrame([{"Repair_ID": rid, "Cust_Phone": ph, "Device": dv, "Issue": is_, "Status": "Received", "Price": 0.0}])
            pd.concat([rep_df, new_rep], ignore_index=True).to_csv(FILES["repairs"], index=False)
            st.success(f"Logged ID: {rid}")
            st.rerun()

elif nav == "📊 Dashboard":
    st.header("Business Summary")
    s_df = pd.read_csv(FILES["sales"])
    st.metric("Total Revenue", f"GHS {s_df['Total'].sum():,.2f}")
    st.line_chart(s_df.tail(10).set_index("Timestamp")["Total"])