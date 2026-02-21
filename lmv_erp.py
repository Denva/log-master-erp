import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. SECURE CONFIGURATION ---
# This looks for your "Secrets" online. If not found, it uses the local defaults.
COMPANY_NAME = "LOG MASTER VENTURES"
COMPANY_PHONE = st.secrets.get("COMPANY_PHONE", "0545531632")
COMPANY_EMAIL = st.secrets.get("COMPANY_EMAIL", "logmastergh@gmail.com")
MASTER_PASS = st.secrets.get("ADMIN_PASSWORD", "master77")

st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="⚖️")

# --- 2. DATA FILING SYSTEM ---
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR = "product_images"
BACKUP_DIR = "backups"

HEADERS = {
    "sales": [
        "Timestamp", "Type", "Item", "Qty", "Price", "Total", 
        "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", 
        "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"
    ],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

# --- 3. SYSTEM INITIALIZATION ---
def init_system():
    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)
    
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            missing = [c for c in HEADERS[key] if c not in df.columns]
            if missing:
                for col in missing:
                    df[col] = 0.0 if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"] else ("" if col != "Min_Stock" else 2.0)
                df.to_csv(path, index=False)
    
    # Ensure Admin exists with Secure Password
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty:
        pd.DataFrame([{"username": "ADMIN", "password": MASTER_PASS, "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_system()

# --- 4. RECEIPT SYSTEM ---
def get_receipt(row):
    return f"""
    <div style="border:2px solid black; padding:15px; width:280px; font-family:monospace; margin:auto; background:white; color:black;">
        <h3 style="text-align:center;">{COMPANY_NAME}</h3>
        <p style="text-align:center; font-size:10px;">{COMPANY_PHONE}</p>
        <hr>
        <p style="font-size:11px;"><b>Date:</b> {row['Timestamp']}<br><b>Staff:</b> {row['Staff']}</p>
        <hr>
        <p style="font-size:11px;"><b>Item:</b> {row['Item']}</p>
        <table style="width:100%; font-size:13px;">
            <tr><td><b>TOTAL</b></td><td style="text-align:right;"><b>GHS {row['Total']:.2f}</b></td></tr>
        </table>
        <hr>
        <button onclick="window.print()" style="width:100%; background:black; color:white; border:none; padding:5px;">PRINT</button>
    </div>
    """

# --- 5. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title(f"⚖️ {COMPANY_NAME} Online")
    t1, t2 = st.tabs(["🔒 Login", "🔎 Repair Check"])
    with t1:
        with st.form("login"):
            u = st.text_input("Username").upper().strip()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Access System"):
                udb = pd.read_csv(FILES["users"])
                match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                    st.rerun()
                else: st.error("Access Denied")
    with t2:
        q = st.text_input("Enter Phone/IMEI")
        if q:
            sdb = pd.read_csv(FILES["sales"])
            found = sdb[(sdb['Cust_Phone'].astype(str) == q) | (sdb['IMEI_Serial'].astype(str) == q)]
            for _, r in found.iterrows(): st.info(f"**{r['Item']}**: {r['Status']}")
    st.stop()

# --- 6. NAVIGATION ---
sales_df = pd.read_csv(FILES["sales"])
stock_df = pd.read_csv(FILES["inventory"])
users_df = pd.read_csv(FILES["users"])

st.sidebar.title(f"👤 {st.session_state.user}")
nav = ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"]
if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
choice = st.sidebar.radio("Navigation", nav)

if st.sidebar.button("Log Out"):
    st.session_state.auth = False
    st.rerun()

# --- 7. MODULES ---

if choice == "📊 Insights":
    st.header("📊 Business Insights")
    low = stock_df[stock_df['Stock'] <= stock_df['Min_Stock']]
    if not low.empty: st.error(f"🚨 LOW STOCK: {len(low)} items need attention!")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock Value", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Total Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        c3.metric("Net Profit", f"GHS {sales_df['Profit'].sum():,.2f}")
    st.dataframe(sales_df.tail(10), use_container_width=True)

elif choice == "🛒 Sales POS":
    st.header("🛒 Sales")
    with st.form("pos", clear_on_submit=True):
        ca, cb = st.columns([2, 1])
        with ca:
            cn, cp = st.text_input("Customer Name"), st.text_input("Phone")
            items = stock_df[stock_df['Stock'] > 0]['Product Name'].tolist()
            item = st.selectbox("Select Product", items if items else ["No Stock"])
            qty, pr = st.number_input("Quantity", 1), st.number_input("Price", 0.0)
            sn, n = st.text_input("IMEI/Serial"), st.text_input("Notes")
        with cb:
            if item != "No Stock":
                path = stock_df[stock_df['Product Name'] == item]['Image_Path'].values[0]
                if pd.notnull(path) and os.path.exists(str(path)): st.image(str(path), width=150)
        
        if st.form_submit_button("Complete Sale"):
            cost = float(stock_df[stock_df['Product Name'] == item]['Cost Price'].iloc[0])
            total = qty * pr
            new_row = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT", "Item": item,
                "Qty": qty, "Price": pr, "Total": total, "Cost": cost*qty, "Profit": total-(cost*qty),
                "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": sn,
                "Device_Fault": "", "Parts_Needed": "", "Status": "Sold", "Notes": n
            }
            pd.concat([sales_df, pd.DataFrame([new_row])], ignore_index=True).to_csv(FILES["sales"], index=False)
            stock_df.loc[stock_df['Product Name'] == item, 'Stock'] -= qty
            stock_df.to_csv(FILES["inventory"], index=False)
            st.success("Sale Recorded!")
            st.rerun()

elif choice == "🛠️ Repairs":
    st.header("🛠️ Repair Booking")
    with st.form("rep", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cn, cp = st.text_input("Customer Name"), st.text_input("Phone")
            dev, sn = st.text_input("Model"), st.text_input("IMEI/Serial")
        with c2:
            fault, parts = st.text_area("Fault"), st.text_area("Parts")
            fee = st.number_input("Total Fee", 0.0)
        if st.form_submit_button("Book Job"):
            new_r = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "SERVICE", "Item": dev,
                "Qty": 1, "Price": fee, "Total": fee, "Cost": 0.0, "Profit": fee,
                "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": sn,
                "Device_Fault": fault, "Parts_Needed": parts, "Status": "Repairing", "Notes": ""
            }
            pd.concat([sales_df, pd.DataFrame([new_r])], ignore_index=True).to_csv(FILES["sales"], index=False)
            st.success("Repair Logged!")
            st.rerun()

elif choice == "📦 Inventory":
    st.header("📦 Inventory")
    t1, t2 = st.tabs(["Stock List", "Add New"])
    with t1:
        st.dataframe(stock_df, use_container_width=True, column_config={"Image_Path": st.column_config.ImageColumn("Preview")})
    with t2:
        with st.form("add_i"):
            n, b, cp, sp, s = st.text_input("Name"), st.text_input("Brand"), st.number_input("Cost"), st.number_input("Sell"), st.number_input("Stock")
            up = st.file_uploader("Image", type=['jpg','png'])
            if st.form_submit_button("Save Product"):
                path = os.path.join(IMG_DIR, f"{n.replace(' ','_')}.png") if up else ""
                if up: Image.open(up).save(path)
                pd.concat([stock_df, pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": 2, "Image_Path": path}])], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()

elif choice == "⚙️ Admin":
    st.header("⚙️ Admin Settings")
    tab_m, tab_u = st.tabs(["📑 Orders", "👥 User Control"])
    with tab_m:
        q = st.text_input("Search (Name/IMEI)").lower()
        f_df = sales_df[sales_df.apply(lambda r: q in r.astype(str).str.lower().values, axis=1)] if q else sales_df.tail(10)
        if not f_df.empty:
            idx = st.selectbox("Select ID", f_df.index)
            r = sales_df.loc[idx]
            st.write(f"**Fault:** {r['Device_Fault']} | **Staff:** {r['Staff']}")
            ca, cb = st.columns(2)
            with ca:
                if st.button("📄 Receipt"): st.markdown(get_receipt(r), unsafe_allow_html=True)
            with cb:
                wa_url = f"https://wa.me/{r['Cust_Phone']}?text=Hello {r['Cust_Name']}, your {r['Item']} is {r['Status']}."
                st.markdown(f'<a href="{urllib.parse.quote(wa_url, safe='/:?=&')}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%;">WhatsApp</button></a>', unsafe_allow_html=True)
            with st.form("up_s"):
                ns = st.selectbox("Status", ["Repairing", "Ready", "Collected", "Sold", "Cancelled"])
                if st.form_submit_button("Update"):
                    sales_df.at[idx, 'Status'] = ns
                    sales_df.to_csv(FILES["sales"], index=False)
                    st.rerun()
    with tab_u:
        st.subheader("Manage Staff")
        st.table(users_df[['username', 'role']])
        with st.form("add_u"):
            un, up, ur = st.text_input("Username").upper(), st.text_input("Pass"), st.selectbox("Role", ["STAFF", "OWNER"])
            if st.form_submit_button("Add Staff"):
                pd.concat([users_df, pd.DataFrame([{"username": un, "password": up, "role": ur}])], ignore_index=True).to_csv(FILES["users"], index=False)
                st.rerun()