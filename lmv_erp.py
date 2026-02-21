import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. SETTINGS & BRANDING ---
COMPANY = "LOG MASTER VENTURES"
ADMIN_USER = "ADMIN"
ADMIN_PASS = "Premium@09"

# Database file paths
FILES = {
    "sales": "lmv_sales.csv", 
    "inventory": "lmv_stock.csv", 
    "claims": "lmv_claims.csv" 
}

# Protected Column Headers (Integrity Check)
HEADERS = {
    "sales": ["Invoice_ID", "Timestamp", "Item", "Qty", "Price", "Total", "Staff", "Cust_Name", "IMEI_Serial", "Warranty_Expiry"],
    "inventory": ["Product Name", "Selling Price", "Stock", "Min_Stock"],
    "claims": ["Claim_ID", "Date_In", "IMEI_Serial", "Cust_Name", "Fault", "Parts_Cost", "Labor_Charge", "Total_Bill", "Repair_Profit", "Status"]
}

# --- 2. DATA GUARDIAN ENGINE (Deep Error Check) ---
def load_and_fix():
    data = {}
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        
        try:
            df = pd.read_csv(path)
        except:
            df = pd.DataFrame(columns=HEADERS[key])
            
        # Ensure every single column exists to prevent "Tab Crashes"
        for col in HEADERS[key]:
            if col not in df.columns:
                df[col] = 0.0 if any(x in col for x in ["Price", "Total", "Profit", "Cost", "Stock"]) else "N/A"
        data[key] = df
    return data

db = load_and_fix()

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title=COMPANY, layout="wide", page_icon="🛡️")

# --- 4. LOGIN GATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title(f"🔐 {COMPANY} Gate")
    u = st.text_input("Admin ID").upper().strip()
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == ADMIN_USER and p == ADMIN_PASS:
            st.session_state.auth, st.session_state.user = True, u
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 5. THE "NEVER-VANISH" NAVIGATION ---
# I have grouped these 5 specific modules into a fixed list
st.sidebar.title(f"🛡️ {COMPANY}")
menu_options = ["📊 Dashboard", "🛒 Sales POS", "🔧 Repair Center", "📦 Inventory", "⚙️ Admin Tools"]
menu = st.sidebar.radio("Navigate System", menu_options)

st.sidebar.divider()
st.sidebar.write(f"User: {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

# --- 6. MODULES LOGIC ---

# MODULE 1: DASHBOARD
if menu == "📊 Dashboard":
    st.title("📊 Business Intelligence")
    col1, col2, col3 = st.columns(3)
    s_total = db["sales"]["Total"].fillna(0).sum()
    r_profit = db["claims"]["Repair_Profit"].fillna(0).sum()
    col1.metric("POS Revenue", f"GHS {s_total:,.2f}")
    col2.metric("Repair Profit", f"GHS {r_profit:,.2f}")
    col3.metric("Total Income", f"GHS {s_total + r_profit:,.2f}")
    st.subheader("Recent Sales Activity")
    st.dataframe(db["sales"].tail(10), use_container_width=True)

# MODULE 2: SALES POS
elif menu == "🛒 Sales POS":
    st.title("🛒 Sales Terminal")
    if db["inventory"].empty:
        st.error("Inventory empty. Please add items first.")
    else:
        with st.form("pos"):
            item = st.selectbox("Product", db["inventory"]["Product Name"].tolist())
            cust = st.text_input("Customer Name")
            imei = st.text_input("IMEI / Serial")
            qty = st.number_input("Qty", min_value=1, step=1)
            if st.form_submit_button("Finalize Sale"):
                stock = db["inventory"][db["inventory"]["Product Name"] == item].iloc[0]
                if stock["Stock"] < qty:
                    st.error("Insufficient Stock!")
                else:
                    price = stock["Selling Price"]
                    exp = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
                    new_sale = pd.DataFrame([{
                        "Invoice_ID": f"INV-{datetime.now().strftime('%M%S')}", "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Item": item, "Qty": qty, "Price": price, "Total": price * qty, "Staff": st.session_state.user,
                        "Cust_Name": cust, "IMEI_Serial": imei, "Warranty_Expiry": exp
                    }])
                    db["inventory"].loc[db["inventory"]["Product Name"] == item, "Stock"] -= qty
                    db["inventory"].to_csv(FILES["inventory"], index=False)
                    pd.concat([db["sales"], new_sale], ignore_index=True).to_csv(FILES["sales"], index=False)
                    st.success("Sale Recorded!")
                    st.rerun()

# MODULE 3: REPAIR CENTER
elif menu == "🔧 Repair Center":
    st.title("🔧 Repair Management")
    t1, t2 = st.tabs(["Log New Job", "Repair Logs"])
    with t1:
        imei_s = st.text_input("Scan/Type IMEI")
        c_val = ""
        if imei_s:
            match = db["sales"][db["sales"]["IMEI_Serial"].astype(str) == str(imei_s)]
            if not match.empty:
                st.success(f"Customer: {match.iloc[-1]['Cust_Name']} | Warranty: {match.iloc[-1]['Warranty_Expiry']}")
                c_val = match.iloc[-1]['Cust_Name']
        with st.form("repair"):
            cn = st.text_input("Customer", value=c_val)
            fl = st.text_input("Fault")
            pc, lc = st.columns(2)
            p_cost = pc.number_input("Parts Cost")
            l_charge = lc.number_input("Labor Profit")
            if st.form_submit_button("Save Job"):
                new_rep = pd.DataFrame([{
                    "Claim_ID": f"REP-{datetime.now().strftime('%d%H')}", "Date_In": datetime.now().strftime("%Y-%m-%d"),
                    "IMEI_Serial": imei_s, "Cust_Name": cn, "Fault": fl, "Parts_Cost": p_cost, "Labor_Charge": l_charge,
                    "Total_Bill": p_cost+l_charge, "Repair_Profit": l_charge, "Status": "Received"
                }])
                pd.concat([db["claims"], new_rep], ignore_index=True).to_csv(FILES["claims"], index=False)
                st.rerun()
    with t2:
        st.dataframe(db["claims"], use_container_width=True)

# MODULE 4: INVENTORY
elif menu == "📦 Inventory":
    st.title("📦 Inventory Management")
    search = st.text_input("Search Products...").lower()
    view_df = db["inventory"][db["inventory"]["Product Name"].str.lower().str.contains(search)]
    st.dataframe(view_df, use_container_width=True)
    with st.expander("Add Stock"):
        with st.form("inv"):
            n, p, s = st.text_input("Name"), st.number_input("Price"), st.number_input("Stock")
            if st.form_submit_button("Add"):
                new_i = pd.DataFrame([{"Product Name": n, "Selling Price": p, "Stock": s, "Min_Stock": 5}])
                pd.concat([db["inventory"], new_i], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()

# MODULE 5: ADMIN TOOLS
elif menu == "⚙️ Admin Tools":
    st.title("⚙️ Admin & Database Control")
    st.subheader("Database Backups")
    for key in FILES.keys():
        csv = db[key].to_csv(index=False).encode('utf-8')
        st.download_button(f"Download {key.upper()} File", csv, f"lmv_{key}.csv", "text/csv")
    
    st.divider()
    if st.button("Reset Entire System (CAUTION)"):
        if st.checkbox("I am sure I want to delete everything"):
            for key, path in FILES.items():
                pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
            st.success("All data cleared.")
            st.rerun()