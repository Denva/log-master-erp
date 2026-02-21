import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. GLOBAL SETTINGS ---
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

# --- 2. THE "NO-ERROR" ENGINE (Self-Healing) ---
# This function checks if files exist. If not, it creates them so the code never fails.
def system_self_heal():
    for key, path in FILES.items():
        if not os.path.exists(path):
            if key == "stock":
                cols = ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock", "Image_URL"]
            elif key == "sales":
                cols = ["Invoice_ID", "Timestamp", "Item", "Total", "Staff", "Payment"]
            elif key == "repairs":
                cols = ["Repair_ID", "Cust_Phone", "Device", "Issue", "Status", "Price"]
            elif key == "users":
                cols = ["username", "password", "role"]
            
            df = pd.DataFrame(columns=cols)
            if key == "users":
                # Inject your specific admin credentials immediately
                df = pd.DataFrame([{"username": ADMIN_USER, "password": ADMIN_PASS, "role": "ADMIN"}])
            
            df.to_csv(path, index=False)

# Run health check immediately on startup
system_self_heal()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title=f"{COMPANY} ERP", layout="wide", page_icon="🏢")

# --- 4. LAYER 1: MASTER SECURITY GATE ---
if 'master_unlocked' not in st.session_state:
    st.session_state.master_unlocked = False

if not st.session_state.master_unlocked:
    st.title(f"🔐 {COMPANY} - Master Access")
    m_key = st.text_input("Enter Master Business Key", type="password", help="Use your Premium Master Key")
    if st.button("Unlock System"):
        if m_key == MASTER_KEY:
            st.session_state.master_unlocked = True
            st.rerun()
        else:
            st.error("Invalid Master Key. Access Denied.")
    st.stop()

# --- 5. LAYER 2: STAFF LOGIN GATE ---
if 'staff_auth' not in st.session_state:
    st.session_state.staff_auth = False

if not st.session_state.staff_auth:
    st.subheader("👤 Staff Login")
    u_name = st.text_input("Username").strip().upper()
    p_word = st.text_input("Password", type="password")
    
    if st.button("Login"):
        users_df = pd.read_csv(FILES["users"])
        # Direct check against your Admin credentials
        if u_name == ADMIN_USER and p_word == ADMIN_PASS:
            st.session_state.staff_auth = True
            st.session_state.current_user = ADMIN_USER
            st.rerun()
        # Check database for other staff
        elif not users_df[(users_df['username'] == u_name) & (users_df['password'] == p_word)].empty:
            st.session_state.staff_auth = True
            st.session_state.current_user = u_name
            st.rerun()
        else:
            st.error("Access Denied. Check Username/Password.")
    st.stop()

# --- 6. APP NAVIGATION ---
st.sidebar.title(f"Logged in: {st.session_state.current_user}")
menu = st.sidebar.radio("Navigate", ["🛒 POS (Barcode Scan)", "📦 Inventory Control", "🔧 Repair Tracking", "📊 Sales Reports"])

if st.sidebar.button("Logout"):
    st.session_state.master_unlocked = False
    st.session_state.staff_auth = False
    st.rerun()

# --- 7. MODULE: BARCODE POS ---
if menu == "🛒 POS (Barcode Scan)":
    st.header("⚡ Fast-Scan Checkout")
    stock_df = pd.read_csv(FILES["stock"])
    
    if 'cart' not in st.session_state:
        st.session_state.cart = []

    # Scanner Function
    def handle_scan():
        code = st.session_state.barcode_scanner_input
        if code:
            match = stock_df[stock_df['Barcode'].astype(str) == str(code)]
            if not match.empty:
                st.session_state.cart.append(match.iloc[0].to_dict())
                st.toast(f"Added {match.iloc[0]['Product Name']}", icon="✅")
            else:
                st.error(f"Barcode '{code}' not found in stock.")
        st.session_state.barcode_scanner_input = "" # Clear for next beep

    st.text_input("BEEP BARCODE HERE", key="barcode_scanner_input", on_change=handle_scan)

    if st.session_state.cart:
        st.write("### Current Items")
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df[["Product Name", "Selling Price"]], use_container_width=True)
        total = cart_df["Selling Price"].sum()
        st.subheader(f"Total Amount: GHS {total:,.2f}")
        
        if st.button("Complete Transaction"):
            sales_df = pd.read_csv(FILES["sales"])
            new_sale = pd.DataFrame([{
                "Invoice_ID": f"INV-{datetime.now().strftime('%d%H%M')}",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Item": ", ".join(cart_df["Product Name"].tolist()),
                "Total": total,
                "Staff": st.session_state.current_user,
                "Payment": "Verified"
            }])
            pd.concat([sales_df, new_sale], ignore_index=True).to_csv(FILES["sales"], index=False)
            st.session_state.cart = []
            st.success("Sale Recorded Successfully!")
            st.rerun()
            
# --- 8. MODULE: INVENTORY ---
elif menu == "📦 Inventory Control":
    st.header("Stock Management")
    stock_df = pd.read_csv(FILES["stock"])
    st.dataframe(stock_df, use_container_width=True)
    
    with st.expander("➕ Add New Item to Stock"):
        with st.form("add_item_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_b = st.text_input("Barcode Number")
                new_n = st.text_input("Product Name")
            with col_b:
                new_p = st.number_input("Selling Price (GHS)", min_value=0.0)
                new_s = st.number_input("Stock Quantity", min_value=0)
            
            if st.form_submit_button("Save Product"):
                if new_b and new_n:
                    new_entry = pd.DataFrame([{"Barcode": new_b, "Product Name": new_n, "Selling Price": new_p, "Stock": new_s, "Min_Stock": 5}])
                    pd.concat([stock_df, new_entry], ignore_index=True).to_csv(FILES["stock"], index=False)
                    st.success(f"{new_n} added to inventory!")
                    st.rerun()
                else:
                    st.error("Barcode and Name are required!")

# --- 9. MODULE: REPAIRS ---
elif menu == "🔧 Repair Tracking":
    st.header("Repair Center")
    rep_df = pd.read_csv(FILES["repairs"])
    st.dataframe(rep_df, use_container_width=True)
    
    with st.form("log_repair"):
        phone = st.text_input("Customer Phone Number")
        device = st.text_input("Device Model (e.g. Samsung S24)")
        problem = st.text_area("Fault Description")
        if st.form_submit_button("Create Repair Order"):
            rid = f"REP-{datetime.now().strftime('%M%S')}"
            new_r = pd.DataFrame([{"Repair_ID": rid, "Cust_Phone": phone, "Device": device, "Issue": problem, "Status": "Pending", "Price": 0.0}])
            pd.concat([rep_df, new_r], ignore_index=True).to_csv(FILES["repairs"], index=False)
            st.success(f"Order Created! ID: {rid}")
            st.rerun()

# --- 10. MODULE: ANALYTICS ---
elif menu == "📊 Sales Reports":
    st.header("Business Performance")
    sales_df = pd.read_csv(FILES["sales"])
    if not sales_df.empty:
        st.metric("Total Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        st.write("### Recent Sales")
        st.dataframe(sales_df.tail(10), use_container_width=True)
    else:
        st.info("No sales data available yet.")