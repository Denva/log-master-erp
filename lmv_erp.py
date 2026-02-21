import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & IDENTITY ---
COMPANY_NAME = "LOG MASTER VENTURES"
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
HEADERS = {
    "sales": ["Timestamp", "Type", "Item", "Qty", "Price", "Total", "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="⚖️")

# --- 2. AUTO-REPAIR ENGINE (The "Anti-Mess" Logic) ---
def repair_and_load():
    data = {}
    for key, path in FILES.items():
        # Create file if it doesn't exist
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        
        df = pd.read_csv(path)
        
        # Check for missing columns and add them
        missing_cols = [c for c in HEADERS[key] if c not in df.columns]
        if missing_cols:
            for col in missing_cols:
                df[col] = 0.0 if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"] else ""
            df.to_csv(path, index=False)
        
        # Numeric Sanitization (Preventing 'Access Denied' and math errors)
        if key == "users":
            df['username'] = df['username'].astype(str).str.upper().str.strip()
            df['password'] = df['password'].astype(str).str.strip()
        elif key == "inventory":
            for col in ["Cost Price", "Selling Price", "Stock"]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        elif key == "sales":
            for col in ["Total", "Cost", "Profit", "Qty"]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        data[key] = df
    return data

# Initialize
db = repair_and_load()

# Ensure Admin exists
if db["users"].empty or "ADMIN" not in db["users"]['username'].values:
    admin_fix = pd.DataFrame([{"username": "ADMIN", "password": "master77", "role": "OWNER"}])
    pd.concat([db["users"], admin_fix], ignore_index=True).to_csv(FILES["users"], index=False)
    db = repair_and_load()

# --- 3. LOGIN SYSTEM ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center;'>⚖️ {COMPANY_NAME}</h1>", unsafe_allow_html=True)
    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("secure_login"):
                u_input = st.text_input("Username").upper().strip()
                p_input = st.text_input("Password", type="password").strip()
                if st.form_submit_button("LOGIN"):
                    # Match credentials
                    user_row = db["users"][(db["users"]['username'] == u_input) & (db["users"]['password'] == p_input)]
                    if not user_row.empty:
                        st.session_state.auth = True
                        st.session_state.user = u_input
                        st.session_state.role = user_row.iloc[0]['role']
                        st.rerun()
                    else:
                        st.error("Invalid Credentials. Please try again.")
    st.stop()

# --- 4. NAVIGATION & SIDEBAR ---
with st.sidebar:
    st.title("Main Menu")
    st.info(f"User: {st.session_state.user} ({st.session_state.role})")
    options = ["📊 Insights", "🛒 Sales & Repairs", "📦 Inventory", "⚙️ Admin"]
    if st.session_state.role != "OWNER": options.remove("⚙️ Admin")
    menu = st.radio("Go to:", options)
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 5. DASHBOARD ---
if menu == "📊 Insights":
    st.title("📊 Enterprise Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Warehouse Value", f"GHS { (db['inventory']['Stock'] * db['inventory']['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Total Sales", f"GHS {db['sales']['Total'].sum():,.2f}")
        c3.metric("Net Profit", f"GHS {db['sales']['Profit'].sum():,.2f}")
    st.subheader("Recent Activity")
    st.dataframe(db["sales"].tail(10), use_container_width=True)

# --- 6. SALES & REPAIRS ---
elif menu == "🛒 Sales & Repairs":
    st.title("🛒 Sales Terminal")
    t1, t2 = st.tabs(["Sell Product", "Register Repair"])
    
    with t1:
        if db["inventory"].empty:
            st.warning("Please add items to Inventory first.")
        else:
            with st.form("pos_sale"):
                item = st.selectbox("Product", db["inventory"]["Product Name"].tolist())
                qty = st.number_input("Qty", 1)
                price = st.number_input("Sale Price", 0.0)
                cust = st.text_input("Customer Name")
                if st.form_submit_button("COMPLETE SALE"):
                    cost_p = db["inventory"].loc[db["inventory"]["Product Name"] == item, "Cost Price"].values[0]
                    # Create dict with ALL 16 columns to avoid "messed up" structure
                    new_sale = {col: "" for col in HEADERS["sales"]}
                    new_sale.update({
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT",
                        "Item": item, "Qty": qty, "Price": price, "Total": qty*price,
                        "Cost": cost_p*qty, "Profit": (qty*price)-(cost_p*qty),
                        "Staff": st.session_state.user, "Cust_Name": cust, "Status": "Sold"
                    })
                    pd.concat([db["sales"], pd.DataFrame([new_sale])], ignore_index=True).to_csv(FILES["sales"], index=False)
                    # Deduct stock
                    db["inventory"].loc[db["inventory"]["Product Name"] == item, "Stock"] -= qty
                    db["inventory"].to_csv(FILES["inventory"], index=False)
                    st.success("Sale Recorded!")
                    st.rerun()

# --- 7. INVENTORY & STOCK ADJUST ---
elif menu == "📦 Inventory":
    st.title("📦 Warehouse Control")
    v1, v2 = st.tabs(["Inventory List", "Stock Adjustment"])
    
    with v1:
        st.dataframe(db["inventory"], use_container_width=True)
        with st.expander("Add New Item"):
            with st.form("new_item"):
                ni = st.text_input("Product Name")
                nb = st.text_input("Brand")
                ncp = st.number_input("Cost Price", 0.0)
                nsp = st.number_input("Selling Price", 0.0)
                nq = st.number_input("Qty", 0)
                if st.form_submit_button("Save Item"):
                    new_row = pd.DataFrame([{"Product Name": ni, "Brand": nb, "Cost Price": ncp, "Selling Price": nsp, "Stock": nq}])
                    pd.concat([db["inventory"], new_row], ignore_index=True).to_csv(FILES["inventory"], index=False)
                    st.rerun()

    with v2:
        if not db["inventory"].empty:
            with st.form("adj"):
                target = st.selectbox("Select Item", db["inventory"]["Product Name"].tolist())
                cur = db["inventory"].loc[db["inventory"]["Product Name"] == target, "Stock"].values[0]
                st.write(f"Current Stock: {cur}")
                amt = st.number_input("Amount to add/remove (+/-)", 0)
                if st.form_submit_button("Update Stock"):
                    db["inventory"].loc[db["inventory"]["Product Name"] == target, "Stock"] += amt
                    db["inventory"].to_csv(FILES["inventory"], index=False)
                    st.success("Stock Level Updated!")
                    st.rerun()

# --- 8. ADMIN ---
elif menu == "⚙️ Admin":
    st.title("⚙️ Staff Management")
    st.dataframe(db["users"][["username", "role"]], use_container_width=True)
    with st.form("ch_pass"):
        st.write("Update User Password")
        target_u = st.selectbox("Select User", db["users"]["username"].tolist())
        new_p = st.text_input("New Password", type="password")
        if st.form_submit_button("Save Password"):
            db["users"].loc[db["users"]["username"] == target_u, "password"] = new_p
            db["users"].to_csv(FILES["users"], index=False)
            st.success("Password Updated!")
            st.rerun()