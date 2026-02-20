import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURATION & IDENTITY ---
st.set_page_config(page_title="LOG MASTER VENTURES", layout="wide", page_icon="⚖️")
COMPANY_NAME = "LOG MASTER VENTURES"
COMPANY_PHONE = "0545531632"
COMPANY_EMAIL = "logmastergh@gmail.com"

# --- 2. DATA FILING SYSTEM ---
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR = "product_images"
BACKUP_DIR = "backups"

# THE MASTER STRUCTURE - DO NOT ALTER
HEADERS = {
    "sales": [
        "Timestamp", "Type", "Item", "Qty", "Price", "Total", 
        "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", 
        "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"
    ],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

# --- 3. DEEP SYSTEM INITIALIZATION ---
def init_system():
    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)
    
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            # Integrity Check: Ensure every required column exists
            missing_cols = [c for c in HEADERS[key] if c not in df.columns]
            if missing_cols:
                for col in missing_cols:
                    if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"]:
                        df[col] = 0.0
                    elif col == "Min_Stock":
                        df[col] = 2.0
                    else:
                        df[col] = "N/A"
                df.to_csv(path, index=False)
    
    # Automatic Daily Backup
    today = datetime.now().strftime("%Y-%m-%d")
    for key, path in FILES.items():
        b_path = os.path.join(BACKUP_DIR, f"{today}_{path}")
        if not os.path.exists(b_path) and os.path.exists(path):
            shutil.copy(path, b_path)
    
    # Create Default Admin if missing
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty:
        pd.DataFrame([{"username": "ADMIN", "password": "master77", "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_system()

# --- 4. UTILITIES ---
def get_receipt(row):
    return f"""
    <div style="border:2px solid black; padding:15px; width:280px; font-family:monospace; background:white; color:black;">
        <h3 style="text-align:center;">{COMPANY_NAME}</h3>
        <p style="text-align:center; font-size:10px;">{COMPANY_PHONE} | {COMPANY_EMAIL}</p>
        <hr style="border-top: 1px dashed black;">
        <p style="font-size:11px;"><b>Date:</b> {row['Timestamp']}<br><b>Staff:</b> {row['Staff']}<br><b>Cust:</b> {row['Cust_Name']}</p>
        <hr style="border-top: 1px dashed black;">
        <p style="font-size:11px;"><b>Item:</b> {row['Item']}<br><b>IMEI:</b> {row['IMEI_Serial']}</p>
        {f"<p style='font-size:10px;'><b>Fault:</b> {row['Device_Fault']}</p>" if row['Type'] == 'SERVICE' else ""}
        <hr style="border-top: 1px dashed black;">
        <table style="width:100%; font-size:13px;">
            <tr><td><b>TOTAL</b></td><td style="text-align:right;"><b>GHS {row['Total']:.2f}</b></td></tr>
        </table>
        <hr style="border-top: 1px dashed black;">
        <p style="text-align:center; font-size:9px;">No Refund After Sales. Thank You!</p>
        <button onclick="window.print()" style="width:100%; background:black; color:white; border:none; padding:5px; cursor:pointer;">PRINT</button>
    </div>
    """

# --- 5. ACCESS CONTROL ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title(f"⚖️ {COMPANY_NAME}")
    tab_l, tab_t = st.tabs(["🔒 Staff Login", "🔎 Repair Tracker"])
    with tab_l:
        with st.form("login"):
            u = st.text_input("User").upper().strip()
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("Log In"):
                udb = pd.read_csv(FILES["users"])
                match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                    st.rerun()
                else: st.error("Invalid Credentials")
    with tab_t:
        track_q = st.text_input("Enter Phone/IMEI").strip()
        if track_q:
            sdb = pd.read_csv(FILES["sales"])
            found = sdb[(sdb['Cust_Phone'].astype(str) == track_q) | (sdb['IMEI_Serial'].astype(str) == track_q)]
            for _, r in found.iterrows(): st.info(f"**{r['Item']}**: {r['Status']}")
    st.stop()

# --- 6. CORE LOGIC ---
sales_df = pd.read_csv(FILES["sales"])
stock_df = pd.read_csv(FILES["inventory"])
users_df = pd.read_csv(FILES["users"])

st.sidebar.title(f"👋 {st.session_state.user}")
st.sidebar.info(f"Role: {st.session_state.role}")
nav = ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"]
if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
choice = st.sidebar.radio("Go To", nav)

if st.sidebar.button("Log Out"):
    st.session_state.auth = False
    st.rerun()

# --- 7. MODULES ---

if choice == "📊 Insights":
    st.header("📊 Dashboard")
    low_stock = stock_df[stock_df['Stock'] <= stock_df['Min_Stock']]
    if not low_stock.empty: st.error(f"⚠️ {len(low_stock)} Items are Low on Stock!")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock Value", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        c3.metric("Profit", f"GHS {sales_df['Profit'].sum():,.2f}")
    st.subheader("Recent Sales Log")
    st.dataframe(sales_df.tail(15), use_container_width=True)

elif choice == "🛒 Sales POS":
    st.header("🛒 Sales Terminal")
    with st.form("pos_form", clear_on_submit=True):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            c_name, c_phone = st.text_input("Customer Name"), st.text_input("Customer Phone")
            items = stock_df[stock_df['Stock'] > 0]['Product Name'].tolist()
            item = st.selectbox("Product", items if items else ["Out of Stock"])
            q, p = st.number_input("Quantity", 1), st.number_input("Price (GHS)", 0.0)
            sn, n = st.text_input("IMEI / Serial"), st.text_input("Notes")
        with col_b:
            if item != "Out of Stock":
                img_p = stock_df[stock_df['Product Name'] == item]['Image_Path'].values[0]
                if pd.notnull(img_p) and os.path.exists(str(img_p)): st.image(str(img_p), width=180)
        
        if st.form_submit_button("Process Sale"):
            if item != "Out of Stock":
                cost = float(stock_df[stock_df['Product Name'] == item]['Cost Price'].iloc[0])
                total = q * p
                new_data = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT", "Item": item,
                    "Qty": q, "Price": p, "Total": total, "Cost": cost*q, "Profit": total-(cost*q),
                    "Staff": st.session_state.user, "Cust_Name": c_name, "Cust_Phone": c_phone,
                    "IMEI_Serial": sn, "Device_Fault": "", "Parts_Needed": "", "Status": "Sold", "Notes": n
                }
                pd.concat([sales_df, pd.DataFrame([new_data])], ignore_index=True).to_csv(FILES["sales"], index=False)
                stock_df.loc[stock_df['Product Name'] == item, 'Stock'] -= q
                stock_df.to_csv(FILES["inventory"], index=False)
                st.success("Sale Completed!")
                st.rerun()

elif choice == "🛠️ Repairs":
    st.header("🛠️ Repair Intake")
    with st.form("repair_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cn, cp = st.text_input("Customer Name"), st.text_input("Phone Number")
            dev, sn = st.text_input("Device Model"), st.text_input("IMEI / Serial")
        with c2:
            fault = st.text_area("Fault / Problem")
            parts = st.text_area("Parts Needed")
            fee = st.number_input("Estimated Fee", 0.0)
        if st.form_submit_button("Book Repair Job"):
            new_rep = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "SERVICE", "Item": dev,
                "Qty": 1, "Price": fee, "Total": fee, "Cost": 0.0, "Profit": fee,
                "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": sn,
                "Device_Fault": fault, "Parts_Needed": parts, "Status": "Repairing", "Notes": ""
            }
            pd.concat([sales_df, pd.DataFrame([new_rep])], ignore_index=True).to_csv(FILES["sales"], index=False)
            st.success("Repair Job Logged!")
            st.rerun()

elif choice == "📦 Inventory":
    st.header("📦 Inventory & Stock")
    t_view, t_add = st.tabs(["Stock List", "New Product"])
    with t_view:
        st.dataframe(stock_df, use_container_width=True, column_config={"Image_Path": st.column_config.ImageColumn("Preview")})
    with t_add:
        with st.form("add_item"):
            n, b, cp, sp, s = st.text_input("Name"), st.text_input("Brand"), st.number_input("Cost"), st.number_input("Sell"), st.number_input("Stock")
            ms = st.number_input("Min Stock Level", value=2)
            u = st.file_uploader("Image", type=['jpg','png'])
            if st.form_submit_button("Save Item"):
                path = os.path.join(IMG_DIR, f"{n.replace(' ','_')}.png") if u else ""
                if u: Image.open(u).save(path)
                pd.concat([stock_df, pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": ms, "Image_Path": path}])], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()

elif choice == "⚙️ Admin":
    st.header("⚙️ Owner Control Panel")
    t_orders, t_staff, t_sys = st.tabs(["📑 Order Management", "👥 Staff Control", "💾 System"])
    
    with t_orders:
        query = st.text_input("Search Customer/IMEI").lower()
        filtered = sales_df[sales_df.apply(lambda r: query in r.astype(str).str.lower().values, axis=1)] if query else sales_df.tail(10)
        if not filtered.empty:
            idx = st.selectbox("Choose Record", filtered.index)
            r = sales_df.loc[idx]
            st.write(f"**Fault:** {r['Device_Fault']} | **Staff:** {r['Staff']}")
            ca, cb = st.columns(2)
            with ca:
                if st.button("📄 Show Receipt"): st.markdown(get_receipt(r), unsafe_allow_html=True)
            with cb:
                wa_msg = f"LOG MASTER: Hello {r['Cust_Name']}, your {r['Item']} is {r['Status']}."
                st.markdown(f'<a href="https://wa.me/{r['Cust_Phone']}?text={urllib.parse.quote(wa_msg)}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%;">Notify WhatsApp</button></a>', unsafe_allow_html=True)
            
            with st.form("status_up"):
                new_s = st.selectbox("Set Status", ["Repairing", "Ready", "Collected", "Sold", "Cancelled"])
                if st.form_submit_button("Update Status"):
                    sales_df.at[idx, 'Status'] = new_s
                    sales_df.to_csv(FILES["sales"], index=False)
                    st.rerun()

    with t_staff:
        st.subheader("User Permissions")
        st.table(users_df[['username', 'role']])
        with st.form("add_user"):
            un, up, ur = st.text_input("New Username").upper(), st.text_input("Password"), st.selectbox("Role", ["STAFF", "OWNER"])
            if st.form_submit_button("Add Staff"):
                pd.concat([users_df, pd.DataFrame([{"username": un, "password": up, "role": ur}])], ignore_index=True).to_csv(FILES["users"], index=False)
                st.rerun()

    with t_sys:
        if st.button("🚀 Run Manual Backup Now"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            for k, p in FILES.items(): shutil.copy(p, os.path.join(BACKUP_DIR, f"MANUAL_{ts}_{p}"))
            st.success("System Data Safely Backed Up!")