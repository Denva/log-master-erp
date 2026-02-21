import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. SETTINGS & BRANDING ---
COMPANY = "LOG MASTER VENTURES"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"

FILES = {
    "sales": "lmv_sales.csv", 
    "inventory": "lmv_stock.csv", 
    "claims": "lmv_claims.csv" 
}

# EXACT HEADERS for your business logic
HEADERS = {
    "sales": ["Invoice_ID", "Timestamp", "Item", "Qty", "Price", "Total", "Staff", "Cust_Name", "IMEI_Serial", "Warranty_Expiry"],
    "inventory": ["Product Name", "Selling Price", "Stock", "Min_Stock"],
    "claims": ["Claim_ID", "Date_In", "IMEI_Serial", "Cust_Name", "Fault", "Parts_Cost", "Labor_Charge", "Total_Bill", "Repair_Profit", "Status"]
}

# --- 2. DATA ENGINE (The "Silent Healer") ---
def load_data():
    data = {}
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        df = pd.read_csv(path)
        # Auto-fix missing columns if any
        for col in HEADERS[key]:
            if col not in df.columns:
                df[col] = 0.0 if "Price" in col or "Total" in col or "Profit" in col or "Cost" in col or "Stock" in col else ""
        data[key] = df
    return data

db = load_data()

# --- 3. UI LAYOUT ---
st.set_page_config(page_title=COMPANY, layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title(f"🔐 {COMPANY} Login")
    u = st.text_input("User").upper()
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.auth, st.session_state.user = True, u
            st.rerun()
        else: st.error("Wrong credentials")
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Go To:", ["📊 Dashboard", "🛒 Sales POS", "🔧 Repair Center", "📦 Inventory"])
st.sidebar.divider()
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

# --- 5. MODULES ---

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title(f"📊 {COMPANY} Overview")
    sales_total = db["sales"]["Total"].sum()
    repair_profit = db["claims"]["Repair_Profit"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales", f"GHS {sales_total:,.2f}")
    c2.metric("Repair Profit (Labor)", f"GHS {repair_profit:,.2f}")
    c3.metric("Total Cash Flow", f"GHS {sales_total + repair_profit:,.2f}")
    
    st.subheader("Recent Sales")
    st.table(db["sales"].tail(5))

# --- SALES POS ---
elif menu == "🛒 Sales POS":
    st.title("🛒 Sell a Phone/Item")
    if db["inventory"].empty:
        st.error("No items in stock. Add them in 'Inventory' first.")
    else:
        with st.form("sale_form"):
            item = st.selectbox("Select Product", db["inventory"]["Product Name"].tolist())
            cust = st.text_input("Customer Name")
            imei = st.text_input("IMEI / Serial Number")
            qty = st.number_input("Qty", min_value=1, value=1)
            
            if st.form_submit_button("Complete Sale"):
                row = db["inventory"][db["inventory"]["Product Name"] == item].iloc[0]
                if row["Stock"] < qty:
                    st.error("Not enough stock!")
                else:
                    price = row["Selling Price"]
                    expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
                    new_s = pd.DataFrame([{
                        "Invoice_ID": f"INV-{datetime.now().strftime('%M%S')}",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Item": item, "Qty": qty, "Price": price, "Total": price * qty,
                        "Staff": st.session_state.user, "Cust_Name": cust, 
                        "IMEI_Serial": imei, "Warranty_Expiry": expiry
                    }])
                    # Deduct stock and save
                    db["inventory"].loc[db["inventory"]["Product Name"] == item, "Stock"] -= qty
                    db["inventory"].to_csv(FILES["inventory"], index=False)
                    pd.concat([db["sales"], new_s], ignore_index=True).to_csv(FILES["sales"], index=False)
                    st.success(f"Sold! Warranty ends: {expiry}")
                    st.rerun()

# --- REPAIR CENTER ---
elif menu == "🔧 Repair Center":
    st.title("🔧 Repairs & Service")
    t1, t2 = st.tabs(["New Job", "All Repairs"])
    
    with t1:
        imei_check = st.text_input("Search IMEI for Warranty")
        suggested_name = ""
        if imei_check:
            past_sale = db["sales"][db["sales"]["IMEI_Serial"].astype(str) == str(imei_check)]
            if not past_sale.empty:
                st.success(f"Customer: {past_sale.iloc[-1]['Cust_Name']} | Warranty until: {past_sale.iloc[-1]['Warranty_Expiry']}")
                suggested_name = past_sale.iloc[-1]['Cust_Name']

        with st.form("rep_form"):
            cn = st.text_input("Customer Name", value=suggested_name)
            flt = st.text_input("Fault Description")
            c1, c2 = st.columns(2)
            pc = c1.number_input("Parts Cost (GHS)", min_value=0.0)
            lc = c2.number_input("Labor Charge (GHS)", min_value=0.0)
            
            if st.form_submit_button("Log Job"):
                new_r = pd.DataFrame([{
                    "Claim_ID": f"REP-{datetime.now().strftime('%d%H')}",
                    "Date_In": datetime.now().strftime("%Y-%m-%d"),
                    "IMEI_Serial": imei_check, "Cust_Name": cn, "Fault": flt,
                    "Parts_Cost": pc, "Labor_Charge": lc, "Total_Bill": pc+lc,
                    "Repair_Profit": lc, "Status": "Received"
                }])
                pd.concat([db["claims"], new_r], ignore_index=True).to_csv(FILES["claims"], index=False)
                st.success("Repair Logged!")
                st.rerun()
    with t2:
        st.dataframe(db["claims"], use_container_width=True)

# --- INVENTORY ---
elif menu == "📦 Inventory":
    st.title("📦 Inventory Management")
    search = st.text_input("🔍 Search items...", "").lower()
    filtered = db["inventory"][db["inventory"]["Product Name"].str.lower().str.contains(search)]
    
    st.dataframe(filtered, use_container_width=True)
    
    with st.expander("Add New Item"):
        with st.form("inv"):
            n = st.text_input("Product Name")
            p = st.number_input("Selling Price", min_value=0.0)
            s = st.number_input("Initial Stock", min_value=0)
            if st.form_submit_button("Save Item"):
                new_i = pd.DataFrame([{"Product Name": n, "Selling Price": p, "Stock": s, "Min_Stock": 5}])
                pd.concat([db["inventory"], new_i], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()