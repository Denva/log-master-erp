import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. SYSTEM IDENTITY & SECRETS ---
COMPANY = "LOG MASTER VENTURES"
MASTER_KEY = "Premium@1233"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"
LOGO_FILE = "logo.png"  # Ensure your logo is named logo.png in the same folder

FILES = {
    "stock": "lmv_stock.csv",
    "sales": "lmv_sales.csv",
    "repairs": "lmv_repairs.csv",
    "users": "lmv_users.csv"
}

# --- 2. THE SCHEMA GUARDIAN (Day 1 Consistency Logic) ---
def schema_guardian():
    BLUEPRINTS = {
        "stock": ["Barcode", "Product Name", "Category", "Selling Price", "Stock", "Min_Stock", "Image_URL"],
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
            # Check for deleted columns and restore them without losing rows
            df = pd.read_csv(path)
            missing = [c for c in cols if c not in df.columns]
            if missing:
                for c in missing:
                    # Default numeric columns to 0 or 5 (for stock), text to "N/A"
                    if c == "Min_Stock": df[c] = 5
                    elif c in ["Selling Price", "Total", "Price", "Stock"]: df[c] = 0.0
                    else: df[c] = "N/A"
                df.to_csv(path, index=False)
                st.toast(f"Guardian Restored: {missing}", icon="🛡️")

# Run Guardian Audit immediately
schema_guardian()

# --- 3. PAGE SETUP & BRANDING ---
st.set_page_config(page_title=f"{COMPANY} HQ", layout="wide", page_icon="🏢")

# Display Logo or Company Name in Sidebar
if os.path.exists(LOGO_FILE):
    st.sidebar.image(LOGO_FILE, use_container_width=True)
else:
    st.sidebar.title(f"🏢 {COMPANY}")

# --- 4. ACCESS CONTROL (2-LAYER SECURITY) ---
if 'master_verified' not in st.session_state: st.session_state.master_verified = False
if 'staff_verified' not in st.session_state: st.session_state.staff_verified = False

if not st.session_state.master_verified:
    st.title(f"🔐 {COMPANY} Master Gate")
    m_code = st.text_input("Master Business Key", type="password")
    if st.button("Unlock System"):
        if m_code == MASTER_KEY:
            st.session_state.master_verified = True
            st.rerun()
        else: st.error("Access Denied.")
    st.stop()

if not st.session_state.staff_verified:
    st.subheader("👤 Staff Identity Required")
    u_log = st.text_input("Username").upper().strip()
    p_log = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_log == ADMIN_USER and p_log == ADMIN_PASS:
            st.session_state.staff_verified = True
            st.session_state.current_user = u_log
            st.rerun()
        else: st.error("Invalid Username or Password.")
    st.stop()

# --- 5. APP NAVIGATION ---
nav = st.sidebar.radio("Navigate", ["🛒 POS & Receipts", "📦 Inventory Control", "🔧 Repair Tracking", "📊 Business Reports"])

if st.sidebar.button("Logout"):
    st.session_state.master_verified = False
    st.session_state.staff_verified = False
    st.rerun()

# --- 6. CORE MODULES ---

# MODULE: POS
if nav == "🛒 POS & Receipts":
    st.header("Point of Sale")
    df_stock = pd.read_csv(FILES["stock"])
    if 'cart' not in st.session_state: st.session_state.cart = []

    def handle_scan():
        code = st.session_state.pos_scanner
        match = df_stock[df_stock['Barcode'].astype(str) == str(code)]
        if not match.empty:
            st.session_state.cart.append(match.iloc[0].to_dict())
            st.toast(f"Added {match.iloc[0]['Product Name']}")
        st.session_state.pos_scanner = ""

    st.text_input("BEEP BARCODE HERE", key="pos_scanner", on_change=handle_scan)
    
    if st.session_state.cart:
        c_df = pd.DataFrame(st.session_state.cart)
        st.table(c_df[["Product Name", "Selling Price"]])
        total = c_df["Selling Price"].sum()
        
        if st.button(f"💰 Complete Sale (GHS {total:,.2f})"):
            inv_id = f"LMV-{datetime.now().strftime('%d%H%M')}"
            sales_df = pd.read_csv(FILES["sales"])
            new_sale = pd.DataFrame([{
                "Invoice_ID": inv_id, 
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                "Item": "Retail Sale", 
                "Total": total, 
                "Staff": st.session_state.current_user, 
                "Payment": "Verified"
            }])
            pd.concat([sales_df, new_sale], ignore_index=True).to_csv(FILES["sales"], index=False)
            
            # Professional Receipt Preview
            receipt = f"*{COMPANY} RECEIPT*\nID: {inv_id}\nTotal: GHS {total}\nServed by: {st.session_state.current_user}\nThank you!"
            st.success("Transaction Complete!")
            st.info("Copy for Customer WhatsApp:")
            st.code(receipt)
            st.session_state.cart = []

# MODULE: INVENTORY
elif nav == "📦 Inventory Control":
    st.header("Inventory Management")
    inv_df = pd.read_csv(FILES["stock"])
    
    # Low Stock Alert Check
    low_stock = inv_df[inv_df['Stock'].astype(float) <= inv_df['Min_Stock'].astype(float)]
    if not low_stock.empty:
        st.warning(f"⚠️ LOW STOCK ALERT: {len(low_stock)} items need attention!")
        st.dataframe(low_stock[["Product Name", "Stock", "Min_Stock"]], use_container_width=True)

    st.write("### Full Stock Data")
    st.dataframe(inv_df, use_container_width=True)

# MODULE: REPAIRS
elif nav == "🔧 Repair Tracking":
    st.header("Repair Center")
    rep_df = pd.read_csv(FILES["repairs"])
    
    with st.expander("➕ Log New Repair Entry"):
        with st.form("repair_form"):
            c_ph, c_dv, c_is = st.text_input("Customer Phone"), st.text_input("Device"), st.text_area("Fault Description")
            if st.form_submit_button("Save Repair Order"):
                rid = f"REP-{datetime.now().strftime('%M%S')}"
                new_rep = pd.DataFrame([{"Repair_ID": rid, "Cust_Phone": c_ph, "Device": c_dv, "Issue": c_is, "Status": "Received", "Price": 0.0}])
                pd.concat([rep_df, new_rep], ignore_index=True).to_csv(FILES["repairs"], index=False)
                st.rerun()

    st.write("### Active Trackings")
    for i, row in rep_df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"**{row['Device']}**")
        c2.write(f"Status: {row['Status']}")
        c3.write(row['Cust_Phone'])
        
        # WhatsApp Notification Link
        msg = f"Hello! Your {row['Device']} repair is currently: *{row['Status']}* at {COMPANY}."
        wa_url = f"https://wa.me/{row['Cust_Phone']}?text={urllib.parse.quote(msg)}"
        c4.link_button("📲 Notify", wa_url)

# MODULE: REPORTS
elif nav == "📊 Business Reports":
    st.header("Executive Analytics")
    s_df = pd.read_csv(FILES["sales"])
    st.metric("Total Revenue", f"GHS {s_df['Total'].sum():,.2f}")
    st.write("### Recent Sales Timeline")
    st.line_chart(s_df.tail(20).set_index("Timestamp")["Total"])