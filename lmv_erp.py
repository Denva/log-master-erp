import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CORE IDENTITY & SECRETS ---
COMPANY = "LOG MASTER VENTURES"
MASTER_KEY = "Premium@1233"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"
WHATSAPP_LINK = "https://wa.me/"

FILES = {
    "stock": "lmv_stock.csv",
    "sales": "lmv_sales.csv",
    "repairs": "lmv_repairs.csv",
    "users": "lmv_users.csv"
}

# --- 2. THE SCHEMA GUARDIAN (Safety First) ---
def guardian_audit():
    SCHEMAS = {
        "stock": ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock", "Image_URL"],
        "sales": ["Invoice_ID", "Timestamp", "Item", "Total", "Staff", "Payment"],
        "repairs": ["Repair_ID", "Cust_Phone", "Device", "Issue", "Status", "Price"],
        "users": ["username", "password", "role"]
    }
    for key, cols in SCHEMAS.items():
        path = FILES[key]
        if not os.path.exists(path):
            df = pd.DataFrame(columns=cols)
            if key == "users": df = pd.DataFrame([{"username": ADMIN_USER, "password": ADMIN_PASS, "role": "ADMIN"}])
            df.to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            missing = [c for c in cols if c not in df.columns]
            if missing:
                for c in missing:
                    df[c] = 5 if c == "Min_Stock" else (0.0 if c in ["Price", "Total", "Selling Price"] else "N/A")
                df.to_csv(path, index=False)

guardian_audit()

# --- 3. SECURITY GATES ---
st.set_page_config(page_title=f"{COMPANY} ERP", layout="wide")
if 'm_auth' not in st.session_state: st.session_state.m_auth = False
if 's_auth' not in st.session_state: st.session_state.s_auth = False

if not st.session_state.m_auth:
    st.title("🔐 Master Gate")
    if st.text_input("Master Key", type="password") == MASTER_KEY:
        if st.button("Unlock"): 
            st.session_state.m_auth = True
            st.rerun()
    st.stop()

if not st.session_state.s_auth:
    st.title("👤 Staff Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u.upper() == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.s_auth, st.session_state.user = True, u.upper()
            st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
nav = st.sidebar.radio("Menu", ["🛒 POS", "📦 Inventory", "🔧 Repairs", "📊 Dashboard"])

# --- 5. MODULES (Upgraded) ---

if nav == "🛒 POS":
    st.header("Point of Sale")
    stock_df = pd.read_csv(FILES["stock"])
    if 'cart' not in st.session_state: st.session_state.cart = []

    def on_scan():
        code = st.session_state.scanner
        match = stock_df[stock_df['Barcode'].astype(str) == str(code)]
        if not match.empty:
            st.session_state.cart.append(match.iloc[0].to_dict())
        st.session_state.scanner = ""

    st.text_input("Scan Item", key="scanner", on_change=on_scan)
    
    if st.session_state.cart:
        c_df = pd.DataFrame(st.session_state.cart)
        st.table(c_df[["Product Name", "Selling Price"]])
        total = c_df["Selling Price"].sum()
        
        # FEATURE: Professional Invoicing (WhatsApp Preview)
        if st.button(f"✅ Complete Sale & Send Receipt (GHS {total})"):
            inv_id = f"LMV-{datetime.now().strftime('%d%H%M')}"
            sales_df = pd.read_csv(FILES["sales"])
            new_sale = pd.DataFrame([{"Invoice_ID": inv_id, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": "Retail Sale", "Total": total, "Staff": st.session_state.user, "Payment": "Cash"}])
            pd.concat([sales_df, new_sale], ignore_index=True).to_csv(FILES["sales"], index=False)
            
            # Prepare WhatsApp Receipt text
            receipt_text = f"📄 *{COMPANY} RECEIPT*\nID: {inv_id}\nTotal: GHS {total}\nThank you for your business!"
            st.success("Sale Recorded!")
            st.info("Copy this for the customer:")
            st.code(receipt_text)
            st.session_state.cart = []

elif nav == "📦 Inventory":
    st.header("Stock Control")
    df = pd.read_csv(FILES["stock"])
    
    # FEATURE: Low-Stock Alerts
    low_stock = df[df['Stock'] <= df['Min_Stock']]
    if not low_stock.empty:
        st.error(f"⚠️ ALERT: {len(low_stock)} items are running low!")
        st.dataframe(low_stock[["Product Name", "Stock", "Min_Stock"]])

    st.write("### Full Inventory")
    st.dataframe(df, use_container_width=True)

elif nav == "🔧 Repairs":
    st.header("Repair Center")
    rep_df = pd.read_csv(FILES["repairs"])
    
    with st.expander("New Repair Entry"):
        with st.form("r_form"):
            ph, dv, is_ = st.text_input("Customer Phone"), st.text_input("Device"), st.text_area("Issue")
            if st.form_submit_button("Log Repair"):
                rid = f"REP-{datetime.now().strftime('%M%S')}"
                new_r = pd.DataFrame([{"Repair_ID": rid, "Cust_Phone": ph, "Device": dv, "Issue": is_, "Status": "Received", "Price": 0.0}])
                pd.concat([rep_df, new_r], ignore_index=True).to_csv(FILES["repairs"], index=False)
                st.rerun()

    # FEATURE: WhatsApp Repair Status
    st.write("### Active Repairs")
    for i, row in rep_df.iterrows():
        cols = st.columns([2, 2, 2, 1])
        cols[0].write(row['Device'])
        cols[1].write(row['Status'])
        cols[2].write(row['Cust_Phone'])
        
        # Generate WhatsApp link for status update
        msg = f"Hello! Your {row['Device']} repair status at {COMPANY} is now: *{row['Status']}*."
        wa_url = f"https://wa.me/{row['Cust_Phone']}?text={urllib.parse.quote(msg)}"
        cols[3].link_button("📲 SMS", wa_url)

elif nav == "📊 Dashboard":
    st.header("Business Reports")
    s_df = pd.read_csv(FILES["sales"])
    st.metric("Total Revenue", f"GHS {s_df['Total'].sum():,.2f}")
    st.line_chart(s_df.tail(20).set_index("Timestamp")["Total"])