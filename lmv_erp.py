import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SYSTEM IDENTITY & SECRETS ---
COMPANY = "LOG MASTER VENTURES"
MASTER_KEY = "Premium@1233"  # Your Custom Master Key
FILES = {
    "stock": "lmv_stock.csv",
    "sales": "lmv_sales.csv",
    "repairs": "lmv_repairs.csv",
    "users": "lmv_users.csv"
}

# --- 2. DATA INTEGRITY ENGINE (Self-Healing) ---
def initialize_system():
    for key, path in FILES.items():
        if not os.path.exists(path):
            if key == "stock":
                cols = ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock", "Image_URL"]
            elif key == "sales":
                cols = ["Invoice_ID", "Timestamp", "Item", "Qty", "Total", "Staff", "Payment"]
            elif key == "repairs":
                cols = ["Repair_ID", "Cust_Phone", "Device", "Issue", "Status", "Price"]
            elif key == "users":
                cols = ["username", "password", "role"]
            
            df = pd.DataFrame(columns=cols)
            # Default Admin User with your specific password
            if key == "users":
                df = pd.DataFrame([{"username": "ADMIN", "password": "Premium@09", "role": "ADMIN"}])
            
            df.to_csv(path, index=False)

# Auto-fix databases on launch
initialize_system()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title=f"{COMPANY} HQ", layout="wide", page_icon="🏢")

# --- 4. SECURITY LAYER 1: MASTER ACCESS ---
if 'master_unlocked' not in st.session_state:
    st.session_state.master_unlocked = False

if not st.session_state.master_unlocked:
    st.title(f"🔐 {COMPANY} - Master Access")
    m_key = st.text_input("Enter Master Business Key", type="password")
    if st.button("Unlock System"):
        if m_key == MASTER_KEY:
            st.session_state.master_unlocked = True
            st.rerun()
        else:
            st.error("Invalid Master Key. Access Denied.")
    st.stop()

# --- 5. SECURITY LAYER 2: STAFF LOGIN ---
if 'staff_auth' not in st.session_state:
    st.session_state.staff_auth = False

if not st.session_state.staff_auth:
    st.subheader("👤 Staff Identity Required")
    u_name = st.text_input("Username").upper().strip()
    p_word = st.text_input("Password", type="password")
    
    if st.button("Login"):
        users_df = pd.read_csv(FILES["users"])
        # Check against your specific Admin credentials first
        if u_name == "ADMIN" and p_word == "Premium@09":
            st.session_state.staff_auth = True
            st.session_state.current_user = "ADMIN"
            st.rerun()
        # Then check database for other staff
        elif not users_df[(users_df['username'] == u_name) & (users_df['password'] == p_word)].empty:
            st.session_state.staff_auth = True
            st.session_state.current_user = u_name
            st.rerun()
        else:
            st.error("Invalid Username or Password.")
    st.stop()

# --- 6. NAVIGATION ---
st.sidebar.title(f"User: {st.session_state.current_user}")
menu = st.sidebar.radio("Navigate", ["🛒 Barcode POS", "📦 Inventory", "🔧 Repairs", "📈 Sales Analysis"])

if st.sidebar.button("Logout"):
    st.session_state.master_unlocked = False
    st.session_state.staff_auth = False
    st.rerun()

# --- 7. BARCODE POS ---
if menu == "🛒 Barcode POS":
    st.header("⚡ Fast Checkout")
    stock_df = pd.read_csv(FILES["stock"])
    if 'cart' not in st.session_state: st.session_state.cart = []

    def scan_item():
        code = st.session_state.barcode_scan
        match = stock_df[stock_df['Barcode'].astype(str) == str(code)]
        if not match.empty:
            st.session_state.cart.append(match.iloc[0].to_dict())
            st.toast(f"Added {match.iloc[0]['Product Name']}")
        st.session_state.barcode_scan = ""

    st.text_input("BEEP BARCODE HERE", key="barcode_scan", on_change=scan_item)

    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.table(cart_df[["Product Name", "Selling Price"]])
        total = cart_df["Selling Price"].sum()
        st.subheader(f"Total: GHS {total:,.2f}")
        if st.button("Finalize Sale"):
            sales_df = pd.read_csv(FILES["sales"])
            new_sale = pd.DataFrame([{
                "Invoice_ID": f"INV-{datetime.now().strftime('%M%S')}",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Item": ", ".join(cart_df["Product Name"].tolist()),
                "Qty": len(cart_df),
                "Total": total,
                "Staff": st.session_state.current_user,
                "Payment": "Cash/MoMo"
            }])
            pd.concat([sales_df, new_sale]).to_csv(FILES["sales"], index=False)
            st.session_state.cart = []
            st.success("Transaction Recorded!")
            st.rerun()

# --- 8. INVENTORY ---
elif menu == "📦 Inventory":
    st.header("Stock Management")
    df = pd.read_csv(FILES["stock"])
    st.dataframe(df)
    with st.expander("Add New Stock"):
        with st.form("add_stock"):
            b = st.text_input("Barcode")
            n = st.text_input("Product Name")
            p = st.number_input("Price (GHS)", min_value=0.0)
            q = st.number_input("Stock Qty", min_value=0)
            if st.form_submit_button("Add Item"):
                new_item = pd.DataFrame([{"Barcode": b, "Product Name": n, "Selling Price": p, "Stock": q, "Min_Stock": 5}])
                pd.concat([df, new_item]).to_csv(FILES["stock"], index=False)
                st.success("Inventory Updated!")
                st.rerun()

# --- 9. REPAIRS ---
elif menu == "🔧 Repairs":
    st.header("Repair Tracker")
    rep_df = pd.read_csv(FILES["repairs"])
    st.dataframe(rep_df)
    with st.form("rep_form"):
        c = st.text_input("Customer Phone")
        d = st.text_input("Device Model")
        i = st.text_area("Issue")
        if st.form_submit_button("Log Repair"):
            rid = f"REP-{datetime.now().strftime('%M%S')}"
            new_r = pd.DataFrame([{"Repair_ID": rid, "Cust_Phone": c, "Device": d, "Issue": i, "Status": "Received", "Price": 0.0}])
            pd.concat([rep_df, new_r]).to_csv(FILES["repairs"], index=False)
            st.success(f"Repair ID {rid} created.")
            st.rerun()