import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import urllib.parse

# --- 1. SYSTEM IDENTITY & BRANDING ---
COMPANY_NAME = "LOG MASTER VENTURES"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"

FILES = {
    "sales": "lmv_sales.csv", 
    "inventory": "lmv_stock.csv", 
    "users": "lmv_users.csv",
    "claims": "lmv_claims.csv" 
}

HEADERS = {
    "sales": ["Invoice_ID", "Timestamp", "Item", "Qty", "Price", "Total", "Staff", "Cust_Name", "Cust_Phone", "IMEI_Serial", "Warranty_Expiry", "Extended_Warranty"],
    "inventory": ["Product Name", "Selling Price", "Stock", "Min_Stock", "Warranty_Months"],
    "users": ["username", "password", "role"],
    "claims": ["Claim_ID", "Date_In", "IMEI_Serial", "Cust_Name", "Fault", "Warranty_Status", "Parts_Cost", "Labor_Charge", "Total_Bill", "Repair_Profit", "Status", "Date_Out"]
}

# --- 2. THE SILENT HEALER ---
def load_and_fix():
    data = {}
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        
        try:
            df = pd.read_csv(path)
        except:
            df = pd.DataFrame(columns=HEADERS[key])
        
        # Ensure structural integrity to prevent blank tabs
        missing = [c for c in HEADERS[key] if c not in df.columns]
        if missing:
            for col in missing:
                df[col] = 0.0 if col in ["Parts_Cost", "Labor_Charge", "Total_Bill", "Repair_Profit", "Selling Price", "Stock", "Total", "Qty"] else "N/A"
            df.to_csv(path, index=False)
        data[key] = df
    return data

# Force fresh data load
db = load_and_fix()

# --- 3. UI CONFIG ---
st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="🛡️")

# --- 4. SECURITY ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title(f"🔐 {COMPANY_NAME} Admin Gate")
    u = st.text_input("Admin ID").upper().strip()
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.auth, st.session_state.user = True, u
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 5. NAVIGATION ---
nav = st.sidebar.radio("Navigate", ["📊 Dashboard", "🛒 Sales POS", "🔧 Repair & Warranty", "📦 Inventory"])

if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

# --- 6. MODULES ---

if nav == "📊 Dashboard":
    st.title("📊 Business Intelligence")
    # Fillna(0) is critical here so metrics don't break
    sales_total = db["sales"]["Total"].fillna(0).sum()
    repair_profit = db["claims"]["Repair_Profit"].fillna(0).sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sales Revenue", f"GHS {sales_total:,.2f}")
    c2.metric("Repair Profit", f"GHS {repair_profit:,.2f}")
    c3.metric("Total Income", f"GHS {sales_total + repair_profit:,.2f}")

    if not db["claims"].empty:
        st.subheader("Financial Breakdown")
        fig = px.pie(values=[db["claims"]["Parts_Cost"].sum(), db["claims"]["Repair_Profit"].sum()], 
                     names=['Parts Cost', 'Labor Profit'], hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

elif nav == "🔧 Repair & Warranty":
    st.title("🔧 Repair Manager")
    t1, t2 = st.tabs(["🆕 New Job", "📈 Logs"])
    
    with t1:
        imei = st.text_input("IMEI / Serial")
        c_name = ""
        if imei:
            # Force string comparison to find records reliably
            match = db["sales"][db["sales"]["IMEI_Serial"].astype(str) == str(imei)]
            if not match.empty:
                last_s = match.iloc[-1]
                st.success(f"Customer Found: {last_s['Cust_Name']} | Warranty Expiry: {last_s['Warranty_Expiry']}")
                c_name = last_s["Cust_Name"]

            with st.form("repair_form"):
                cust = st.text_input("Name", value=c_name)
                fault = st.text_input("Fault")
                c1, c2 = st.columns(2)
                p_cost = c1.number_input("Parts Cost (GHS)", min_value=0.0)
                l_charge = c2.number_input("Labor Charge (GHS)", min_value=0.0)
                
                if st.form_submit_button("Save Job"):
                    new_r = pd.DataFrame([{
                        "Claim_ID": f"REP-{datetime.now().strftime('%d%H%M')}",
                        "Date_In": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "IMEI_Serial": imei, "Cust_Name": cust, "Fault": fault,
                        "Warranty_Status": "Manual Check", "Parts_Cost": p_cost,
                        "Labor_Charge": l_charge, "Total_Bill": p_cost + l_charge,
                        "Repair_Profit": l_charge, "Status": "Received", "Date_Out": ""
                    }])
                    pd.concat([db["claims"], new_r], ignore_index=True).to_csv(FILES["claims"], index=False)
                    st.success("Repair Job Saved")
                    st.rerun()
    with t2:
        st.dataframe(db["claims"], use_container_width=True)

elif nav == "🛒 Sales POS":
    st.title("🛒 Sales Terminal")
    if db["inventory"].empty:
        st.error("No items in inventory.")
    else:
        with st.form("pos_form"):
            prod = st.selectbox("Product", db["inventory"]["Product Name"].tolist())
            cust = st.text_input("Customer Name")
            imei_s = st.text_input("IMEI / Serial")
            qty = st.number_input("Qty", min_value=1)
            if st.form_submit_button("Complete Sale"):
                price = db["inventory"][db["inventory"]["Product Name"] == prod].iloc[0]["Selling Price"]
                exp = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
                new_s = pd.DataFrame([{
                    "Invoice_ID": f"INV-{datetime.now().strftime('%M%S')}", "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Item": prod, "Qty": qty, "Price": price, "Total": price * qty, "Staff": st.session_state.user,
                    "Cust_Name": cust, "Cust_Phone": "N/A", "IMEI_Serial": imei_s, "Warranty_Expiry": exp, "Extended_Warranty": "No"
                }])
                pd.concat([db["sales"], new_s], ignore_index=True).to_csv(FILES["sales"], index=False)
                st.rerun()

elif nav == "📦 Inventory":
    st.title("📦 Inventory")
    st.dataframe(db["inventory"], use_container_width=True)
    with st.expander("Add Stock"):
        with st.form("add_inv"):
            n, p, s = st.text_input("Name"), st.number_input("Price"), st.number_input("Qty")
            if st.form_submit_button("Add"):
                new_i = pd.DataFrame([{"Product Name": n, "Selling Price": p, "Stock": s, "Min_Stock": 5, "Warranty_Months": 12}])
                pd.concat([db["inventory"], new_i], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()